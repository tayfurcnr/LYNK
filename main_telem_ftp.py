# main.py

import threading
import time
import sys
import os

# Windows ve Unix uyumlu
try:
    import msvcrt
except ImportError:
    msvcrt = None

import select

from apscheduler.schedulers.background import BackgroundScheduler
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

def job_telemetry(interface, src, dst):
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

def job_frame_processing(interface):
    raw = interface.read()
    if not raw:
        return
    try:
        frame = parse_mesh_frame(raw)
    except ValueError as e:
        print(f"[ERROR] Frame parse edilemedi: {e} raw={raw.hex()}")
        return

    route_frame(frame, interface)
    cache = get_all_cached_data()
    print(f"[CACHE] {cache}")

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
        waypoints = [(37.001, 35.002, 50.0),
                     (37.002, 35.003, 60.0)]
        cmd_waypoints(interface,
                      waypoints=waypoints,
                      src=src,
                      dst=dst)
    elif key == 'F':
        path = r"C:\Users\KAIROS\Desktop\example.png"
        if not os.path.isfile(path):
            print(f"[FTP] Hata: Dosya bulunamadı: {path}")
        else:
            print(f"[FTP] Otomatik gönderiliyor: {path}")
            send_ftp_file(interface, filepath=path, src=src, dst=dst)
            print("[FTP] Gönderim tamamlandı.")
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
            # Windows: doğrudan msvcrt ile oku
            if msvcrt.kbhit():
                ch = msvcrt.getch().decode(errors='ignore')
            else:
                time.sleep(0.1)
                continue
        else:
            # Unix: select ile stdin
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

    # 1) Cache'i tamamen temizle
    reset_cache()

    my_src_id = 2
    other_dst_id = 1

    # 2) Scheduler ile iş parçacıklarını planla
    sched = BackgroundScheduler()
    sched.add_job(job_telemetry,
                  'interval',
                  seconds=1,
                  args=(interface, my_src_id, other_dst_id),
                  id="telemetry")
    sched.add_job(job_frame_processing,
                  'interval',
                  seconds=0.05,
                  args=(interface,),
                  id="frame_proc")
    sched.start()

    # 3) Klavye dinleyicisini başlat
    kb_thread = threading.Thread(
        target=keyboard_listener,
        args=(interface, my_src_id, other_dst_id),
        daemon=True
    )
    kb_thread.start()

    try:
        while kb_thread.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        sched.shutdown(wait=False)
        interface.stop()
        print("Program sonlandırıldı.")

if __name__ == "__main__":
    main()
