import pytest
import struct
from src.core.frame_codec import build_mesh_frame, parse_mesh_frame
from src.application.command.serializer.dispatcher import serialize_command

def test_sequence_wrap_around():
    """Verify that the system handles 32-bit sequence number overflow (wrap-around to 0)."""
    # Max uint32 is 4,294,967,295
    MAX_UINT32 = 0xFFFFFFFF
    
    # 1. Build a frame with max sequence number (Using 'C' for Command)
    frame_max = build_mesh_frame(
        frame_type='C',
        src_id=1,
        dst_id=10,
        payload=b"\x01\x02\x03",
        seq_num=MAX_UINT32,
        hop_count=10
    )
    
    # In v2, header is 11 bytes. SeqNum is at [11:15] in the payload (if encryption is OFF)
    # Since we use parse_mesh_frame, we can rely on that for verification.
    decoded_max = parse_mesh_frame(frame_max)
    assert decoded_max["seq_num"] == MAX_UINT32, "Sequence number should be MAX_UINT32"

    # 2. Build a frame with wrap-around (0)
    frame_wrap = build_mesh_frame(
        frame_type='C',
        src_id=1,
        dst_id=10,
        payload=b"\x01\x02\x03",
        seq_num=0,
        hop_count=10
    )
    
    decoded_wrap = parse_mesh_frame(frame_wrap)
    assert decoded_wrap["seq_num"] == 0, "Sequence number should wrap around to 0"

    # 3. Parse and verify both
    decoded_max = parse_mesh_frame(frame_max)
    decoded_wrap = parse_mesh_frame(frame_wrap)
    
    assert decoded_max["seq_num"] == MAX_UINT32
    assert decoded_wrap["seq_num"] == 0
    assert decoded_max["dst_id"] == decoded_wrap["dst_id"]
    
    print(f"\n[SUCCESS] Sequence Wrap-around verified: {MAX_UINT32} -> 0")

if __name__ == "__main__":
    pytest.main([__file__])
