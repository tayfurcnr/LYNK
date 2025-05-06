# test_send_command.py

from src.handlers.comm.mock_handler import MockUARTHandler
from src.tools.command.command_dispatcher import cmd_takeoff, cmd_goto
from src.core.frame_codec import parse_mesh_frame
from src.core.frame_router import route_frame

def main():
    uart = MockUARTHandler()
    uart.start()

    cmd_goto(target_lat = 40.8438,
             target_lon = 31.1565,
             target_alt=80.0,
             dst=1,
             src=0x10,
             uart=uart
    )

    # === Frame Okuma Döngüsü (Sadece Komut için 1 frame bekleniyor) ===
    raw_frame = uart.read()
    if raw_frame:
        print(f"\n📥 Frame alındı ({len(raw_frame)} byte)")
        frame_dict = parse_mesh_frame(raw_frame)
        route_frame(frame_dict, uart_handler=uart)

    uart.stop()

if __name__ == "__main__":
    main()
