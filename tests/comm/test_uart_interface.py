import pytest
from unittest.mock import MagicMock, patch
from src.shared.comm.uart_handler import UARTHandler
from src.core.frame_codec import build_mesh_frame
from src.shared.config import manager

@patch('src.shared.comm.uart_handler.Serial')
def test_uart_handler_extraction(mock_serial_class):
    """Verify that UARTHandler extracts multiple frames from a byte stream."""
    
    # 1. Setup mock config
    manager._config = {
        "protocol": {
            "start_byte": 84,
            "start_byte_2": 199,
            "version": 2,
            "compression_enabled": False
        },
        "vehicle": {"id": 1, "team_id": 1},
        "uart": {
            "port": "MOCK_PORT",
            "baudrate": 115200,
            "timeout": 0.1
        }
    }
    
    # Mock serial instance
    mock_serial = MagicMock()
    mock_serial.is_open = True
    mock_serial_class.return_value = mock_serial
    
    handler = UARTHandler()
    
    # 2. Prepare payload and frames
    payload1 = b"UART_MSG_1"
    payload2 = b"UART_MSG_2_LONGER"
    
    frame1 = build_mesh_frame(frame_type='T', src_id=1, dst_id=2, payload=payload1, seq_num=100)
    frame2 = build_mesh_frame(frame_type='T', src_id=1, dst_id=2, payload=payload2, seq_num=101)
    
    # Noise bytes
    noise = b"\x00\xFF\xAA"
    
    # 3. Simulate arrival of data
    stream = noise + frame1 + noise + frame2
    handler.rx_queue.put(stream)
    
    # 4. Extract and verify
    # First read (should find frame1)
    res1 = handler.read()
    assert res1 == frame1
    
    # Second read (should find frame2)
    res2 = handler.read()
    assert res2 == frame2
    
    # Third read (should be None)
    res3 = handler.read()
    assert res3 is None
    
    print("\n[SUCCESS] UART Interface test verified with 11-byte header support.")

if __name__ == "__main__":
    pytest.main([__file__])
