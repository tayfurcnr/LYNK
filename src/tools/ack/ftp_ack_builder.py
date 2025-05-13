# src/tools/ack/ftp_ack_builder.py

"""
FTP ACK Builder Module

Constructs mesh frames to acknowledge (ACK) or negatively acknowledge (NACK)
FTP file-transfer operations for START, CHUNK, and END phases.
"""

import struct
from typing import Optional, Literal
from src.core.frame_codec import build_mesh_frame, load_device_id

# FTP evrelerinin komut ID'leri
COMMAND_IDS: dict[Literal["START", "CHUNK", "END"], int] = {
    "START": 0x10,
    "CHUNK": 0x11,
    "END":   0x12,
}

def build_ftp_ack_frame(
    target_id: int,
    phase: Literal["START", "CHUNK", "END"],
    success: bool = True,
    status_code: int = 0,
    src: Optional[int] = None
) -> bytes:
    """
    Build an ACK or NACK mesh frame for FTP transfers.

    Args:
        target_id (int): Destination node ID for the ACK/NACK.
        phase (Literal["START","CHUNK","END"]): Which FTP phase is being acknowledged.
        success (bool, optional): True for ACK, False for NACK.
        status_code (int, optional):
            - For START/END: must be 0.
            - For CHUNK: the chunk sequence number (can now be >255).
        src (int | None, optional): Source device ID; if None, loaded via load_device_id().

    Returns:
        bytes: A type-'A' mesh frame containing the ACK/NACK payload.
    """
    source = src if src is not None else load_device_id()
    ack_code = 0xAA if success else 0x55
    try:
        cmd_id = COMMAND_IDS[phase]
    except KeyError:
        raise ValueError(f"Invalid FTP phase: {phase!r}. Must be one of {list(COMMAND_IDS)}")

    # payload: [ACK_CODE(1B), COMMAND_ID(1B), STATUS_CODE(4B)]
    payload = struct.pack(">BBI", ack_code, cmd_id, status_code)
    return build_mesh_frame('A', source, target_id, payload)
