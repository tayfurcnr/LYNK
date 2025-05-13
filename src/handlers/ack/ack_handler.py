from src.serializers.ack_serializer import deserialize_ack
from src.handlers.command.command_handler import command_definitions, CommandDefinition
from src.tools.ack.ack_tracker import register_ack
from src.tools.ack.ftp_ack_builder import COMMAND_IDS as FTP_COMMAND_IDS
from src.tools.log.logger import logger

# Status description map
status_map = {
    0: "SUCCESS",
    1: "INVALID_PARAMS",
    2: "UNSUPPORTED"
}

# Reverse map for FTP phases
FTP_PHASE_BY_ID = {v: k for k, v in FTP_COMMAND_IDS.items()}


def handle_ack(payload: bytes, frame_meta: dict, uart_handler=None):
    """
    Handles 'A' (ACK/NACK) type frames received in the mesh protocol.
    Logs the command status, source, and routing info.
    Also registers ACK into the ack_tracker system, including FTP phases.
    """
    # Log raw payload for debugging
    logger.debug(f"[ACK] RAW PAYLOAD: {payload.hex()}")

    # Parse header fields
    ack_code = payload[0]
    cmd_id    = payload[1]
    # Always take status from last byte to avoid indexing issues
    status_code = payload[-1]
    src_id    = frame_meta.get("src_id")
    dst_id    = frame_meta.get("dst_id")

    # FTP phase ACK/NACK işlemleri
    if cmd_id in FTP_COMMAND_IDS.values():
        is_ack = (ack_code == 0xAA)
        phase_name = FTP_PHASE_BY_ID.get(cmd_id, f"PHASE_{cmd_id}")
        # Determine tracker key
        if phase_name == "CHUNK":
            tracker_key = f"FTP_CHUNK_{status_code}"
        else:
            tracker_key = f"FTP_{phase_name}"

        # Register ACK/NACK (0 if ack else status code for nack)
        register_ack(tracker_key, src_id, 0 if is_ack else status_code)

        # Log FTP ACK/NACK
        ack_type = "ACK" if is_ack else "NACK"
        logger.info(
            f"[ACK] FTP {phase_name} {ack_type} received | SEQ: {status_code} | SRC: {src_id} -> DST: {dst_id}"
        )
        return

    # Generic command ACK/NACK işlemleri
    try:
        ack = deserialize_ack(payload)
        command    = ack["command_id"]
        is_ack     = (ack["ack_code"] == 0xAA)
        ack_type   = "ACK" if is_ack else "NACK"
        status_str = status_map.get(ack["status_code"], f"UNKNOWN({ack['status_code']})")

        # Resolve command name
        cmd_def = command_definitions.get(
            command,
            CommandDefinition(f"CMD_{command}", None)
        )
        cmd_name = cmd_def.name

        # Log generic ACK
        logger.info(
            f"[ACK] RECEIVED | TYPE: {ack_type} | CMD: {cmd_name} | STATUS: {status_str} "
            f"| SRC: {src_id} -> DST: {dst_id}"
        )
        if not is_ack:
            logger.warning(
                f"[ACK] FAILED | NACK received | CMD: {cmd_name} | STATUS: {status_str} "
                f"| SRC: {src_id} -> DST: {dst_id}"
            )

        # Register in ack tracker
        register_ack(cmd_name, src_id, ack["status_code"])

    except Exception as e:
        logger.error(f"[ACK] ERROR | Failed to parse ACK payload: {e} | RAW: {payload}")