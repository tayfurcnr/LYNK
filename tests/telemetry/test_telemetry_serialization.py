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
    # GPS expects lat, lon, alt
    lat, lon, alt = 37.0, 35.0, 100.0
    payload = serialize_telemetry("GPS", lat, lon, alt)
    
    res = deserialize_telemetry(payload)
    
    # Float precision might vary, use approx
    assert res["lat"] == pytest.approx(lat, rel=1e-4)
    assert res["lon"] == pytest.approx(lon, rel=1e-4)
    assert res["alt"] == pytest.approx(alt, rel=1e-4)

def test_telemetry_definition_dynamic():
    # Check if definition for GPS exists and has serialize/deserialize
    
    found = False
    for tlm_id, defn in telemetry_definitions.items():
        if defn.name == "GPS":
             found = True
             # Test bound serializer
             payload = defn.serialize(10.0, 20.0, 30.0)
             res = defn.deserialize(payload)
             assert res["lat"] == pytest.approx(10.0, rel=1e-4)
             break
    assert found
