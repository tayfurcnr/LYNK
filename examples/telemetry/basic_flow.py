#!/usr/bin/env python3
"""
Example 01: Telemetry Flow
Demonstrates how to send system telemetry (Battery, GPS, Heartbeat).

Usage:
    python3 examples/telemetry/basic_flow.py
"""
import os
import time
import lynk

def main():
    print("🚀 initializing LYNK Interface (Mock UART)...")
    
    # Load default config
    lynk.config.load_config("configs/config.yaml")
    
    # Create communication interface
    interface = lynk.create_interface()
    
    # My Device ID (Assuming we are node 1)
    MY_ID = 1
    TARGET_ID = 1 # Send to self/monitor (or GCS ID)

    print("\n🔋 Sending Battery Telemetry...")
    lynk.telemetry.send_tlm_battery(
        interface,
        voltage=12.5,
        current=5.2,
        level=98.0,
        dst=TARGET_ID,
        src=MY_ID
    )
    print("   [OK] Battery data sent.")

    print("\n🛰 Sending GPS Telemetry...")
    lynk.telemetry.send_tlm_gps(
        interface,
        lat=41.0082,
        lon=28.9784,
        alt=100.0,
        dst=TARGET_ID,
        src=MY_ID
    )
    print("   [OK] GPS data sent.")

    print("\n💓 Sending Heartbeat loop (Press Ctrl+C to stop)...")
    try:
        while True:
            lynk.telemetry.send_tlm_heartbeat(
                interface,
                mode="GUIDED",
                health="OK",
                is_armed=True,
                gps_fix=True,
                sat_count=12,
                dst=TARGET_ID,
                src=MY_ID
            )
            print("   [TX] Heartbeat sent")
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n🛑 Stopped.")

if __name__ == "__main__":
    main()
