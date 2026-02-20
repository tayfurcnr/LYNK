import pytest
from unittest.mock import MagicMock, patch
from lynk.application.event.tools.dispatcher import send_event
from lynk.core.frame_codec import parse_mesh_frame
from lynk.core.frame_router import route_frame
from lynk.shared.comm.interface_factory import create_interface
from lynk.application.event.serializer.dispatcher import serialize_event, deserialize_event
# Enum values
EVENT_CUSTOM = 100
PRIORITY_HIGH = 2

@pytest.fixture
def mock_interface():
    interface = MagicMock()
    interface.send = MagicMock()
    return interface

def test_send_event_logic(mock_interface):
    """Test send_event utility with redundancy."""
    
    # Configure redundancy: HIGH priority should send twice (0ms, 100ms)
    with patch("lynk.application.event.tools.dispatcher.get_config") as mock_conf:
        mock_conf.return_value = {
            "event": {
                "redundancy": {
                    "high": {"delays_ms": [0, 50]}
                }
            }
        }
        
        send_event(
            interface=mock_interface,
            event_type=EVENT_CUSTOM,
            priority=PRIORITY_HIGH,
            payload_params={"event_name": "TEST_EVENT", "description": "Integration Test"},
            dst_id=0xFF
        )
        
        # Verify it was called twice (redundancy)
        assert mock_interface.send.call_count == 2
        
        # Verify content of the frame
        call_args = mock_interface.send.call_args[0][0]
        parsed = parse_mesh_frame(call_args)
        assert parsed["frame_type"] == 'E'
        assert parsed["dst_id"] == 0xFF
        
        # Verify inner event
        event = deserialize_event(parsed["payload"])
        assert event["event_type"] == EVENT_CUSTOM
        assert event["payload"]["event_name"] == "TEST_EVENT"

def test_receive_event_dispatch():
    """Test full reception flow: Router -> Dispatcher -> Handler."""
    
    # Construct a valid event frame
    event_payload = serialize_event(
        event_type=EVENT_CUSTOM,
        priority=PRIORITY_HIGH,
        transaction_id="dispatch-test",
        payload_params={"event_name": "DISPATCH_TEST", "description": "Should trigger handler"}
    )
    
    frame_dict = {
        "frame_type": 'E',
        "src_id": 10,
        "dst_id": 0xFF,
        "team_id": 255,
        "payload": event_payload,
        "hop_count": 0
    }
    
    # Patch event definition lookup to inject a deterministic mock handler.
    mock_handler = MagicMock()
    mock_def = MagicMock()
    mock_def.name = "CUSTOM_EVENT"
    mock_def.handler = mock_handler
    with patch("lynk.application.event.handler.dispatcher.event_definitions.get", return_value=mock_def):
        route_frame(frame_dict, interface=None)
        
        # Verify handler was called
        mock_handler.assert_called_once()
        
        # Check args
        args = mock_handler.call_args
        # args[0] = event_type, args[1] = event_data ...
        assert args[0][0] == EVENT_CUSTOM
        assert args[0][1]["payload"]["event_name"] == "DISPATCH_TEST"
