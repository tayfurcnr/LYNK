import threading
import time
import sys
import os
import sched
import json

# Compatible with Windows and Unix
try:
    import msvcrt
except ImportError:
    msvcrt = None

import select

# Import modules with short aliases
import src.tools.comm.interface_factory         as iface
import src.telemetry.tools.dispatcher           as tlm
import src.telemetry.tools.cache                as cache
import src.command.tools.dispatcher             as cmd
import src.core.frame_codec                     as codec
import src.core.frame_router                    as router

# Read source and destination IDs from config
with open("config.json", "r") as f:
    cfg = json.load(f)
    MY_SRC_ID    = cfg["vehicle"]["id"]
    OTHER_DST_ID = 0xFF

# Single scheduler object
scheduler = sched.scheduler(time.time, time.sleep)

def task_send_telemetry(interface, interval=1.0):
    """Periodic telemetry transmission and self-rescheduling."""
    tlm.send_tlm_gps(interface,
                     lat = 37.0,
                     lon = 35.0,
                     alt = 100.0,
                     dst = OTHER_DST_ID,
                     src = MY_SRC_ID
    )
    tlm.send_tlm_imu(interface,
                     roll  = 1.0,
                     pitch = 2.0,
                     yaw   = 3.0,
                     dst   = OTHER_DST_ID,
                     src   = MY_SRC_ID
    )
    tlm.send_tlm_battery(interface,
                         voltage = 11.0,
                         current = 2.0,
                         level   = 90.0,
                         dst     = OTHER_DST_ID,
                         src     = MY_SRC_ID
    )
    tlm.send_tlm_heartbeat(interface,
                           mode      = "AUTO",
                           health    = "OK",
                           is_armed  = True,
                           gps_fix   = True,
                           sat_count = 10,
                           dst       = OTHER_DST_ID,
                           src       = MY_SRC_ID
    )
    # Reschedule
    scheduler.enter(interval, 1, task_send_telemetry, (interface, interval,))

def task_receiver_line(interface, interval=0.05):
    """Periodic frame reading and processing, then rescheduling."""
    raw = interface.read()
    if raw:
        try:
            frame = codec.parse_mesh_frame(raw)
            router.route_frame(frame, interface)
        except ValueError as e:
            print(f"[ERROR] Failed to parse frame: {e} raw={raw.hex()}")
        cache_data = cache.get_all_cached_data()
        print(f"[CACHE] {cache_data}")
    scheduler.enter(interval, 1, task_receiver_line, (interface, interval,))


def task_command_line(interface, key):
    """Execute command based on keyboard input."""
    if key == 'T':
        print("[CMD] TAKEOFF")
        cmd.cmd_takeoff(interface,
                        takeoff_alt = 30,
                        src         = MY_SRC_ID,
                        dst         = OTHER_DST_ID
        )
    elif key == 'L':
        print("[CMD] LANDING")
        cmd.cmd_landing(interface,
                        src = MY_SRC_ID,
                        dst = OTHER_DST_ID
        )
    elif key == 'G':
        print("[CMD] GOTO")
        cmd.cmd_goto(interface,
                     target_lat = 37.001,
                     target_lon = 35.002,
                     target_alt = 50.0,
                     src        = MY_SRC_ID,
                     dst        = OTHER_DST_ID
        )
    elif key == 'W':
        print("[CMD] WAYPOINTS")
        waypoints = [
            (37.001, 35.002, 50.0),
            (37.002, 35.003, 60.0),
            (37.003, 35.004, 70.0)
        ]
        cmd.cmd_waypoints(interface,
                          waypoints = waypoints,
                          src       = MY_SRC_ID,
                          dst       = OTHER_DST_ID
        )
    else:
        print(f"[CMD] Undefined key: {key}")


def keyboard_listener(interface):
    instructions = """
Key assignments:
  T → TAKEOFF
  L → LANDING
  G → GOTO
  W → WAYPOINTS
  Q → QUIT
"""
    print(instructions)
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
        if key == 'Q':
            print("Exiting...")
            break

        task_command_line(interface, key)


def main():
    interface = iface.create_interface()
    interface.start()

    cache.reset_cache()

    # Schedule tasks
    #scheduler.enter(0, 1, task_send_telemetry, (interface, 1.0))
    scheduler.enter(0, 1, task_receiver_line, (interface, 0.05))

    threading.Thread(target=scheduler.run, daemon=True).start()

    keyboard_listener(interface)

    interface.stop()
    print("Program terminated.")


if __name__ == "__main__":
    main()