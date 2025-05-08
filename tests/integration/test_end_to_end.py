# tests/integration/test_end_to_end.py

import pytest

from src.tools.comm.interface_factory import create_interface
from src.core.frame_codec import build_mesh_frame, parse_mesh_frame
from src.core.frame_router import route_frame
from src.serializers.command_serializer import serialize_command
from src.serializers.telemetry_serializer import serialize_telemetry
from src.tools.telemetry.telemetry_cache import get_device_data, reset_cache

# Integration test: Command flow (değişmedi)
def test_command_end_to_end_ack():
    interface = create_interface()
    interface.uart.start()
    local_id = 1
    cmd_payload = serialize_command(0x03, b"")
    frame = build_mesh_frame(
        frame_type='C',
        src_id=local_id,
        dst_id=local_id,
        payload=cmd_payload
    )
    interface.uart.inject_frame(frame)
    raw = interface.read()
    assert raw is not None, "No frame read from interface"
    parsed = parse_mesh_frame(raw)
    route_frame(parsed, interface)
    ack_frame = interface.uart._outbox.pop(0) if interface.uart._outbox else None
    assert ack_frame is not None, "No ACK sent"
    ack_parsed = parse_mesh_frame(ack_frame)
    assert ack_parsed['frame_type'] == ord('A')

# Integration test: Telemetry flow (güncellendi)
def test_telemetry_end_to_end_cache_update():
    """
    Simulate sending a GPS telemetry frame and verify the telemetry cache updates correctly.
    """
    reset_cache()

    interface = create_interface()
    interface.uart.start()

    telemetry_data = {"lat": 37.0, "lon": 35.0, "alt": 100.0}

    # serialize_telemetry(device_id, lat, lon, alt)
    payload = serialize_telemetry(
        1,
        telemetry_data['lat'],
        telemetry_data['lon'],
        telemetry_data['alt']
    )
    frame = build_mesh_frame(
        frame_type='T',
        src_id=1,
        dst_id=1,
        payload=payload
    )

    interface.uart.inject_frame(frame)
    raw = interface.read()
    assert raw is not None, "No telemetry frame read"

    parsed = parse_mesh_frame(raw)
    route_frame(parsed, interface)

    # GPS verisi cache'de "gps" anahtarıyla saklanıyor
    stored = get_device_data(1, 'gps')
    assert stored is not None, "GPS telemetry data not cached"
    assert stored['lat'] == telemetry_data['lat']
    assert stored['lon'] == telemetry_data['lon']
    assert stored['alt'] == telemetry_data['alt']
