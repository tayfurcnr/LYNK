# test_receive_command_takeoff.py

import struct
from src.handlers.comm.mock_handler import MockUARTHandler
from src.serializers.command_serializer import serialize_command
from src.core.frame_codec import build_mesh_frame, parse_mesh_frame
from src.core.frame_router import route_frame

def main():
    uart = MockUARTHandler()
    uart.start()

    # — TAKEOFF sadece irtifa (4 byte)
    payload1 = serialize_command(0x03, struct.pack(">f", 50.0))
    frame1 = build_mesh_frame('C', src_id=0x20, dst_id=1, payload=payload1)
    uart.inject_frame(frame1)

    # — TAKEOFF hedef konumlu (16 byte)
    payload2 = serialize_command(0x03, struct.pack(">ffff", 50.0, 37.7749, 32.7767, 80.0))
    frame2 = build_mesh_frame('C', src_id=0x21, dst_id=1, payload=payload2)
    uart.inject_frame(frame2)

    for _ in range(2):
        raw_frame = uart.read()
        if raw_frame:
            print(f"\n📥 Frame alındı ({len(raw_frame)} byte)")
            parsed = parse_mesh_frame(raw_frame)
            route_frame(parsed, uart_handler=uart)

    uart.stop()

if __name__ == "__main__":
    main()