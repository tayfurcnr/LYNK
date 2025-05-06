# src/handlers/telemetry/telemetry_handler.py

from src.serializers.telemetry_serializer import deserialize_telemetry
from src.tools.telemetry.telemetry_cache import set_device_data
from src.tools.log.logger import logger

def handle_telemetry(payload: bytes, frame_meta: dict, uart_handler=None):
    """
    Processes 'T' (Telemetry) type frames and updates the telemetry cache.
    """
    try:
        data = deserialize_telemetry(payload)
        src_id = frame_meta.get("src_id")
        device_id = data["device_id"]

        # Prepare telemetry entry
        gps_data = {
            "src_id": src_id,
            "device_id": device_id,
            "gps_lat": data["gps_lat"],
            "gps_lon": data["gps_lon"],
            "gps_alt": data["gps_alt"],
        }

        # Update centralized telemetry cache
        set_device_data(device_id, "gps", gps_data)

        # Optional debug logging
        logger.info(f"[TELEMETRY] Received from SRC: {src_id} -> Device: {device_id}")
        logger.info(f"[TELEMETRY] -> LAT: {data['gps_lat']:.6f}, LON: {data['gps_lon']:.6f}, ALT: {data['gps_alt']:.2f} m")

    except Exception as e:
        logger.error(f"[TELEMETRY] Failed to parse or store telemetry data: {e}")
