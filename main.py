from __future__ import annotations
import threading
import time
import sys
import os
import sched
import argparse
import select

# Compatible with Windows and Unix
try:
    import msvcrt
except ImportError:
    msvcrt = None

# Import modules with short aliases
import src.shared.comm.interface_factory         as iface
import src.application.telemetry.tools.dispatcher           as tlm
import src.application.telemetry.tools.cache                as tlm_cache
import src.application.command.tools.dispatcher     as cmd
from src.application.command.tools import cache     as cmd_cache

import src.core.frame_codec                         as codec
import src.core.frame_router                        as router
from src.shared.config import manager               as cfg_manager

# --- Load Config ---
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.json")
cfg_manager.load_config(config_path)
cfg = cfg_manager.get_config()

MY_SRC_ID    = cfg["vehicle"]["id"]
OTHER_DST_ID = 0xFF

# Single scheduler object
scheduler = sched.scheduler(time.time, time.sleep)

# --- Tasks ---
def task_send_telemetry(interface, interval=1.0):
    tlm.send_tlm_gps(interface, lat=37.0, lon=35.0, alt=100.0, dst=OTHER_DST_ID, src=MY_SRC_ID)
    
    tlm.send_tlm_imu(interface, roll=1.0, pitch=2.0, yaw=3.0, dst=OTHER_DST_ID, src=MY_SRC_ID)
    tlm.send_tlm_battery(interface, voltage=11.0, current=2.0, level=90.0, dst=OTHER_DST_ID, src=MY_SRC_ID)
    tlm.send_tlm_heartbeat(interface, mode="AUTO", health="OK", is_armed=True, gps_fix=True, sat_count=10, dst=OTHER_DST_ID, src=MY_SRC_ID)
    tlm.send_tlm_barometer(interface, vertical_speed=1.0, ground_speed=2.0, altitude_relative=100.0, dst=OTHER_DST_ID, src=MY_SRC_ID)
    scheduler.enter(interval, 1, task_send_telemetry, (interface, interval,))

def task_receiver_line(interface, interval=0.05):
    raw = interface.read()
    if raw:
        try:
            frame = codec.parse_mesh_frame(raw)
            router.route_frame(frame, interface)
        except ValueError as e:
            print(f"[ERROR] Failed to parse frame: {e} raw={raw.hex()}")
        print(f"[TELEMETRY CACHE] {tlm_cache.get_all_cached_data()}")
        print(f"[COMMAND CACHE] {cmd_cache.get_last_command()}")
    scheduler.enter(interval, 1, task_receiver_line, (interface, interval,))

def task_command_line(interface, key):
    if key == 'T':
        print("[CMD] TAKEOFF")
        cmd.cmd_takeoff(interface, takeoff_alt=30, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'L':
        print("[CMD] LANDING")
        cmd.cmd_landing(interface, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'G':
        print("[CMD] GOTO")
        cmd.cmd_goto(interface, target_lat=37.001, target_lon=35.002, target_alt=50.0, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'W':
        print("[CMD] WAYPOINTS")
        waypoints = [(37.001, 35.002, 50.0), (37.002, 35.003, 60.0), (37.003, 35.004, 70.0)]
        cmd.cmd_waypoints(interface, waypoints=waypoints, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'R':
        print("[CMD] RELAY")
        cmd.cmd_task_relay(interface, task_id=1, lat=37.005, lon=35.006, alt=80.0, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'S':
        print("[CMD] SET_SPEED")
        cmd.cmd_set_speed(interface, speed=15.0, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'D':
        print("[CMD] SET_DIRECTION")
        cmd.cmd_set_direction(interface, direction=90.0, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'I':
        print("[CMD] SET_DRONE_ID")
        cmd.cmd_set_drone_id(interface, drone_id=10, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'F':
        print("[CMD] SWARM_FORMATER")
        cmd.cmd_swarm_formater(interface, formation="line", src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'H':
        print("[CMD] SWARM_LEADER")
        cmd.cmd_swarm_leader(interface, leader_id=1, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'M':
        print("[CMD] SWARM_MERGE")
        cmd.cmd_swarm_merge(interface, target_id=2, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'P':
        #"Enter mission status (e.g., PAUSE, RESUME, STOP): ")
        cmd.cmd_set_mission_status(interface, status="PAUSE", src=MY_SRC_ID, dst=OTHER_DST_ID)
    #elif key == 'U':
    #    print("[CMD] MISSION_UPLOAD")
    #    cmd.cmd_mission_upload(interface, mission_data="mission1.txt", src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'C':
        print("[CMD] SET_MODE")
        cmd.cmd_set_mode(interface, mode="GUIDED", src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'A':
        print("[CMD] ACK_COMMAND")
        cmd.cmd_ack_command(interface, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'V':
        print("[CMD] STREAM_VIDEO")
        cmd.cmd_stream_video(interface, status=True, src=MY_SRC_ID, dst=OTHER_DST_ID)
    else:
        print(f"[CMD] Undefined key: {key}")

def keyboard_listener(interface):
    print("""
Key assignments:
  T → TAKEOFF              [OKAY]
  L → LANDING              [OKAY]
  G → GOTO                 [OKAY]
  W → WAYPOINTS            [OKAY]
  R → RELAY                [OKAY]
  S → SET_SPEED          + [OKAY]
  D → SET_DIRECTION        [OKAY]
  I → SET_DRONE_ID         [OKAY] İÇERİSİNDE CONFİG DOSYASINI İŞLEYECEK BİR YAPI KURULACAK. (TAYFUR)
  F → SWARM_FORMATER     + [OKAY]
  H → SWARM_LEADER       + [OKAY]
  M → SWARM_MERGE        + [OKAY]
  P → SET_MISSION_STATUS   [OKAY]
  A → ACK_COMMAND        + [OKAY]
  V → STREAM_VIDEO         [OKAY]
  C → SET_MODE             [OKAY]
  Q → QUIT
""")
    while True:
        ch = None
        if msvcrt:
            if msvcrt.kbhit():
                ch = msvcrt.getch().decode(errors='ignore')
            else:
                time.sleep(0.1)
                continue
        else:
            dr, _, _ = select.select([sys.stdin], [], [], 0.1)
            if dr:
                ch = sys.stdin.read(1)
            else:
                continue

        key = ch.upper() if ch else ''
        if not key:
            continue
        if key == 'Q':
            print("Exiting...")
            break
        task_command_line(interface, key)

def main():
    interface = iface.create_interface()
    interface.start()

    tlm_cache.reset_cache()
    cmd_cache.reset_command_cache()

    #scheduler.enter(0, 1, task_send_telemetry, (interface, 1.0))
    scheduler.enter(0, 1, task_receiver_line, (interface, 0.05))

    threading.Thread(target=scheduler.run, daemon=True).start()
    keyboard_listener(interface)

    interface.stop()
    print("Program terminated.")

if __name__ == "__main__":
    main()