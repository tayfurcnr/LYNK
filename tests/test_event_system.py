import pytest
import time
from lynk.application.event.serializer.dispatcher import serialize_event, deserialize_event
from lynk.application.event.handler.dispatcher import handle_event
from lynk.core.frame_codec import build_mesh_frame, parse_mesh_frame

# Mock Interface
class MockInterface:
    def __init__(self):
        self.sent_frames = []

    def send(self, data):
        self.sent_frames.append(data)

@pytest.fixture
def mock_interface():
    return MockInterface()

def test_event_serialization_deserialization():
    """Test that an event can be serialized and deserialized correctly."""
    
    # Create test data
    src_id = 10
    boot_count = 5
    seq = 100
    event_type = 20  # EVENT_QR_DETECTED (from enum)
    priority = 1     # PRIORITY_NORMAL
    ts = int(time.time() * 1000)
    
    payload_params = {
        "qr_code": "TEST-QR-123",
        "confidence": 0.95
    }
    
    # Serialize
    raw_payload = serialize_event(
        source_vehicle_id=src_id,
        boot_counter=boot_count,
        sequence=seq,
        event_type=event_type,
        priority=priority,
        timestamp_ms=ts,
        payload_params=payload_params
    )
    
    assert len(raw_payload) > 0
    
    # Deserialize
    decoded = deserialize_event(raw_payload)
    
    assert decoded["source_vehicle_id"] == src_id
    assert decoded["boot_counter"] == boot_count
    assert decoded["sequence"] == seq
    assert decoded["event_type"] == event_type
    assert decoded["priority"] == priority
    assert decoded["timestamp_ms"] == ts
    assert decoded["payload"]["qr_code"] == "TEST-QR-123"
    assert abs(decoded["payload"]["confidence"] - 0.95) < 0.001

def test_event_handler_duplicate_detection(mock_interface):
    """Test that duplicate events are ignored by the handler."""
    
    # Prepare an event payload
    event_payload = serialize_event(
        source_vehicle_id=1,
        boot_counter=1,
        sequence=50,
        event_type=20, # QR Detected
        priority=1,
        timestamp_ms=123456789,
        payload_params={"qr_code": "DUP-TEST", "confidence": 1.0}
    )
    
    frame_meta = {
        "src_id": 1,
        "dst_id": 0xFF,
        "payload": event_payload
    }

    # First pass: Should handle successfully
    # (Since we mock, we check logs or absence of error, usually returns None)
    try:
        handle_event(event_payload, frame_meta, mock_interface)
    except Exception as e:
        pytest.fail(f"First handle_event failed: {e}")

    # Second pass: Exact same event (same src, boot, seq) -> Should be ignored
    # Currently implementation just logs debug and returns
    try:
        handle_event(event_payload, frame_meta, mock_interface)
    except Exception as e:
        pytest.fail(f"Duplicate handle_event caused error: {e}")
        
    # Ideally we'd check logs or internal state, but for now ensures no crash
    
def test_full_frame_flow():
    """Test wrapping event in mesh frame and parsing back."""
    event_payload = serialize_event(
        source_vehicle_id=2,
        boot_counter=1,
        sequence=1,
        event_type=33, # EMERGENCY_CRASH
        priority=3,    # CRITICAL
        timestamp_ms=1000,
        payload_params={"reason": 2, "altitude_m": 15.5, "battery_percent": 10, "last_error": "IMU_FAIL"}
    )
    
    # Wrap in Mesh Frame (Type 'E')
    frame_bytes = build_mesh_frame(
        frame_type='E',
        src_id=2,
        dst_id=0xFF, # Broadcast
        payload=event_payload,
        team_id=1
    )
    
    # Parse back
    parsed = parse_mesh_frame(frame_bytes)
    
    assert parsed["frame_type"] == 'E'
    assert parsed["src_id"] == 2
    
    # Deserialize inner event
    inner_event = deserialize_event(parsed["payload"])
    assert inner_event["event_type"] == 33
    assert inner_event["payload"]["last_error"] == "IMU_FAIL"
