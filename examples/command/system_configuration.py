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
    print("🚀 Initializing LYNK System Configuration Example...")
    
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
    
    # Let's say we have a node with dummy ID 99 and we want to configure it
    CURRENT_ID = 99
    NEW_ID = 5
    NEW_TEAM = 1 # Team Alpha

    print(f"\n🆔 Renaming Vehicle {CURRENT_ID} to {NEW_ID}...")
    lynk.command.cmd_system_set_vehicle_id(
        interface, 
        id=NEW_ID, 
        dst=CURRENT_ID,
        wait_for_ack=True
    )
    print("   [TX] ID change command sent.")
    
    time.sleep(1)

    print(f"\n👥 Assigning Vehicle {NEW_ID} to Team {NEW_TEAM}...")
    lynk.command.cmd_system_set_team_id(
        interface, 
        team_id=NEW_TEAM, 
        dst=NEW_ID,
        wait_for_ack=True
    )
    print("   [TX] Team assignment sent.")

    time.sleep(1)
    
    print(f"\n🔄 Rebooting Vehicle {NEW_ID} to apply all changes...")
    lynk.command.cmd_system_reboot(interface, dst=NEW_ID)
    print("   [TX] Reboot command sent.")
    
    interface.stop()

if __name__ == "__main__":
    main()
