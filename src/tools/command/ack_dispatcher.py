# src/tools/ack_dispatcher.py

from src.tools.command.ack_builder import build_ack_frame
from src.tools.comm.transmitter import send_frame
from src.tools.log.logger import logger

# Status code to name mapping
STATUS_NAMES = {
    0: "SUCCESS",
    1: "INVALID_PARAMS",
    2: "UNSUPPORTED"
}

def send_ack(interface, command_id: int, target_id: int,
             success: bool = True, status_code: int = 0, src: int = None):
    """
    ACK/NACK çerçevesini üretir ve gönderir.
    """
    frame = build_ack_frame(command_id, target_id, success, status_code, src)
    send_frame(interface, frame)

    ack_type = "ACK" if success else "NACK"
    status_name = STATUS_NAMES.get(status_code, f"UNKNOWN({status_code})")
    logger.info(f"[{ack_type}] SENT | CMD_ID: {command_id} -> DST: {target_id} | STATUS: {status_name}")

