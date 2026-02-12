#!/usr/bin/env python3
"""
MAVLink Multi-Vehicle Gateway (GCS Side) - Twin Port Architecture
Dynamically assigns two UDP ports for each Drone ID discovered on LYNK.
- QGC Port: Where QGC listens for telemetry.
- GW Port: Where the Gateway listens for commands from QGC.

Usage:
    python3 examples/mavlink/real/gcs_multi_vehicle_gateway.py --qgc-start 14550 --gw-start 15550
"""
import os
import time
import threading
import socket
import argparse
import lynk

class VehicleConnection:
    """Manages a local UDP bridge for a specific Drone ID."""
    def __init__(self, drone_id, qgc_port, gw_port, lynk_interface):
        self.drone_id = drone_id
        self.qgc_port = qgc_port
        self.gw_port = gw_port
        self.interface = lynk_interface
        self.running = True
        
        # Socket to talk to GCS software
        # This socket will LISTEN on gw_port for commands and SEND to qgc_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.sock.bind(("127.0.0.1", self.gw_port))
            print(f"✅ [GATEWAY] Drone ID {drone_id} listening for CMDs on UDP {self.gw_port}")
        except Exception as e:
            # We silenly fail here because MAVLinkGateway will probe before calling
            self.running = False
            return

        self.sock.settimeout(0.1)
        self.qgc_addr = ("127.0.0.1", self.qgc_port)
        
        # Thread to read FROM QGC and pipe into LYNK
        self.thread = threading.Thread(target=self._qgc_to_lynk_loop, daemon=True)
        self.thread.start()

    def _qgc_to_lynk_loop(self):
        """Listen for MAVLink FROM GCS software (on gw_port) and pipe it into LYNK."""
        while self.running:
            try:
                data, addr = self.sock.recvfrom(8192)
                if data:
                    print(f"🕹️  [QGC -> LYNK] Sending to LYNK Mesh | DST: {self.drone_id} | Payload: {data.hex()[:20]}...")
                    # Send to LYNK mesh for this specific drone
                    lynk.mavlink.send_mavlink(
                        interface=self.interface,
                        payload=data,
                        dst=self.drone_id,
                        system_id=255, # GCS SysID
                        component_id=1
                    )
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"⚠️ [GATEWAY] Error in QGC loop for Drone {self.drone_id}: {e}")
                break

    def send_to_qgc(self, payload):
        """Send a MAVLink packet from LYNK TO the QGC listening port."""
        try:
            verbose_hex = payload.hex()[:30]
            print(f"📤 [GATEWAY -> QGC] Forwarding to {self.qgc_addr} | Drone: {self.drone_id} | Hex: {verbose_hex}...")
            self.sock.sendto(payload, self.qgc_addr)
        except Exception as e:
            print(f"⚠️ [GATEWAY] Could not send to QGC for Drone {self.drone_id}: {e}")

    def stop(self):
        self.running = False
        self.sock.close()

class MAVLinkGateway:
    def __init__(self, interface, qgc_start_port=14550, gw_start_port=15550):
        self.interface = interface
        self.qgc_start_port = qgc_start_port
        self.gw_start_port = gw_start_port
        self.next_idx = 0
        self.connections = {} # drone_id -> VehicleConnection
        self.lock = threading.Lock()

    def _is_port_free(self, port):
        """Check if a UDP port is available for binding."""
        temp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            temp_sock.bind(("127.0.0.1", port))
            temp_sock.close()
            return True
        except:
            return False

    def handle_incoming_mavlink(self, payload, tunnel_meta, frame_meta):
        drone_id = frame_meta['src_id']
        
        # Log when any MAVLink frame arrives from the mesh
        print(f"📡 [MESH -> GATEWAY] Recv from Drone {drone_id} | Len: {len(payload)}")
        
        with self.lock:
            if drone_id not in self.connections:
                # Find the next available port pair
                idx = self.next_idx
                while True:
                    q_port = self.qgc_start_port + idx
                    g_port = self.gw_start_port + idx
                    
                    # Check if g_port is free on the system
                    if self._is_port_free(g_port):
                        # Also check if another managed connection is using it (unlikely but safe)
                        if not any(c.gw_port == g_port for c in self.connections.values()):
                            break
                    
                    print(f"⚠️ [GATEWAY] Port {g_port} busy, trying next...")
                    idx += 1
                
                conn = VehicleConnection(drone_id, q_port, g_port, self.interface)
                
                if conn.running:
                    self.connections[drone_id] = conn
                    self.next_idx = idx + 1 # Update next_idx to be after this one
                    print(f"✅ [NEW DRONE] ID {drone_id} | QGC:{q_port} | GW:{g_port}")
                else:
                    print(f"❌ [GATEWAY] Failed to start connection for ID {drone_id} on {g_port}")
                    return
            
            conn = self.connections[drone_id]
        
        # Call outside the lock to prevent jitter/blocking
        conn.send_to_qgc(payload)

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
    parser = argparse.ArgumentParser(description="LYNK MAVLink Multi-Vehicle Gateway (Twin-Port)")
    parser.add_argument("--qgc-start", type=int, default=14550, help="Start port QGC listens on")
    parser.add_argument("--gw-start", type=int, default=15550, help="Start port Gateway listens on")
    args = parser.parse_args()

    print("🖥️  MAVLink Multi-Vehicle Gateway Starting (Twin-Port Architecture)...")
    
    # 1. Setup LYNK
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    config_path = os.path.join(base_dir, "configs", "node_1", "config.yaml")
    lynk.config.load_config(config_path)
    
    interface = lynk.create_interface()
    interface.start()
    
    # 2. Setup Gateway
    gateway = MAVLinkGateway(interface, args.qgc_start, args.gw_start)
    lynk.mavlink.on_mavlink_received(gateway.handle_incoming_mavlink)
    
    # 3. Start Router
    threading.Thread(target=router_worker, args=(interface,), daemon=True).start()
    
    print(f"📡 Gateway is ACTIVE.")
    print(f"   - QGC Listen Ports start at: {args.qgc_start}")
    print(f"   - GCS Target Ports start at: {args.gw_start}")
    print("\n💡 INSTRUCTIONS for QGroundControl:")
    print("   1. Add Comm Link (UDP)")
    print(f"   2. Listening Port: {args.qgc_start} (or 14551, 14552...)")
    print(f"   3. Target Host: 127.0.0.1, Port: {args.gw_start} (or 15551, 15552...)")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Gateway...")
    finally:
        # shutdown all connections
        for c in list(gateway.connections.values()):
            try:
                c.stop()
            except:
                pass
        interface.stop()

if __name__ == "__main__":
    main()
