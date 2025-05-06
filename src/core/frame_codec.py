import os
import struct
import json
import crcmod

# CRC-16-CCITT-FALSE (poly=0x1021, init=0xFFFF)
CRC_FUNC = crcmod.predefined.mkPredefinedCrcFun('crc-ccitt-false')

# 🔧 Config'ten cihaz ID'sini al
def load_device_id(config_path=None):
    if config_path is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
        config_path = os.path.join(base_dir, "config.json")
    with open(config_path, "r") as f:
        cfg = json.load(f)
        return cfg["vehicle"]["id"]

# 🔧 Config'ten protokol sabitlerini al
def load_protocol_config(config_path=None):
    if config_path is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
        config_path = os.path.join(base_dir, "config.json")
    with open(config_path, "r") as f:
        cfg = json.load(f)
        proto = cfg.get("protocol", {})
        start_byte = proto["start_byte"]
        terminal_byte = proto["terminal_byte"]
        version = proto["version"]
        return start_byte, terminal_byte, version

# 🧱 Frame oluşturma (encode)
def build_mesh_frame(frame_type: str, src_id: int, dst_id: int, payload: bytes, config_path=None) -> bytes:
    start_byte, terminal_byte, version = load_protocol_config(config_path)
    frame_type_byte = ord(frame_type)
    payload_len = len(payload)

    # Header: start_byte, version, frame_type, src_id, dst_id, payload_len
    header = struct.pack(">BBBBBH", start_byte, version, frame_type_byte, src_id, dst_id, payload_len)
    frame = header + payload

    # CRC ve terminal ekle
    crc = CRC_FUNC(frame)
    frame += struct.pack(">H", crc)            # 2 byte CRC
    frame += struct.pack("B", terminal_byte)   # 1 byte terminal byte

    return frame

# 🧩 Frame çözümleme (decode)
def parse_mesh_frame(data: bytes, config_path=None) -> dict:
    start_byte, terminal_byte, version_config = load_protocol_config(config_path)

    if len(data) < 10:
        raise ValueError("Frame çok kısa")

    if data[0] != start_byte:
        raise ValueError("Geçersiz start byte")
    if data[-1] != terminal_byte:
        raise ValueError("Geçersiz terminal byte")

    header = struct.unpack(">BBBBBH", data[:7])
    _, version, frame_type, src_id, dst_id, payload_len = header

    if version != version_config:
        raise ValueError(f"Protokol versiyonu uyuşmuyor: {version} ≠ {version_config}")

    expected_len = 7 + payload_len + 2 + 1
    if len(data) != expected_len:
        raise ValueError("Frame uzunluğu hatalı")

    payload = data[7:7+payload_len]
    received_crc = struct.unpack(">H", data[7+payload_len:7+payload_len+2])[0]
    calc_crc = CRC_FUNC(data[:7+payload_len])
    if received_crc != calc_crc:
        raise ValueError("CRC uyuşmazlığı")

    return {
        "version": version,
        "frame_type": frame_type,
        "src_id": src_id,
        "dst_id": dst_id,
        "payload": payload
    }