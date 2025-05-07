import threading
import time
from queue import Queue

from src.tools.comm.interface_factory import create_interface
from src.core.frame_codec import parse_mesh_frame
from src.core.frame_router import route_frame
from src.tools.command.command_dispatcher import cmd_takeoff
from src.tools.ack.ack_tracker import get_ack_status

# Telemetri ve ACK için ayrı thread’ler kullanılabilir
FRAME_QUEUE = Queue()

def frame_reader(interface, stop_event):
    """
    Frame'leri UART'tan okuyup sıraya koyar.
    """
    while not stop_event.is_set():
        raw = interface.uart.read()
        if raw:
            FRAME_QUEUE.put(raw)
        else:
            time.sleep(0.01)  # CPU'yu yormamak için kısa bekleme

def frame_processor(interface, stop_event):
    """
    Okunan frame'leri parse edip route eder.
    """
    while not stop_event.is_set() or not FRAME_QUEUE.empty():
        try:
            raw = FRAME_QUEUE.get(timeout=0.1)
            frame = parse_mesh_frame(raw)
            route_frame(frame, interface)
        except Exception:
            continue

def ack_monitor(cmd_name: str, dst_id: int, timeout: float = 5.0):
    """
    Gönderilen komutun sonucunu izler.
    """
    start = time.time()
    while time.time() - start < timeout:
        result = get_ack_status(cmd_name, dst_id)
        if result == 0:
            print(f"✅ Komut başarılı (ACK: SUCCESS)")
            return
        elif result not in (None, "EXPIRED"):
            print(f"❌ Komut başarısız (ACK: Status={result})")
            return
        time.sleep(0.2)
    print("⚠️ Komut sonucu zaman aşımına uğradı (ACK: EXPIRED)")

def test_ack_multitask():
    print("🚀 [TEST] Arayüz başlatılıyor...")
    interface = create_interface()

    stop_event = threading.Event()

    print("🧵 [TEST] Frame listener başlatılıyor...")
    reader_thread = threading.Thread(target=frame_reader, args=(interface, stop_event), daemon=True)
    processor_thread = threading.Thread(target=frame_processor, args=(interface, stop_event), daemon=True)

    reader_thread.start()
    processor_thread.start()

    time.sleep(0.2)  # Sistem otursun

    print("🛰️ [TEST] TAKEOFF komutu gönderiliyor...")
    cmd_takeoff(interface, takeoff_alt=25.0, src=1, dst=1)

    print("📥 [TEST] ACK sonucu izleniyor...")
    ack_monitor("TAKEOFF", dst_id=1)

    # Thread'leri durdur
    stop_event.set()
    reader_thread.join()
    processor_thread.join()

if __name__ == "__main__":
    test_ack_multitask()
