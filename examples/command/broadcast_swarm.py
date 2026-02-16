#!/usr/bin/env python3
"""
Example: Swarm Broadcast
Demonstrates how to send a command to all vehicles in the network.

Usage:
    python3 examples/command/broadcast_swarm.py
"""
import os
import lynk
import time

def main():
    print("🚀 Initializing LYNK Broadcast Example...")
    
    # Load configuration
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, "configs", "config.yaml")
    
    if os.path.exists(config_path):
        lynk.config.load_config(config_path)
    else:
        lynk.config.load_config("configs/config.yaml")
    
    # Create communication interface
    interface = lynk.create_interface()
    
    # Target ID 255 (0xFF) is the broadcast address in LYNK
    BROADCAST_ADDR = 255

    print(f"\n📢 Broadcasting EMERGENCY LAND command to ALL vehicles...")
    lynk.command.cmd_flight_land(interface, dst=BROADCAST_ADDR)
    print("   [TX] Broadcast command sent.")
    
    time.sleep(1)
    
    print(f"\n📢 Broadcasting REBOOT command to ALL vehicles...")
    # Using the generic send_command for variety
    lynk.command.send_command(interface, "SYSTEM_REBOOT", dst=BROADCAST_ADDR)
    print("   [TX] Global reboot signal sent.")
    
    interface.stop()

if __name__ == "__main__":
    main()
