from __future__ import annotations
# /src/ack/tools/dispatcher.py

"""
ACK Dispatcher Module

Constructs and sends various ACK frames over a communication interface.
Each function serializes a specific ACK payload, builds a full LYNK frame,
and transmits it, while logging the action for traceability.
"""

from src.application.ack.serializer.dispatcher import serialize_ack
from src.shared.comm.transmitter import send_frame
from src.shared.log.logger import logger
from src.core.frame_codec import build_mesh_frame, load_device_id

def send_ack_ok(
    interface,
    cmd_id: int,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send an ACK_OK frame with the corresponding command ID.
    """
    if src is None:
        src = load_device_id()
    payload = serialize_ack("ACK_OK", cmd_id)
    frame = build_mesh_frame('A', src, dst, payload)
    send_frame(interface, frame)
    logger.info(
        f"[ACK] SENT ACK_OK | DST: {dst} | For CMD_ID: {cmd_id}"
    )


def send_ack_error(
    interface,
    cmd_id: int,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send an ACK_ERROR frame with the corresponding command ID.
    """
    if src is None:
        src = load_device_id()
    payload = serialize_ack("ACK_ERROR", cmd_id)
    frame = build_mesh_frame('A', src, dst, payload)
    send_frame(interface, frame)
    logger.error(
        f"[ACK] SENT ACK_ERROR | DST: {dst} | For CMD_ID: {cmd_id}"
    )


def send_ack_busy(
    interface,
    cmd_id: int,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send an ACK_BUSY frame with the corresponding command ID.
    """
    if src is None:
        src = load_device_id()
    payload = serialize_ack("ACK_BUSY", cmd_id)
    frame = build_mesh_frame('A', src, dst, payload)
    send_frame(interface, frame)
    logger.warning(
        f"[ACK] SENT ACK_BUSY | DST: {dst} | For CMD_ID: {cmd_id}"
    )

def send_ack_execution_error(
    interface, 
    cmd_id: int,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send an ACK_EXECUTION_ERROR frame with the corresponding command ID.
    """
    if src is None:
        src = load_device_id()
    payload = serialize_ack("ACK_EXECUTION_ERROR", cmd_id)
    frame = build_mesh_frame('A', src, dst, payload)
    send_frame(interface, frame)
    logger.error(
        f"[ACK] SENT ACK_EXECUTION_ERROR | DST: {dst} | For CMD_ID: {cmd_id}"
    )


def send_ack_invalid_cmd(
    interface,
    cmd_id: int,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send an ACK_INVALID_CMD frame with the corresponding command ID.
    """
    if src is None:
        src = load_device_id()
    payload = serialize_ack("ACK_INVALID_CMD", cmd_id)
    frame = build_mesh_frame('A', src, dst, payload)
    send_frame(interface, frame)
    logger.error(
        f"[ACK] SENT ACK_INVALID_CMD | DST: {dst} | For CMD_ID: {cmd_id}"
    )
