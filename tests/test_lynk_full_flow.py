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
import time
import struct


def process_all_frames(interface):
    """Mock arayüzden gelen tüm frame'leri işler."""
    print("🔄 [LYNK TEST] Frame işleme başladı...")
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

    send_tlm_gps(interface, lat=36.1111, lon=33.1111, alt=90.0, dst=1, src=2)
    send_tlm_imu(interface, roll=15.1, pitch=5.0, yaw=7.0, dst=1, src=2)


def verify_telemetry_cache(src_id: int):
    """Verilen src_id için tüm telemetri verilerini kontrol eder."""
    data = get_all_data_for_device(src_id)
    if not data:
        print(f"\n❌ [TEST] Cihaz {src_id} için cache'te veri bulunamadı.")
        return

    print(f"\n✅ [TEST] Cihaz {src_id} için cache'e alınan veriler:")
    for data_type, values in data.items():
        print(f"  🔹 {data_type}:")
        for key, val in values.items():
            print(f"      {key}: {val}")


def list_active_devices(timeout: float = 3.0):
    """Son `timeout` saniyede veri gönderen cihazları listeler."""
    active_ids = get_active_device_ids(timeout=timeout)
    print(f"\n📡 [TEST] Aktif cihazlar (son {timeout} sn): {active_ids}")


def print_full_cache():
    """Tüm cihazlara ait cache'leri detaylı şekilde bastırır."""
    all_data = get_all_cached_data()
    print("\n📦 [TEST] Tüm Telemetri Cache Verisi:")
    for src_id, types in all_data.items():
        print(f"\n📡 Cihaz {src_id}:")
        for data_type, data in types.items():
            print(f"  - {data_type}:")
            for k, v in data.items():
                print(f"      {k}: {v}")


def test_lynk_full_flow(interface):
    """Tüm sistemin baştan sona testini yapar."""
    print("🚀 [LYNK TEST] Başlatılıyor...")
    reset_cache()

    send_all_test_telemetries(interface)
    cmd_takeoff(interface, takeoff_alt=30, src=1, dst=1)

    process_all_frames(interface)

    for src_id in [1, 2]:
        verify_telemetry_cache(src_id)

    list_active_devices()
    print_full_cache()


if __name__ == "__main__":
    print("🚀 [LYNK TEST] Arayüz başlatılıyor...")
    interface = create_interface()

    test_lynk_full_flow(interface)

    print("\n⏳ 4 saniye bekleniyor (aktiflik testine girmemesi için)...")
    time.sleep(4)

    # Yeni cihazdan veri gönder, önceki cihazlar aktiflikten düşecek
    send_tlm_gps(interface, lat=35.1111, lon=33.1111, alt=90.0, dst=1, src=3)
    process_all_frames(interface)

    # Sadece src_id = 3 aktif olacak
    for src_id in [1, 2, 3]:
        verify_telemetry_cache(src_id)

    list_active_devices()
    print_full_cache()