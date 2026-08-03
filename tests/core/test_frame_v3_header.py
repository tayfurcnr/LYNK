import pytest
from unittest.mock import patch
from lynk.core.frame_codec import build_mesh_frame, parse_mesh_frame, CRC8_FUNC
from lynk.shared.utils.crypto import LynkCrypto
from lynk.shared.config import manager


def setup_module():
    manager._config = {
        "protocol": {"start_byte": 84, "start_byte_2": 199, "version": 3},
        "vehicle": {"id": 1, "team_id": 1},
        "security": {"enabled": True, "key": "B" * 64},
    }


def test_header_crc8_catches_header_corruption_distinct_from_frame_crc16():
    """A corrupted header byte must be caught by the header CRC-8, with a
    message distinct from a frame CRC-16 mismatch (corruption in the payload/CRC tail)."""
    frame = build_mesh_frame(frame_type='T', src_id=30, dst_id=1, payload=b"PING", seq_num=100)

    # Corrupt a header field (hop_count, index 7) without refreshing the header CRC-8.
    corrupted_header = bytearray(frame)
    corrupted_header[7] ^= 0xFF
    with pytest.raises(ValueError, match="Header CRC-8 uyuşmazlığı"):
        parse_mesh_frame(bytes(corrupted_header))

    # Corrupt only the trailing frame CRC-16 (header stays intact) -> different error.
    frame2 = build_mesh_frame(frame_type='T', src_id=30, dst_id=1, payload=b"PING", seq_num=101)
    corrupted_tail = bytearray(frame2)
    corrupted_tail[-1] ^= 0xFF
    with pytest.raises(ValueError, match="Frame CRC-16 uyuşmazlığı"):
        parse_mesh_frame(bytes(corrupted_tail))


def test_header_crc8_field_matches_codec():
    """Sanity check that the header CRC-8 byte (index 15) is exactly CRC8_FUNC(header[0:15])."""
    frame = build_mesh_frame(frame_type='T', src_id=31, dst_id=1, payload=b"PONG", seq_num=200)
    assert frame[15] == CRC8_FUNC(frame[0:15])


def test_replay_rejected_before_decryption_is_attempted():
    """Anti-replay must reject a repeated sequence number before the payload is
    ever handed to the crypto engine — verified by spying on LynkCrypto.decrypt."""
    frame = build_mesh_frame(frame_type='T', src_id=42, dst_id=1, payload=b"SECRET", seq_num=9000)

    with patch.object(LynkCrypto, "decrypt", wraps=LynkCrypto.decrypt, autospec=True) as spy_decrypt:
        # First delivery: valid, decrypt is invoked normally.
        parse_mesh_frame(frame)
        assert spy_decrypt.call_count == 1

        # Replayed delivery: must be rejected before decrypt is attempted again.
        with pytest.raises(ValueError, match="Replay detected or old sequence"):
            parse_mesh_frame(frame)
        assert spy_decrypt.call_count == 1, "decrypt() must not be called on a replayed frame"
