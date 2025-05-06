# src/handlers/telemetry_handler.py

import time
from src.serializers.telemetry_serializer import deserialize_telemetry

# ⬇️ Her cihazın verisi ayrı tutulur
_device_data_by_id = {}

# ⬇️ İsteğe bağlı olarak terminal çıktısını aç/kapat
DEBUG = True

def handle_telemetry(payload: bytes, frame_meta: dict, uart_handler=None):
    """
    'T' (Telemetry) türü frame'ini işler ve veriyi çözümler.
    """
    global _device_data_by_id

    try:
        data = deserialize_telemetry(payload)
        src_id = frame_meta.get("src_id")
        device_id = data["device_id"]

        # Her cihazın verisini ayrı sakla, zaman damgasıyla birlikte
        _device_data_by_id[device_id] = {
            "src_id": src_id,
            "device_id": device_id,
            "gps_lat": data["gps_lat"],
            "gps_lon": data["gps_lon"],
            "gps_alt": data["gps_alt"],
            "timestamp": time.time()
        }

        if DEBUG:
            print(f"[Telemetry] 🔗 Gönderen Cihaz: {src_id}")
            print(f"[Telemetry] 📡 Cihaz ID: {device_id}")
            print(f"            🌍 Enlem: {data['gps_lat']:.6f}")
            print(f"            🌍 Boylam: {data['gps_lon']:.6f}")
            print(f"            ⛰️ Yükseklik: {data['gps_alt']:.2f} m")

    except Exception as e:
        print(f"[Telemetry] ❌ Ayrıştırma hatası: {e}")

# ⬇️ Tüm cihaz verilerini döndür
def get_all_telemetry():
    return _device_data_by_id.copy()

# ⬇️ Belirli bir cihazın verisini al
def get_telemetry_by_device(device_id: int):
    return _device_data_by_id.get(device_id, None)

# ⬇️ Veriyi sıfırla (özellikle testler için)
def reset_telemetry_data():
    _device_data_by_id.clear()

# ⬇️ En son veri alınan cihaz ID'sini döndür
def get_latest_device_id():
    if not _device_data_by_id:
        return None
    return max(_device_data_by_id.items(), key=lambda x: x[1]["timestamp"])[0]

# ⬇️ Ağdaki aktif (veri gönderen) kaynak cihaz ID'lerini (src_id) listeler
def get_active_nodes(timeout: float = 10.0):
    """
    Belirtilen süre (timeout, saniye) içinde veri göndermiş src_id'leri listeler.
    """
    now = time.time()
    active_src_ids = {
        data["src_id"]
        for data in _device_data_by_id.values()
        if now - data["timestamp"] <= timeout
    }
    return sorted(active_src_ids)
