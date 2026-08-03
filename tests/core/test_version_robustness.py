import pytest
import struct
from lynk.core.frame_codec import build_mesh_frame, parse_mesh_frame, CRC8_FUNC
from lynk.shared.config import manager

def setup_module():
    manager._config = {
        "protocol": {
            "start_byte": 84, "start_byte_2": 199, "version": 2
        },
        "vehicle": {"id": 1, "team_id": 1},
        "security": {"enabled": False}
    }

def _with_refreshed_header_crc(frame: bytes) -> bytes:
    """Recompute the header CRC-8 (byte 15) after mutating a header field,
    so the frame reaches the version check instead of failing header integrity."""
    frame = bytearray(frame)
    frame[15] = CRC8_FUNC(bytes(frame[0:15]))
    return bytes(frame)

def test_version_mismatch_rejection():
    """Verify that frames with incorrect protocol versions are rejected."""

    # 1. Valid v2 frame
    valid_v2 = build_mesh_frame(frame_type='T', src_id=1, dst_id=2, payload=b"HELLO", seq_num=6000)
    decoded = parse_mesh_frame(valid_v2)
    assert decoded["version"] == 2

    # 2. Fabricate a v1 frame (version is at index 2, inside the header-CRC-8-covered region)
    v1_frame = bytearray(valid_v2)
    v1_frame[2] = 1
    v1_frame = _with_refreshed_header_crc(bytes(v1_frame))

    with pytest.raises(ValueError, match="Protokol versiyonu uyuşmuyor"):
        parse_mesh_frame(v1_frame)

    # 3. Future version (v99)
    v99_frame = bytearray(valid_v2)
    v99_frame[2] = 99
    v99_frame = _with_refreshed_header_crc(bytes(v99_frame))
    with pytest.raises(ValueError, match="Protokol versiyonu uyuşmuyor"):
        parse_mesh_frame(v99_frame)

    print("\n[SUCCESS] Version mismatch rejection verified.")

def test_header_completeness_robustness():
    """Verify that truncated frames are handled without crashing."""

    # Min length is 18 bytes (15-byte header + 1-byte header CRC-8 + 2-byte frame CRC-16)
    with pytest.raises(ValueError, match="Frame çok kısa"):
        parse_mesh_frame(b"LY") # Only start bytes

    with pytest.raises(ValueError, match="Frame çok kısa"):
        parse_mesh_frame(b"LY" + b"\x02\x43\x01\x01\x01\x00\x00\x00\x00\x00") # 12 bytes

    print("[SUCCESS] Header completeness robustness verified.")

if __name__ == "__main__":
    pytest.main([__file__])
