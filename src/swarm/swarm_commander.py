# src/tools/swarm_commander.py

import time
from src.serializers.swarm_serializer import serialize_swarm_command
from src.core.frame_codec import build_mesh_frame
from src.tools.comm.transmitter import send_frame
from src.core.frame_codec import load_device_id

def send_goto(uart, drone_id: int, lat: float, lon: float, alt: float, delay_sec: int = 5, task_id: int = 42):
    """
    Belirli bir drone’a koordineli GOTO görevi gönderir.

    :param uart: UART handler (gerçek ya da mock)
    :param drone_id: Hedef drone ID’si
    :param lat: Hedef enlem (float)
    :param lon: Hedef boylam (float)
    :param alt: Hedef irtifa (float)
    :param delay_sec: Görevin kaç saniye sonra başlayacağı
    :param task_id: Göreve atanacak ID (varsayılan 42)
    """
    task_type = 1  # GOTO
    param_flags = 0b00000111  # lat/lon/alt aktif
    start_time = int(time.time()) + delay_sec

    # Payload'u oluştur
    payload = serialize_swarm_command(
        task_type=task_type,
        task_id=task_id,
        param_flags=param_flags,
        start_time=start_time,
        p1=lat,
        p2=lon,
        p3=alt
    )

    # Cihaz ID'sini config.json'dan al
    src_id = load_device_id()

    # Frame'i oluştur ve gönder
    frame = build_mesh_frame(
        frame_type='S',
        src_id=src_id,
        dst_id=drone_id,
        payload=payload
    )

    send_frame(uart, frame)
    print(f"[SwarmCommander] GOTO gönderildi → Drone {drone_id} | LAT: {lat}, LON: {lon}, ALT: {alt} | Başlangıç: {start_time} ({delay_sec}s sonra)")
