from __future__ import annotations
import threading
import time
import sys
import os
import sched
import argparse
import select
import json
import logging
from typing import Callable, Dict
from collections import OrderedDict  # <-- eklendi

# Compatible with Windows and Unix
try:
    import msvcrt
except ImportError:
    msvcrt = None

# Import modules with short aliases
import src.shared.comm.interface_factory          as iface
import src.application.telemetry.tools.dispatcher as tlm
import src.application.telemetry.tools.cache       as tlm_cache
import src.application.command.tools.dispatcher    as cmd
from src.application.command.tools import cache    as cmd_cache

import src.core.frame_codec                        as codec
import src.core.frame_router                       as router
from src.shared.config import manager              as cfg_manager

# ---------------------------
# Logging
# ---------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("lynk_cli")

# ---------------------------
# Globals
# ---------------------------
scheduler       = sched.scheduler(time.time, time.sleep)
shutdown_event  = threading.Event()

# Default intervals (seconds)
DEFAULT_INTERVALS = {
    "gps":       1.0,
    "imu":       1.0,
    "battery":   1.0,
    "heartbeat": 1.0,
    "barometer": 2.0,
    "ping":      1.0,
}

# ---------------------------
# Utils
# ---------------------------
def pretty(obj) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)

def schedule_periodic(interval: float, fn: Callable, *args):
    """Schedules fn(*args) every `interval` seconds until shutdown."""
    def _runner():
        if shutdown_event.is_set():
            return
        try:
            fn(*args)
        except Exception as e:
            log.exception("Task %s failed: %s", getattr(fn, "__name__", fn), e)
        finally:
            if not shutdown_event.is_set():
                scheduler.enter(interval, 1, _runner)
    scheduler.enter(0, 1, _runner)

def print_compact_cache(cached: dict):
    """
    cached: { src_id: { "gps": {...}, "imu": {...}, ... }, ... }
    Her alt-tipi tek satır JSON olarak yazar; timestamp'ı en sona koyar.
    """
    preferred_order = ["gps", "imu", "battery", "heartbeat", "barometer", "ping"]

    for src_id, data_types in cached.items():
        print(f"[RECV TELEMETRY] SRC {src_id}")
        others = [k for k in data_types.keys() if k not in preferred_order]
        ordered_keys = preferred_order + sorted(others)
        for key in ordered_keys:
            if key not in data_types:
                continue
            payload = data_types[key]
            # timestamp'ı sona al — kozmetik
            if isinstance(payload, dict):
                ts = payload.get("timestamp", None)
                od = OrderedDict((k, v) for k, v in payload.items() if k != "timestamp")
                if ts is not None:
                    od["timestamp"] = ts
                compact = json.dumps(od, ensure_ascii=False, separators=(", ", ": "))
            else:
                compact = json.dumps(payload, ensure_ascii=False, separators=(", ", ": "))
            print(f"  {key}: {compact}")

# ---------------------------
# Receiver
# ---------------------------
def task_receiver_line(interface, interval=0.05):
    """
    Non-blocking receive loop: reads one frame per tick (or drain quickly),
    routes it, and logs/prints cache for T and last command for C.
    """
    max_per_tick = 10
    processed = 0

    while processed < max_per_tick:
        raw = interface.read()
        if not raw:
            break
        try:
            frame = codec.parse_mesh_frame(raw)
        except ValueError as e:
            log.warning("[PARSE] Failed: %s raw=%s", e, raw.hex())
            processed += 1
            continue

        try:
            router.route_frame(frame, interface)
        except Exception as e:
            log.exception("[ROUTER] Error routing frame: %s | frame=%s", e, frame)

        ftype = chr(frame.get("frame_type", 0))
        if ftype == 'T':
            tlm_type = frame.get("tlm_type") or frame.get("subtype") or frame.get("type")
            log.debug("[TLM] subtype=%s keys=%s", tlm_type, list(frame.keys()))
            cached = tlm_cache.get_all_cached_data()
            # <-- Burayı tek satırlık JSON çıktısı için değiştirdik
            print_compact_cache(cached)

        elif ftype == 'C':
            last_cmd = cmd_cache.get_last_command()
            print(f"[RECV COMMAND] Cache ->\n{pretty(last_cmd)}")
        else:
            log.debug("[FRAME] Unknown frame_type=%r keys=%s", ftype, list(frame.keys()))

        processed += 1

    if not shutdown_event.is_set():
        scheduler.enter(interval, 1, task_receiver_line, (interface, interval,))

# ---------------------------
# Telemetry senders
# ---------------------------
def send_gps(interface, my_id, dst_id):
    tlm.send_tlm_gps(interface, lat=37.0, lon=35.0, alt=100.0, dst=dst_id, src=my_id)

def send_imu(interface, my_id, dst_id):
    tlm.send_tlm_imu(interface, roll=1.0, pitch=2.0, yaw=3.0, dst=dst_id, src=my_id)

def send_battery(interface, my_id, dst_id):
    tlm.send_tlm_battery(interface, voltage=11.0, current=2.0, level=90.0, dst=dst_id, src=my_id)

def send_heartbeat(interface, my_id, dst_id):
    tlm.send_tlm_heartbeat(interface, mode="AUTO", health="OK", is_armed=True, gps_fix=True, sat_count=10, dst=dst_id, src=my_id)

def send_barometer(interface, my_id, dst_id):
    tlm.send_tlm_barometer(interface, vertical_speed=1.0, ground_speed=2.0, altitude_relative=100.0, dst=dst_id, src=my_id)

def send_ping(interface, my_id, dst_id):
    tlm.send_tlm_ping(interface, dst=dst_id, src=my_id)

# ---------------------------
# Commands (keymap)
# ---------------------------
def mission_example():
    return [
        {"seq": 0, "command": "TAKEOFF",  "lat": 0.0,    "lon": 0.0,    "alt": 10.0},
        {"seq": 1, "command": "WAYPOINT", "lat": 37.001, "lon": 35.002, "alt": 20.0, "hold_time": 5.0},
        {"seq": 2, "command": "LAND",     "lat": 37.001, "lon": 35.002, "alt": 0.0},
    ]

def build_keymap(my_id: int, dst_id: int) -> Dict[str, Callable[[any], None]]:
    return {
        # System
        "I": lambda interface: (log.info("[CMD] SYSTEM_SET_VEHICLE_ID"),
                                cmd.cmd_system_set_vehicle_id(interface, id=10, src=my_id, dst=dst_id)),
        "R": lambda interface: (log.info("[CMD] SYSTEM_REBOOT"),
                                cmd.cmd_system_reboot(interface, dst=dst_id, src=my_id)),

        # Flight
        "C": lambda interface: (log.info("[CMD] FLIGHT_SET_MODE GUIDED"),
                                cmd.cmd_flight_set_mode(interface, mode="GUIDED", src=my_id, dst=dst_id)),
        "X": lambda interface: (log.info("[CMD] FLIGHT_ARMING ARM"),
                                cmd.cmd_flight_arming(interface, arm=True, src=my_id, dst=dst_id)),
        "Y": lambda interface: (log.info("[CMD] FLIGHT_ARMING DISARM"),
                                cmd.cmd_flight_arming(interface, arm=False, src=my_id, dst=dst_id)),
        "T": lambda interface: (log.info("[CMD] FLIGHT_TAKEOFF 30m"),
                                cmd.cmd_flight_takeoff(interface, altitude_m=30, src=my_id, dst=dst_id)),
        "L": lambda interface: (log.info("[CMD] FLIGHT_LAND"),
                                cmd.cmd_flight_land(interface, src=my_id, dst=dst_id)),
        "G": lambda interface: (log.info("[CMD] FLIGHT_GOTO (37.001,35.002,50)"),
                                cmd.cmd_flight_goto(interface, lat=37.001, lon=35.002, alt=50.0, src=my_id, dst=dst_id)),
        "S": lambda interface: (log.info("[CMD] FLIGHT_SET_SPEED 15"),
                                cmd.cmd_flight_set_speed(interface, speed_mps=15.0, src=my_id, dst=dst_id)),
        "D": lambda interface: (log.info("[CMD] FLIGHT_SET_HEADING abs 90deg"),
                                cmd.cmd_flight_set_heading(interface, mode=0, yaw_deg=90.0, src=my_id, dst=dst_id)),
        "J": lambda interface: (log.info("[CMD] FLIGHT_SET_HOME current"),
                                cmd.cmd_flight_set_home(interface, src=my_id, dst=dst_id)),
        "O": lambda interface: (log.info("[CMD] FLIGHT_SET_ROI (37.005,35.005,10)"),
                                cmd.cmd_flight_set_roi(interface, roi_mode=1, lat=37.005, lon=35.005, alt_m=10.0, src=my_id, dst=dst_id)),
        "A": lambda interface: (log.info("[CMD] FLIGHT_SET_ALTITUDE 40"),
                                cmd.cmd_flight_set_altitude(interface, alt_m=40.0, src=my_id, dst=dst_id)),

        # Mission
        "U": lambda interface: (log.info("[CMD] MISSION_UPLOAD id=101"),
                                cmd.cmd_mission_upload(interface, mission_id=101, waypoints=mission_example(), src=my_id, dst=dst_id)),
        "K": lambda interface: (log.info("[CMD] MISSION_CONTROL START"),
                                cmd.cmd_mission_control(interface, action="START", src=my_id, dst=dst_id)),

        # Swarm
        "1": lambda interface: (log.info("[CMD] SWARM_FORMATION_EXECUTE line"),
                                cmd.cmd_swarm_formation_execute(interface, leader_id=1, formation_type="line", spacing_offset=10.0, altitude_offset=5.0, src=my_id, dst=dst_id)),
        "2": lambda interface: (log.info("[CMD] SWARM_SET_LEADER 2"),
                                cmd.cmd_swarm_set_leader(interface, leader_id=2, src=my_id, dst=dst_id)),
        "3": lambda interface: (log.info("[CMD] SWARM_SET_FORMATION_TYPE v_formation"),
                                cmd.cmd_swarm_set_formation_type(interface, formation_type="v_formation", src=my_id, dst=dst_id)),
        "4": lambda interface: (log.info("[CMD] SWARM_SET_SPACING 15"),
                                cmd.cmd_swarm_set_spacing(interface, spacing_offset=15.0, src=my_id, dst=dst_id)),
        "5": lambda interface: (log.info("[CMD] SWARM_SET_ALTITUDE_OFFSET 10"),
                                cmd.cmd_swarm_set_altitude_offset(interface, altitude_offset=10.0, src=my_id, dst=dst_id)),
        "6": lambda interface: (log.info("[CMD] SWARM_SET_STATUS HOLD"),
                                cmd.cmd_swarm_set_status(interface, status="HOLD", src=my_id, dst=dst_id)),
    }

# ---------------------------
# Keyboard
# ---------------------------
HELP_TEXT = """
Key assignments:
  --- System Commands ---
  I → SYSTEM_SET_VEHICLE_ID
  R → SYSTEM_REBOOT

  --- Flight Commands ---
  C → FLIGHT_SET_MODE
  X → FLIGHT_ARMING (ARM)
  Y → FLIGHT_ARMING (DISARM)
  T → FLIGHT_TAKEOFF
  L → FLIGHT_LAND
  G → FLIGHT_GOTO
  S → FLIGHT_SET_SPEED
  D → FLIGHT_SET_HEADING
  J → FLIGHT_SET_HOME
  O → FLIGHT_SET_ROI
  A → FLIGHT_SET_ALTITUDE

  --- Mission Commands ---
  U → MISSION_UPLOAD
  K → MISSION_CONTROL

  --- Swarm Commands ---
  1 → SWARM_FORMATION_EXECUTE
  2 → SWARM_SET_LEADER
  3 → SWARM_SET_FORMATION_TYPE
  4 → SWARM_SET_SPACING
  5 → SWARM_SET_ALTITUDE_OFFSET
  6 → SWARM_SET_STATUS

  --- General ---
  H → HELP
  Q → QUIT
"""

def keyboard_listener(interface, keymap: Dict[str, Callable], poll=0.1):
    print(HELP_TEXT)
    while not shutdown_event.is_set():
        ch = None
        try:
            if msvcrt:
                if msvcrt.kbhit():
                    ch = msvcrt.getch().decode(errors='ignore')
                else:
                    time.sleep(poll)
                    continue
            else:
                dr, _, _ = select.select([sys.stdin], [], [], poll)
                if dr:
                    ch = sys.stdin.read(1)
                else:
                    continue
        except (KeyboardInterrupt, EOFError):
            break

        if not ch:
            continue

        key = ch.upper()
        if key == 'Q':
            log.info("Exiting by user request (Q)")
            shutdown_event.set()
            break
        if key == 'H':
            print(HELP_TEXT)
            continue

        handler = keymap.get(key)
        if not handler:
            log.warning("[CMD] Undefined key: %s", key)
            continue

        try:
            handler(interface)
        except Exception as e:
            log.exception("Command %s failed: %s", key, e)

# ---------------------------
# Main
# ---------------------------
def parse_args():
    p = argparse.ArgumentParser(description="LYNK Test Console")
    p.add_argument("--config", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"),
                   help="Config JSON path (default: ./config.json)")
    # interval overrides
    p.add_argument("--gps",       type=float, default=None, help="GPS telemetry interval (s)")
    p.add_argument("--imu",       type=float, default=None, help="IMU telemetry interval (s)")
    p.add_argument("--battery",   type=float, default=None, help="Battery telemetry interval (s)")
    p.add_argument("--heartbeat", type=float, default=None, help="Heartbeat telemetry interval (s)")
    p.add_argument("--barometer", type=float, default=None, help="Barometer telemetry interval (s)")
    p.add_argument("--ping",      type=float, default=None, help="Ping telemetry interval (s)")
    p.add_argument("--log-level", default="INFO", choices=["DEBUG","INFO","WARNING","ERROR"], help="Logging level")
    return p.parse_args()

def main():
    args = parse_args()
    log.setLevel(getattr(logging, args.log_level))

    # Load config
    cfg_manager.load_config(args.config)
    cfg = cfg_manager.get_config()
    my_src_id    = cfg["vehicle"]["id"]
    other_dst_id = 0xFF

    # Resolve intervals
    intervals = DEFAULT_INTERVALS.copy()
    for key in intervals.keys():
        override = getattr(args, key, None)
        if override is not None and override > 0:
            intervals[key] = override

    log.info("Starting with intervals: %s", intervals)

    # Interface
    interface = iface.create_interface()
    interface.start()

    # Reset caches
    tlm_cache.reset_cache()
    cmd_cache.reset_command_cache()

    # Periodic telemetry tasks
    schedule_periodic(intervals["gps"],       send_gps,       interface, my_src_id, other_dst_id)
    schedule_periodic(intervals["imu"],       send_imu,       interface, my_src_id, other_dst_id)
    schedule_periodic(intervals["battery"],   send_battery,   interface, my_src_id, other_dst_id)
    schedule_periodic(intervals["heartbeat"], send_heartbeat, interface, my_src_id, other_dst_id)
    schedule_periodic(intervals["barometer"], send_barometer, interface, my_src_id, other_dst_id)
    schedule_periodic(intervals["ping"],      send_ping,      interface, my_src_id, other_dst_id)

    # Receiver task
    scheduler.enter(0, 1, task_receiver_line, (interface, 0.05))

    # Run scheduler and keyboard in parallel
    keymap = build_keymap(my_src_id, other_dst_id)
    sched_thread = threading.Thread(target=scheduler.run, daemon=True)
    sched_thread.start()

    try:
        keyboard_listener(interface, keymap)
    except KeyboardInterrupt:
        log.info("KeyboardInterrupt received. Shutting down...")
    finally:
        shutdown_event.set()
        time.sleep(0.1)
        try:
            interface.stop()
        except Exception:
            pass
        log.info("Program terminated.")

if __name__ == "__main__":
    main()
