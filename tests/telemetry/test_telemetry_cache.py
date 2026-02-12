from __future__ import annotations
import pytest
import time

from lynk.application.telemetry.tools.cache import (
    set_device_data,
    get_device_data,
    get_active_device_ids,
    get_all_data_for_device,
    get_all_cached_data,
    reset_cache
)

@pytest.fixture(autouse=True)
def clear_cache_before_test():
    reset_cache()
    yield
    reset_cache()


def test_set_and_get_data_with_timestamp():
    src_id = 1
    data_type = "gps"
    payload = {"lat": 1.0, "lon": 2.0, "alt": 3.0}

    set_device_data(src_id, data_type, payload)
    result = get_device_data(src_id, data_type)

    assert result is not None
    assert "timestamp" in result
    assert result["lat"] == 1.0
    assert result["alt"] == 3.0
    assert isinstance(result["timestamp"], float)


def test_overwrite_existing_entry():
    src_id = 42
    data_type = "battery"
    old = {"voltage": 11.1}
    new = {"voltage": 11.8}

    set_device_data(src_id, data_type, old)
    time.sleep(0.01)
    set_device_data(src_id, data_type, new)

    result = get_device_data(src_id, data_type)
    assert result["voltage"] == 11.8
    assert "timestamp" in result


def test_get_unknown_returns_none():
    assert get_device_data(999, "imu") is None


def test_get_all_data_for_device():
    src_id = 7
    set_device_data(src_id, "gps", {"lat": 10})
    set_device_data(src_id, "imu", {"roll": 1})

    all_data = get_all_data_for_device(src_id)
    assert "gps" in all_data
    assert "imu" in all_data
    assert all_data["gps"]["lat"] == 10


def test_get_all_cached_data_structure():
    src_id = 123
    set_device_data(src_id, "heartbeat", {"mode": "AUTO", "src_id": 999})

    cached = get_all_cached_data()
    assert src_id in cached
    assert "team_id" in cached[src_id]
    assert "telemetry" in cached[src_id]
    assert "heartbeat" in cached[src_id]["telemetry"]
    # We no longer filter out src_id from the payload in get_all_cached_data for performance/simplicity
    assert cached[src_id]["telemetry"]["heartbeat"]["src_id"] == 999


def test_active_device_ids_detects_recent_data():
    src_1 = 1
    src_2 = 2

    # lynk_1 eski veri
    set_device_data(src_1, "imu", {"x": 1})
    time.sleep(1.1)  # lynk_1 eskidi

    # lynk_2 yeni veri
    set_device_data(src_2, "gps", {"lat": 0})

    # lynk_1 artık timeout dışında, src_2 içinde
    active = get_active_device_ids(timeout=1.0)
    assert src_2 in active
    assert src_1 not in active

def test_type_errors():
    with pytest.raises(TypeError):
        set_device_data("not_int", "gps", {})

    with pytest.raises(TypeError):
        set_device_data(1, 123, {})

    with pytest.raises(TypeError):
        set_device_data(1, "gps", "not_dict")

def test_active_device_ids_with_team():
    # Device on Team 10
    set_device_data(1, "gps", {"lat": 1}, team_id=10)
    # Device on Team 20
    set_device_data(2, "gps", {"lat": 2}, team_id=20)
    
    # Filter for Team 10
    active_10 = get_active_device_ids(team_id=10)
    assert 1 in active_10
    assert 2 not in active_10
    
    # Filter for Team 20
    active_20 = get_active_device_ids(team_id=20)
    assert 2 in active_20
    assert 1 not in active_20
    
    # Filter for everyone (None)
    active_all = get_active_device_ids(team_id=None)
    assert 1 in active_all
    assert 2 in active_all
