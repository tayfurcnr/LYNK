#!/usr/bin/env python3
"""
Example: Team-Targeted Command
Demonstrates how to send a command to a specific team of vehicles.

Usage:
    python3 examples/command/team_targeted.py
"""
import lynk
import time

def main():
    print("🚀 Initializing Team-Targeted Command Example...")
    
    # Load configuration
    lynk.config.load_config("configs/config.yaml")
    
    # Create communication interface
    interface = lynk.create_interface()
    
    TARGET_TEAM = 1  # Target Team ID Alpha

    print(f"\n👥 Sending TAKEOFF command to TEAM {TARGET_TEAM}...")
    # When dst_team_id is set, the packet is filtered by team
    lynk.command.cmd_flight_takeoff(
        interface, 
        altitude_m=10.0, 
        dst=255, # Broadcast to everyone, but only team 1 will accept
        dst_team_id=TARGET_TEAM
    )
    print(f"   [TX] Team {TARGET_TEAM} takeoff command sent.")

if __name__ == "__main__":
    main()
