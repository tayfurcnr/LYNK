def test_mock_uart_interface_send_and_read():
    from src.tools.comm.interface_factory import create_interface

    # Assumes config.json is set to use MOCK_UART
    interface = create_interface()

    # Basic send/read functionality
    data = b'\x01\x02\x03'
    interface.send(data)
    received = interface.read()
    assert received == data, f"Expected {data!r}, got {received!r}"
