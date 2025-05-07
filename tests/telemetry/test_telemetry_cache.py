def test_telemetry_cache_update():
    from src.tools.telemetry.telemetry_cache import set_device_data, get_device_data, reset_cache
    reset_cache()
    set_device_data(1, "gps", {"lat": 37.0, "lon": 35.0, "alt": 100})
    gps = get_device_data(1, "gps")
    assert gps is not None
    assert gps["lat"] == 37.0