
import pytest
from unittest.mock import MagicMock, patch
from lynk.core.frame_codec import build_mesh_frame, parse_mesh_frame, load_team_id
from lynk.core.frame_router import route_frame

@pytest.fixture
def mock_config():
    with patch("lynk.core.frame_codec.get_config") as mock_get:
        mock_get.return_value = {
            "vehicle": {"id": 10, "team_id": 1},
            "protocol": {"start_byte": 0x54, "start_byte_2": 0xC7, "version": 1}
        }
        yield mock_get

def test_codec_team_id(mock_config):
    # Test Building Frame
    payload = b"HELLO"
    frame_bytes = build_mesh_frame(frame_type='C', src_id=10, dst_id=20, payload=payload)
    
    # Expected length v2: 11(header) + 4(seq) + 5(payload) + 2(crc) = 22
    assert len(frame_bytes) == 22, f"Frame length should be 22, got {len(frame_bytes)}"
    
    # Test Parsing Frame
    parsed = parse_mesh_frame(frame_bytes)
    assert parsed["team_id"] == 1
    assert parsed["src_id"] == 10
    assert parsed["dst_id"] == 20
    assert parsed["payload"] == payload

def test_router_filtering_success(mock_config):
    # Setup
    payload = b"CMD"
    frame_bytes = build_mesh_frame(frame_type='C', src_id=20, dst_id=0xFF, payload=payload) # Broadcast
    frame_dict = parse_mesh_frame(frame_bytes)
    
    # Mock Handler
    mock_handler = MagicMock()
    with patch("lynk.core.frame_router.dispatch_table", {'C': mock_handler}):
        route_frame(frame_dict, interface=None)
        
    # Should be called because team_id=1 (from build) matches config team_id=1
    mock_handler.assert_called_once()

def test_router_filtering_fail(mock_config):
    # Setup - Inject a frame with DIFFERENT Team ID manually
    # We can't use build_mesh_frame easily to fake it without patching config again for the build step
    # So we'll validly build one, then hack the byte.
    
    payload = b"CMD"
    frame_bytes = build_mesh_frame(frame_type='C', src_id=10, dst_id=0xFF, payload=payload)
    # Frame struct: start(0), start2(1), ver(2), type(3), TEAM(4)...
    # Change byte 4 from 1 to 2
    mutable_frame = bytearray(frame_bytes)
    mutable_frame[4] = 2
    # Note: CRC will fail if we parse normally. 
    # But route_frame takes a DICT. So let's cheat and construct the dict manually
    # or re-calculate CRC.
    
    frame_dict = {
        "frame_type": 'C',
        "team_id": 2, # DIFFERENT TEAM
        "src_id": 10,
        "dst_id": 0xFF,
        "payload": payload
    }
    
    # Mock Handler
    mock_handler = MagicMock()
    with patch("lynk.core.frame_router.dispatch_table", {'C': mock_handler}):
        # Patch load_team_id in router to ensure it sees '1'
        with patch("lynk.core.frame_router.load_team_id", return_value=1):
            route_frame(frame_dict, interface=None)
        
    # Should NOT be called
    mock_handler.assert_not_called()
