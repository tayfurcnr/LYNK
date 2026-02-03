from __future__ import annotations
import threading
import time
import sys
sys.dont_write_bytecode = True
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
    "imu":       0.2,  # 5.0 Hz (Fast)
    "gps":       0.5,  # 2.0 Hz
    "heartbeat": 1.0,  # 1.0 Hz (Standard)
    "barometer": 2.0,  # 0.5 Hz
    "ping":      3.0,  # 0.33 Hz
    "battery":   10.0, # 0.1 Hz (Slow)
}

# Real-time telemetry toggle status (START DISABLED)
telemetry_status = {k: False for k in DEFAULT_INTERVALS.keys()}

# ---------------------------
# Utils
# ---------------------------
def pretty(obj, compact=True) -> str:
    def _sanitize(o):
        if isinstance(o, dict):
            return {k: _sanitize(v) for k, v in o.items()}
        elif isinstance(o, (list, tuple)):
            return [_sanitize(x) for x in o]
        elif isinstance(o, bytes):
            return f"hex({o.hex()})"
        return o

    try:
        indent = None if compact else 2
        return json.dumps(_sanitize(obj), ensure_ascii=False, indent=indent)
    except Exception as e:
        return f"[PRETTY ERROR: {e}] {str(obj)}"

def schedule_periodic(interval: float, fn: Callable, *args):
    """Schedules fn(*args) every `interval` seconds until shutdown."""
    def _runner():
        if shutdown_event.is_set():
            return
        
        # Check if this specific telemetry type is enabled
        # args[0] is typically the data name for our periodic tasks
        data_name = fn.__name__.replace("send_", "")
        if telemetry_status.get(data_name, True):
            try:
                fn(*args)
            except Exception as e:
                log.exception("Task %s failed: %s", getattr(fn, "__name__", fn), e)
        
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
def task_receiver_line(interface, interval=0.05, filter_self: Optional[int] = None):
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
            accepted = router.route_frame(frame, interface)
        except Exception as e:
            log.exception("[ROUTER] Error routing frame: %s | frame=%s", e, frame)
            accepted = False

        ftype = chr(frame.get("frame_type", 0))
        if ftype == 'T' and accepted:
            # clarify source
            remote_id = frame.get("src_id", "?")
            
            # Filter self-telemetry to reduce noise if specified
            if filter_self is not None and remote_id == filter_self:
                continue
            
            # Hide loopback noise if desired (optional)
            # if remote_id == my_src_id: return
            
            tlm_type = frame.get("tlm_type") or frame.get("subtype") or frame.get("type")
            log.debug("[TLM] subtype=%s keys=%s", tlm_type, list(frame.keys()))
            cached = tlm_cache.get_all_cached_data()
            
            print(f"\n[RECV TELEMETRY] From SRC {remote_id} (Router: {router.__name__ if hasattr(router, '__name__') else 'Core'})")
            print_compact_cache(cached)

        elif ftype == 'C' and accepted:
            src_id = frame.get("src_id", "?")
            last_cmd = cmd_cache.get_last_command()
            if last_cmd:
                formatted = pretty(last_cmd, compact=True)
                print(f"[RECV COMMAND] From SRC {src_id} | Cache: {formatted}")
            else:
                print(f"[RECV COMMAND] From SRC {src_id} | Cache is EMPTY")
        else:
            log.debug("[FRAME] Unknown frame_type=%r keys=%s", ftype, list(frame.keys()))

        processed += 1

    if not shutdown_event.is_set():
        scheduler.enter(interval, 1, task_receiver_line, (interface, interval, filter_self))

# ---------------------------
# Telemetry senders (Dynamic Mock)
# ---------------------------
import random

def send_gps(interface, my_id, dst_id):
    if not telemetry_status.get("gps", True): return
    # Oscillate around 37, 35
    lat = 37.0 + (random.random() * 0.01)
    lon = 35.0 + (random.random() * 0.01)
    alt = 100.0 + random.randint(-5, 5)
    tlm.send_tlm_gps(interface, lat=lat, lon=lon, alt=alt, dst=dst_id, src=codec.load_device_id())
    print(f"[SEND] GPS -> Current: ({lat:.4f}, {lon:.4f}) -> DST: {dst_id}")

def send_imu(interface, my_id, dst_id):
    if not telemetry_status.get("imu", True): return
    r = random.uniform(-5, 5)
    p = random.uniform(-5, 5)
    y = random.uniform(0, 360)
    tlm.send_tlm_imu(interface, roll=r, pitch=p, yaw=y, dst=dst_id, src=codec.load_device_id())
    print(f"[SEND] IMU -> R:{r:.1f} P:{p:.1f} Y:{y:.1f} -> DST: {dst_id}")

def send_battery(interface, my_id, dst_id):
    if not telemetry_status.get("battery", True): return
    level = random.uniform(85, 95)
    tlm.send_tlm_battery(interface, voltage=11.4, current=1.5, level=level, dst=dst_id, src=codec.load_device_id())
    print(f"[SEND] BATTERY -> {level:.1f}% -> DST: {dst_id}")

def send_heartbeat(interface, my_id, dst_id):
    if not telemetry_status.get("heartbeat", True): return
    tlm.send_tlm_heartbeat(interface, mode="STABILIZE", health="OK", is_armed=True, gps_fix=True, sat_count=12, dst=dst_id, src=codec.load_device_id())
    print(f"[SEND] HEARTBEAT -> DST: {dst_id}")

def send_barometer(interface, my_id, dst_id):
    if not telemetry_status.get("barometer", True): return
    alt = 100.0 + random.uniform(-2, 2)
    tlm.send_tlm_barometer(interface, vertical_speed=0.1, ground_speed=4.5, altitude_relative=alt, dst=dst_id, src=codec.load_device_id())
    print(f"[SEND] BAROMETER -> AltRel:{alt:.2f} -> DST: {dst_id}")

def send_ping(interface, my_id, dst_id):
    if not telemetry_status.get("ping", True): return
    tlm.send_tlm_ping(interface, dst=dst_id, src=codec.load_device_id())
    print(f"[SEND] PING -> DST: {dst_id}")

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
        # Broadcast / Team
        "B": lambda interface: (log.info("[CMD] TEAM_BROADCAST (Ping to dst=0)"),
                                tlm.send_tlm_ping(interface, dst=0, src=codec.load_device_id())),
        # System
        "I": lambda interface: (log.info(f"[CMD] SYSTEM_SET_VEHICLE_ID to {10 if codec.load_device_id() != 10 else 5}"),
                                cmd.cmd_system_set_vehicle_id(interface, id=10 if codec.load_device_id() != 10 else 5, src=codec.load_device_id(), dst=dst_id)),
        "E": lambda interface: (log.info(f"[CMD] SYSTEM_SET_TEAM_ID Toggle ({codec.load_team_id()} -> {2 if codec.load_team_id()==1 else (0 if codec.load_team_id()==2 else 1)})"),
                                cmd.cmd_system_set_team_id(interface, team_id=2 if codec.load_team_id()==1 else (0 if codec.load_team_id()==2 else 1), src=codec.load_device_id(), dst=dst_id)),
        "R": lambda interface: (log.info("[CMD] SYSTEM_REBOOT"),
                                cmd.cmd_system_reboot(interface, dst=dst_id, src=codec.load_device_id())),

        # Flight
        "C": lambda interface: (log.info("[CMD] FLIGHT_SET_MODE GUIDED"),
                                cmd.cmd_flight_set_mode(interface, mode="GUIDED", src=codec.load_device_id(), dst=dst_id)),
        "X": lambda interface: (log.info("[CMD] FLIGHT_ARMING ARM"),
                                cmd.cmd_flight_arming(interface, arm=True, src=codec.load_device_id(), dst=dst_id)),
        "Y": lambda interface: (log.info("[CMD] FLIGHT_ARMING DISARM"),
                                cmd.cmd_flight_arming(interface, arm=False, src=codec.load_device_id(), dst=dst_id)),
        "T": lambda interface: (log.info("[CMD] FLIGHT_TAKEOFF 30m"),
                                cmd.cmd_flight_takeoff(interface, altitude_m=30, src=codec.load_device_id(), dst=dst_id)),
        "L": lambda interface: (log.info("[CMD] FLIGHT_LAND"),
                                cmd.cmd_flight_land(interface, src=codec.load_device_id(), dst=dst_id)),
        "G": lambda interface: (log.info("[CMD] FLIGHT_GOTO (37.001,35.002,50)"),
                                cmd.cmd_flight_goto(interface, lat=37.001, lon=35.002, alt=50.0, src=codec.load_device_id(), dst=dst_id)),
        "S": lambda interface: (log.info("[CMD] FLIGHT_SET_SPEED 15"),
                                cmd.cmd_flight_set_speed(interface, speed_mps=15.0, src=codec.load_device_id(), dst=dst_id)),
        "D": lambda interface: (log.info("[CMD] FLIGHT_SET_HEADING abs 90deg"),
                                cmd.cmd_flight_set_heading(interface, mode=0, yaw_deg=90.0, src=codec.load_device_id(), dst=dst_id)),
        "J": lambda interface: (log.info("[CMD] FLIGHT_SET_HOME current"),
                                cmd.cmd_flight_set_home(interface, src=codec.load_device_id(), dst=dst_id)),
        "O": lambda interface: (log.info("[CMD] FLIGHT_SET_ROI (37.005,35.005,10)"),
                                cmd.cmd_flight_set_roi(interface, roi_mode=1, lat=37.005, lon=35.005, alt_m=10.0, src=codec.load_device_id(), dst=dst_id)),
        "A": lambda interface: (log.info("[CMD] FLIGHT_SET_ALTITUDE 40"),
                                cmd.cmd_flight_set_altitude(interface, alt_m=40.0, src=codec.load_device_id(), dst=dst_id)),

        # Mission
        "U": lambda interface: (log.info("[CMD] MISSION_UPLOAD id=101"),
                                cmd.cmd_mission_upload(interface, mission_id=101, waypoints=mission_example(), src=codec.load_device_id(), dst=dst_id)),
        "K": lambda interface: (log.info("[CMD] MISSION_CONTROL START"),
                                cmd.cmd_mission_control(interface, action="START", src=codec.load_device_id(), dst=dst_id)),

        # Swarm
        "1": lambda interface: (log.info("[CMD] SWARM_FORMATION_EXECUTE line"),
                                cmd.cmd_swarm_formation_execute(interface, leader_id=1, formation_type="line", spacing_offset=10.0, altitude_offset=5.0, src=codec.load_device_id(), dst=dst_id)),
        "2": lambda interface: (log.info("[CMD] SWARM_SET_LEADER 2"),
                                cmd.cmd_swarm_set_leader(interface, leader_id=2, src=codec.load_device_id(), dst=dst_id)),
        "3": lambda interface: (log.info("[CMD] SWARM_SET_FORMATION_TYPE v_formation"),
                                cmd.cmd_swarm_set_formation_type(interface, formation_type="v_formation", src=codec.load_device_id(), dst=dst_id)),
        "4": lambda interface: (log.info("[CMD] SWARM_SET_SPACING 15"),
                                cmd.cmd_swarm_set_spacing(interface, spacing_offset=15.0, src=codec.load_device_id(), dst=dst_id)),
        "5": lambda interface: (log.info("[CMD] SWARM_SET_ALTITUDE_OFFSET 10"),
                                cmd.cmd_swarm_set_altitude_offset(interface, altitude_offset=10.0, src=codec.load_device_id(), dst=dst_id)),
        "6": lambda interface: (log.info("[CMD] SWARM_SET_STATUS HOLD"),
                                cmd.cmd_swarm_set_status(interface, status="HOLD", src=codec.load_device_id(), dst=dst_id)),

        # Telemetry Toggles
        "7": lambda interface: toggle_telemetry("gps"),
        "8": lambda interface: toggle_telemetry("imu"),
        "9": lambda interface: toggle_telemetry("battery"),
        "0": lambda interface: toggle_telemetry("heartbeat"),
        "-": lambda interface: toggle_telemetry("barometer"),
        "=": lambda interface: toggle_telemetry("ping"),

        # Cross-Team / Global Tests
        "V": lambda interface: (log.info("[CMD] GLOBAL_TEAM_BROADCAST (Team=0, Dst=0)"),
                                tlm.send_tlm_ping(interface, dst=0, src=codec.load_device_id(), dst_team_id=0)),
        "Z": lambda interface: (log.info("[CMD] TARGETED_TEAM_ARM (Team=2, Dst=2)"),
                                cmd.cmd_flight_arming(interface, arm=True, src=codec.load_device_id(), dst=2, dst_team_id=2)),
    }

def toggle_telemetry(name: str):
    telemetry_status[name] = not telemetry_status[name]
    state = "ENABLED" if telemetry_status[name] else "DISABLED"
    print(f"\n[SYS] Telemetry {name.upper()} is now {state}\n")
    log.info(f"[SYS] Telemetry {name.upper()} is now {state}")

# ---------------------------
# Keyboard
# ---------------------------
HELP_TEXT = """
Key assignments:
  --- System Commands ---
  I → SYSTEM_SET_VEHICLE_ID
  E → SYSTEM_SET_TEAM_ID
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

  --- Telemetry Toggles (NEW) ---
  7 → Toggle GPS Telemetry
  8 → Toggle IMU Telemetry
  9 → Toggle Heartbeat Telemetry
  0 → Toggle ALL Telemetry

  --- General ---
  B → TEAM_BROADCAST (dst=0)
  V → GLOBAL_TEAM_BROADCAST (team=0, dst=0)
  Z → TARGETED_TEAM_2_ARM (node=2, team=2)
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

        if not ch or ch in ['\n', '\r']:
            continue

        key = ch.upper()
        if key == 'Q':
            log.info("[SYS] Exiting by user request (Q)")
            shutdown_event.set()
            break
        elif key == '7':
            telemetry_status['gps'] = not telemetry_status['gps']
            log.info(f"[CLI] GPS telemetry: {'ON' if telemetry_status['gps'] else 'OFF'}")
        elif key == '8':
            telemetry_status['imu'] = not telemetry_status['imu']
            log.info(f"[CLI] IMU telemetry: {'ON' if telemetry_status['imu'] else 'OFF'}")
        elif key == '9':
            telemetry_status['heartbeat'] = not telemetry_status['heartbeat']
            log.info(f"[CLI] Heartbeat telemetry: {'ON' if telemetry_status['heartbeat'] else 'OFF'}")
        elif key == '0':
            # Toggle ALL telemetry
            all_on = all(telemetry_status.values())
            for k in telemetry_status:
                telemetry_status[k] = not all_on
            log.info(f"[CLI] ALL telemetry: {'ON' if not all_on else 'OFF'}")
        if key == 'H':
            print(HELP_TEXT)
            continue

        handler = keymap.get(key)
        if not handler:
            # Sadece tekli karakterler için log bas (newline karakterlerini önceden ayıkladık)
            if len(key.strip()) > 0:
                log.warning("[CMD] Undefined key: %s (ord=%s)", key, ord(key[0]))
            continue

        try:
            handler(interface)
        except Exception as e:
            log.exception("[CMD] Command %s failed: %s", key, e)

# ---------------------------
# Main
# ---------------------------
def parse_args():
    p = argparse.ArgumentParser(description="LYNK Test Console")
    p.add_argument("--config", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs", "config.yaml"),
                   help="Config YAML path (default: ./configs/config.yaml)")
    # interval overrides
    p.add_argument("--gps",       type=float, default=None, help="GPS telemetry interval (s)")
    p.add_argument("--imu",       type=float, default=None, help="IMU telemetry interval (s)")
    p.add_argument("--battery",   type=float, default=None, help="Battery telemetry interval (s)")
    p.add_argument("--heartbeat", type=float, default=None, help="Heartbeat telemetry interval (s)")
    p.add_argument("--barometer", type=float, default=None, help="Barometer telemetry interval (s)")
    p.add_argument("--ping",      type=float, default=None, help="Ping telemetry interval (s)")
    p.add_argument("--log-level", default="INFO", choices=["DEBUG","INFO","WARNING","ERROR"], help="Logging level")
    p.add_argument("--no-loopback", action="store_true", help="Filter out own telemetry from logs")
    return p.parse_args()

def main():
    args = parse_args()
    log.setLevel(getattr(logging, args.log_level))

    # Load config
    if not os.path.exists(args.config):
        print(f"\n[ERROR] Config dosyası bulunamadı: {args.config}")
        print("Lütfen --config parametresi ile geçerli bir yol belirtin.")
        print("Örn: python3 main.py --config configs/node_1/config.yaml\n")
        sys.exit(1)

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
    filter_id = my_src_id if args.no_loopback else None
    scheduler.enter(0, 1, task_receiver_line, (interface, 0.05, filter_id))

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
