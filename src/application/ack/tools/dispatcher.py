from __future__ import annotations
# /src/ack/tools/dispatcher.py

"""
ACK Dispatcher Module

Constructs and sends various ACK frames over a communication interface.
Each function builds a specific ACK payload (ACK_OK, ACK_ERROR, ACK_BUSY, ACK_INVALID_CMD)
and transmits it, while logging the action for traceability.
"""

from src.application.ack.tools.builder import (
    build_ack_ok,
    build_ack_error,
    build_ack_busy,
    build_ack_invalid_cmd
)
from src.shared.comm.transmitter import send_frame
from src.shared.log.logger import logger

def send_ack_ok(
    interface,
    message: str,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send an ACK_OK frame.
    """
    frame = build_ack_ok(message, dst, src)
    send_frame(interface, frame)
    logger.info(
        f"[ACK] SENT ACK_OK | DST: {dst} | Message: {message}"
    )


def send_ack_error(
    interface,
    message: str,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send an ACK_ERROR frame.
    """
    frame = build_ack_error(message, dst, src)
    send_frame(interface, frame)
    logger.error(
        f"[ACK] SENT ACK_ERROR | DST: {dst} | Message: {message}"
    )


def send_ack_busy(
    interface,
    message: str,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send an ACK_BUSY frame.
    """
    frame = build_ack_busy(message, dst, src)
    send_frame(interface, frame)
    logger.warning(
        f"[ACK] SENT ACK_BUSY | DST: {dst} | Message: {message}"
    )


def send_ack_invalid_cmd(
    interface,
    message: str,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send an ACK_INVALID_CMD frame.
    """
    frame = build_ack_invalid_cmd(message, dst, src)
    send_frame(interface, frame)
    logger.error(
        f"[ACK] SENT ACK_INVALID_CMD | DST: {dst} | Message: {message}"
    )