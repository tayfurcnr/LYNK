#!/usr/bin/env python3
"""
Example 05: MAVLink Tunneling
Demonstrates how to send a raw MAVLink packet tunneled inside LYNK.

Usage:
    python3 examples/mavlink/tunnel_demo.py
"""
import os
import time
import lynk

def main():
    print("🚀 initializing LYNK MAVLink Bridge Simulation...")
    
    # 1. Load configuration (Using Node 1 for Sender)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, "configs", "node_1", "config.yaml")
    lynk.config.load_config(config_path)
    
    # 2. Create LYNK interface
    interface = lynk.create_interface()
    
    # 3. Simulate a raw MAVLink HEARTBEAT packet
    # Standard MAVLink v1 Heartbeat (simplified representation for demo)
    # Header: 0xFE, Len: 9, Seq: 1, Sys: 1, Comp: 1, MsgID: 0 (HEARTBEAT)
    # Payload: 9 bytes
    # CRC: 2 bytes
    mavlink_heartbeat = bytes([
        0xFE, 0x09, 0x01, 0x01, 0x01, 0x00, # Header
        0x00, 0x00, 0x00, 0x04, 0x03, 0x00, 0x00, 0x00, 0x03, # Payload (Type: GCS, Autopilot: MAV_AUTOPILOT_ARDUPILOTMEGA...)
        0x12, 0x34 # CRC
    ])

    print(f"\n📦 Preparing MAVLink packet ({len(mavlink_heartbeat)} bytes)...")
    print(f"🔗 Tunneling through LYNK to Destination ID 2...")

    # 4. Send through LYNK Tunnel
    interface.start()
    time.sleep(0.5) # Give interface a moment
    
    lynk.mavlink.send_mavlink(
        interface=interface,
        payload=mavlink_heartbeat,
        dst=2,
        system_id=1,
        component_id=1
    )

    print("   [OK] MAVLink packet sent through LYNK.")
    time.sleep(1.0) # Wait for buffer to flush
    interface.stop()
    
    print("   [INFO] In a real scenario, the LYNK receiver on the drone would")
    print("          extract this payload and write it to the Pixhawk's Serial port.")

if __name__ == "__main__":
    main()
