from unittest.mock import MagicMock, patch
from lynk.shared.comm.uart_handler import UARTHandler
from lynk.core.frame_codec import build_mesh_frame
from lynk.shared.config import manager


@patch('lynk.shared.comm.uart_handler.Serial')
def test_uart_handler_drops_header_crc8_corrupted_frame_and_resyncs(mock_serial_class):
    """A frame with a corrupted header (breaking the header CRC-8) must be dropped
    without desyncing the framer — the next valid frame on the wire must still be found."""
    manager._config = {
        "protocol": {"start_byte": 84, "start_byte_2": 199, "version": 2},
        "vehicle": {"id": 1, "team_id": 1},
        "uart": {"port": "MOCK_PORT", "baudrate": 115200, "timeout": 0.1},
    }

    mock_serial = MagicMock()
    mock_serial.is_open = True
    mock_serial_class.return_value = mock_serial

    handler = UARTHandler()

    good_frame = build_mesh_frame(frame_type='T', src_id=1, dst_id=2, payload=b"GOOD_AFTER_BAD", seq_num=300)

    bad_frame = bytearray(build_mesh_frame(frame_type='T', src_id=1, dst_id=2, payload=b"CORRUPTED", seq_num=200))
    bad_frame[7] ^= 0xFF  # corrupt hop_count -> header CRC-8 mismatch, without touching sync bytes

    stream = bytes(bad_frame) + good_frame
    handler.rx_queue.put(stream)

    found = []
    for _ in range(len(stream) + 10):
        frame = handler.read()
        if frame is not None:
            found.append(frame)

    assert good_frame in found
    assert bytes(bad_frame) not in found
