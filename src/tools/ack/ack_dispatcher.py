# src/tools/ack/ack_dispatcher.py

"""
ACK Dispatcher Module

Constructs and sends ACK/NACK frames for both general commands and FTP transfers,
and logs each transmission.
"""

from src.tools.ack.ack_builder import build_ack_frame
from src.tools.ack.ftp_ack_builder import build_ftp_ack_frame
from src.tools.comm.transmitter import send_frame
from src.tools.log.logger import logger

# Mapping of status codes to human-readable labels
STATUS_NAMES = {
    0: "SUCCESS",
    1: "INVALID_PARAMS",
    2: "UNSUPPORTED"
}


def send_ack(
    interface,
    command_id: int,
    target_id: int,
    success: bool = True,
    status_code: int = 0,
    src: int = None
) -> None:
    """
    Build and send a generic ACK/NACK frame for a command.

    Args:
        interface: Communication interface (e.g., UARTInterface).
        command_id (int): Identifier of the command being acknowledged.
        target_id (int): Destination node ID to receive the ACK/NACK.
        success (bool): True for ACK, False for NACK.
        status_code (int): Status code (default 0 for SUCCESS).
        src (int, optional): Source device ID; if None, loaded internally.
    """
    frame = build_ack_frame(command_id, target_id, success, status_code, src)
    send_frame(interface, frame)

    ack_type = "ACK" if success else "NACK"
    status_name = STATUS_NAMES.get(status_code, f"UNKNOWN({status_code})")
    logger.info(
        f"[{ack_type}] SENT | CMD_ID: {command_id} -> DST: {target_id} | STATUS: {status_name}"
    )


def send_ftp_ack(
    interface,
    target_id: int,
    phase: str,
    success: bool = True,
    status_code: int = 0,
    src: int = None
) -> None:
    """
    Build and send an ACK/NACK frame for an FTP transfer phase.

    Args:
        interface: Communication interface.
        target_id (int): Destination node ID.
        phase (str): One of "START", "CHUNK", or "END".
        success (bool): True for ACK, False for NACK.
        status_code (int): For CHUNK NACKs, the missing chunk sequence number.
        src (int, optional): Source device ID; if None, loaded internally.
    """
    frame = build_ftp_ack_frame(
        target_id=target_id,
        phase=phase,
        success=success,
        status_code=status_code,
        src=src
    )
    send_frame(interface, frame)

    ack_type = "ACK" if success else "NACK"
    logger.info(
        f"[FTP {ack_type}] SENT | PHASE: {phase} -> DST: {target_id} | STATUS: {status_code}"
    )
