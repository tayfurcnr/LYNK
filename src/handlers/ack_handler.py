# src/handlers/ack_handler.py

from src.serializers.ack_serializer import deserialize_ack
from src.tools.logger import logger

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
    """
    try:
        ack = deserialize_ack(payload)
        src_id = frame_meta["src_id"]
        dst_id = frame_meta["dst_id"]

        is_ack = ack["ack_code"] == 0xAA
        ack_type = "ACK" if is_ack else "NACK"
        status_str = status_map.get(ack["status_code"], f"UNKNOWN({ack['status_code']})")

        logger.info(
            f"[ACK] RECEIVED | TYPE: {ack_type} | CMD_ID: {ack['command_id']} | STATUS: {status_str} "
            f"| SRC: {src_id} -> DST: {dst_id}"
        )

        if not is_ack:
            logger.warning(
                f"[ACK] FAILED | NACK received | CMD_ID: {ack['command_id']} | STATUS: {status_str} "
                f"| SRC: {src_id} -> DST: {dst_id}"
            )

    except Exception as e:
        logger.error(f"[ACK] ERROR | Failed to parse ACK payload: {e} | RAW: {payload}")
