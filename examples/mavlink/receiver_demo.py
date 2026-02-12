#!/usr/bin/env python3
"""
Example 06: MAVLink Receiver
Demonstrates how to listen for and process tunneled MAVLink packets.

Usage:
    python3 examples/mavlink/receiver_demo.py
"""
import os
import time
import lynk

def on_mav_received(payload: bytes, tunnel_meta: dict, frame_meta: dict):
    """
    Callback triggered whenever a MAVLink packet arrives via LYNK.
    """
    print(f"\n📩 [RECEIVED] MAVLink Packet!")
    print(f"   - Raw Payload: {payload.hex()[:40]}...")
    print(f"   - Payload Size: {len(payload)} bytes")
    print(f"   - LYNK Source ID: {frame_meta['src_id']}")
    print(f"   - MAVLink System ID: {tunnel_meta['system_id']}")
    print(f"   - Timestamp (us): {tunnel_meta['timestamp_us']}")
    print(f"   - Hop Count: {frame_meta['hop_count']}")

def main():
    print("🛰️ Starting LYNK MAVLink Receiver Simulation...")
    
    # 1. Load configuration (Using Node 2 for Receiver)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, "configs", "node_2", "config.yaml")
    lynk.config.load_config(config_path)
    
    # 2. Register the MAVLink callback
    lynk.mavlink.on_mavlink_received(on_mav_received)
    
    # 3. Create and start LYNK interface
    # Using default config (usually UDP for desktop testing)
    interface = lynk.create_interface()
    interface.start()
    
    print("\n👂 Listening for MAVLink packets through LYNK tunnel...")
    print("   (Hint: Run 'python3 examples/mavlink/tunnel_demo.py' in another terminal)")
    
    try:
        while True:
            # 4. Read raw bytes from interface
            raw = interface.read()
            if raw:
                try:
                    # 5. Parse raw bytes into a LYNK Mesh Frame
                    frame = lynk.codec.parse_mesh_frame(raw)
                    
                    # 6. Route the frame (this triggers our on_mav_received callback)
                    lynk.router.route_frame(frame, interface)
                except Exception as e:
                    print(f"Error processing frame: {e}")
            
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nStopping receiver...")
    finally:
        interface.stop()

if __name__ == "__main__":
    main()
