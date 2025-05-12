# src/tools/ack/ftp_ack_builder.py

"""
FTP ACK Builder Module

Constructs mesh frames to acknowledge (ACK) or negatively acknowledge (NACK)
FTP file-transfer operations for START, CHUNK, and END phases.
"""

import struct
from typing import Optional

from src.core.frame_codec import build_mesh_frame, load_device_id


def build_ftp_ack_frame(
    target_id: int,
    success: bool = True,
    status_code: int = 0,
    src: Optional[int] = None
) -> bytes:
    """
    Build an ACK or NACK mesh frame for FTP transfers.

    Args:
        target_id (int): Destination node ID for the ACK/NACK.
        success (bool, optional): True for ACK, False for NACK (payload identical).
        status_code (int, optional):
            - 0 for START or END acknowledgment (empty payload).
            - >0 to acknowledge a specific chunk number.
        src (int | None, optional):
            Source device ID; if None, loaded via load_device_id().

    Returns:
        bytes: A type-'A' mesh frame containing the ACK/NACK payload.
    """
    source = src if src is not None else load_device_id()

    # START/END frames use empty payload; chunk ACKs include the sequence number
    if status_code == 0:
        payload = b""
    else:
        payload = struct.pack("!I", status_code)

    return build_mesh_frame('A', source, target_id, payload)
