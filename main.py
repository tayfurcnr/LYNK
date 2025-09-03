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
            # Yalnızca ilgili çerçeve türleri için önbellek içeriğini yazdır
            frame_type_char = chr(frame.get("frame_type", 0))
            if frame_type_char == 'T':
                #print(f"[RECV TELEMETRY] Cache: {tlm_cache.get_all_cached_data()}")
                print(f"    ")
            elif frame_type_char == 'C':
                print(f"[RECV COMMAND] Cache: {cmd_cache.get_last_command()}")
        except ValueError as e:
            print(f"[ERROR] Failed to parse frame: {e} raw={raw.hex()}")
    scheduler.enter(interval, 1, task_receiver_line, (interface, interval,))

def task_command_line(interface, key):
    # Test için örnek görev planı
    waypoints_example = [
        {"seq": 0, "command": "TAKEOFF", "lat": 0.0, "lon": 0.0, "alt": 10.0},
        {"seq": 1, "command": "WAYPOINT", "lat": 37.001, "lon": 35.002, "alt": 20.0, "hold_time": 5.0},
        {"seq": 2, "command": "LAND", "lat": 37.001, "lon": 35.002, "alt": 0.0}
    ]

    # ==============================================================================
    # --- Sistem Komutları ---
    # ==============================================================================
    if key == 'I':
        # Araca kalıcı olarak yeni bir ID atar. Değişikliğin tam olarak uygulanması için yeniden başlatma gerekebilir.
        print("[CMD] SYSTEM_SET_VEHICLE_ID")
        cmd.cmd_system_set_vehicle_id(interface, id=10, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'R':
        # Hedef sistemi yeniden başlatır.
        print("[CMD] SYSTEM_REBOOT")
        cmd.cmd_system_reboot(interface, dst=OTHER_DST_ID, src=MY_SRC_ID)

    # ==============================================================================
    # --- Uçuş Komutları ---
    # ==============================================================================
    elif key == 'C':
        # Aracın uçuş modunu değiştirir.
        print("[CMD] FLIGHT_SET_MODE")
        cmd.cmd_flight_set_mode(interface, mode="GUIDED", src=MY_SRC_ID, dst=OTHER_DST_ID)
        # Diğer modları test etmek için:
        # cmd.cmd_flight_set_mode(interface, mode="LOITER", src=MY_SRC_ID, dst=OTHER_DST_ID)
        # cmd.cmd_flight_set_mode(interface, mode="RTL", src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'X':
        # Aracı arm durumuna alır.
        print("[CMD] FLIGHT_ARMING (ARM)")
        cmd.cmd_flight_arming(interface, arm=True, src=MY_SRC_ID, dst=OTHER_DST_ID)
        # Güvenlik kontrollerini atlayarak zorla arm etmek için:
        # cmd.cmd_flight_arming(interface, arm=True, force=True, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'Y':
        # Aracı disarm durumuna alır.
        print("[CMD] FLIGHT_ARMING (DISARM)")
        cmd.cmd_flight_arming(interface, arm=False, src=MY_SRC_ID, dst=OTHER_DST_ID)
        # Güvenlik kontrollerini atlayarak zorla disarm etmek için:
        # cmd.cmd_flight_arming(interface, arm=False, force=True, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'T':
        # Aracı belirtilen irtifaya kaldırır.
        print("[CMD] FLIGHT_TAKEOFF")
        cmd.cmd_flight_takeoff(interface, altitude_m=30, src=MY_SRC_ID, dst=OTHER_DST_ID)
        # Sabit kanatlı bir araç için minimum tırmanış açısı belirterek kalkış:
        # cmd.cmd_flight_takeoff(interface, altitude_m=30, min_pitch_deg=15.0, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'L':
        # Aracı mevcut konumuna indirir.
        print("[CMD] FLIGHT_LAND")
        cmd.cmd_flight_land(interface, src=MY_SRC_ID, dst=OTHER_DST_ID)
        # Belirli bir konuma ve yöne bakarak hassas iniş yapmak için:
        # cmd.cmd_flight_land(interface, mode=1, target_lat=37.001, target_lon=35.002, yaw=180.0, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'G':
        # Aracı belirtilen GPS koordinatlarına yönlendirir.
        print("[CMD] FLIGHT_GOTO")
        cmd.cmd_flight_goto(interface, lat=37.001, lon=35.002, alt=50.0, src=MY_SRC_ID, dst=OTHER_DST_ID)
        # İrtifa referansını deniz seviyesi (AMSL) olarak belirterek gitmek için:
        # cmd.cmd_flight_goto(interface, lat=37.001, lon=35.002, alt=150.0, alt_ref=1, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'S':
        # Aracın yer hızını ayarlar.
        print("[CMD] FLIGHT_SET_SPEED")
        cmd.cmd_flight_set_speed(interface, speed_mps=15.0, src=MY_SRC_ID, dst=OTHER_DST_ID)
        # Hız değişikliğini sadece görev (AUTO) modunda geçerli kılmak için:
        # cmd.cmd_flight_set_speed(interface, speed_mps=10.0, scope=2, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'D':
        # Aracın yönünü (heading) mutlak olarak ayarlar.
        print("[CMD] FLIGHT_SET_HEADING (Absolute)")
        cmd.cmd_flight_set_heading(interface, mode=0, yaw_deg=90.0, src=MY_SRC_ID, dst=OTHER_DST_ID)
        # Mevcut yöne göre 45 derece sağa dönmek için (Relative):
        # cmd.cmd_flight_set_heading(interface, mode=1, yaw_deg=45.0, src=MY_SRC_ID, dst=OTHER_DST_ID)
        # Mevcut yöne göre 90 derece sola, saat yönünün tersine (CCW) dönmek için:
        # cmd.cmd_flight_set_heading(interface, mode=1, yaw_deg=-90.0, turn=-1, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'J':
        # Aracın mevcut konumunu yeni HOME noktası olarak ayarlar.
        print("[CMD] FLIGHT_SET_HOME (Current Position)")
        cmd.cmd_flight_set_home(interface, src=MY_SRC_ID, dst=OTHER_DST_ID)
        # Belirli bir konumu HOME olarak ayarlamak için:
        # cmd.cmd_flight_set_home(interface, lat=37.000, lon=35.000, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'O':
        # Kameranın veya gimbalin bakacağı bir ilgi noktası (ROI) belirler.
        print("[CMD] FLIGHT_SET_ROI (Location)")
        cmd.cmd_flight_set_roi(interface, roi_mode=1, lat=37.005, lon=35.005, alt_m=10.0, src=MY_SRC_ID, dst=OTHER_DST_ID)
        # Ayarlanmış ROI'yi temizlemek için:
        # cmd.cmd_flight_set_roi(interface, roi_mode=0, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'A':
        # Aracın hedef irtifasını değiştirir.
        print("[CMD] FLIGHT_SET_ALTITUDE")
        cmd.cmd_flight_set_altitude(interface, alt_m=40.0, src=MY_SRC_ID, dst=OTHER_DST_ID)
        # İrtifayı deniz seviyesine göre (AMSL) ayarlamak için:
        # cmd.cmd_flight_set_altitude(interface, alt_m=140.0, alt_ref=1, src=MY_SRC_ID, dst=OTHER_DST_ID)

    # ==============================================================================
    # --- Görev Komutları ---
    # ==============================================================================
    elif key == 'U':
        # Araca yeni bir görev planı yükler (mevcut görevi siler).
        print("[CMD] MISSION_UPLOAD")
        cmd.cmd_mission_upload(interface, mission_id=101, waypoints=waypoints_example, src=MY_SRC_ID, dst=OTHER_DST_ID)
        # Mevcut görevin üzerine ekleme yapmak için (replace_existing=False):
        # waypoints_to_add = [
        #     {"seq": 3, "command": "WAYPOINT", "lat": 37.005, "lon": 35.006, "alt": 25.0}
        # ]
        # cmd.cmd_mission_upload(interface, mission_id=101, waypoints=waypoints_to_add, replace_existing=False, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == 'K':
        # Yüklenmiş bir görevi başlatır.
        print("[CMD] MISSION_CONTROL (START)")
        cmd.cmd_mission_control(interface, action="START", src=MY_SRC_ID, dst=OTHER_DST_ID)
        # Görevi belirli bir adımdan başlatmak için:
        # cmd.cmd_mission_control(interface, action="START", start_index=2, src=MY_SRC_ID, dst=OTHER_DST_ID)
        # Görevi duraklatmak için:
        # cmd.cmd_mission_control(interface, action="PAUSE", src=MY_SRC_ID, dst=OTHER_DST_ID)
        # Göreve devam etmek için:
        # cmd.cmd_mission_control(interface, action="RESUME", src=MY_SRC_ID, dst=OTHER_DST_ID)
        # Görevi iptal etmek için:
        # cmd.cmd_mission_control(interface, action="ABORT", abort_mode="RTL", src=MY_SRC_ID, dst=OTHER_DST_ID)

    # ==============================================================================
    # --- Swarm Komutları ---
    # ==============================================================================
    elif key == '1':
        print("[CMD] SWARM_FORMATION_EXECUTE")
        cmd.cmd_swarm_formation_execute(interface, leader_id=1, formation_type="line", spacing_offset=10.0, altitude_offset=5.0, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == '2':
        print("[CMD] SWARM_SET_LEADER")
        cmd.cmd_swarm_set_leader(interface, leader_id=2, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == '3':
        print("[CMD] SWARM_SET_FORMATION_TYPE")
        cmd.cmd_swarm_set_formation_type(interface, formation_type="v_formation", src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == '4':
        print("[CMD] SWARM_SET_SPACING")
        cmd.cmd_swarm_set_spacing(interface, spacing_offset=15.0, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == '5':
        print("[CMD] SWARM_SET_ALTITUDE_OFFSET")
        cmd.cmd_swarm_set_altitude_offset(interface, altitude_offset=10.0, src=MY_SRC_ID, dst=OTHER_DST_ID)
    elif key == '6':
        print("[CMD] SWARM_SET_STATUS")
        cmd.cmd_swarm_set_status(interface, status="HOLD", src=MY_SRC_ID, dst=OTHER_DST_ID)

    else:
        print(f"[CMD] Undefined key: {key}")

def keyboard_listener(interface):
    print("""
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