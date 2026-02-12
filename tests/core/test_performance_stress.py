import pytest
import time
import os
from lynk.core.frame_codec import build_mesh_frame, parse_mesh_frame
from lynk.shared.config import manager

def setup_module():
    manager._config = {
        "protocol": {
            "start_byte": 84, "start_byte_2": 199, "version": 2,
            "compression_enabled": True,
            "compression_threshold": 128
        },
        "vehicle": {"id": 1, "team_id": 1},
        "security": {"enabled": False} # Disable security for raw performance focus
    }

def test_performance_lz4_compression_efficiency():
    """Verify that LZ4 compression handles different payload types correctly."""
    
    # 1. Non-compressible data (Random)
    random_payload = os.urandom(200)
    frame_rand = build_mesh_frame(frame_type='D', src_id=1, dst_id=2, payload=random_payload)
    decoded_rand = parse_mesh_frame(frame_rand)
    assert decoded_rand["payload"] == random_payload
    # Should NOT be compressed (overhead > gain)
    assert not (decoded_rand["flags"] & 0x01)
    
    # 2. Highly-compressible data (Zeros)
    zero_payload = b"\x00" * 500
    frame_zero = build_mesh_frame(frame_type='D', src_id=1, dst_id=2, payload=zero_payload)
    decoded_zero = parse_mesh_frame(frame_zero)
    assert decoded_zero["payload"] == zero_payload
    # MUST be compressed
    assert (decoded_zero["flags"] & 0x01)
    # Compressed size should be much smaller than 500
    # Header 11 + Payload Len field in header...
    import struct
    payload_len = struct.unpack(">H", frame_zero[9:11])[0]
    assert payload_len < 100 # LZ4 should crush zeros
    
    # 3. Exactly at threshold
    threshold_payload = b"A" * 128
    frame_t = build_mesh_frame(frame_type='D', src_id=1, dst_id=2, payload=threshold_payload)
    decoded_t = parse_mesh_frame(frame_t)
    assert not (decoded_t["flags"] & 0x01), "Should not compress if len == threshold"

    print("\n[SUCCESS] LZ4 compression efficiency verified.")

def test_performance_flood_load():
    """Simulate a high-frequency packet stream."""
    packet_count = 100
    start_time = time.time()
    
    for i in range(packet_count):
        payload = f"FLOOD_PACKET_{i}".encode()
        frame = build_mesh_frame(frame_type='T', src_id=1, dst_id=2, payload=payload, seq_num=5000+i)
        decoded = parse_mesh_frame(frame)
        assert decoded["payload"] == payload
        
    duration = time.time() - start_time
    pps = packet_count / duration
    print(f"\n[SUCCESS] Flood test: {packet_count} packets in {duration:.3f}s ({pps:.1f} packets/sec)")
    # Basic sanity check
    assert duration < 1.0, f"Performance too low: {duration}s for {packet_count} packets"

if __name__ == "__main__":
    pytest.main([__file__])
