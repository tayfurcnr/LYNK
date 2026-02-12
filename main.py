from __future__ import annotations
import threading
import time
import sys
sys.dont_write_bytecode = True
import os

# sys.path.insert(0, ...) is now handled automatically by 'import lynk' in lynk/__init__.py
import sched
import argparse
import select
import json
import logging
from typing import Callable, Dict, Optional
from collections import OrderedDict  # <-- eklendi

# Compatible with Windows and Unix
try:
    import msvcrt
except ImportError:
    msvcrt = None

# Import LYNK Library
import lynk
# Internal caches are now accessible via lynk.tlm_cache and lynk.cmd_cache

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
telemetry_report_writer = None
telemetry_intervals = {}
flow_lock = threading.Lock()
flow_bytes = {"tx": 0, "rx": 0}

# Default intervals (seconds)
DEFAULT_INTERVALS = {
    "imu":       0.2,  # 5.0 Hz
    "gps":       0.1,  # 10.0 Hz
    "heartbeat": 0.5,  # 2.0 Hz
    "barometer": 0.5,  # 2.0 Hz
    "ping":      0.5,  # 2.0 Hz
    "battery":   0.5,  # 2.0 Hz
}

# Real-time telemetry toggle status (START ENABLED)
telemetry_status = {k: True for k in DEFAULT_INTERVALS.keys()}

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
        return json.dumps(_sanitize(obj), ensure_ascii=True, indent=indent)
    except Exception as e:
        # Sanitize error message to prevent XSS
        error_msg = str(e).replace('<', '&lt;').replace('>', '&gt;')
        obj_str = str(obj)[:100]  # Limit length
        obj_str = obj_str.replace('<', '&lt;').replace('>', '&gt;')
        return f"[PRETTY ERROR: {error_msg}] {obj_str}"

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
                od = OrderedDict()
                for k, v in payload.items():
                    if k != "timestamp":
                        od[k] = v
                if ts is not None:
                    od["timestamp"] = ts
                compact = json.dumps(od, ensure_ascii=True, separators=(", ", ": "))
            else:
                compact = json.dumps(payload, ensure_ascii=True, separators=(", ", ": "))
            print(f"  {key}: {compact}")

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class TelemetryReportWriter:
    def __init__(self, path: str):
        self.path = path
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        except OSError as e:
            log.warning(f"Failed to create directory for {path}: {e}")

    def write_lines(self, tag: str, lines: list[str]) -> None:
        if not lines:
            return
        ts = time.strftime("%H:%M:%S")
        with open(self.path, "a", encoding="utf-8") as f:
            for line in lines:
                f.write(f"{ts} {tag} {line}\n")

class CountingInterface:
    def __init__(self, inner):
        self.inner = inner

    def start(self):
        self.inner.start()

    def stop(self):
        self.inner.stop()

    def send(self, data: bytes):
        if data:
            with flow_lock:
                flow_bytes["tx"] += len(data)
        return self.inner.send(data)

    def read(self):
        data = self.inner.read()
        if data:
            with flow_lock:
                flow_bytes["rx"] += len(data)
        return data

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
            frame = lynk.codec.parse_mesh_frame(raw)
        except ValueError as e:
            log.debug("[PARSE] Failed: %s raw=%s", e, raw.hex())
            processed += 1
            continue

        try:
            accepted = lynk.router.route_frame(frame, interface)
        except ValueError as e:
            log.error("[ROUTER] Invalid frame data: %s", e)
            accepted = False
        except Exception as e:
            log.exception("[ROUTER] Unexpected error routing frame: %s", e)
            accepted = False

        # Handle frame_type: could be int (67) or str ('C')
        ft_raw = frame.get("frame_type", 0)
        ftype = ft_raw if isinstance(ft_raw, str) else chr(ft_raw) if ft_raw else '?'
        
        if ftype == 'T' and accepted:
            # clarify source
            remote_id = frame.get("src_id", "?")
            
            # Filter self-telemetry to reduce noise if specified
            if filter_self is not None and isinstance(remote_id, int) and remote_id == filter_self:
                continue
            
            tlm_type = frame.get("tlm_type") or frame.get("subtype") or frame.get("type")
            log.debug("[TLM] subtype=%s keys=%s", tlm_type, list(frame.keys()))
            cached = lynk.tlm_cache.get_all_cached_data()
            
            # print(f"\n{Colors.CYAN}[RECV TELEMETRY]{Colors.ENDC} From SRC {Colors.BOLD}{remote_id}{Colors.ENDC} (Router: {lynk.router.__name__ if hasattr(router, '__name__') else 'Core'})")
            # print_compact_cache(cached)

        elif ftype == 'C' and accepted:
            src_id = frame.get("src_id", "?")
            last_cmd = lynk.cmd_cache.get_last_command()
            if last_cmd:
                formatted = pretty(last_cmd, compact=True)
                log.debug("[RECV COMMAND] From SRC %s | Cache: %s", src_id, formatted)
            else:
                log.debug("[RECV COMMAND] From SRC %s | Cache is EMPTY", src_id)
        
        elif ftype == 'A' and accepted:
            log.debug("[ACK] Received from SRC %s", frame.get("src_id", "?"))

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
    lynk.telemetry.send_tlm_gps(interface, lat=lat, lon=lon, alt=alt, dst=dst_id, src=lynk.codec.load_device_id())
    # print(f"{Colors.BLUE}[SEND] GPS{Colors.ENDC} -> Current: ({lat:.4f}, {lon:.4f}) -> DST: {dst_id}")

def send_imu(interface, my_id, dst_id):
    if not telemetry_status.get("imu", True): return
    r = random.uniform(-5, 5)
    p = random.uniform(-5, 5)
    y = random.uniform(0, 360)
    lynk.telemetry.send_tlm_imu(interface, roll=r, pitch=p, yaw=y, dst=dst_id, src=lynk.codec.load_device_id())
    # print(f"{Colors.BLUE}[SEND] IMU{Colors.ENDC} -> R:{r:.1f} P:{p:.1f} Y:{y:.1f} -> DST: {dst_id}")

def send_battery(interface, my_id, dst_id):
    if not telemetry_status.get("battery", True): return
    level = random.uniform(85, 95)
    lynk.telemetry.send_tlm_battery(interface, voltage=11.4, current=1.5, level=level, dst=dst_id, src=lynk.codec.load_device_id())
    # print(f"{Colors.BLUE}[SEND] BATTERY{Colors.ENDC} -> {level:.1f}% -> DST: {dst_id}")

def send_heartbeat(interface, my_id, dst_id):
    if not telemetry_status.get("heartbeat", True):
        return
    lynk.telemetry.send_tlm_heartbeat(
        interface,
        mode="STABILIZE",
        health="OK",
        is_armed=True,
        gps_fix=True,
        sat_count=12,
        dst=dst_id,
        src=lynk.codec.load_device_id()
    )
    # print(f"{Colors.BLUE}[SEND] HEARTBEAT{Colors.ENDC} -> DST: {dst_id}")

def send_barometer(interface, my_id, dst_id):
    if not telemetry_status.get("barometer", True):
        return
    alt = 100.0 + random.uniform(-2, 2)
    lynk.telemetry.send_tlm_barometer(
        interface,
        vertical_speed=0.1,
        ground_speed=4.5,
        altitude_relative=alt,
        dst=dst_id,
        src=lynk.codec.load_device_id()
    )
    # print(f"{Colors.BLUE}[SEND] BAROMETER{Colors.ENDC} -> AltRel:{alt:.2f} -> DST: {dst_id}")

def send_ping(interface, my_id, dst_id):
    if not telemetry_status.get("ping", True): return
    lynk.telemetry.send_tlm_ping(interface, dst=dst_id, src=lynk.codec.load_device_id())

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
        "B": lambda interface: lynk.telemetry.send_tlm_ping(interface, dst=0, src=lynk.codec.load_device_id()),
        # Telemetry debug
        "P": lambda interface: dump_telemetry_ages(),
        # System
        "I": lambda interface: lynk.command.cmd_system_set_vehicle_id(
            interface,
            id=10 if lynk.codec.load_device_id() != 10 else 5,
            src=lynk.codec.load_device_id(),
            dst=dst_id
        ),
        "E": lambda interface: lynk.command.cmd_system_set_team_id(interface, team_id=2 if lynk.codec.load_team_id()==1 else (0 if lynk.codec.load_team_id()==2 else 1), src=lynk.codec.load_device_id(), dst=dst_id),
        "R": lambda interface: lynk.command.cmd_system_reboot(interface, dst=dst_id, src=lynk.codec.load_device_id()),

        # Flight
        "C": lambda interface: lynk.command.cmd_flight_set_mode(interface, mode="GUIDED", src=lynk.codec.load_device_id(), dst=dst_id),
        "X": lambda interface: lynk.command.send_command(interface, "FLIGHT_ARMING", arm=True, force=False, src=lynk.codec.load_device_id(), dst=dst_id, wait_for_ack=True, max_retries=3),
        "Y": lambda interface: lynk.command.send_command(interface, "FLIGHT_ARMING", arm=False, force=False, src=lynk.codec.load_device_id(), dst=dst_id, wait_for_ack=True, max_retries=3),
        "T": lambda interface: lynk.command.send_command(interface, "FLIGHT_TAKEOFF", altitude_m=30.0, min_pitch_deg=0.0, src=lynk.codec.load_device_id(), dst=dst_id, wait_for_ack=True, max_retries=3),
        "L": lambda interface: lynk.command.send_command(interface, "FLIGHT_LAND", mode=0, has_target=False, src=lynk.codec.load_device_id(), dst=dst_id, wait_for_ack=True, max_retries=3),
        "G": lambda interface: lynk.command.cmd_flight_goto(interface, lat=37.001, lon=35.002, alt=50.0, src=lynk.codec.load_device_id(), dst=dst_id, wait_for_ack=True, max_retries=3),
        "S": lambda interface: lynk.command.cmd_flight_set_speed(interface, speed_mps=15.0, src=lynk.codec.load_device_id(), dst=dst_id),
        "D": lambda interface: lynk.command.cmd_flight_set_heading(interface, mode=0, yaw_deg=90.0, src=lynk.codec.load_device_id(), dst=dst_id),
        "J": lambda interface: lynk.command.cmd_flight_set_home(interface, src=lynk.codec.load_device_id(), dst=dst_id),
        "O": lambda interface: lynk.command.cmd_flight_set_roi(interface, roi_mode=1, lat=37.005, lon=35.005, alt_m=10.0, src=lynk.codec.load_device_id(), dst=dst_id),
        "A": lambda interface: lynk.command.cmd_flight_set_altitude(interface, alt_m=40.0, src=lynk.codec.load_device_id(), dst=dst_id),

        # Mission
        "U": lambda interface: lynk.command.cmd_mission_upload(interface, mission_id=101, waypoints=mission_example(), src=lynk.codec.load_device_id(), dst=dst_id),
        "K": lambda interface: lynk.command.cmd_mission_control(interface, action="START", src=lynk.codec.load_device_id(), dst=dst_id),

        # Swarm
        "1": lambda interface: lynk.command.cmd_swarm_formation_execute(interface, leader_id=1, formation_type="line", spacing_offset=10.0, altitude_offset=5.0, src=lynk.codec.load_device_id(), dst=dst_id),
        "2": lambda interface: lynk.command.cmd_swarm_set_leader(interface, leader_id=2, src=lynk.codec.load_device_id(), dst=dst_id),
        "3": lambda interface: lynk.command.cmd_swarm_set_formation_type(interface, formation_type="v_formation", src=lynk.codec.load_device_id(), dst=dst_id),
        "4": lambda interface: lynk.command.cmd_swarm_set_spacing(interface, spacing_offset=15.0, src=lynk.codec.load_device_id(), dst=dst_id),
        "5": lambda interface: lynk.command.cmd_swarm_set_altitude_offset(interface, altitude_offset=10.0, src=lynk.codec.load_device_id(), dst=dst_id),
        "6": lambda interface: lynk.command.cmd_swarm_set_status(interface, status="HOLD", src=lynk.codec.load_device_id(), dst=dst_id),

        # Telemetry Toggles
        "7": lambda interface: toggle_telemetry("gps"),
        "8": lambda interface: toggle_telemetry("imu"),
        "9": lambda interface: toggle_telemetry("battery"),
        "0": lambda interface: toggle_telemetry("heartbeat"),
        "-": lambda interface: toggle_telemetry("barometer"),
        "=": lambda interface: toggle_telemetry("ping"),

        # Cross-Team / Global Tests
        "V": lambda interface: lynk.telemetry.send_tlm_ping(interface, dst=0, src=lynk.codec.load_device_id(), dst_team_id=0),
        "Z": lambda interface: lynk.command.cmd_flight_arming(interface, arm=True, src=lynk.codec.load_device_id(), dst=2, dst_team_id=2),
    }

def toggle_telemetry(name: str):
    telemetry_status[name] = not telemetry_status[name]
    state = "ENABLED" if telemetry_status[name] else "DISABLED"
    print(f"\n[SYS] Telemetry {name.upper()} is now {state}\n")
    log.info(f"[SYS] Telemetry {name.upper()} is now {state}")

def _format_telemetry_ages() -> list[str]:
    from lynk.application.telemetry.tools.cache import get_all_cached_data
    now = time.monotonic()
    data = get_all_cached_data()
    if not data:
        return []
    lines = []
    for src_id, info in sorted(data.items()):
        tlm = info.get("telemetry", {})
        if not tlm:
            continue
        parts = []
        for name, payload in sorted(tlm.items()):
            age = now - payload.get("timestamp", 0)
            parts.append(f"{name}={age:.3f}s")
        lines.append(f"SRC {src_id}: " + ", ".join(parts))
    return lines

def dump_telemetry_ages() -> None:
    lines = _format_telemetry_ages()
    if not lines:
        log.info("[TELEMETRY] No cached data.")
        return
    for line in lines:
        log.info(f"[TELEMETRY] AGE | {line}")

def _health_status(age: float, expected: float) -> tuple[str, str]:
    if expected <= 0:
        return Colors.GREEN, "OK"
    if age <= expected * 1.5:
        return Colors.GREEN, "OK"
    if age <= expected * 3.0:
        return Colors.YELLOW, "WARN"
    return Colors.RED, "MISS"

def _format_telemetry_health(intervals: Dict[str, float], colored: bool = True) -> list[str]:
    from lynk.application.telemetry.tools.cache import get_all_cached_data
    now = time.monotonic()
    data = get_all_cached_data()
    if not data:
        return []
    out_lines = []
    for src_id, info in sorted(data.items()):
        tlm = info.get("telemetry", {})
        if not tlm:
            continue
        parts = []
        for name, payload in sorted(tlm.items()):
            if name not in intervals:
                continue
            age = now - payload.get("timestamp", 0)
            color, label = _health_status(age, intervals[name])
            if colored:
                parts.append(f"{color}{name}={age:.2f}s({label}){Colors.ENDC}")
            else:
                parts.append(f"{name}={age:.2f}s({label})")
        if parts:
            out_lines.append(f"SRC {src_id}: " + ", ".join(parts))
    return out_lines

def telemetry_health_loop(intervals: Dict[str, float], period: float = 1.0) -> None:
    while not shutdown_event.is_set():
        health_lines = _format_telemetry_health(intervals, colored=True)
        for line in health_lines:
            log.info(f"[TELEMETRY] HEALTH | {line}")
        if telemetry_report_writer:
            age_lines = _format_telemetry_ages()
            file_health = _format_telemetry_health(intervals, colored=False)
            telemetry_report_writer.write_lines("[AGE]", age_lines)
            telemetry_report_writer.write_lines("[HEALTH]", file_health)
        time.sleep(period)

def flow_report_loop(period: float = 1.0) -> None:
    last = time.monotonic()
    last_tx = 0
    last_rx = 0
    while not shutdown_event.is_set():
        time.sleep(period)
        now = time.monotonic()
        with flow_lock:
            tx = flow_bytes["tx"]
            rx = flow_bytes["rx"]
        dt = max(now - last, 1e-6)
        tx_bps = (tx - last_tx) / dt
        rx_bps = (rx - last_rx) / dt
        total_bps = tx_bps + rx_bps
        log.info("[FLOW] TX: %.1f B/s | RX: %.1f B/s | TOTAL: %.1f B/s", tx_bps, rx_bps, total_bps)
        last = now
        last_tx = tx
        last_rx = rx

# ---------------------------
# Keyboard
# ---------------------------
# Help text displayed to users showing available keyboard commands
# This text is shown when user presses 'H' or at startup
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

  --- General ---
  B → TEAM_BROADCAST (dst=0)
  V → GLOBAL_TEAM_BROADCAST (team=0, dst=0)
  Z → TARGETED_TEAM_2_ARM (node=2, team=2)
  P → PRINT TELEMETRY AGE
  H → HELP
  Q → QUIT
"""

def keyboard_listener(interface, keymap: Dict[str, Callable], poll=0.1):
    """Listen for keyboard input and execute mapped commands.
    
    Args:
        interface: Communication interface for sending commands
        keymap: Dictionary mapping keys to command handlers
        poll: Polling interval in seconds
    """
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
    """Parse command line arguments.
    
    Returns:
        Parsed arguments with config path and telemetry intervals
    """
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
    """Main entry point for LYNK test console.
    
    Initializes the system, starts telemetry tasks, and runs the keyboard listener.
    """
    global telemetry_report_writer, telemetry_intervals
    args = parse_args()
    log.setLevel(getattr(logging, args.log_level))

    # Load config
    if not os.path.exists(args.config):
        print(f"\n[ERROR] Config dosyası bulunamadı: {args.config}")
        print("Lütfen --config parametresi ile geçerli bir yol belirtin.")
        print("Örn: python3 main.py --config configs/node_1/config.yaml\n")
        sys.exit(1)

    lynk.config.load_config(args.config)
    cfg = lynk.config.get_config()
    my_src_id    = cfg["vehicle"]["id"]
    other_dst_id = 0xFF

    # Resolve intervals
    intervals = DEFAULT_INTERVALS.copy()
    for key in intervals.keys():
        override = getattr(args, key, None)
        if override is not None and override > 0:
            intervals[key] = override
    telemetry_intervals = intervals

    log.info("Starting with intervals: %s", intervals)

    # Interface
    interface = CountingInterface(lynk.create_interface())
    interface.start()

    # Reset caches
    lynk.tlm_cache.reset_cache()
    lynk.cmd_cache.reset_command_cache()

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

    # Telemetry report writer (optional)
    report_cfg = cfg.get("telemetry_monitor", {})
    if report_cfg.get("enabled", True):
        report_path = report_cfg.get(
            "file_path",
            os.path.join("logs", f"telemetry_monitor_node_{my_src_id}.log"),
        )
        telemetry_report_writer = TelemetryReportWriter(report_path)
    report_period = float(report_cfg.get("interval_sec", 1.0))

    # Run scheduler and keyboard in parallel
    keymap = build_keymap(my_src_id, other_dst_id)
    sched_thread = threading.Thread(target=scheduler.run, daemon=True)
    sched_thread.start()
    health_thread = threading.Thread(target=telemetry_health_loop, args=(intervals, report_period), daemon=True)
    health_thread.start()
    flow_thread = threading.Thread(target=flow_report_loop, args=(1.0,), daemon=True)
    flow_thread.start()

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
