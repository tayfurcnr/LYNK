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
    print("🚀 Initializing LYNK Swarm Formation Example...")
    
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
    
    LEADER_ID = 2
    FORMATION = "V_SHAPE"
    SPACING = 5.0
    ALTITUDE_OFFSET = 2.0

    print(f"\n👑 Setting Node {LEADER_ID} as the Global Swarm Leader...")
    lynk.command.cmd_swarm_set_leader(interface, leader_id=LEADER_ID, dst=255)
    print("   [TX] Leader assignment broadcasted.")
    
    time.sleep(1)

    print(f"\n📐 Configuring Formation Architecture...")
    print(f"   - Type: {FORMATION}")
    print(f"   - Spacing: {SPACING}m")
    lynk.command.cmd_swarm_set_formation_type(interface, formation_type=FORMATION, dst=255)
    lynk.command.cmd_swarm_set_spacing(interface, spacing_offset=SPACING, dst=255)
    print("   [TX] Formation parameters sent.")

    time.sleep(1)

    print(f"\n🚀 EXECUTING FORMATION...")
    # This command triggers the transition and waits for ACK
    lynk.command.cmd_swarm_formation_execute(
        interface, 
        leader_id=LEADER_ID, 
        formation_type=FORMATION,
        spacing_offset=SPACING,
        altitude_offset=ALTITUDE_OFFSET,
        dst=255,
        wait_for_ack=True,
        max_retries=2
    )
    print("   [TX] Formation execution command sent.")
    
    interface.stop()

if __name__ == "__main__":
    main()
