#!/usr/bin/env python3
"""
Example 04: Custom Events
Demonstrates how to send application-specific custom events.
Useful for flexible logging or dynamic events not defined in Protobuf.

Usage:
    python3 examples/event/custom_events.py
"""
import os
import time
import lynk

EVENT_CUSTOM = 100
PRIORITY_HIGH = 2

def main():
    print("🚀 initializing LYNK Interface...")
    
    # Load configuration
    lynk.config.load_config("configs/config.yaml")
    
    # Create communication interface
    interface = lynk.create_interface()
    interface.start() # Start the transport
    
    DST_ID = 0xFF # Broadcast

    print("\n🔔 Sending Custom User Event...")
    
    # You can put any string data here.
    # The 'metadata' field is a map<string, string>
    lynk.event.send_event(
        interface=interface,
        event_type=EVENT_CUSTOM,
        priority=PRIORITY_HIGH,
        payload_params={
            "event_name": "MISSION_CHECKPOINT",
            "description": "Reached deliver/drop zone A",
            "metadata": {
                "user": "Pilot_1",
                "zone_id": "Z-42",
                "cargo_status": "RELEASED"
            }
        },
        dst_id=DST_ID
    )
    print("   [TX] Custom Event sent.")
    
    time.sleep(1)
    interface.stop() # Clean exit

if __name__ == "__main__":
    main()
