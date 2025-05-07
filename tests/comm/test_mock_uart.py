def test_mock_uart_send_and_read():
    from src.handlers.comm.mock_handler import MockUARTHandler
    uart = MockUARTHandler()
    uart.start()
    uart.send(b'\x01\x02\x03')
    frame = uart.read()
    assert frame == b'\x01\x02\x03'