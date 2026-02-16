import os
import lynk
import time
import threading

def start_background_listener(interface):
    """Simple background listener to route incoming packets (essential for ACKs)."""
    def listener():
        while True:
            try:
                raw = interface.read()
                if raw:
                    lynk.process(raw, interface)
            except Exception:
                pass
            time.sleep(0.01)
    
    t = threading.Thread(target=listener, daemon=True)
    t.start()

def main():
    print("🚀 Initializing LYNK Mission Manager Example...")
    
    # Load configuration
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, "configs", "config.yaml")
    
    if os.path.exists(config_path):
        lynk.config.load_config(config_path)
    else:
        lynk.config.load_config("configs/config.yaml")
    
    # Create communication interface
    interface = lynk.create_interface()
    interface.start()
    
    # Start the background listener so we can process incoming ACKs
    start_background_listener(interface)
    
    TARGET_VEHICLE = 2
    
    # Example waypoint list (Lat, Lon, Alt)
    waypoints = [
        {"lat": 39.9255, "lon": 32.8663, "alt": 20.0},
        {"lat": 39.9260, "lon": 32.8670, "alt": 25.0},
        {"lat": 39.9250, "lon": 32.8680, "alt": 15.0}
    ]

    print(f"\n📤 Uploading Mission (3 waypoints) to Vehicle {TARGET_VEHICLE}...")
    # This will block until ACK is received because wait_for_ack=True
    lynk.command.cmd_mission_upload(
        interface, 
        mission_id=101, 
        waypoints=waypoints, 
        dst=TARGET_VEHICLE,
        wait_for_ack=True
    )
    print("   [TX] Mission upload complete.")
    
    time.sleep(1)

    print(f"\n▶️ Starting Mission Execution...")
    lynk.command.cmd_mission_control(
        interface, 
        action="START", 
        start_index=0, 
        dst=TARGET_VEHICLE
    )
    print("   [TX] Start command sent.")

    time.sleep(5) # Simulating some flight time

    print(f"\n⏸️ Pausing Mission...")
    lynk.command.cmd_mission_control(
        interface, 
        action="PAUSE", 
        dst=TARGET_VEHICLE
    )
    print("   [TX] Pause command sent.")
    
    interface.stop()

if __name__ == "__main__":
    main()
