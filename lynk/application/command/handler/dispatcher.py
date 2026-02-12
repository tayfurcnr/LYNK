from __future__ import annotations
from lynk.application.command.serializer.dispatcher import deserialize_command
from lynk.application.command.definitions import command_definitions
from lynk.shared.log.logger import logger
from lynk.application.command.handler.cache import get_cmd_idempotency_cache

def unknown(cmd_id: int, params: bytes, src_id: int, transaction_id: str = "", interface=None):
    logger.warning(f"[COMMAND] Unknown command ID {cmd_id} from SRC: {src_id} | Protobuf mapping missing.")
    if interface:
        from lynk.application.ack.tools.dispatcher import send_ack_invalid_cmd
        send_ack_invalid_cmd(interface, transaction_id, cmd_id, dst=src_id)

def handle_command(payload: bytes, frame_meta: dict, interface=None):
    """
    Parse and handle an incoming 'C' (Command) frame.

    Args:
        payload (bytes): Raw command payload.
        frame_meta (dict): Frame metadata including src_id, dst_id, etc.
        interface: Optional interface object to allow response sending.
    """
    try:
        src_id = frame_meta.get("src_id")
        data = deserialize_command(payload)

        cmd_id = data.get("command_id")
        params = data.get("params")
        transaction_id = data.get("transaction_id", "")  # Extract transaction_id

        if not isinstance(cmd_id, int):
            raise ValueError(f"Invalid command ID type: {type(cmd_id)}")

        if not isinstance(params, (bytes, dict)):
            raise ValueError(f"Invalid parameters format: expected bytes or dict, got {type(params)}")

        # --- IDEMPOTENCY CHECK ---
        # Check if we already processed this specific transaction from this source
        idempotency = get_cmd_idempotency_cache()
        if idempotency.is_processed(src_id, transaction_id):
            color = "\033[95m\033[1m"
            reset = "\033[0m"
            logger.warning(f"{color}[COMMAND] IDEMPOTENCY | DUPLICATE detected (TX_ID={transaction_id}). Skipping execution, resending.{reset}")
            if interface:
                from lynk.application.ack.tools.dispatcher import send_ack_ok
                send_ack_ok(interface, transaction_id, cmd_id, dst=src_id)
            return
        # -------------------------

        cmd_def = command_definitions.get(cmd_id)
        if cmd_def:
            param_str = params.hex() if isinstance(params, bytes) else str(params)
            dst_id = frame_meta.get("dst_id")
            color = "\033[92m\033[1m"
            reset = "\033[0m"
            logger.info(
                f"{color}[COMMAND] RECV | TYPE: {cmd_def.name} | SRC: {src_id} -> DST: {dst_id} | TX_ID: {transaction_id}{reset}"
            )
            cmd_label = cmd_def.name if cmd_def else f"CMD_ID:{cmd_id}"
            logger.info(
                f"{color}[COMMAND] {cmd_label} PARAMS: {param_str}{reset}"
            )
            try:
                cmd_def.handler(cmd_id, params, src_id, interface)
                logger.debug(f"[COMMAND] HANDLED | CMD: {cmd_id} ({cmd_def.name})") # Confirm return
                
                # Automatically send success ACK if not already handled
                # (Handlers can still send specific ACKs if they want, but this is the safety net)
                if interface:
                    from lynk.application.ack.tools.dispatcher import send_ack_ok
                    send_ack_ok(interface, transaction_id, cmd_id, dst=src_id)
            except Exception as e:
                logger.error(f"[COMMAND] HANDLER EXCEPTION | CMD: {cmd_id}: {e}")
                if interface:
                    from lynk.application.ack.tools.dispatcher import send_ack_execution_error
                    send_ack_execution_error(interface, transaction_id, cmd_id, dst=src_id)
                raise e
        else:
            unknown(cmd_id, params, src_id, transaction_id, interface)

    except Exception as e:
        logger.error(f"[COMMAND] ERROR | Failed to handle command: {e}")
        logger.debug(f"[COMMAND] Exception detail:", exc_info=True)
