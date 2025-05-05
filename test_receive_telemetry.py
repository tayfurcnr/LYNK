# test_receive_telemetry.py

import time
from mock_uart import MockUARTHandler
from src.frame_router import route_frame
from src.frame_codec import parse_mesh_frame
from src.tools.telemetry import build_telemetry_frame
from src.handlers.telemetry_handler import (
    get_all_telemetry,
    get_latest_device_id,
    get_active_nodes
)

def main():
    uart = MockUARTHandler()
    uart.start()

    # 3 farklı cihazdan gelen telemetri frame’leri
    frames = [
        build_telemetry_frame(
            device_id=1,
            lat=37.0001,
            lon=32.0001,
            alt=1000.0,
            src_id=0x05,
            dst_id=1
        ),
        build_telemetry_frame(
            device_id=2,
            lat=37.1111,
            lon=32.1111,
            alt=1200.0,
            src_id=0x06,
            dst_id=1
        )
    ]

    # İlk 2 frame'i sırayla işleyelim (her biri 1 saniye arayla)
    for frame in frames:
        uart.inject_frame(frame)
        time.sleep(1.0)  # simülasyon gecikmesi
        raw_frame = uart.read()
        if raw_frame:
            frame_dict = parse_mesh_frame(raw_frame)
            route_frame(frame_dict, uart_handler=uart)

    # 10 saniye bekle → ilk iki cihaz zaman aşımına uğrayacak
    print("\n⌛ 10 saniye bekleniyor (bazı cihazlar aktiflik dışına çıkacak)...\n")
    time.sleep(10)

    # 3. cihazdan veri şimdi geliyor (hala aktif sayılmalı)
    frame3 = build_telemetry_frame(
        device_id=3,
        lat=37.2222,
        lon=32.2222,
        alt=1500.0,
        src_id=0x07,
        dst_id=1
    )
    uart.inject_frame(frame3)
    raw_frame = uart.read()
    if raw_frame:
        frame_dict = parse_mesh_frame(raw_frame)
        route_frame(frame_dict, uart_handler=uart)

    uart.stop()

    # === Sonuçları yazdır ===
    print("\n=== 📊 Toplanan Telemetri Verileri ===")
    all_data = get_all_telemetry()
    for device_id, data in all_data.items():
        print(f"Cihaz {device_id}: Yükseklik={data['gps_alt']} m | Kaynak Node={data['src_id']}")

    print(f"\n🕐 En son veri gelen cihaz ID: {get_latest_device_id()}")
    print(f"🌐 🌱 Aktif kaynak cihazlar (src_id) [10 saniyelik pencere]: {get_active_nodes(timeout=10)}")

if __name__ == "__main__":
    main()