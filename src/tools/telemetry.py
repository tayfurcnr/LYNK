# tools/telemetry.py

from src.serializers.telemetry_serializer import serialize_telemetry
from src.frame_codec import build_mesh_frame

def build_telemetry_frame(device_id: int, lat: float, lon: float, alt: float,
                           src_id: int, dst_id: int = 0xFF,
                           config_path=None) -> bytes:
    """
    Telemetri verilerini alır, uygun çerçeveyi oluşturur.

    Parameters:
        device_id (int): Cihaz ID'si
        lat (float): GPS enlem
        lon (float): GPS boylam
        alt (float): Yükseklik
        src_id (int): Kaynak ID (örneğin drone)
        dst_id (int): Hedef ID (default: broadcast)
        config_path (str | None): config.json yolunu manuel belirtmek istersen

    Returns:
        bytes: Tam çerçeve
    """
    payload = serialize_telemetry(device_id, lat, lon, alt)
    return build_mesh_frame('T', src_id, dst_id, payload, config_path=config_path)
