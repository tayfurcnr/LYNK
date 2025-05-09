import time
import threading
import json
from src.tools.comm.interface_factory import create_interface
from src.tools.telemetry.telemetry_dispatcher import (
    send_tlm_gps,
    send_tlm_imu,
    send_tlm_battery,
    send_tlm_heartbeat
)
from src.tools.command.command_dispatcher import cmd_takeoff
from src.core.frame_codec import parse_mesh_frame
from src.core.frame_router import route_frame
from src.tools.telemetry.telemetry_cache import (
    reset_cache,
    get_all_cached_data
)

# Periodik telemetri gönderim fonksiyonu
def telemetry_sender(interface, src_id, dst_id, interval=1.0):
    while True:
        # GPS telemetri
        send_tlm_gps(interface,
                     lat=37.0 + src_id * 0.001,
                     lon=35.0 + src_id * 0.001,
                     alt=100.0,
                     dst=dst_id,
                     src=src_id)
        # IMU telemetri
        send_tlm_imu(interface,
                     roll=1.0 + src_id,
                     pitch=2.0 + src_id,
                     yaw=3.0 + src_id,
                     dst=dst_id,
                     src=src_id)
        # Batarya telemetri
        send_tlm_battery(interface,
                         voltage=11.0 - src_id * 0.1,
                         current=2.0 + src_id * 0.1,
                         level=90.0 - src_id,
                         dst=dst_id,
                         src=src_id)
        # Heartbeat telemetri
        send_tlm_heartbeat(interface,
                           mode="AUTO",
                           health="OK",
                           is_armed=True,
                           gps_fix=True,
                           sat_count=10 + src_id,
                           dst=dst_id,
                           src=src_id)
        time.sleep(interval)

# Gelen frame'leri işleyen fonksiyon
# Sürekli okuma ve konsola basma
def frame_processor(interface):
    while True:
        raw = interface.read()
        if raw:
            frame_dict = parse_mesh_frame(raw)
            print(f"[RECV] Frame geldi: {frame_dict}")
            route_frame(frame_dict, interface)
            all_telemetry = get_all_cached_data()
            print("HEPSİ YAZZDIRILIYOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
            print(all_telemetry)
        else:
            time.sleep(0.01)

# Ana fonksiyon
def main():
    print("Başlatılıyor: LYNK interface...")
    interface = create_interface()
    interface.start()
    reset_cache()

    # Cihaz ID'lerini ayarla
    my_src_id = 1      # Bu node'un ID'si
    other_dst_id = 1   # Karşı node'un ID'si

    # Telemetri gönderici thread'i
    sender_thread = threading.Thread(
        target=telemetry_sender,
        args=(interface, my_src_id, other_dst_id),
        daemon=True
    )
    sender_thread.start()

    # Opsiyonel: 3s sonra takeoff komutu gönder
    def command_loop():
        time.sleep(3)
        print("[CMD] Takeoff komutu gönderiliyor...")
        cmd_takeoff(interface, takeoff_alt=30, src=my_src_id, dst=other_dst_id)
    cmd_thread = threading.Thread(target=command_loop, daemon=True)
    cmd_thread.start()

    # Gelen frame işleme thread'i
    proc_thread = threading.Thread(
        target=frame_processor,
        args=(interface,),
        daemon=True
    )
    proc_thread.start()


    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Durduruluyor...")
        interface.stop()

if __name__ == '__main__':
    main()