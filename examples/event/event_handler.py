#!/usr/bin/env python3
"""
Example: Event Handling and Callbacks
Demonstrates how to subscribe to and handle incoming swarm events.

Usage:
    python3 examples/event/event_handler.py
"""
import os
import lynk
import time
import threading

def on_battery_event(event_data):
    """Callback for battery events."""
    print(f"\n🔋 [EVENT] Battery Report received from Node {event_data.get('src_id')}:")
    print(f"   - Percentage: {event_data.get('remaining_percent')}%")
    print(f"   - Voltage: {event_data.get('voltage')}V")

def on_custom_event(event_data):
    """Callback for custom user events."""
    print(f"\n🔔 [EVENT] Custom Event From Node {event_data.get('src_id')}:")
    print(f"   - Name: {event_data.get('event_name')}")
    print(f"   - Desc: {event_data.get('description')}")

def start_background_listener(interface):
    """Essential background loop to catch incoming wireless frames."""
    def listener():
        print("🎧 Listener thread active. Waiting for events...")
        while True:
            try:
                raw = interface.read()
                if raw:
                    lynk.process(raw, interface)
            except Exception as e:
                # print(f"Error: {e}")
                pass
            time.sleep(0.01)
    
    t = threading.Thread(target=listener, daemon=True)
    t.start()

def main():
    # Load configuration
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, "configs", "config.yaml")
    
    if os.path.exists(config_path):
        lynk.config.load_config(config_path)
    else:
        # Fallback to local run
        lynk.config.load_config("configs/config.yaml")
    
    # Create communication interface
    interface = lynk.create_interface()
    interface.start()
    
    # 1. Register Callbacks (Subscription Model)
    # Event IDs must match Protobuf definitions (31=Battery, 100=Custom)
    print("📝 Registering event handlers...")
    lynk.event.register_handler(31, on_battery_event)
    lynk.event.register_handler(100, on_custom_event)
    
    # 2. Start background processing
    start_background_listener(interface)
    
    print("\n📡 STANDBY MODE: Monitoring LYNK network for events.")
    print("Try sending an event from another terminal using 'python3 examples/event/system_events.py'")
    print("Press Ctrl+C to exit.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping listener...")
    finally:
        interface.stop()

if __name__ == "__main__":
    main()
