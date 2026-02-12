#!/usr/bin/env python3
"""
MAVLink Real Scenario: Vehicle Bridge (Node 2)
Simulates a Drone that receives MAVLink commands and sends telemetry.
"""
import os
import time
import threading
import lynk

def router_worker(interface):
    """Background thread to process incoming LYNK frames."""
    print("[VEHICLE] Router thread started.")
    while True:
        raw = interface.read()
        if raw:
            try:
                frame = lynk.codec.parse_mesh_frame(raw)
                lynk.router.route_frame(frame, interface)
            except Exception as e:
                print(f"[VEHICLE] Route Error: {e}")
        time.sleep(0.01)

def on_mavlink_from_gcs(payload, tunnel_meta, frame_meta):
    """Callback for MAVLink packets coming FROM the GCS."""
    print(f"\n📡 [VEHICLE RECV] MAVLink Command from GCS (ID {frame_meta['src_id']})")
    print(f"   - Payload Hex: {payload.hex()[:30]}...")
    print(f"   - MAVLink SysID: {tunnel_meta['system_id']}")
    print(f"   => Writing to Pixhawk Serial Port (Simulated)...")

def main():
    print("🛸 MAVLink Vehicle Bridge Starting...")
    
    # 1. Setup paths and load Node 2 config
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    config_path = os.path.join(base_dir, "configs", "node_2", "config.yaml")
    lynk.config.load_config(config_path)
    
    # 2. Register callback for incoming GCS commands
    lynk.mavlink.on_mavlink_received(on_mavlink_from_gcs)
    
    # 3. Start Interface
    interface = lynk.create_interface()
    interface.start()
    
    # 4. Start background router "pump"
    t = threading.Thread(target=router_worker, args=(interface,), daemon=True)
    t.start()
    
    print("🛰️ Vehicle is UP. Sending periodic HEARTBEAT to GCS...")
    
    # Simulated MAVLink Heartbeat
    fake_heartbeat = b"\xFD\x09\x00\x00\x01\x01\x01\x00\x00\x00\x00\x04\x03\x00\x00\x00\x03\xBE\xEF"

    try:
        while True:
            print("\n📤 [VEHICLE SEND] Tunnelling MAVLink Heartbeat to GCS...")
            lynk.mavlink.send_mavlink(
                interface=interface,
                payload=fake_heartbeat,
                dst=1,
                system_id=1,
                component_id=1
            )
            time.sleep(2.0) # Heartbeat every 2 seconds
    except KeyboardInterrupt:
        print("\nClosing Vehicle Bridge...")
    finally:
        interface.stop()

if __name__ == "__main__":
    main()
