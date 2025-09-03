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

def _send_ack(interface, ack_name: str, cmd_id: int, dst: int, src: int | None):
    """A helper function to build and send any type of ACK."""
    # 1. Serialize the specific ACK payload (e.g., ack_id + cmd_id)
    ack_payload = serialize_ack(ack_name, cmd_id)

    # 2. Determine the source ID if not provided
    source_id = src if src is not None else load_device_id()

    # 3. Build the complete LYNK frame
    final_frame = build_mesh_frame('A', source_id, dst, ack_payload)

    # 4. Send the final frame
    send_frame(interface, final_frame)

def send_ack_ok(
    interface,
    cmd_id: int,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """Send an ACK_OK frame with the corresponding command ID."""
    _send_ack(interface, "ACK_OK", cmd_id, dst, src)
    logger.info(f"[ACK] SENT ACK_OK | DST: {dst} | For CMD_ID: {cmd_id}")

def send_ack_error(
    interface,
    cmd_id: int,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """Send an ACK_ERROR frame with the corresponding command ID."""
    _send_ack(interface, "ACK_ERROR", cmd_id, dst, src)
    logger.error(f"[ACK] SENT ACK_ERROR | DST: {dst} | For CMD_ID: {cmd_id}")

def send_ack_busy(
    interface,
    cmd_id: int,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """Send an ACK_BUSY frame with the corresponding command ID."""
    _send_ack(interface, "ACK_BUSY", cmd_id, dst, src)
    logger.warning(f"[ACK] SENT ACK_BUSY | DST: {dst} | For CMD_ID: {cmd_id}")

def send_ack_invalid_cmd(
    interface,
    cmd_id: int,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """Send an ACK_INVALID_CMD frame with the corresponding command ID."""
    _send_ack(interface, "ACK_INVALID_CMD", cmd_id, dst, src)
    logger.error(f"[ACK] SENT ACK_INVALID_CMD | DST: {dst} | For CMD_ID: {cmd_id}")