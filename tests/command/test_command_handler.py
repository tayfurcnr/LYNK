# tests/command/test_command_handler.py

import pytest
from src.handlers.command.command_handler import handle_command, CommandID
from src.serializers.command_serializer import serialize_command
from src.tools.comm.mock_handler import MockUARTHandler as MockHandler
from src.core.frame_codec import build_mesh_frame
from src.tools.log.logger import logger

logger.disabled = True


def create_mock_frame(command_id: int, params: bytes = b'') -> bytes:
    """Creates a mock command frame for testing."""
    payload = serialize_command(command_id, params)
    frame = build_mesh_frame('C', 0x01, 0xFF, payload)
    return frame


@pytest.fixture
def mock_interface():
    """Provides a mock interface for testing."""
    interface = MockHandler()
    return interface


def test_handle_reboot_command(mock_interface):
    """Tests the handle_reboot command."""
    command_id = CommandID.REBOOT.value
    frame = create_mock_frame(command_id, b'')
    handle_command(frame[3:], {"src_id": 0x01}, mock_interface)
    assert "[COMMAND] SENT | CMD: REBOOT" in str(mock_interface.buffer[0])


def test_handle_set_mode_command(mock_interface):
    """Tests the handle_set_mode command."""
    mode = 1  # Example mode
    command_id = CommandID.SET_MODE.value
    frame = create_mock_frame(command_id, bytes([mode]))
    handle_command(frame[3:], {"src_id": 0x01}, mock_interface)
    assert "[COMMAND] SENT | CMD: SET_MODE | MODE: 1" in str(mock_interface.buffer[0])


def test_handle_unknown_command(mock_interface):
    """Tests handling of an unknown command."""
    unknown_cmd_id = 0x99  # An ID not defined in CommandID
    frame = create_mock_frame(unknown_cmd_id, b'')
    handle_command(frame[3:], {"src_id": 0x01}, mock_interface)
    assert f"[COMMAND] UNKNOWN CMD: {unknown_cmd_id} FROM SRC: 1" in str(mock_interface.buffer[0])
