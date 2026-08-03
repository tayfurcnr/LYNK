import pytest
import time
import os
from lynk.core.frame_codec import build_mesh_frame, parse_mesh_frame
from lynk.shared.config import manager

def setup_module():
    manager._config = {
        "protocol": {
            "start_byte": 84, "start_byte_2": 199, "version": 3
        },
        "vehicle": {"id": 1, "team_id": 1},
        "security": {"enabled": False} # Disable security for raw performance focus
    }

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
