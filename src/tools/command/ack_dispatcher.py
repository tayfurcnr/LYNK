# src/tools/ack_dispatcher.py

from src.tools.command.ack_builder import build_ack_frame
from src.tools.comm.transmitter import send_frame
from src.tools.log.logger import logger

def send_ack(interface, command_id: int, target_id: int,
             success: bool = True, status_code: int = 0, src: int = None):
    """
    ACK/NACK çerçevesini üretir ve gönderir.
    """
    frame = build_ack_frame(command_id, target_id, success, status_code, src)
    send_frame(interface, frame)

    ack_type = "ACK" if success else "NACK"
    logger.info(f"[{ack_type}] SENT | CMD_ID: {command_id} -> DST: {target_id} | STATUS: {status_code}")

