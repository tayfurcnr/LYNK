# src/serializers/ftp_serializer.py
"""
FTP payload serialize/deserialize:
 - START:  [0x00][name_len:2B][name...]
 - CHUNK:  [0x01][seq:3B][data...]
 - END:    [0x02][total_chunks:3B]
"""
from typing import Tuple

FTP_PHASE_IDS = {
    "START": 0x00,
    "CHUNK": 0x01,
    "END":   0x02,
}

def serialize_ftp_start(filename: str) -> bytes:
    name_b = filename.encode()
    return bytes([FTP_PHASE_IDS["START"]]) + len(name_b).to_bytes(2, "big") + name_b

def serialize_ftp_chunk(seq: int, data: bytes) -> bytes:
    return bytes([FTP_PHASE_IDS["CHUNK"]]) + seq.to_bytes(3, "big") + data

def serialize_ftp_end(total_chunks: int) -> bytes:
    return bytes([FTP_PHASE_IDS["END"]]) + total_chunks.to_bytes(3, "big")

def deserialize_ftp_start(payload: bytes) -> str:
    if payload[0] != FTP_PHASE_IDS["START"]:
        raise ValueError("Beklenmeyen faz, START değil")
    name_len = int.from_bytes(payload[1:3], "big")
    return payload[3:3+name_len].decode()

def deserialize_ftp_chunk(payload: bytes) -> Tuple[int, bytes]:
    if payload[0] != FTP_PHASE_IDS["CHUNK"]:
        raise ValueError("Beklenmeyen faz, CHUNK değil")
    seq = int.from_bytes(payload[1:4], "big")
    return seq, payload[4:]

def deserialize_ftp_end(payload: bytes) -> int:
    if payload[0] != FTP_PHASE_IDS["END"]:
        raise ValueError("Beklenmeyen faz, END değil")
    return int.from_bytes(payload[1:4], "big")
