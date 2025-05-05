from mock_uart import MockUARTHandler
from src.tools.command_dispatcher import cmd_landing
from src.frame_codec import parse_mesh_frame
from src.frame_router import route_frame
from src.serializers.ack_serializer import deserialize_ack

def process_one_command(uart: MockUARTHandler):
    raw_frame = uart.read()
    if raw_frame:
        print(f"📥 Frame alındı ({len(raw_frame)} byte)")
        frame_dict = parse_mesh_frame(raw_frame)
        route_frame(frame_dict, uart_handler=uart)

def check_for_ack(uart: MockUARTHandler, expected_cmd_id: int):
    for i in range(2):  # İlk komut, sonra ACK
        raw_frame = uart.read()  # Burada gönderilen frame'in kopyasını alıyoruz
        if raw_frame:
            print(f"\n📥 Frame {i+1} alındı ({len(raw_frame)} byte)")
            frame_dict = parse_mesh_frame(raw_frame)
            route_frame(frame_dict, uart_handler=uart)

    uart.stop()

def test_landing_without_target():
    print("\n=== Test: LANDING → Mevcut konuma iniş (parametresiz) ===")
    uart = MockUARTHandler()
    uart.start()

    cmd_landing(dst=1, src=0x01, uart=uart)

    process_one_command(uart)
    check_for_ack(uart, expected_cmd_id=0x04)

def test_landing_with_target():
    print("\n=== Test: LANDING → Hedef konuma iniş (LAT, LON) ===")
    uart = MockUARTHandler()
    uart.start()

    cmd_landing(
        target_lat=37.123456,
        target_lon=32.654321,
        dst=1,
        src=0x01,
        uart=uart
    )

    process_one_command(uart)
    check_for_ack(uart, expected_cmd_id=0x04)

if __name__ == "__main__":
    test_landing_without_target()
    test_landing_with_target()
