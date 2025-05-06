# tests/test_swarm_goto.py

from src.swarm.swarm_commander import send_goto
from src.core.frame_codec import parse_mesh_frame, load_device_id
from src.handlers.swarm.swarm_handler import handle_swarm
from src.handlers.ack.ack_handler import handle_ack
from src.handlers.comm.mock_handler import MockUARTHandler

def test_swarm_goto():
    mock_uart = MockUARTHandler()
    mock_uart.start()
    local_id = load_device_id()

    try:
        # 1️⃣ GOTO görevi gönder
        send_goto(
            uart=mock_uart,
            drone_id=local_id,  # Bu test cihazının kendisine gönderiliyor
            lat=37.423,
            lon=27.221,
            alt=55.0,
            delay_sec=3
        )

        # 2️⃣ GOTO frame alınır ve işlenir
        frame1 = mock_uart.read()
        if not frame1:
            print("[Test] ⚠️ GOTO frame alınamadı")
            return

        parsed1 = parse_mesh_frame(frame1)
        if chr(parsed1["frame_type"]) != 'S' or parsed1["dst_id"] != local_id:
            print(f"[Test] ⛔ Bu cihaza ait olmayan GOTO frame → dst={parsed1['dst_id']}, local={local_id}")
            return

        print("[Test] ✅ GOTO frame alındı, işleniyor...")
        handle_swarm(
            payload=parsed1["payload"],
            frame_meta={"src_id": parsed1["src_id"], "dst_id": parsed1["dst_id"]},
            uart_handler=mock_uart
        )

        # 3️⃣ ACK frame alınır ve işlenir
        frame2 = mock_uart.read()
        if not frame2:
            print("[Test] ⚠️ ACK frame alınamadı")
            return

        parsed2 = parse_mesh_frame(frame2)
        if chr(parsed2["frame_type"]) != 'A' or parsed2["dst_id"] != local_id:
            print(f"[Test] ⛔ Gelen frame ACK değil ya da hedef değil → type={parsed2['frame_type']}, dst={parsed2['dst_id']}")
            return

        print("[Test] ✅ ACK alındı, işleniyor...")
        handle_ack(
            payload=parsed2["payload"],
            frame_meta={"src_id": parsed2["src_id"]},
            uart_handler=mock_uart
        )

    except Exception as e:
        print(f"[Test] ❌ Hata oluştu: {e}")

    finally:
        mock_uart.stop()

if __name__ == "__main__":
    test_swarm_goto()
