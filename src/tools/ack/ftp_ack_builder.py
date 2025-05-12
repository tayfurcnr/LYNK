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
    "END": 0x12,
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
        success (bool, optional): True for ACK (0xAA), False for NACK (0x55).
        status_code (int, optional):
            - For START/END: must be 0.
            - For CHUNK: the chunk sequence number.
        src (int | None, optional): Source device ID; if None, loaded via load_device_id().

    Returns:
        bytes: A type-'A' mesh frame containing the 3-byte ACK/NACK payload.
    """
    # Kaynak ID’si
    source = src if src is not None else load_device_id()

    # ACK kodu: 0xAA = ACK, 0x55 = NACK
    ack_code = 0xAA if success else 0x55

    # İlgili komut ID’sini al
    try:
        cmd_id = COMMAND_IDS[phase]
    except KeyError:
        raise ValueError(f"Invalid FTP phase: {phase!r}. Must be one of {list(COMMAND_IDS)}")

    # payload: [ACK_CODE][COMMAND_ID][STATUS_CODE] (3 bayt)
    payload = struct.pack(">BBB", ack_code, cmd_id, status_code)

    # 'A' tipinde mesh frame oluştur ve döndür
    return build_mesh_frame('A', source, target_id, payload)
