# src/handlers/swarm_handler.py

import time
from src.serializers.swarm_serializer import deserialize_swarm_command
from src.tools.ack_dispatcher import send_ack

def handle_swarm(payload: bytes, frame_meta: dict, uart_handler):
    """
    Gelen 'S' frame’ini işler. Swarm görevlerini başlatır.
    """
    cmd = deserialize_swarm_command(payload)
    drone_id = frame_meta["src_id"]
    task_type = cmd["task_type"]
    task_id = cmd["task_id"]
    start_time = cmd["start_time"]
    lat, lon, alt = cmd["params"]

    now = int(time.time())
    delay = start_time - now

    if delay > 0:
        print(f"[SwarmHandler] Görev {task_id} bekletiliyor ({delay} sn)...")
        time.sleep(delay)

    print(f"[SwarmHandler] Drone {drone_id} → Görev {task_id} başlatılıyor: {task_type=}")

    if task_type == 1:
        print(f"[SwarmHandler] GOTO → LAT: {lat}, LON: {lon}, ALT: {alt}")
        # Burada gerçek sistemde MAVLink entegrasyonu olur

        # ✅ Başarılı görev ACK
        send_ack(command_id=task_id, dst_id=drone_id, success=True, status_code=0, uart_handler=uart_handler)

    else:
        print(f"[SwarmHandler] Desteklenmeyen görev türü: {task_type}")
        # ❗ Hatalı görev NACK
        send_ack(command_id=task_id, dst_id=drone_id, success=False, status_code=2, uart_handler=uart_handler)
