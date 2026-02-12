#!/usr/bin/env python3
"""
Example 02: Command Control
Demonstrates how to send commands (Arming, Takeoff) to a vehicle.

Usage:
    python3 examples/command/vehicle_control.py
"""
import os
import time
import lynk

def main():
    print("🚀 initializing LYNK Interface...")
    
    # Load configuration
    lynk.config.load_config("configs/config.yaml")
    
    # Create communication interface
    interface = lynk.create_interface()
    
    TARGET_VEHICLE = 2  # ID of the vehicle we act as GCS for

    print(f"\n🎮 Sending ARM command to Vehicle {TARGET_VEHICLE}...")
    lynk.command.cmd_flight_arming(interface, arm=True, dst=TARGET_VEHICLE)
    print("   [TX] ARM command sent.")
    
    time.sleep(1)

    print(f"\n✈️ Sending TAKEOFF (15m) to Vehicle {TARGET_VEHICLE}...")
    lynk.command.cmd_flight_takeoff(interface, altitude_m=15.0, dst=TARGET_VEHICLE)
    print("   [TX] TAKEOFF command sent.")

    time.sleep(5) # Simulating flight time

    print(f"\n🛬 Sending LAND command to Vehicle {TARGET_VEHICLE}...")
    lynk.command.cmd_flight_land(interface, dst=TARGET_VEHICLE)
    print("   [TX] LAND command sent.")

if __name__ == "__main__":
    main()
