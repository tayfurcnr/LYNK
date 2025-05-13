#!/usr/bin/env python3
import os
import struct
import json
import crcmod

# CRC-16-CCITT-FALSE (poly=0x1021, init=0xFFFF)
CRC_FUNC = crcmod.predefined.mkPredefinedCrcFun('crc-ccitt-false')

def load_protocol_config(config_path=None):
    """
    Config'ten protokol sabitlerini alır:
      - start_byte: frame'in ilk baytı
      - start_byte_2: frame'in ikinci baytı
      - version: protokol versiyonu
    """
    if config_path is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),))
        config_path = os.path.join(base_dir, "config.json")
    with open(config_path, "r") as f:
        cfg = json.load(f)
        proto = cfg.get("protocol", {})
        return proto["start_byte"], proto["start_byte_2"], proto["version"]

def build_mesh_frame(frame_type: str, src_id: int, dst_id: int, payload: bytes, config_path=None) -> bytes:
    """
    Frame oluşturma:
      [start_byte][start_byte_2][version][frame_type][src_id][dst_id][payload_len]
      [payload...]
      [CRC-16 (2 bytes)]
    """
    start_byte, start_byte_2, version = load_protocol_config(config_path)
    frame_type_byte = ord(frame_type)
    payload_len = len(payload)

    # Header: iki start baytı, versiyon, frame tipi, src_id, dst_id, payload uzunluğu
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

def parse_mesh_frame(data: bytes, config_path=None) -> dict:
    """
    Frame çözümleme ve doğrulama:
      - İlk iki baytı kontrol et (start bytes)
      - Header unpack et
      - Payload ve CRC'yi ayır, CRC doğrula
    """
    start_byte, start_byte_2, version_expected = load_protocol_config(config_path)

    # En kısa frame: 2 start + 1 versiyon + 1 tip + 1 src + 1 dst + 2 len + 2 CRC = 10 bayt
    min_len = 1 + 1 + 1 + 1 + 1 + 1 + 2 + 2
    if len(data) < min_len:
        raise ValueError("Frame çok kısa")

    # Başlangıç baytları kontrolü
    if data[0] != start_byte or data[1] != start_byte_2:
        raise ValueError("Geçersiz start bytes")

    # Header alanını çöz (bytes 2-7)
    version, frame_type, src_id, dst_id, payload_len = struct.unpack(
        ">BBBBH",
        data[2:8]
    )

    if version != version_expected:
        raise ValueError(f"Protokol versiyonu uyuşmuyor: {version} ≠ {version_expected}")

    expected_len = min_len + payload_len
    if len(data) != expected_len:
        raise ValueError(f"Frame uzunluğu hatalı: {len(data)} ≠ {expected_len}")

    # Payload ve CRC ayırma
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

def _write_default_config(config_path):
    default = {
        "protocol": {
            "start_byte": 84,
            "start_byte_2": 199,
            "version": 1
        },
        "vehicle": {
            "id": 1
        }
    }
    with open(config_path, "w") as f:
        json.dump(default, f, indent=2)

def run_tests():
    # Create a temporary config.json in the script directory
    base_dir = os.path.abspath(os.path.dirname(__file__))
    config_path = os.path.join(base_dir, "config.json")
    _write_default_config(config_path)

    # Test data
    frame_type = 'T'
    src_id = 5
    dst_id = 7
    payload = b'ABC123'

    print("Building frame...")
    frame = build_mesh_frame(frame_type, src_id, dst_id, payload, config_path=config_path)
    print(f"Built frame bytes: {frame.hex()}")

    print("Parsing frame...")
    parsed = parse_mesh_frame(frame, config_path=config_path)

    assert parsed["frame_type"] == ord(frame_type)
    assert parsed["src_id"] == src_id
    assert parsed["dst_id"] == dst_id
    assert parsed["payload"] == payload

    print("All tests passed successfully!")

if __name__ == "__main__":
    run_tests()
