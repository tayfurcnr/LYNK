from src.handlers.comm.mock_handler import MockUARTHandler
from src.tools.command.command_dispatcher import cmd_waypoints  # WAYPOINTS komutunu ekliyoruz
from src.core.frame_codec import parse_mesh_frame
from src.core.frame_router import route_frame

def main():
    uart = MockUARTHandler()
    uart.start()

    # === WAYPOINTS Komutunu Gönder ===
    waypoints = [
        (37.7749, 32.7767, 80.0),  # Waypoint 1
        (37.7750, 32.7768, 85.0),  # Waypoint 2
        (37.7751, 32.7769, 90.0)   # Waypoint 3
    ]

    cmd_waypoints(
        waypoints=waypoints,  # Waypoint listesi
        dst=1,
        src=0x01,
        uart=uart
    )

    # === Frame Okuma Döngüsü (Komut + ACK için 2 frame bekleniyor) ===
    for i in range(2):  # İlk komut, sonra ACK
        raw_frame = uart.read()  # Burada gönderilen frame'in kopyasını alıyoruz
        if raw_frame:
            print(f"\n📥 Frame {i+1} alındı ({len(raw_frame)} byte)")
            frame_dict = parse_mesh_frame(raw_frame)
            route_frame(frame_dict, uart_handler=uart)

    uart.stop()

if __name__ == "__main__":
    main()