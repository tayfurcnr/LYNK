#!/usr/bin/env python3
"""
Example 03: System Events
Demonstrates how to send standard system events (Battery Low, GPS Degraded).
These events have predefined Protobuf structures.

Usage:
    python3 examples/event/system_events.py
"""
import os
import time
import lynk

# Enum IDs from msg/event/event_enums.proto
EVENT_BATTERY_LOW = 31
EVENT_GPS_DEGRADED = 40
PRIORITY_CRITICAL = 3
PRIORITY_NORMAL = 1

def main():
    print("🚀 initializing LYNK Interface...")
    
    # Load configuration
    lynk.config.load_config("configs/config.yaml")
    
    # Create communication interface
    interface = lynk.create_interface()
    
    # Broadcast to all
    DST_ID = 0xFF 

    print("\n⚠️ Sending BATTERY LOW Alert (Critical Priority)...")
    # This will be handled by the lynk.event dispatcher
    lynk.event.send_event(
        interface=interface,
        event_type=EVENT_BATTERY_LOW,
        priority=PRIORITY_CRITICAL,
        payload_params={
            "voltage": 10.5,
            "remaining_percent": 15
        },
        dst_id=DST_ID
    )
    print("   [TX] Battery Low Event sent.")

    time.sleep(1)

    print("\n📡 Sending GPS Degraded Warning (Normal Priority)...")
    lynk.event.send_event(
        interface=interface,
        event_type=EVENT_GPS_DEGRADED,
        priority=PRIORITY_NORMAL,
        payload_params={
            "satellites": 4,
            "hdop": 2.5
        },
        dst_id=DST_ID
    )
    print("   [TX] GPS Warning sent.")

if __name__ == "__main__":
    main()
