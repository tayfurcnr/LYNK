import pytest
import struct
from lynk.core.frame_codec import build_mesh_frame, parse_mesh_frame
from lynk.shared.config import manager

def setup_module():
    manager._config = {
        "protocol": {
            "start_byte": 84, "start_byte_2": 199, "version": 2,
            "compression_enabled": False
        },
        "vehicle": {"id": 1, "team_id": 1},
        "security": {"enabled": False}
    }

def test_version_mismatch_rejection():
    """Verify that frames with incorrect protocol versions are rejected."""
    
    # 1. Valid v2 frame
    valid_v2 = build_mesh_frame(frame_type='T', src_id=1, dst_id=2, payload=b"HELLO", seq_num=6000)
    decoded = parse_mesh_frame(valid_v2)
    assert decoded["version"] == 2
    
    # 2. Fabricate a v1 frame (Version is at index 2)
    v1_frame = bytearray(valid_v2)
    v1_frame[2] = 1
    # Need to update CRC if we want to test version check specifically after CRC
    # but parse_mesh_frame checks version BEFORE CRC? No, it usually checks CRC first or has a basic check.
    # Actually, parse_mesh_frame in v2 checks version at data[2].
    
    with pytest.raises(ValueError, match="Protokol versiyonu uyuşmuyor"):
        parse_mesh_frame(bytes(v1_frame))
        
    # 3. Future version (v99)
    v99_frame = bytearray(valid_v2)
    v99_frame[2] = 99
    with pytest.raises(ValueError, match="Protokol versiyonu uyuşmuyor"):
        parse_mesh_frame(bytes(v99_frame))

    print("\n[SUCCESS] Version mismatch rejection verified.")

def test_header_completeness_robustness():
    """Verify that truncated frames are handled without crashing."""
    
    # Min length is 13 bytes
    with pytest.raises(ValueError, match="Frame çok kısa"):
        parse_mesh_frame(b"LY") # Only start bytes
        
    with pytest.raises(ValueError, match="Frame çok kısa"):
        parse_mesh_frame(b"LY" + b"\x02\x43\x01\x01\x01\x00\x00\x00\x00\x00") # 12 bytes
        
    print("[SUCCESS] Header completeness robustness verified.")

if __name__ == "__main__":
    pytest.main([__file__])
