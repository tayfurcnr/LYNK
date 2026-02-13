#!/usr/bin/env python3
"""
Example: Waypoint and Navigation
Demonstrates how to send GOTO and navigation commands.

Usage:
    python3 examples/command/mission_waypoint.py
"""
import lynk
import time

def main():
    print("🚀 Initializing Navigation Example...")
    
    # Load configuration
    lynk.config.load_config("configs/config.yaml")
    
    # Create communication interface
    interface = lynk.create_interface()
    
    TARGET_VEHICLE = 2

    print(f"\n📍 Sending GOTO command to Vehicle {TARGET_VEHICLE}...")
    # Parameters: Latitude, Longitude, Altitude
    lynk.command.cmd_flight_goto(
        interface,
        lat=39.9255, # Example coordinates
        lon=32.8663,
        alt=20.0,
        dst=TARGET_VEHICLE
    )
    print("   [TX] Waypoint coordinate sent.")

    time.sleep(1)

    print(f"\n🔄 Setting HEADING to 90 degrees (East)...")
    lynk.command.cmd_flight_set_heading(
        interface,
        mode=0, # Absolute heading
        yaw_deg=90.0,
        dst=TARGET_VEHICLE
    )
    print("   [TX] Heading update sent.")

if __name__ == "__main__":
    main()
