# main.py

import threading
import time
import sys
import os
import sched

# Windows ve Unix uyumlu
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
    cmd_takeoff, cmd_landing, cmd_goto, cmd_waypoints
)
from src.tools.ftp.ftp_builder import send_ftp_file
from src.core.frame_codec import parse_mesh_frame
from src.core.frame_router import route_frame
from src.tools.telemetry.telemetry_cache import reset_cache, get_all_cached_data

# Tek scheduler objesi
scheduler = sched.scheduler(time.time, time.sleep)

def job_telemetry(interface, src, dst, interval=1.0):
    """Periyodik telemetri gönderimi ve kendini yeniden zamanlama."""
    send_tlm_gps(interface, lat=37.0 + src*0.001, lon=35.0 + src*0.001,
                 alt=100.0, dst=dst, src=src)
    send_tlm_imu(interface, roll=1.0 + src, pitch=2.0 + src,
                 yaw=3.0 + src, dst=dst, src=src)
    send_tlm_battery(interface, voltage=11.0 - src*0.1,
                     current=2.0 + src*0.1, level=90.0 - src,
                     dst=dst, src=src)
    send_tlm_heartbeat(interface, mode="AUTO", health="OK",
                       is_armed=True, gps_fix=True,
                       sat_count=10 + src, dst=dst, src=src)
    # Kendini yeniden planla
    scheduler.enter(interval, 1, job_telemetry, (interface, src, dst, interval))

def job_frame_processing(interface, interval=0.05):
    """Periyodik frame okuma ve işleme, sonra yeniden zamanlama."""
    raw = interface.read()
    if raw:
        try:
            frame = parse_mesh_frame(raw)
            route_frame(frame, interface)
        except ValueError as e:
            print(f"[ERROR] Frame parse edilemedi: {e} raw={raw.hex()}")
        cache = get_all_cached_data()
        print(f"[CACHE] {cache}")
    scheduler.enter(interval, 1, job_frame_processing, (interface, interval,))

def send_file(interface, path, src, dst):
    if not os.path.isfile(path):
        print(f"[FTP] Hata: Dosya bulunamadı: {path}")
    else:
        print(f"[FTP] Otomatik gönderiliyor: {path}")
        send_ftp_file(interface, filepath=path, src=src, dst=dst)
        print("[FTP] Gönderim tamamlandı.")


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
                 target_lat=37.001, target_lon=35.002,
                 target_alt=50.0, src=src, dst=dst)
    elif key == 'W':
        print("[CMD] WAYPOINTS")
        waypoints = [(37.001, 35.002, 50.0),
                     (37.002, 35.003, 60.0),
                     (37.003, 35.004, 70.0)]
        cmd_waypoints(interface,
                      waypoints=waypoints,
                      src=src, dst=dst)
    elif key == 'F':
        send_file(interface, r"C:\Users\KAIROS\Desktop\example.png", src, 2)
    elif key == 'B':
        send_file(interface, r"C:\Users\KAIROS\Desktop\example.png", src, 3)
    else:
        print(f"[CMD] Tanımsız tuş: {key}")

def keyboard_listener(interface, src, dst):
    instructions = """
Tuş atamaları:
  T → TAKEOFF
  L → LANDING
  G → GOTO (örnek koordinat)
  W → WAYPOINTS (örnek rota)
  F → FTP dosya gönderimi (example.png)
  Q → ÇIKIŞ
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
            print("Çıkış yapılıyor…")
            break

        send_command(interface, src, dst, key)

def main():
    interface = create_interface()
    interface.start()

    # Önce cache'i temizle
    reset_cache()

    my_src_id = 1
    other_dst_id = 0xFF

    # Scheduler'a ilk işlerin eklenmesi
    #scheduler.enter(0, 1, job_telemetry, (interface, my_src_id, other_dst_id, 1.0))
    scheduler.enter(0, 1, job_frame_processing, (interface, 0.05))

    # Scheduler'ı ayrı bir thread'te çalıştır
    threading.Thread(target=scheduler.run, daemon=True).start()

    # Klavye dinleyicisini başlat
    keyboard_listener(interface, my_src_id, other_dst_id)

    # Program sonlandırma
    interface.stop()
    print("Program sonlandırıldı.")

if __name__ == "__main__":
    main()
