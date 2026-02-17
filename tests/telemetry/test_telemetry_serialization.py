from __future__ import annotations
import sys
import os
import pytest

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../lynk/shared/proto')))

from lynk.application.telemetry.serializer.dispatcher import serialize_telemetry, deserialize_telemetry
from lynk.application.telemetry.definitions import telemetry_definitions

def test_telemetry_serialization_gps():
    # GPS expects 8 parameters: lat, lon, alt_m, rel_alt_m, fix_type, sat_count, hdop, timestamp_ms
    lat, lon, alt_m, rel_alt_m = 37.1234567, 35.1234567, 100.5, 50.2
    fix_type, sat_count, hdop, ts = 3, 12, 1.2, 1718888888000
    
    payload = serialize_telemetry("GPS", lat, lon, alt_m, rel_alt_m, fix_type, sat_count, hdop, ts)
    
    res = deserialize_telemetry(payload)
    
    # Double precision for lat/lon, float for alt_m/rel_alt_m/hdop
    assert res["lat"] == pytest.approx(lat, abs=1e-8)
    assert res["lon"] == pytest.approx(lon, abs=1e-8)
    assert res["alt_m"] == pytest.approx(alt_m, rel=1e-4)
    assert res["rel_alt_m"] == pytest.approx(rel_alt_m, rel=1e-4)
    assert res["fix_type"] == fix_type
    assert res["sat_count"] == sat_count
    assert res["hdop"] == pytest.approx(hdop, rel=1e-4)
    assert res["timestamp_ms"] == ts


def test_telemetry_serialization_vfr_hud():
    # VFR_HUD expects 7 parameters: airspeed, groundspeed, heading, throttle, alt, climb, ts
    airspeed, gs, hdg, throttle, alt, climb, ts = 15.1, 15.5, 90.0, 0.6, 100.5, 0.1, 1718888888000
    
    payload = serialize_telemetry("VFR_HUD", airspeed, gs, hdg, throttle, alt, climb, ts)
    
    res = deserialize_telemetry(payload)
    
    assert res["airspeed_ms"] == pytest.approx(airspeed, rel=1e-4)
    assert res["groundspeed_ms"] == pytest.approx(gs, rel=1e-4)
    assert res["heading_deg"] == pytest.approx(hdg, rel=1e-4)
    assert res["throttle"] == pytest.approx(throttle, rel=1e-4)
    assert res["alt_m"] == pytest.approx(alt, rel=1e-4)
    assert res["climb_ms"] == pytest.approx(climb, rel=1e-4)
    assert res["timestamp_ms"] == ts

def test_telemetry_serialization_heartbeat():
    # HEARTBEAT expects 2 parameters: sequence, timestamp_ms
    seq, ts = 123, 1718888888000
    
    payload = serialize_telemetry("HEARTBEAT", seq, ts)
    
    res = deserialize_telemetry(payload)
    
    assert res["sequence"] == seq
    assert res["timestamp_ms"] == ts

def test_telemetry_definition_dynamic_heartbeat():
    # Check if definition for HEARTBEAT exists
    found = False
    for tlm_id, defn in telemetry_definitions.items():
        if defn.name == "HEARTBEAT":
             found = True
             # Test bound serializer with 2 parameters
             payload = defn.serialize(456, 0)
             res = defn.deserialize(payload)
             assert res["sequence"] == 456
             break
    assert found
