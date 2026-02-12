import pytest
import struct
import lynk
from lynk.application.mavlink.serializer.dispatcher import (
    serialize_mavlink,
    deserialize_mavlink
)
from lynk.core.frame_codec import build_mesh_frame, parse_mesh_frame

def test_mavlink_proto_serialization():
    """Test that MAVLink packets are correctly mapped to Protobuf."""
    raw_mavlink = b"\xFE\x09\x01\x01\x01\x00_payload_\x12\x34"
    sys_id = 1
    comp_id = 190
    
    # Serialize
    proto_data = serialize_mavlink(raw_mavlink, system_id=sys_id, component_id=comp_id)
    assert len(proto_data) > 0
    
    # Deserialize
    decoded = deserialize_mavlink(proto_data)
    assert decoded["payload"] == raw_mavlink
    assert decoded["system_id"] == sys_id
    assert decoded["component_id"] == comp_id
    assert "timestamp_us" in decoded

def test_mavlink_full_frame_flow():
    """Test the full flow from MAVLink payload to LYNK frame and back."""
    raw_mavlink = b"\xFD\x09\x00\x00\x00\x01\x00\x00\x00_mavlink_v2_\xAB\xCD"
    dst_id = 5
    src_id = 1
    
    # 1. Serialize to proto
    proto_payload = serialize_mavlink(raw_mavlink)
    
    # 2. Build LYNK Frame (Type 'M')
    frame = build_mesh_frame(
        frame_type='M',
        src_id=src_id,
        dst_id=dst_id,
        payload=proto_payload
    )
    
    # 3. Parse LYNK Frame
    parsed_lynk = parse_mesh_frame(frame)
    assert parsed_lynk["frame_type"] == 'M'
    assert parsed_lynk["src_id"] == src_id
    assert parsed_lynk["dst_id"] == dst_id
    
def test_mavlink_callback_triggering():
    """Test that registering a callback and receiving a frame works."""
    import lynk
    received_packets = []
    
    def my_callback(raw, tunnel, frame):
        received_packets.append(raw)
        
    # Register
    lynk.mavlink.on_mavlink_received(my_callback)
    
    # Simulate receiving an 'M' frame
    raw_mavlink = b"\xFD_TEST_PACKET_"
    proto_payload = serialize_mavlink(raw_mavlink)
    frame_meta = {"src_id": 10, "dst_id": 1, "frame_type": 'M', "hop_count": 0}
    
    from lynk.application.mavlink.handler.dispatcher import handle_mavlink
    handle_mavlink(proto_payload, frame_meta)
    
    assert len(received_packets) == 1
    assert received_packets[0] == raw_mavlink

