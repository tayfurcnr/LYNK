import pytest
import struct
from lynk.core.frame_codec import build_mesh_frame, parse_mesh_frame
from lynk.shared.config import manager

def setup_module():
    # Setup standard config for security tests
    manager._config = {
        "protocol": {
            "start_byte": 84, "start_byte_2": 199, "version": 2
        },
        "vehicle": {"id": 1, "team_id": 10},
        "security": {
            "enabled": True,
            "key": "A" * 64 # 32-byte hex key
        }
    }

def test_security_tamper_detection():
    """Verify that any modification to the encrypted payload or CRC is detected."""
    # Each sub-case uses its own seq_num: anti-replay is checked before the CRC-16
    # check, so reusing a seq_num across parse_mesh_frame() calls in this test would
    # trigger a replay rejection instead of exercising the tamper detection path.

    # Tamper with the encrypted portion (payload starts at index 16: 15-byte header + 1-byte header CRC-8)
    frame1 = build_mesh_frame(frame_type='T', src_id=2, dst_id=1, payload=b"SECRET_DATA", seq_num=2000)
    tampered_payload = bytearray(frame1)
    mid_payload_idx = 16 + (len(frame1) - 16 - 2) // 2
    tampered_payload[mid_payload_idx] ^= 0xFF # Flip bits in the middle of the encrypted payload

    with pytest.raises(ValueError, match="Decryption failed|CRC-16 uyuşmazlığı"):
        parse_mesh_frame(bytes(tampered_payload))

    # Tamper with frame CRC-16 (last 2 bytes)
    frame2 = build_mesh_frame(frame_type='T', src_id=2, dst_id=1, payload=b"SECRET_DATA", seq_num=2001)
    tampered_crc = bytearray(frame2)
    tampered_crc[-1] ^= 0x01
    with pytest.raises(ValueError, match="CRC-16 uyuşmazlığı"):
        parse_mesh_frame(bytes(tampered_crc))
    
    print("\n[SUCCESS] Tamper detection verified.")

def test_security_replay_attack():
    """Verify that re-sending the same packet is rejected by SequenceManager."""
    src_id = 5
    seq = 3000
    frame = build_mesh_frame(frame_type='T', src_id=src_id, dst_id=1, payload=b"REPLAY_ME", seq_num=seq)
    
    # 1. First time should pass
    decoded = parse_mesh_frame(frame)
    assert decoded["seq_num"] == seq
    
    # 2. Second time with exact same frame/seq should fail
    with pytest.raises(ValueError, match="Replay detected or old sequence"):
        parse_mesh_frame(frame)
        
    # 3. Third time with OLDER sequence should also fail
    old_frame = build_mesh_frame(frame_type='T', src_id=src_id, dst_id=1, payload=b"OLD", seq_num=seq-1)
    with pytest.raises(ValueError, match="Replay detected or old sequence"):
        parse_mesh_frame(old_frame)

    print("[SUCCESS] Replay attack prevention verified.")

def test_security_team_id_isolation():
    """Verify that packets from a different Team ID are correctly identified."""
    # Current team is 10 (from setup)
    enemy_team = 99
    frame = build_mesh_frame(frame_type='T', src_id=2, dst_id=1, payload=b"ENEMY_INTEL", team_id=enemy_team, seq_num=4000)
    
    decoded = parse_mesh_frame(frame)
    assert decoded["team_id"] == enemy_team
    
    # In a real app, the dispatcher would drop this. 
    # Here we just verify the codec extracts it correctly for the higher layer to decide.
    assert decoded["team_id"] != manager.get("vehicle.team_id")
    
    print("[SUCCESS] Team ID isolation verified.")

if __name__ == "__main__":
    pytest.main([__file__])
