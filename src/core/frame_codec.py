from __future__ import annotations
import struct
import crcmod
from src.shared.config.manager import get_config

# CRC-16-CCITT-FALSE (poly=0x1021, init=0xFFFF)
CRC_FUNC = crcmod.predefined.mkPredefinedCrcFun('crc-ccitt-false')

def load_protocol_config():
    """Config'ten protokol sabitlerini alır."""
    proto = get_config().get("protocol", {})
    return proto["start_byte"], proto["start_byte_2"], proto["version"]

def load_device_id():
    """Config'ten cihaz ID'sini alır."""
    return get_config()["vehicle"]["id"]

def build_mesh_frame(frame_type: str, src_id: int, dst_id: int, payload: bytes) -> bytes:
    """
    Frame oluşturma:
      [start_byte][start_byte_2][version][frame_type][src_id][dst_id][payload_len]
      [payload...]
      [CRC-16 (2 bytes)]
    """
    start_byte, start_byte_2, version = load_protocol_config()
    frame_type_byte = ord(frame_type)
    payload_len = len(payload)

    header = struct.pack(
        ">BBBBBBH",
        start_byte,
        start_byte_2,
        version,
        frame_type_byte,
        src_id,
        dst_id,
        payload_len
    )

    frame_wo_crc = header + payload
    crc = CRC_FUNC(frame_wo_crc)
    return frame_wo_crc + struct.pack(">H", crc)

def parse_mesh_frame(data: bytes) -> dict:
    """
    Frame çözümleme ve doğrulama:
      - Start bytes kontrolü
      - Header parse
      - CRC doğrulama
    """
    start_byte, start_byte_2, version_expected = load_protocol_config()

    min_len = 10  # 2 start + 1 vers + 1 type + 1 src + 1 dst + 2 len + 2 crc
    if len(data) < min_len:
        raise ValueError("Frame çok kısa")

    if data[0] != start_byte or data[1] != start_byte_2:
        raise ValueError("Geçersiz start bytes")

    version, frame_type, src_id, dst_id, payload_len = struct.unpack(">BBBBH", data[2:8])

    expected_len = min_len + payload_len - 10  # since min_len already includes CRC + header
    if len(data) != min_len + payload_len:
        raise ValueError(f"Frame uzunluğu hatalı: {len(data)} ≠ {min_len + payload_len}")

    if version != version_expected:
        raise ValueError(f"Protokol versiyonu uyuşmuyor: {version} ≠ {version_expected}")

    payload_start = 8
    payload = data[payload_start:payload_start + payload_len]

    crc_received = struct.unpack(">H", data[payload_start + payload_len:payload_start + payload_len + 2])[0]
    crc_calc = CRC_FUNC(data[:payload_start + payload_len])
    if crc_received != crc_calc:
        raise ValueError("CRC uyuşmazlığı")

    return {
        "version": version,
        "frame_type": frame_type,
        "src_id": src_id,
        "dst_id": dst_id,
        "payload": payload
    }
