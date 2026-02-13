#!/usr/bin/env python3
"""
MAVLink Real Scenario: ArduPilot/Pixhawk Bridge
Connects a physical Serial port (ArduPilot) to the LYNK MAVLink Tunnel.

Requirements:
    pip install pyserial

Usage:
    python3 examples/mavlink/real/ardupilot_vehicle_bridge.py --port /dev/ttyAMA0 --baud 921600
"""
import os
import time
import threading
import argparse
import serial
import lynk

# Global serial object
ser = None

def serial_reader_thread(interface, dst_id, system_id):
    """Reads raw bytes from Serial (Pixhawk) and sends via LYNK."""
    global ser
    if not ser:
        return
    
    print(f"[SERIAL] Serial reader thread started on {ser.port}")
    while True:
        try:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                if data:
                    lynk.mavlink.send_mavlink(
                        interface=interface,
                        payload=data,
                        dst=dst_id,
                        system_id=system_id,
                        component_id=1
                    )
        except Exception as e:
            print(f"[WARNING] Serial Read Error: {e}")
            break
        time.sleep(0.005)

def software_heartbeat_thread(interface, dst_id, system_id):
    """Periodically sends a MAVLink Heartbeat generated entirely by software."""
    print("[INFO] Software Heartbeat thread started.")
    # Standard MAVLink Heartbeat
    heartbeat = b"\xFD\x09\x00\x00\x01\x01\x01\x00\x00\x00\x00\x04\x03\x00\x00\x00\x03\xBE\xEF"
    
    while True:
        print(f"[MAVLINK] [SOFTWARE] Sending Heartbeat to GCS (ID {dst_id})...")
        lynk.mavlink.send_mavlink(
            interface=interface,
            payload=heartbeat,
            dst=dst_id,
            system_id=system_id,
            component_id=191 # 191 is a common 'companion computer' ID
        )
        time.sleep(5.0) # Every 5 seconds

def on_mavlink_received_from_lynk(payload, tunnel_meta, frame_meta):
    """Callback for MAVLink packets coming FROM GCS via LYNK Mesh."""
    global ser
    print(f"[RECV] [VEHICLE] Received Command from GCS (ID {frame_meta['src_id']}): {payload.hex()}")
    if ser and ser.is_open:
        ser.write(payload)
    else:
        print(f"[RECV] [SOFTWARE RECV] MAVLink from GCS: {payload.hex()[:20]}... (Serial not active)")

def router_worker(interface):
    """Background thread to process incoming LYNK frames."""
    while True:
        raw = interface.read()
        if raw:
            try:
                frame = lynk.codec.parse_mesh_frame(raw)
                lynk.router.route_frame(frame, interface)
            except Exception:
                pass
        time.sleep(0.01)

def main():
    parser = argparse.ArgumentParser(description="LYNK ArduPilot Bridge")
    parser.add_argument("--node", type=int, default=2, help="LYNK Node ID (loads configs/node_X/config.yaml)")
    parser.add_argument("--port", default="/dev/serial/by-id/usb-CubePilot_CubeOrange+_420024001551323039383833-if00", help="Serial port path.")
    parser.add_argument("--baud", type=int, default=57600, help="Baudrate (default: 57600)")
    parser.add_argument("--dst", type=int, default=1, help="Target GCS ID")
    args = parser.parse_args()

    # 2. Setup LYNK
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    config_path = os.path.join(base_dir, "configs", f"node_{args.node}", "config.yaml")

    if not os.path.exists(config_path):
        print(f"[ERROR] Config file not found: {config_path}")
        return

    lynk.config.load_config(config_path)

    # Auto-get sysid from config
    mav_sys_id = lynk.codec.load_device_id()
    
    global ser
    print(f"[INFO] Starting ArduPilot <-> LYNK Bridge (Node {args.node})...")

    # 1. Open Serial Port
    try:
        ser = serial.Serial(args.port, args.baud, timeout=0.1)
        print(f"[OK] Serial port {args.port} opened at {args.baud} baud.")
    except Exception as e:
        print(f"[ERROR] Failed to open serial port: {e}")
        print(f"[HINT] Hint: Check if the device is plugged in or try /dev/ttyACM0 directly.")
        return
    
    # 3. Start Interface
    interface = lynk.create_interface()
    interface.start()
    
    # 4. Register callback
    lynk.mavlink.on_mavlink_received(on_mavlink_received_from_lynk)
    
    # 5. Start threads
    threading.Thread(target=router_worker, args=(interface,), daemon=True).start()
    threading.Thread(target=serial_reader_thread, args=(interface, args.dst, mav_sys_id), daemon=True).start()
    
    print("\n[INFO] Bridge is ACTIVE.")
    print(f"   - LYNK Node ID: {args.node}")
    print(f"   - LYNK Target GCS ID: {args.dst}")
    print(f"   - MAVLink System ID: {mav_sys_id}")
    print("\nPress Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Bridge...")
    finally:
        if ser: ser.close()
        interface.stop()

if __name__ == "__main__":
    main()
