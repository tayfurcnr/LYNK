# tests/test_lynk.integration.py

import time
from src.tools.comm.interface_factory import create_interface
from src.serializers.telemetry_serializer import serialize_telemetry
from src.serializers.command_serializer import serialize_command
from src.core.frame_router import route_frame
from src.core.frame_codec import parse_mesh_frame, build_mesh_frame
from src.tools.telemetry.telemetry_dispatcher import send_tlm_gps, send_tlm_imu, send_tlm_battery
from src.tools.telemetry.telemetry_cache import (
    get_active_device_ids,
    get_device_data,
    get_all_cached_data,
    get_all_data_for_device,
    reset_cache
)
from src.tools.command.command_dispatcher import cmd_takeoff


def process_all_frames(interface):
    """Mock arayüzden gelen tüm frame'leri işler."""
    while True:
        raw = interface.uart.read()
        if not raw:
            break
        frame_dict = parse_mesh_frame(raw)
        route_frame(frame_dict, interface)


def send_all_test_telemetries(interface):
    """İki farklı cihazdan örnek telemetri verileri gönderir."""
    send_tlm_gps(interface, lat=37.1111, lon=35.1111, alt=100.0, dst=1, src=1)
    send_tlm_imu(interface, roll=1.1, pitch=2.2, yaw=3.3, dst=1, src=1)
    send_tlm_battery(interface, voltage=11.1, current=4.2, level=95.0, dst=1, src=1)

    send_tlm_gps(interface, lat=36.1111, lon=33.1111, alt=90.0, dst=1, src=2)
    send_tlm_imu(interface, roll=15.1, pitch=5.0, yaw=7.0, dst=1, src=2)
    send_tlm_battery(interface, voltage=10.9, current=4.1, level=77.0, dst=1, src=2)


def test_lynk_full_flow():
    """LYNK sisteminin uçtan uca testi."""
    print("\n🚀 [LYNK TEST] Arayüz başlatılıyor...")
    interface = create_interface()
    reset_cache()

    send_all_test_telemetries(interface)
    cmd_takeoff(interface, takeoff_alt=30, src=1, dst=1)

    process_all_frames(interface)

    # ✅ Telemetri cache doğrulama
    for src_id in [1, 2]:
        data = get_all_data_for_device(src_id)
        assert data is not None, f"❌ Cihaz {src_id} için telemetri verisi yok!"
        print(f"\n✅ [CACHE] Cihaz {src_id} verileri:")
        for dtype, values in data.items():
            print(f"  - {dtype}: {values}")

    # ✅ Aktif cihaz kontrolü
    active_ids = get_active_device_ids(timeout=3.0)
    print(f"\n📡 [ACTIVE] Aktif cihazlar (ilk test): {active_ids}")
    assert 1 in active_ids and 2 in active_ids, "❌ Cihaz 1 veya 2 aktif görünmüyor!"

    # ⏳ Bekleyip 3. cihaza yeni veri gönder
    print("\n⏳ 4 saniye bekleniyor (1 ve 2 zaman aşımına girsin)...")
    time.sleep(4)

    send_tlm_gps(interface, lat=35.1111, lon=33.1111, alt=90.0, dst=1, src=3)
    process_all_frames(interface)

    # ✅ Yeni aktif cihaz kontrolü
    active_ids = get_active_device_ids(timeout=3.0)
    print(f"\n📡 [ACTIVE] Aktif cihazlar (son test): {active_ids}")
    assert active_ids == [3], "❌ Yalnızca cihaz 3 aktif olmalıydı!"

    # ✅ Cihaz 2 için battery verisi kontrolü
    battery_data = get_device_data(2, "battery")
    assert battery_data is not None, "❌ Cihaz 2 için battery verisi bulunamadı!"
    print("\n🔋 [BATTERY] Cihaz 2 battery verisi:")
    for k, v in battery_data.items():
        print(f"   {k}: {v}")

    # ✅ Tüm cache çıktısını göster
    print("\n📦 [CACHE] Tüm sistem verisi:")
    print(get_all_cached_data())
