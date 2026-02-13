import pytest
from unittest.mock import MagicMock, patch
import lynk

def test_command_wrapper_kwargs():
    """Verify that **kwargs are properly passed from wrappers to send_command."""
    mock_interface = MagicMock()
    
    # We will patch send_command inside dispatcher to see what it receives
    with patch("lynk.application.command.tools.dispatcher.send_command") as mock_send_command:
        # Call a wrapper with a callback (which is a kwarg in the wrapper)
        my_callback = lambda x: print(x)
        lynk.command.cmd_flight_arming(
            mock_interface, 
            arm=True, 
            dst=5, 
            callback=my_callback,
            retry_interval=1.5
        )
        
        # Check if send_command was called with the correct kwargs
        args, kwargs = mock_send_command.call_args
        assert kwargs["callback"] == my_callback
        assert kwargs["retry_interval"] == 1.5
        assert kwargs["arm"] == True
        assert kwargs["dst"] == 5

def test_event_register_handler():
    """Verify that register_handler properly registers and triggers callbacks."""
    mock_callback = MagicMock()
    EVENT_TYPE = 999
    
    lynk.event.register_handler(EVENT_TYPE, mock_callback)
    
    # Simulate an incoming event of that type
    event_data = {"event_type": EVENT_TYPE, "source_vehicle_id": 10}
    
    # We call the internal dispatcher handle_event or route_frame
    from lynk.application.event.handler.dispatcher import handle_event
    
    # We need to mock deserialize_event to return our dict
    with patch("lynk.application.event.handler.dispatcher.deserialize_event", return_value=event_data):
        with patch("lynk.application.event.handler.dispatcher.event_definitions", {}):
             handle_event(b"dummy_payload", {"src_id": 10}, MagicMock())
    
    mock_callback.assert_called_once_with(event_data)

def test_unified_process_api():
    """Verify that lynk.process() correctly parses and routes."""
    mock_interface = MagicMock()
    dummy_raw = b"dummy_raw_frame"
    dummy_dict = {"frame_type": "C", "dst_id": 0xFF}
    
    with patch("lynk.core.frame_router.parse_mesh_frame", return_value=dummy_dict) as mock_parse:
        with patch("lynk.core.frame_router.route_frame", return_value=True) as mock_route:
            result = lynk.process(dummy_raw, mock_interface)
            
            assert result is True
            mock_parse.assert_called_once_with(dummy_raw)
            mock_route.assert_called_once_with(dummy_dict, mock_interface)

def test_telemetry_register_handler():
    """Verify that telemetry register_handler correctly triggers callbacks."""
    from lynk.application.telemetry.tools.dispatcher import register_handler
    from lynk.application.telemetry.handler.dispatcher import handle_telemetry
    
    mock_cb = MagicMock()
    # Battery TLM ID is 34
    register_handler(34, mock_cb)
    
    tlm_data = {"tlm_id": 34, "voltage": 12.0, "level": 85.0}
    
    with patch("lynk.application.telemetry.handler.dispatcher.deserialize_telemetry", return_value=tlm_data):
        handle_telemetry(b"dummy_payload", {"src_id": 10, "hop_count": 1})
        
    # Verification (Callback receives data and meta)
    assert mock_cb.called
    data, meta = mock_cb.call_args[0]
    assert data["level"] == 85.0
    assert meta["src_id"] == 10
