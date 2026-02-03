from __future__ import annotations
import struct
from typing import Optional
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

def load_team_id():
    """Config'ten takım ID'sini alır."""
    return get_config()["vehicle"].get("team_id", 1)

def get_seq_manager():
    """Sequence manager instance'ını döndürür."""
    from src.core.sequence_manager import get_sequence_manager
    return get_sequence_manager()

def get_crypto_engine():
    """Config'e göre şifreleme motorunu döndürür."""
    cfg = get_config()
    sec = cfg.get("security", {})
    if sec.get("enabled", False):
        from src.shared.utils.crypto import LynkCrypto
        return LynkCrypto(sec.get("key", "0"*64))
    return None

def build_mesh_frame(frame_type: str, src_id: int, dst_id: int, payload: bytes, team_id: Optional[int] = None, hop_count: int = 0) -> bytes:
    """
    Frame oluşturma:
      [start_byte][start_byte_2][version][frame_type][src_id][dst_id][payload_len]
      [payload...]
      [CRC-16 (2 bytes)]
    """
    start_byte, start_byte_2, version = load_protocol_config()
    frame_type_byte = ord(frame_type)
    
    # Use provided team_id or load from config
    final_team_id = team_id if team_id is not None else load_team_id()
    
    # 1. Anti-Replay: Prepend Sequence Number (4 bytes)
    seq_manager = get_seq_manager()
    out_seq = seq_manager.get_next_out_seq()
    payload_with_seq = struct.pack(">I", out_seq) + payload

    # 2. Encryption Hook
    crypto = get_crypto_engine()
    final_payload = payload_with_seq
    if crypto:
        # We use a static AD (start_byte_2 + version + frame_type) for basic tampering protection
        associated_data = struct.pack(">BBB", start_byte_2, version, ord(frame_type))
        final_payload = crypto.encrypt(payload_with_seq, associated_data)

    payload_len = len(final_payload)

    header = struct.pack(
        ">BBBBBBBBH",
        start_byte,
        start_byte_2,
        version,
        frame_type_byte,
        final_team_id,
        src_id,
        dst_id,
        hop_count,
        payload_len
    )

    frame_wo_crc = header + final_payload
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

    min_len = 12  # 2 start + 1 vers + 1 type + 1 team + 1 src + 1 dst + 1 hop + 2 len + 2 crc
    if len(data) < min_len:
        raise ValueError("Frame çok kısa")

    if data[0] != start_byte or data[1] != start_byte_2:
        raise ValueError("Geçersiz start bytes")

    version, frame_type, team_id, src_id, dst_id, hop_count, payload_len = struct.unpack(">BBBBBBH", data[2:10])

    expected_len = min_len + payload_len - 11  # since min_len already includes CRC + header
    if len(data) != min_len + payload_len:
        raise ValueError(f"Frame uzunluğu hatalı: {len(data)} ≠ {min_len + payload_len}")

    if version != version_expected:
        raise ValueError(f"Protokol versiyonu uyuşmuyor: {version} ≠ {version_expected}")

    payload_start = 10
    raw_payload = data[payload_start:payload_start + payload_len]

    # CRC Validation
    crc_received = struct.unpack(">H", data[payload_start + payload_len:payload_start + payload_len + 2])[0]
    crc_calc = CRC_FUNC(data[:payload_start + payload_len])
    if crc_received != crc_calc:
        raise ValueError(f"CRC uyuşmazlığı: Recv={crc_received}, Calc={crc_calc}")

    # 1. Decryption Hook
    crypto = get_crypto_engine()
    decrypted_payload = raw_payload
    if crypto:
        try:
            associated_data = struct.pack(">BBB", start_byte_2, version_expected, frame_type)
            decrypted_payload = crypto.decrypt(raw_payload, associated_data)
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")

    # 2. Anti-Replay: Extract and Verify Sequence Number
    if len(decrypted_payload) < 4:
        raise ValueError("Payload sequence number missing (too short)")
    
    seq_num = struct.unpack(">I", decrypted_payload[:4])[0]
    final_payload = decrypted_payload[4:]

    seq_manager = get_seq_manager()
    if not seq_manager.verify_in_seq(src_id, seq_num):
        raise ValueError(f"Replay detected or old sequence: {seq_num} (SRC: {src_id})")

    return {
        "version": version,
        "frame_type": frame_type,
        "team_id": team_id,
        "src_id": src_id,
        "dst_id": dst_id,
        "hop_count": hop_count,
        "payload": final_payload
    }
