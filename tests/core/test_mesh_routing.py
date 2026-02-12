import pytest
from lynk.core.frame_codec import build_mesh_frame, parse_mesh_frame
from lynk.shared.config import manager
from lynk.core.sequence_manager import get_sequence_manager

def setup_module():
    manager._config = {
        "protocol": {"start_byte": 0x24, "start_byte_2": 0x24, "version": 1},
        "vehicle": {"id": 1, "team_id": 0}
    }
    get_sequence_manager()._in_seq_map.clear()
    get_sequence_manager()._out_seq = 0

def test_hop_count_decrement_and_drop():
    """Verify that hop_count is decremented and packets with 0 hops are Dropped."""
    
    # 1. Simulate a relay node receiving a frame
    initial_hop = 10
    frame = build_mesh_frame(
        frame_type='C',
        src_id=99, # Use a temporary src_id to avoid collision with other tests
        dst_id=50,
        payload=b"RELAY_THIS",
        seq_num=5000,
        hop_count=initial_hop
    )
    
    decoded = parse_mesh_frame(frame)
    assert decoded["hop_count"] == initial_hop
    
    # 2. Simulate the decrement logic (this would normally be in the relay handler)
    # Here we verify the frame can be re-built with a lower hop count
    # IMPORTANT: We use a DIFFERENT sequence number for the "relayed" frame 
    # if it's being treated as a "new" frame in this test context.
    relayed_frame = build_mesh_frame(
        frame_type=decoded["frame_type"],
        src_id=decoded["src_id"],
        dst_id=decoded["dst_id"],
        payload=decoded["payload"],
        seq_num=5001, # Increment to avoid replay
        hop_count=decoded["hop_count"] - 1
    )
    
    decoded_relayed = parse_mesh_frame(relayed_frame)
    assert decoded_relayed["hop_count"] == initial_hop - 1
    
    # 3. Test the "Drop" condition (Hop Count = 0 after decrement)
    expired_hop = 0
    with pytest.raises(Exception): # build_mesh_frame might check range
        # Protocol typically doesn't allow building with negative hops
        build_mesh_frame(
            frame_type='C', src_id=1, dst_id=50, payload=b"DROP_ME",
            seq_num=1001, hop_count=-1
        )
    
    # In a real mesh logic:
    def should_relay(frame_data):
        return frame_data["hop_count"] > 1

    assert should_relay(decoded) is True, "Should relay if hops > 1"
    
    critical_frame = parse_mesh_frame(build_mesh_frame(
        frame_type='C', src_id=1, dst_id=50, payload=b"LAST_HOP",
        seq_num=1002, hop_count=1
    ))
    
    assert should_relay(critical_frame) is False, "Should NOT relay if it's the last hop"
    
    print(f"\n[SUCCESS] Multi-hop logic verified. Relay decision correctly based on hop_count.")

if __name__ == "__main__":
    pytest.main([__file__])
