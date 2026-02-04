import pytest
import struct
from src.core.frame_codec import build_mesh_frame, parse_mesh_frame
from src.shared.config import manager

def setup_module():
    # Setup standard config for security tests
    manager._config = {
        "protocol": {
            "start_byte": 84, "start_byte_2": 199, "version": 2,
            "compression_enabled": False
        },
        "vehicle": {"id": 1, "team_id": 10},
        "security": {
            "enabled": True,
            "key": "A" * 64 # 32-byte hex key
        }
    }

def test_security_tamper_detection():
    """Verify that any modification to the encrypted payload or CRC is detected."""
    frame = build_mesh_frame(frame_type='T', src_id=2, dst_id=1, payload=b"SECRET_DATA", seq_num=2000)
    
    # Tamper with the encrypted portion (starts at index 11)
    tampered_payload = bytearray(frame)
    tampered_payload[15] ^= 0xFF # Flip bits in the middle of payload
    
    with pytest.raises(ValueError, match="Decryption failed|CRC uyuşmazlığı"):
        parse_mesh_frame(bytes(tampered_payload))

    # Tamper with CRC (last 2 bytes)
    tampered_crc = bytearray(frame)
    tampered_crc[-1] ^= 0x01
    with pytest.raises(ValueError, match="CRC uyuşmazlığı"):
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
