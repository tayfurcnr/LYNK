# test_receive_command.py

import struct
from src.handlers.comm.mock_handler import MockUARTHandler
from src.serializers.command_serializer import serialize_command
from src.core.frame_codec import build_mesh_frame, parse_mesh_frame
from src.core.frame_router import route_frame

def inject_and_process(uart, frame):
    uart.inject_frame(frame)
    raw = uart.read()
    if raw:
        print(f"\n📥 Frame alındı ({len(raw)} byte)")
        parsed = parse_mesh_frame(raw)
        route_frame(parsed, uart_handler=uart)

def main():
    uart = MockUARTHandler()
    uart.start()

    print("\n=== 🚁 TEST 1: TAKEOFF (sadece irtifa) ===")
    payload1 = serialize_command(0x03, struct.pack(">f", 50.0))
    frame1 = build_mesh_frame('C', src_id=0x20, dst_id=1, payload=payload1)
    inject_and_process(uart, frame1)

    print("\n=== 🛰️ TEST 2: TAKEOFF (hedef lokasyonlu) ===")
    payload2 = serialize_command(0x03, struct.pack(">ffff", 50.0, 37.7749, 32.7767, 80.0))
    frame2 = build_mesh_frame('C', src_id=0x21, dst_id=1, payload=payload2)
    inject_and_process(uart, frame2)

    print("\n=== 🔁 TEST 3: REBOOT (parametresiz) ===")
    payload3 = serialize_command(0x01)
    frame3 = build_mesh_frame('C', src_id=0x30, dst_id=1, payload=payload3)
    inject_and_process(uart, frame3)

    print("\n=== ⚙️ TEST 4: SET_MODE (mode=3) ===")
    payload4 = serialize_command(0x02, bytes([3]))
    frame4 = build_mesh_frame('C', src_id=0x40, dst_id=1, payload=payload4)
    inject_and_process(uart, frame4)

    print("\n=== ❌ TEST 5: GEÇERSİZ KOMUT (0x99) ===")
    payload5 = serialize_command(0x99, b'\x00\x01')
    frame5 = build_mesh_frame('C', src_id=0x50, dst_id=1, payload=payload5)
    inject_and_process(uart, frame5)

    uart.stop()

if __name__ == "__main__":
    main()
