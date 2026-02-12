#!/usr/bin/env python3
"""
LYNK MAVLink Bridge: ROS (MAVROS) to LYNK Tunnel
Replaces direct Serial/UART with ROS Topics.

This script allows LYNK to bridge an ArduPilot/PX4 vehicle that is already 
connected to MAVROS. It uses the transparent MAVLink forwarding topics.

Topics used:
- Subscribes to: /mavlink/from  (Messages FROM FCU -> ROS -> LYNK)
- Publishes to:  /mavlink/to    (Messages FROM LYNK -> ROS -> FCU)

Usage:
    python3 examples/mavlink/ros/ros_mavros_bridge.py --node 2
"""
import os
import rospy
from mavros_msgs.msg import Mavlink
import lynk
import argparse
import threading
import time

class RosMavrosBridge:
    def __init__(self, node_id):
        self.node_id = node_id
        
        # 1. Initialize ROS first
        rospy.init_node(f'lynk_mavros_bridge_{node_id}', anonymous=True)
        
        # 2. Initialize LYNK
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        config_path = os.path.join(base_dir, "configs", f"node_{node_id}", "config.yaml")
        lynk.config.load_config(config_path)
        
        # Auto-set sysid from config device_id
        self.sysid = lynk.codec.load_device_id()
        
        self.interface = lynk.create_interface()
        
        # Standard MAVROS topics are usually under /mavros/ namespace, but user setup has them at root
        self.ros_pub = rospy.Publisher("/mavlink/to", Mavlink, queue_size=10)
        rospy.Subscriber("/mavlink/from", Mavlink, self.ros_to_lynk_callback)
        
        # 3. Setup LYNK callback
        lynk.mavlink.on_mavlink_received(self.lynk_to_ros_callback)
        
        # 4. Start LYNK Interface and Router thread
        self.interface.start()
        threading.Thread(target=self.router_worker, daemon=True).start()
        
        print(f"[INFO] LYNK-MAVROS Bridge Active (Node {node_id})")
        print(f"   - Listening to: /mavlink/from")
        print(f"   - Forwarding to LYNK Mesh (Target GCS ID: 0)")

    def ros_to_lynk_callback(self, ros_msg):
        """Reconstruct full MAVLink frame from ROS message and send to LYNK."""
        try:
            # Use LYNK's ROS converter utility
            frame = lynk.ros.ros_mavlink_to_binary(ros_msg)
            
            # Safe attribute access with fallback for different MAVROS versions
            sysid = getattr(ros_msg, "sysid", 1)
            compid = getattr(ros_msg, "compid", 1)
            
            lynk.mavlink.send_mavlink(
                interface=self.interface,
                payload=frame,
                dst=0, 
                system_id=sysid,
                component_id=compid
            )
        except Exception as e:
            print(f"[ERROR] [RECONSTRUCT ERROR]: {e}")

    def lynk_to_ros_callback(self, payload, tunnel_meta, frame_meta):
        """Raw MAVLink from LYNK -> Disassemble and publish to MAVROS topic."""
        try:
            # Convert binary to ROS message dict
            msg_data = lynk.ros.binary_to_ros_mavlink(payload)
            
            # Create ROS message
            ros_msg = Mavlink()
            try:
                ros_msg.header.stamp = rospy.Time.now()
            except:
                pass
            
            # Populate fields safely using __slots__ to avoid type/attribute errors
            # Some ROS msg versions might not have all fields
            fields = set(ros_msg.__slots__)
            for key, value in msg_data.items():
                if key in fields:
                    setattr(ros_msg, key, value)
            
            self.ros_pub.publish(ros_msg)
            
        except Exception as e:
            print(f"[ERROR] [PARSE ERROR]: {e}")

    def router_worker(self):
        while not rospy.is_shutdown():
            received_any = False
            # Drain the buffer to prevent accumulation
            while True:
                raw = self.interface.read()
                if not raw:
                    break
                received_any = True
                try:
                    frame = lynk.codec.parse_mesh_frame(raw)
                    lynk.router.route_frame(frame, self.interface)
                except Exception as e:
                    print(f"[WARNING] [ROUTER ERROR]: {e}")
            
            # Adaptive sleep: shorter sleep if busy, 1ms if idle
            time.sleep(0.001 if received_any else 0.005)

    def run(self):
        rospy.spin()
        self.interface.stop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="LYNK ROS-MAVROS Bridge")
    parser.add_argument("--node", type=int, default=2, help="LYNK Node ID")
    args = parser.parse_args()

    try:
        bridge = RosMavrosBridge(args.node)
        bridge.run()
    except rospy.ROSInterruptException:
        pass
