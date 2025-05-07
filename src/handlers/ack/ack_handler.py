# src/handlers/ack_handler.py

from src.serializers.ack_serializer import deserialize_ack
from src.handlers.command.command_handler import command_definitions, CommandDefinition
from src.tools.ack.ack_tracker import register_ack
from src.tools.log.logger import logger

# Status description map
status_map = {
    0: "SUCCESS",
    1: "INVALID_PARAMS",
    2: "UNSUPPORTED"
}

def handle_ack(payload: bytes, frame_meta: dict, uart_handler=None):
    """
    Handles 'A' (ACK/NACK) type frames received in the mesh protocol.
    Logs the command status, source, and routing info.
    Also registers ACK into the ack_tracker system.
    """
    try:
        ack = deserialize_ack(payload)
        src_id = frame_meta["src_id"]
        dst_id = frame_meta["dst_id"]

        is_ack = ack["ack_code"] == 0xAA
        ack_type = "ACK" if is_ack else "NACK"
        status_str = status_map.get(ack["status_code"], f"UNKNOWN({ack['status_code']})")

        # Komut adını ID'den çözümle
        cmd_def = command_definitions.get(
            ack["command_id"],
            CommandDefinition(f"CMD_{ack['command_id']}", None)
        )
        cmd_name = cmd_def.name

        logger.info(
            f"[ACK] RECEIVED | TYPE: {ack_type} | CMD: {cmd_name} | STATUS: {status_str} "
            f"| SRC: {src_id} -> DST: {dst_id}"
        )

        if not is_ack:
            logger.warning(
                f"[ACK] FAILED | NACK received | CMD: {cmd_name} | STATUS: {status_str} "
                f"| SRC: {src_id} -> DST: {dst_id}"
            )

        # 🔁 ACK Tracker'a kayıt (komut adıyla)
        register_ack(cmd_name, src_id, ack["status_code"])

    except Exception as e:
        logger.error(f"[ACK] ERROR | Failed to parse ACK payload: {e} | RAW: {payload}")
