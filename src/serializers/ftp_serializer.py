# src/serializers/ftp_serializer.py

from struct import pack, unpack
from io import BytesIO
from typing import Tuple

# --- FTP START: filename uzunluğu (2B) + UTF-8 baytlar
def serialize_ftp_start(filename: str) -> bytes:
    name_b = filename.encode('utf-8')
    return pack("!H", len(name_b)) + name_b

def deserialize_ftp_start(payload: bytes) -> str:
    buf = BytesIO(payload)
    length = unpack("!H", buf.read(2))[0]
    return buf.read(length).decode('utf-8')

# --- FTP CHUNK: seq_no (4B) + veri parçacığı
def serialize_ftp_chunk(seq: int, data: bytes) -> bytes:
    return pack("!I", seq) + data

def deserialize_ftp_chunk(payload: bytes) -> Tuple[int, bytes]:
    seq = unpack("!I", payload[:4])[0]
    return seq, payload[4:]

# --- FTP END: toplam parça sayısı (4B)
def serialize_ftp_end(total_chunks: int) -> bytes:
    return pack("!I", total_chunks)

def deserialize_ftp_end(payload: bytes) -> int:
    return unpack("!I", payload)[0]
