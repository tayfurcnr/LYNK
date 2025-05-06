# tests/telemetry/test_receive_telemetry_from_uart.py

from src.handlers.comm.mock_handler import MockUARTHandler
from src.core.frame_router import route_frame
from src.core.frame_codec import parse_mesh_frame
from src.tools.telemetry.telemetry import build_telemetry_frame
from src.tools.telemetry.telemetry_cache import (
    get_device_data,
    get_latest_device_id,
    get_active_device_ids,
    reset_cache
)

def test_receive_multiple_telemetry_frames(frames, expected_latest):
    reset_cache()
    uart = MockUARTHandler()
    uart.start()

    for device_id, lat, lon, alt, src_id in frames:
        frame = build_telemetry_frame(
            device_id=device_id,
            lat=lat,
            lon=lon,
            alt=alt,
            src_id=src_id,
            dst_id=1
        )
        uart.inject_frame(frame)
        raw = uart.read()
        assert raw is not None, "Frame could not be read from UART"
        parsed = parse_mesh_frame(raw)
        route_frame(parsed, uart_handler=uart)

    uart.stop()

    print("\n📡 Received Telemetry Data:")
    for device_id, lat, lon, alt, src_id in frames:
        data = get_device_data(device_id, "gps")
        assert data is not None, f"No telemetry stored for device {device_id}"
        assert abs(data["gps_lat"] - lat) < 1e-5
        assert abs(data["gps_lon"] - lon) < 1e-5
        assert abs(data["gps_alt"] - alt) < 1e-1
        assert data["src_id"] == src_id

        print(f"• Device {device_id} | SRC: {src_id} → "
              f"LAT: {data['gps_lat']:.6f}, LON: {data['gps_lon']:.6f}, ALT: {data['gps_alt']:.2f} m")

    assert get_latest_device_id() == expected_latest
    active_ids = get_active_device_ids()
    expected_ids = [d[0] for d in frames]
    assert set(active_ids) == set(expected_ids)

    print(f"\n✅ [TEST PASSED] All devices processed correctly.")
    print(f"📍 Latest Device ID: {expected_latest}")
    print(f"🌐 Active Device IDs: {active_ids}")


def main():
    test_receive_multiple_telemetry_frames(
        frames=[
            (11, 37.1111, 35.1111, 100.0, 0x11),
            (22, 37.2222, 35.2222, 200.0, 0x22),
            (33, 37.3333, 35.3333, 300.0, 0x33),
        ],
        expected_latest=33
    )


if __name__ == "__main__":
    main()
