# test_receive_command_set_mode.py

from src.handlers.comm.mock_handler import MockUARTHandler
from src.serializers.command_serializer import serialize_command
from src.core.frame_codec import build_mesh_frame, parse_mesh_frame
from src.core.frame_router import route_frame

def main():
    uart = MockUARTHandler()
    uart.start()

    # — SET_MODE (komut ID: 0x02, param: 3)
    payload = serialize_command(0x02, bytes([3]))
    frame = build_mesh_frame('C', src_id=0x40, dst_id=1, payload=payload)
    uart.inject_frame(frame)

    raw_frame = uart.read()
    if raw_frame:
        parsed = parse_mesh_frame(raw_frame)
        route_frame(parsed, uart_handler=uart)

    uart.stop()

if __name__ == "__main__":
    main()
