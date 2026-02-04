from __future__ import annotations
import src.shared.comm.interface_factory as factory
from src.shared.config import manager

def test_mock_uart_interface_send_and_read():
    # Clear singleton cache for clean test
    factory._interface_instance = None
    
    # Setup config
    manager._config = {
        "interface": {"comm_type": "MOCK_UART"},
        "protocol": {"start_byte": 84, "start_byte_2": 199, "version": 2}
    }
    
    interface = factory.create_interface()

    # Basic send/read functionality
    data = b'\x01\x02\x03'
    interface.send(data)
    received = interface.read()
    assert received == data, f"Expected {data!r}, got {received!r}"
