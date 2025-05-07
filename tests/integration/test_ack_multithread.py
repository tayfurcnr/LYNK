# tests/test_ack_multithread.py

import threading
import time
from queue import Queue

from src.tools.comm.interface_factory import create_interface
from src.core.frame_codec import parse_mesh_frame
from src.core.frame_router import route_frame
from src.tools.command.command_dispatcher import cmd_takeoff
from src.tools.ack.ack_tracker import get_ack_status

# Frame kuyruğu global
FRAME_QUEUE = Queue()

def frame_reader(interface, stop_event):
    """
    UART'tan frame okur ve kuyruğa ekler.
    """
    while not stop_event.is_set():
        raw = interface.uart.read()
        if raw:
            FRAME_QUEUE.put(raw)
        else:
            time.sleep(0.01)

def frame_processor(interface, stop_event):
    """
    Kuyruktan frame alır, çözümler ve yönlendirir.
    """
    while not stop_event.is_set() or not FRAME_QUEUE.empty():
        try:
            raw = FRAME_QUEUE.get(timeout=0.1)
            frame = parse_mesh_frame(raw)
            route_frame(frame, interface)
        except Exception:
            continue

def ack_monitor(cmd_name: str, dst_id: int, timeout: float = 5.0) -> bool:
    """
    Belirli komutun ACK durumunu izler. Başarılıysa True döner.
    """
    start = time.time()
    while time.time() - start < timeout:
        result = get_ack_status(cmd_name, dst_id)
        if result == 0:
            print(f"✅ Komut başarılı (ACK: SUCCESS)")
            return True
        elif result not in (None, "EXPIRED"):
            print(f"❌ Komut başarısız (ACK: Status={result})")
            return False
        time.sleep(0.2)
    print("⚠️ Komut sonucu zaman aşımına uğradı (ACK: EXPIRED)")
    return False

def test_ack_multitask():
    """
    TAKEOFF komutu gönderilir, ACK başarılı mı kontrol edilir.
    """
    interface = create_interface()
    stop_event = threading.Event()

    reader_thread = threading.Thread(target=frame_reader, args=(interface, stop_event), daemon=True)
    processor_thread = threading.Thread(target=frame_processor, args=(interface, stop_event), daemon=True)

    reader_thread.start()
    processor_thread.start()

    time.sleep(0.2)  # Sistem hazır olsun

    cmd_takeoff(interface, takeoff_alt=25.0, src=1, dst=1)
    success = ack_monitor("TAKEOFF", dst_id=1)

    stop_event.set()
    reader_thread.join()
    processor_thread.join()

    assert success, "TAKEOFF komutu için ACK başarısız veya zaman aşımına uğradı"
