import struct
from typing import Optional
import crcmod
import lz4.block
from src.shared.config.manager import get_config

# CRC-16-CCITT-FALSE (poly=0x1021, init=0xFFFF)
CRC_FUNC = crcmod.predefined.mkPredefinedCrcFun('crc-ccitt-false')

# FLAGS CONSTANTS
FLAG_COMPRESSED = 0x01
ALGO_LZ4 = 0x00 # 00 in bits 1-2

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

def build_mesh_frame(frame_type: str, src_id: int, dst_id: int, payload: bytes, team_id: Optional[int] = None, hop_count: int = 0, seq_num: Optional[int] = None) -> bytes:
    """
    Frame oluşturma (v2):
      [start_byte][start_byte_2][version][frame_type][team_id][src_id][dst_id][hop_count][flags][payload_len (2B)]
      [payload...] (Encrypted: [SeqNum (4B)][Payload...])
      [CRC-16 (2 bytes)]
    """
    start_byte, start_byte_2, version = load_protocol_config()
    frame_type_byte = ord(frame_type)
    final_team_id = team_id if team_id is not None else load_team_id()
    
    # 1. Smart Compression
    flags = 0x00
    processed_payload = payload
    proto_cfg = get_config().get("protocol", {})
    
    if proto_cfg.get("compression_enabled", True):
        threshold = proto_cfg.get("compression_threshold", 128)
        if len(payload) > threshold:
            try:
                # Trail compression
                trial = lz4.block.compress(payload, store_size=False)
                # Compare: compressed_len + 4 (orig_size) < original_len
                if len(trial) + 4 < len(payload):
                    processed_payload = struct.pack(">I", len(payload)) + trial
                    flags |= FLAG_COMPRESSED
                    # Bits 1-2 remain 0 for LZ4
            except:
                pass

    # 2. Anti-Replay: Prepend Sequence Number (4 bytes)
    if seq_num is None:
        seq_manager = get_seq_manager()
        out_seq = seq_manager.get_next_out_seq()
    else:
        out_seq = seq_num

    data_to_encrypt = struct.pack(">I", out_seq) + processed_payload

    # 3. Encryption Hook
    crypto = get_crypto_engine()
    final_payload = data_to_encrypt
    if crypto:
        # Static AD includes the new flags byte in v2
        associated_data = struct.pack(">BBBB", start_byte_2, version, frame_type_byte, flags)
        final_payload = crypto.encrypt(data_to_encrypt, associated_data)

    payload_len = len(final_payload)

    # Header packing (11 bytes total with 2B start and 2B len)
    # >BBBBBBBBBH -> 9 bytes + 2 bytes result = 11? 
    # Actually: 2B start + 1B ver + 1B type + 1B team + 1B src + 1B dst + 1B hop + 1B flags + 2B len = 11 bytes.
    header = struct.pack(
        ">BBBBBBBBBH",
        start_byte,
        start_byte_2,
        version,
        frame_type_byte,
        final_team_id,
        src_id,
        dst_id,
        hop_count,
        flags,
        payload_len
    )

    frame_wo_crc = header + final_payload
    crc = CRC_FUNC(frame_wo_crc)
    return frame_wo_crc + struct.pack(">H", crc)

def parse_mesh_frame(data: bytes) -> dict:
    """
    Frame çözümleme (v2)
    """
    start_byte, start_byte_2, version_expected = load_protocol_config()

    # Min len: 2 start + 1 ver + 1 type + 1 team + 1 src + 1 dst + 1 hop + 1 flags + 2 len + 2 crc = 13 bytes
    min_len = 13
    if len(data) < min_len:
        raise ValueError("Frame çok kısa")

    if data[0] != start_byte or data[1] != start_byte_2:
        raise ValueError("Geçersiz start bytes")

    # Header parsing
    (version, frame_type_byte, team_id, src_id, dst_id, 
     hop_count, flags, payload_len) = struct.unpack(">BBBBBBBH", data[2:11])

    if len(data) != min_len + payload_len - 2: # min_len already has CRC space... wait.
        # Let's count again:
        # Header: 0..10 (11 bytes) -> data[0:11]
        # Payload: data[11:11+payload_len]
        # CRC: data[11+payload_len:11+payload_len+2]
        # Total: 13 + payload_len
        pass
    
    expected_total = 11 + payload_len + 2
    if len(data) != expected_total:
        raise ValueError(f"Frame uzunluğu hatalı: {len(data)} ≠ {expected_total}")

    if version != version_expected:
        raise ValueError(f"Protokol versiyonu uyuşmuyor: {version} ≠ {version_expected}")

    raw_payload = data[11:11 + payload_len]

    # CRC Validation
    crc_received = struct.unpack(">H", data[11+payload_len:11+payload_len+2])[0]
    crc_calc = CRC_FUNC(data[:11+payload_len])
    if crc_received != crc_calc:
        raise ValueError(f"CRC uyuşmazlığı: Recv={crc_received}, Calc={crc_calc}")

    # 1. Decryption Hook
    crypto = get_crypto_engine()
    decrypted_data = raw_payload
    if crypto:
        try:
            associated_data = struct.pack(">BBBB", start_byte_2, version, frame_type_byte, flags)
            decrypted_data = crypto.decrypt(raw_payload, associated_data)
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")

    # 2. Extract SeqNum
    if len(decrypted_data) < 4:
        raise ValueError("Payload sequence number missing")
    
    seq_num = struct.unpack(">I", decrypted_data[:4])[0]
    payload_after_seq = decrypted_data[4:]

    # 3. Handle Compression
    final_payload = payload_after_seq
    if flags & FLAG_COMPRESSED:
        algo_id = (flags & 0x06) >> 1
        if algo_id == ALGO_LZ4:
            if len(payload_after_seq) < 4:
                raise ValueError("Compressed payload missing original size header")
            orig_size = struct.unpack(">I", payload_after_seq[:4])[0]
            try:
                final_payload = lz4.block.decompress(payload_after_seq[4:], uncompressed_size=orig_size)
            except Exception as e:
                raise ValueError(f"Decompression failed: {e}")
        else:
            raise ValueError(f"Unsupported compression algorithm ID: {algo_id}")

    # 4. Anti-Replay Verification
    # EXCEPTION: ACK frames are exempt from replay detection
    # Rationale: ACKs are idempotent confirmations - receiving duplicates is harmless
    # This allows proper ACK delivery in multicast environments where loopback occurs
    frame_type_char = chr(frame_type_byte)
    if frame_type_char != 'A':
        seq_manager = get_seq_manager()
        if not seq_manager.verify_in_seq(src_id, seq_num):
            last_seq = seq_manager._in_seq_map.get(src_id, 0)
            raise ValueError(f"Replay detected or old sequence: {seq_num} (SRC: {src_id}, LAST: {last_seq})")

    return {
        "version": version,
        "frame_type": chr(frame_type_byte),
        "team_id": team_id,
        "src_id": src_id,
        "dst_id": dst_id,
        "hop_count": hop_count,
        "flags": flags,
        "seq_num": seq_num,
        "payload": final_payload
    }
