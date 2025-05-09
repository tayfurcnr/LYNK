import threading
import time
import sys

# Windows and Unix compatibility for keyboard input
try:
    import msvcrt
except ImportError:
    msvcrt = None

import select

from src.tools.comm.interface_factory import create_interface
from src.tools.telemetry.telemetry_dispatcher import (
    send_tlm_gps, send_tlm_imu, send_tlm_battery, send_tlm_heartbeat
)
from src.tools.command.command_dispatcher import (
    cmd_takeoff,
    cmd_landing,
    cmd_goto,
    cmd_waypoints
)
from src.core.frame_codec import parse_mesh_frame
from src.core.frame_router import route_frame
from src.tools.telemetry.telemetry_cache import reset_cache, get_all_cached_data

# Thread-safe stop event
stop_event = threading.Event()

# Telemetry sending loop
def telemetry_loop(interface, src, dst, interval=1.0):
    while not stop_event.is_set():
        send_tlm_gps(interface, lat=37.0 + src * 0.001, lon=35.0 + src * 0.001,
                     alt=100.0, dst=dst, src=src)
        send_tlm_imu(interface, roll=1.0 + src, pitch=2.0 + src,
                     yaw=3.0 + src, dst=dst, src=src)
        send_tlm_battery(interface,
                         voltage=11.0 - src * 0.1,
                         current=2.0 + src * 0.1,
                         level=90.0 - src,
                         dst=dst,
                         src=src)
        send_tlm_heartbeat(interface,
                           mode="AUTO",
                           health="OK",
                           is_armed=True,
                           gps_fix=True,
                           sat_count=10 + src,
                           dst=dst,
                           src=src)
        time.sleep(interval)

# Frame processing loop
def frame_processing_loop(interface, interval=0.05):
    while not stop_event.is_set():
        raw = interface.read()
        if raw:
            try:
                frame = parse_mesh_frame(raw)
                route_frame(frame, interface)
            except ValueError as e:
                print(f"[ERROR] Frame parse failed: {e} raw={raw.hex()}")
            cache = get_all_cached_data()
            print(f"[CACHE] {cache}")
        time.sleep(interval)

# Send command based on key press
def send_command(interface, src, dst, key):
    if key == 'T':
        print("[CMD] TAKEOFF")
        cmd_takeoff(interface, takeoff_alt=30, src=src, dst=dst)
    elif key == 'L':
        print("[CMD] LANDING")
        cmd_landing(interface, src=src, dst=dst)
    elif key == 'G':
        print("[CMD] GOTO")
        cmd_goto(interface,
                 target_lat=37.001,
                 target_lon=35.002,
                 target_alt=50.0,
                 src=src,
                 dst=dst)
    elif key == 'W':
        print("[CMD] WAYPOINTS")
        waypoints = [(37.001, 35.002, 50.0), (37.002, 35.003, 60.0)]
        cmd_waypoints(interface, waypoints=waypoints, src=src, dst=dst)
    else:
        print(f"[CMD] Unknown key: {key}")

# Keyboard listener thread
def keyboard_listener(interface, src, dst):
    instructions = """
Key mappings:
  T → TAKEOFF
  L → LANDING
  G → GOTO
  W → WAYPOINTS
  Q → QUIT
"""
    print(instructions)
    while not stop_event.is_set():
        ch = None
        if msvcrt:
            if msvcrt.kbhit():
                ch = msvcrt.getch().decode(errors='ignore')
        else:
            dr, _, _ = select.select([sys.stdin], [], [], 0.1)
            if dr:
                ch = sys.stdin.read(1)
        if not ch:
            continue
        key = ch.upper()
        if key == 'Q':
            print("Exiting...")
            stop_event.set()
            break
        send_command(interface, src, dst, key)

# Main entry point
def main():
    interface = create_interface()
    interface.start()
    reset_cache()

    my_src_id = 2
    other_dst_id = 1

    # Start telemetry and frame processing threads
    telemetry_thread = threading.Thread(
        target=telemetry_loop,
        args=(interface, my_src_id, other_dst_id),
        daemon=True
    )
    frame_thread = threading.Thread(
        target=frame_processing_loop,
        args=(interface,),
        daemon=True
    )
    kb_thread = threading.Thread(
        target=keyboard_listener,
        args=(interface, my_src_id, other_dst_id),
        daemon=True
    )

    telemetry_thread.start()
    frame_thread.start()
    kb_thread.start()

    try:
        # Wait until keyboard thread signals stop
        while not stop_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        stop_event.set()
    finally:
        interface.stop()
        print("Program terminated.")

if __name__ == "__main__":
    main()
