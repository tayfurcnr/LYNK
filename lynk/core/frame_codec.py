import struct
from typing import Optional
import crcmod
from lynk.shared.config.manager import get_config

# CRC-16-CCITT-FALSE (poly=0x1021, init=0xFFFF)
CRC16_FUNC = crcmod.predefined.mkPredefinedCrcFun('crc-ccitt-false')
# CRC-8 (poly=0x07, init=0x00)
CRC8_FUNC = crcmod.mkCrcFun(0x107, initCrc=0x00, rev=False)

def load_protocol_config():
    """Config'ten protokol sabitlerini alır."""
    proto = get_config().get("protocol", {})
    return proto.get("start_byte", 0x55), proto.get("start_byte_2", 0xAA), proto.get("version", 3)

def load_device_id():
    """Config'ten cihaz ID'sini alır."""
    return get_config()["vehicle"]["id"]

def load_team_id():
    """Config'ten takım ID'sini alır."""
    return get_config()["vehicle"].get("team_id", 1)

def get_seq_manager():
    """Sequence manager instance'ını döndürür."""
    from lynk.core.sequence_manager import get_sequence_manager
    return get_sequence_manager()

def get_crypto_engine():
    """Config'e göre şifreleme motorunu döndürür."""
    cfg = get_config()
    sec = cfg.get("security", {})
    if sec.get("enabled", False):
        from lynk.shared.utils.crypto import LynkCrypto
        return LynkCrypto(sec.get("key", "0"*64))
    return None

def build_mesh_frame(frame_type: str, src_id: int, dst_id: int, payload: bytes, team_id: Optional[int] = None, hop_count: int = 0, seq_num: Optional[int] = None) -> bytes:
    """
    Frame oluşturma (v3):
      [15-byte Header] -> [CRC-8 (1B)] -> [Payload...] -> [CRC-16 (2B)]
    """
    start_byte, start_byte_2, version = load_protocol_config()
    frame_type_byte = ord(frame_type)
    final_team_id = team_id if team_id is not None else load_team_id()
    
    flags = 0x00

    # 1. Sequence Number
    if seq_num is None:
        seq_manager = get_seq_manager()
        out_seq = seq_manager.get_next_out_seq()
    else:
        out_seq = seq_num

    # 2. Encryption Hook
    crypto = get_crypto_engine()
    final_payload = payload
    if crypto:
        associated_data = struct.pack(">BBBB", start_byte_2, version, frame_type_byte, flags)
        final_payload = crypto.encrypt(payload, associated_data)

    payload_len = len(final_payload)

    # 3. Header packing (15 bytes)
    header = struct.pack(
        ">BBBBBBBBIBH",
        start_byte,
        start_byte_2,
        version,
        frame_type_byte,
        final_team_id,
        src_id,
        dst_id,
        hop_count,
        out_seq,
        flags,
        payload_len
    )

    # 4. Header CRC-8 (1 byte)
    header_crc = CRC8_FUNC(header)
    header_with_crc = header + struct.pack(">B", header_crc)

    # 5. Frame CRC-16
    frame_wo_crc = header_with_crc + final_payload
    crc = CRC16_FUNC(frame_wo_crc)
    
    return frame_wo_crc + struct.pack(">H", crc)

def parse_mesh_frame(data: bytes) -> dict:
    """
    Frame çözümleme (v3)
    """
    start_byte, start_byte_2, version_expected = load_protocol_config()

    min_len = 18 # 16 (Header) + 2 (CRC16)
    if len(data) < min_len:
        raise ValueError("Frame çok kısa")

    if data[0] != start_byte or data[1] != start_byte_2:
        raise ValueError("Geçersiz start bytes")

    # Header parsing (15 bytes)
    (_, _, version, frame_type_byte, team_id, src_id, dst_id, 
     hop_count, seq_num, flags, payload_len) = struct.unpack(">BBBBBBBBIBH", data[0:15])

    # Header CRC-8 Check
    header_crc_received = data[15]
    header_crc_calc = CRC8_FUNC(data[0:15])
    if header_crc_received != header_crc_calc:
        raise ValueError(f"Header CRC-8 uyuşmazlığı (Buffer Overflow Koruması): Recv={header_crc_received}, Calc={header_crc_calc}")

    expected_total = 16 + payload_len + 2
    if len(data) < expected_total:
        raise ValueError(f"Frame eksik veya uzunluğu hatalı: {len(data)} < {expected_total}")

    if version != version_expected:
        raise ValueError(f"Protokol versiyonu uyuşmuyor: {version} ≠ {version_expected}")

    # Anti-Replay Verification BEFORE Decryption
    frame_type_char = chr(frame_type_byte)
    if frame_type_char != 'A':
        seq_manager = get_seq_manager()
        if not seq_manager.verify_in_seq(src_id, seq_num):
            last_seq = seq_manager._in_seq_map.get(src_id, 0)
            raise ValueError(f"Replay detected or old sequence: {seq_num} (SRC: {src_id}, LAST: {last_seq})")

    raw_payload = data[16:16 + payload_len]

    # Frame CRC-16 Check
    crc_received = struct.unpack(">H", data[16+payload_len:16+payload_len+2])[0]
    crc_calc = CRC16_FUNC(data[:16+payload_len])
    if crc_received != crc_calc:
        raise ValueError(f"Frame CRC-16 uyuşmazlığı: Recv={crc_received}, Calc={crc_calc}")

    # Decryption
    crypto = get_crypto_engine()
    decrypted_data = raw_payload
    if crypto:
        try:
            associated_data = struct.pack(">BBBB", start_byte_2, version, frame_type_byte, flags)
            decrypted_data = crypto.decrypt(raw_payload, associated_data)
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")

    return {
        "version": version,
        "frame_type": frame_type_char,
        "team_id": team_id,
        "src_id": src_id,
        "dst_id": dst_id,
        "hop_count": hop_count,
        "flags": flags,
        "seq_num": seq_num,
        "payload": decrypted_data
    }
