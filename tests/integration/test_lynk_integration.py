import time
from src.tools.comm.interface_factory import create_interface
from src.serializers.telemetry_serializer import serialize_telemetry
from src.serializers.command_serializer import serialize_command
from src.core.frame_router import route_frame
from src.core.frame_codec import parse_mesh_frame, build_mesh_frame
from src.tools.telemetry.telemetry_dispatcher import (
    send_tlm_gps,
    send_tlm_imu,
    send_tlm_battery,
    send_tlm_heartbeat
)
from src.tools.telemetry.telemetry_cache import (
    get_active_device_ids,
    get_device_data,
    get_all_cached_data,
    get_all_data_for_device,
    reset_cache
)
from src.tools.command.command_dispatcher import cmd_takeoff


def process_all_frames(interface):
    """
    Reads all pending frames from the mock interface and routes them.
    """
    while True:
        raw = interface.uart.read()
        if not raw:
            break
        frame_dict = parse_mesh_frame(raw)
        route_frame(frame_dict, interface)


def send_all_test_telemetries(interface):
    """
    Sends GPS, IMU, BATTERY, and HEARTBEAT telemetry for devices 1 and 2.
    """
    now = time.time()

    send_tlm_gps(interface, lat=37.1111, lon=35.1111, alt=100.0, dst=1, src=1)
    send_tlm_imu(interface, roll=1.1, pitch=2.2, yaw=3.3, dst=1, src=1)
    send_tlm_battery(interface, voltage=11.1, current=4.2, level=95.0, dst=1, src=1)
    send_tlm_heartbeat(interface, mode="GUIDED", health="OK", is_armed=True,
                       gps_fix=True, sat_count=10, dst=1, src=1)

    send_tlm_gps(interface, lat=36.1111, lon=33.1111, alt=90.0, dst=1, src=2)
    send_tlm_imu(interface, roll=15.1, pitch=5.0, yaw=7.0, dst=1, src=2)
    send_tlm_battery(interface, voltage=10.9, current=4.1, level=77.0, dst=1, src=2)
    send_tlm_heartbeat(interface, mode="AUTO", health="OK", is_armed=True,
                       gps_fix=True, sat_count=11, dst=1, src=2)


def test_lynk_full_flow():
    """
    Full end-to-end test of the LYNK telemetry and command system.
    """
    print("\n🚀 [LYNK TEST] Starting interface...")
    interface = create_interface()
    reset_cache()

    send_all_test_telemetries(interface)
    cmd_takeoff(interface, takeoff_alt=30, src=1, dst=1)
    process_all_frames(interface)

    # ✅ Verify telemetry data and heartbeat for devices 1, 2
    for src_id in [1, 2]:
        data = get_all_data_for_device(src_id)
        assert data is not None, f"❌ No telemetry data for device {src_id}!"
        print(f"\n✅ [CACHE] Device {src_id} data:")
        for dtype, values in data.items():
            print(f"  - {dtype}: {values}")

        assert "heartbeat" in data, f"❌ No heartbeat data for device {src_id}!"
        print(f"  ✅ Heartbeat: {data['heartbeat']}")

    # ✅ Active device check (before timeout)
    active_ids = get_active_device_ids(timeout=3.0)
    print(f"\n📡 [ACTIVE] Active devices (initial): {active_ids}")
    assert 1 in active_ids and 2 in active_ids, "❌ Device 1 or 2 is not active!"

    # ⏳ Wait for 4s → simulate timeout for device 1 and 2
    print("\n⏳ Waiting 4 seconds (devices 1 and 2 should timeout)...")
    time.sleep(4)

    # 🛰 Send GPS + HEARTBEAT for new device 3
    send_tlm_gps(interface, lat=35.1111, lon=33.1111, alt=90.0, dst=1, src=3)
    send_tlm_heartbeat(interface, mode="RTL", health="OK", is_armed=False,
                       gps_fix=True, sat_count=9, dst=1, src=3)

    process_all_frames(interface)

    # ✅ Final active device check
    active_ids = get_active_device_ids(timeout=3.0)
    print(f"\n📡 [ACTIVE] Active devices (final): {active_ids}")
    assert active_ids == [3], "❌ Only device 3 should be active!"

    # ✅ Battery check for device 2
    battery_data = get_device_data(2, "battery")
    assert battery_data is not None, "❌ No battery data found for device 2!"
    print("\n🔋 [BATTERY] Device 2 battery data:")
    for k, v in battery_data.items():
        print(f"   {k}: {v}")

    # ✅ Heartbeat check for all devices
    print("\n🫀 [HEARTBEAT] Verifying heartbeat presence:")
    for src_id in [1, 2, 3]:
        heartbeat = get_device_data(src_id, "heartbeat")
        assert heartbeat is not None, f"❌ No heartbeat data for device {src_id}!"
        print(f"   ✅ Device {src_id}: {heartbeat}")

    # ✅ Final telemetry cache printout
    print("\n📦 [CACHE] All cached telemetry data:")
    print(get_all_cached_data())
