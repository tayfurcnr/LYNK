# test_receive_command_invalid.py

from mock_uart import MockUARTHandler
from src.serializers.command_serializer import serialize_command
from src.frame_codec import build_mesh_frame, parse_mesh_frame
from src.frame_router import route_frame

def main():
    uart = MockUARTHandler()
    uart.start()

    # — Bilinmeyen komut ID: 0x99
    payload = serialize_command(0x99, b'\x00\x01')
    frame = build_mesh_frame('C', src_id=0x50, dst_id=1, payload=payload)
    uart.inject_frame(frame)

    raw_frame = uart.read()
    if raw_frame:
        parsed = parse_mesh_frame(raw_frame)
        route_frame(parsed, uart_handler=uart)

    uart.stop()

if __name__ == "__main__":
    main()
