import lynk
import time
import threading

def on_command_ack(results):
    """Callback function executed when command status changes."""
    print(f"\n🔔 [CALLBACK] Command Status Updated:")
    for node_id, status in results.items():
        print(f"   - Node {node_id}: {status}")

def start_background_listener(interface):
    """Simple background listener to route incoming packets (essential for ACKs)."""
    def listener():
        while True:
            try:
                raw = interface.read()
                if raw:
                    # Single call to parse and route to handlers
                    lynk.process(raw, interface)
            except Exception:
                pass
            time.sleep(0.01)
    
    t = threading.Thread(target=listener, daemon=True)
    t.start()

def main():
    print("🚀 Initializing Async ACK Example...")
    
    # Load configuration
    lynk.config.load_config("configs/config.yaml")
    
    # Create communication interface
    interface = lynk.create_interface()
    interface.start()
    
    # Start the background listener so we can process incoming ACKs
    start_background_listener(interface)
    
    TARGET_VEHICLE = 2

    print(f"\n⚡ Sending ARM command (Async mode)...")
    lynk.command.cmd_flight_arming(
        interface, 
        arm=True, 
        dst=TARGET_VEHICLE,
        wait_for_ack=False, # Set to False for true async/non-blocking behavior
        max_retries=3,
        callback=on_command_ack
    )
    print("   [TX] Command sent. Moving on immediately...")
    print("   [WAIT] Main thread is free. Waiting 5s for background callback...")
    
    # Wait to see the callback in action
    time.sleep(5)
    
    interface.stop()

if __name__ == "__main__":
    main()
