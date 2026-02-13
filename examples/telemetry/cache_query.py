#!/usr/bin/env python3
"""
Example: Telemetry Cache Query
Demonstrates how to use the LYNK Telemetry Cache to access the last known state 
of vehicles in the mesh network.
"""
import os
import time
import lynk

def main():
    print("🚀 initializing LYNK Telemetry Cache Demo...")
    
    # 1. Load configuration
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, "configs", "node_1", "config.yaml")
    if os.path.exists(config_path):
        lynk.config.load_config(config_path)
    else:
        lynk.config.load_config("configs/config.yaml")

    # 2. Setup Interface
    interface = lynk.create_interface()
    interface.start()
    
    # 3. Simulate incoming telemetry data (to populate the cache)
    print("\n📥 Simulating incoming telemetry packages...")
    
    # Populate cache for Vehicle 10 (GCS/Lidder viewpoint)
    # We use the newly exposed lynk.handle_telemetry for simulation
    from unittest.mock import patch
    with patch("lynk.application.telemetry.handler.dispatcher.deserialize_telemetry") as mock_d:
        # Simulate GPS TLM (ID: 1)
        # Requirements: lat, lon, alt
        mock_d.return_value = {"tlm_id": 1, "lat": 41.0, "lon": 28.0, "alt": 150.5}
        lynk.handle_telemetry(b"dummy_gps", {"src_id": 10, "team_id": 1})
        
        # Simulate Battery TLM (ID: 3)
        # Requirements: voltage, current, level
        mock_d.return_value = {"tlm_id": 3, "voltage": 11.8, "current": 5.0, "level": 82.5}
        lynk.handle_telemetry(b"dummy_bat", {"src_id": 10, "team_id": 1})
        
        # Simulate Vehicle 11
        mock_d.return_value = {"tlm_id": 1, "lat": 41.1, "lon": 28.1, "alt": 100.0}
        lynk.handle_telemetry(b"dummy_gps_11", {"src_id": 11, "team_id": 1})

    # 4. Querying the Cache
    print("\n🔍 Querying the Telemetry Cache:")
    
    # List active vehicles (sent data in last 10 seconds)
    active_ids = lynk.tlm_cache.get_active_device_ids(timeout=10.0)
    print(f"   - Active Vehicles: {active_ids}")
    
    # Get specific data
    v10_gps = lynk.tlm_cache.get_vehicle_telemetry(10, "GPS")
    if v10_gps:
        print(f"   - Vehicle 10 GPS: {v10_gps['lat']}, {v10_gps['lon']} (Alt: {v10_gps['alt']}m)")
        print(f"     [TS: {v10_gps['timestamp']:.2f}]")

    # Get vehicle snapshot (includes team and hop count)
    v11_snap = lynk.tlm_cache.get_vehicle_snapshot(11)
    if v11_snap:
        print(f"   - Vehicle 11 Snapshot: Team={v11_snap['team_id']}, Hops={v11_snap['last_hop_count']}")
        print(f"     Telemetry keys: {list(v11_snap['telemetry'].keys())}")

    # Full Snapshot
    full_snap = lynk.tlm_cache.get_cache_snapshot()
    print(full_snap)
    print(f"\n📊 Total Vehicles in Cache: {len(full_snap['vehicles'])}")
    
    interface.stop()
    print("\nDemo finished.")

def import_mock():
    # Helper to avoid heavy imports at top level if just demonstrating
    from unittest.mock import patch
    return patch("lynk.application.telemetry.handler.dispatcher.deserialize_telemetry")

if __name__ == "__main__":
    main()
