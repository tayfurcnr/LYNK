#!/usr/bin/env python3
"""
MAVLink Real Scenario: GCS Bridge (Node 1)
Simulates a Ground Control Station that tunnels MAVLink to a vehicle.
"""
import os
import time
import threading
import lynk

def router_worker(interface):
    """Background thread to process incoming LYNK frames."""
    print("[GCS] Router thread started.")
    while True:
        raw = interface.read()
        if raw:
            try:
                frame = lynk.codec.parse_mesh_frame(raw)
                lynk.router.route_frame(frame, interface)
            except Exception as e:
                print(f"[GCS] Route Error: {e}")
        time.sleep(0.01)

def on_mavlink_from_vehicle(payload, tunnel_meta, frame_meta):
    """Callback for MAVLink packets coming FROM the vehicle."""
    print(f"\n🛸 [GCS RECV] MAVLink from Vehicle (Drone {frame_meta['src_id']})")
    print(f"   - Payload Hex: {payload.hex()[:30]}...")
    print(f"   - MAVLink SysID: {tunnel_meta['system_id']}")

def main():
    print("🖥️  MAVLink GCS Bridge Starting...")
    
    # 1. Setup paths and load Node 1 config
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    config_path = os.path.join(base_dir, "configs", "node_1", "config.yaml")
    lynk.config.load_config(config_path)
    
    # 2. Register callback for incoming vehicle telemetry
    lynk.mavlink.on_mavlink_received(on_mavlink_from_vehicle)
    
    # 3. Start Interface
    interface = lynk.create_interface()
    interface.start()
    
    # 4. Start background router "pump"
    t = threading.Thread(target=router_worker, args=(interface,), daemon=True)
    t.start()
    
    print("📡 GCS is UP. Sending periodic commands to Drone 2...")
    
    # Simulated MAVLink Command: MAV_CMD_COMPONENT_ARM_DISARM (simplified)
    fake_cmd = b"\xFD\x05\x00\x00\x01\x01\x01\x92\x00\x00\x01\x00\x00\x00\x00\xDE\xAD"

    try:
        while True:
            print("\n📤 [GCS SEND] Tunnelling MAVLink Command to Drone 2...")
            lynk.mavlink.send_mavlink(
                interface=interface,
                payload=fake_cmd,
                dst=2,
                system_id=255, # GCS usually 255
                component_id=1
            )
            time.sleep(5.0) # Send command every 5 seconds
    except KeyboardInterrupt:
        print("\nClosing GCS Bridge...")
    finally:
        interface.stop()

if __name__ == "__main__":
    main()
