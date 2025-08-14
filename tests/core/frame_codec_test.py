from __future__ import annotations
#!/usr/bin/env python3

import os
import struct
import crcmod
from src.shared.config.manager import get_config

# CRC-16-CCITT-FALSE
CRC_FUNC = crcmod.predefined.mkPredefinedCrcFun('crc-ccitt-false')


def build_mesh_frame(frame_type: str, src_id: int, dst_id: int, payload: bytes) -> bytes:
    """
    Frame oluşturma:
    [start_byte][start_byte_2][version][frame_type][src_id][dst_id][payload_len][payload...][CRC-16]
    """
    cfg = get_config()
    proto_cfg = cfg.get("protocol", {})

    start_byte   = proto_cfg.get("start_byte", 84)
    start_byte_2 = proto_cfg.get("start_byte_2", 199)
    version      = proto_cfg.get("version", 1)

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
    Gelen veriyi çözümler, doğrulama yapar ve parçalar.
    """
    cfg = get_config()
    proto_cfg = cfg.get("protocol", {})

    start_byte   = proto_cfg.get("start_byte", 84)
    start_byte_2 = proto_cfg.get("start_byte_2", 199)
    version_expected = proto_cfg.get("version", 1)

    min_len = 10  # start bytes + header + CRC

    if len(data) < min_len:
        raise ValueError("Frame çok kısa")

    if data[0] != start_byte or data[1] != start_byte_2:
        raise ValueError("Geçersiz start bytes")

    version, frame_type, src_id, dst_id, payload_len = struct.unpack(
        ">BBBBH", data[2:8]
    )

    if version != version_expected:
        raise ValueError(f"Protokol versiyonu uyuşmuyor: {version} ≠ {version_expected}")

    expected_len = min_len + payload_len - 6  # 6: payload_len hariç header farkı
    if len(data) != expected_len:
        raise ValueError(f"Frame uzunluğu hatalı: {len(data)} ≠ {expected_len}")

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


# Opsiyonel test fonksiyonu
def run_tests():
    from src.shared.config.manager import _force_reload_config

    print("[TEST] Forcing config reload...")
    _force_reload_config(config_path="config.json")  # Test amaçlı
    print("[TEST] Building test frame...")

    frame = build_mesh_frame("T", 5, 7, b'ABC123')
    print(f"  Frame: {frame.hex()}")

    parsed = parse_mesh_frame(frame)

    assert parsed["frame_type"] == ord("T")
    assert parsed["src_id"] == 5
    assert parsed["dst_id"] == 7
    assert parsed["payload"] == b'ABC123'
    print("All tests passed successfully!")


if __name__ == "__main__":
    run_tests()
