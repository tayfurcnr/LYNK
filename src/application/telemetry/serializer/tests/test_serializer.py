from __future__ import annotations
# powershell -> pytest src/telemetry/serializer/tests/test_serializer.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))
# ...existing code...

import pytest
import struct

from telemetry.serializer.impl import (
    serialize_gps, deserialize_gps,
    serialize_imu, deserialize_imu,
    serialize_battery, deserialize_battery,
    serialize_heartbeat, deserialize_heartbeat
)

def test_serialize_deserialize_gps():
    lat, lon, alt = 1.23, 4.56, 7.89
    data = serialize_gps(lat, lon, alt)
    assert isinstance(data, bytes)
    assert len(data) == 12
    result = deserialize_gps(data)
    assert result["lat"] == pytest.approx(lat)
    assert result["lon"] == pytest.approx(lon)
    assert result["alt"] == pytest.approx(alt)

def test_serialize_deserialize_imu():
    roll, pitch, yaw = -1.0, 0.0, 3.14
    data = serialize_imu(roll, pitch, yaw)
    assert isinstance(data, bytes)
    assert len(data) == 12
    result = deserialize_imu(data)
    assert result["roll"] == pytest.approx(roll)
    assert result["pitch"] == pytest.approx(pitch)
    assert result["yaw"] == pytest.approx(yaw)

def test_serialize_deserialize_battery():
    voltage, current, level = 11.1, 2.2, 99.9
    data = serialize_battery(voltage, current, level)
    assert isinstance(data, bytes)
    assert len(data) == 12
    result = deserialize_battery(data)
    assert result["voltage"] == pytest.approx(voltage)
    assert result["current"] == pytest.approx(current)
    assert result["level"] == pytest.approx(level)

def test_serialize_deserialize_heartbeat():
    mode = "AUTO"
    health = "OK"
    is_armed = True
    gps_fix = False
    sat_count = 7
    data = serialize_heartbeat(mode, health, is_armed, gps_fix, sat_count)
    assert isinstance(data, bytes)
    assert len(data) == 67
    result = deserialize_heartbeat(data)
    assert result["mode"] == mode
    assert result["health"] == health
    assert result["is_armed"] == is_armed
    assert result["gps_fix"] == gps_fix
    assert result["sat_count"] == sat_count

def test_heartbeat_string_truncation_and_padding():
    mode = "A" * 40  # longer than 32
    health = "B" * 40
    data = serialize_heartbeat(mode, health, True, True, 255)
    assert len(data) == 67
    result = deserialize_heartbeat(data)
    assert result["mode"] == "A" * 32
    assert result["health"] == "B" * 32

def test_deserialize_gps_invalid_length():
    with pytest.raises(struct.error):
        deserialize_gps(b"\x00" * 8)

def test_deserialize_imu_invalid_length():
    with pytest.raises(struct.error):
        deserialize_imu(b"\x00" * 4)

def test_deserialize_battery_invalid_length():
    with pytest.raises(struct.error):
        deserialize_battery(b"\x00" * 2)

def test_deserialize_heartbeat_invalid_length():
    with pytest.raises(struct.error):
        deserialize_heartbeat(b"\x00" * 10)
