#!/usr/bin/env python3
"""
Example 01: Telemetry Flow
Demonstrates how to send and receive telemetry (Battery, GPS, Heartbeat).
Includes a background listener and dynamic callback registration.

Usage:
    python3 examples/telemetry/basic_flow.py
"""
import os
import time
import threading
import lynk

def on_battery_received(data: dict, meta: dict):
    """Callback for incoming battery data."""
    print(f"\n🔋 [RECV] Battery from {meta['src_id']}: {data['voltage']}V, {data['level']}%")

def background_listener(interface):
    """Thread to process incoming frames."""
    print("👂 Listener thread active.")
    while True:
        raw = interface.read()
        if raw:
            lynk.process(raw, interface)
        time.sleep(0.01)

def main():
    print("🚀 initializing LYNK Telemetry Node...")
    
    # 1. Load configuration (Using Node 1)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, "configs", "node_1", "config.yaml")
    
    if os.path.exists(config_path):
        lynk.config.load_config(config_path)
    else:
        # Fallback for generic runs
        lynk.config.load_config("configs/config.yaml")
    
    # 2. Setup Interface
    interface = lynk.create_interface()
    interface.start()
    
    # 3. Register a dynamic handler for Battery (ID 34)
    # IDs can be found in lynk/application/telemetry/definitions.py or Protobuf schemas
    lynk.telemetry.register_handler(34, on_battery_received)
    
    # 4. Start background processing
    threading.Thread(target=background_listener, args=(interface,), daemon=True).start()
    
    # 5. Sending Telemetry
    print("\n📡 Sending Telemetry Loop (Broadcasting to self/monitor)...")
    try:
        while True:
            # Send Battery (This will trigger our own callback above if we are monitoring dst=1/broadcast)
            lynk.telemetry.send_tlm_battery(
                interface,
                voltage=12.5,
                current=5.2,
                level=98.0,
                dst=1 # Sending to ourselves to see the callback work
            )
            
            # Send GPS
            lynk.telemetry.send_tlm_gps(
                interface,
                lat=41.0082,
                lon=28.9784,
                alt=100.0,
                dst=255 # Broadcast
            )
            
            print("   [TX] Battery and GPS sent.")
            time.sleep(2.0)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopped.")
    finally:
        interface.stop()

if __name__ == "__main__":
    main()
