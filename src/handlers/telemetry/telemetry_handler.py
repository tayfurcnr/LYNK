from src.serializers.telemetry_serializer import deserialize_telemetry
from src.tools.telemetry.telemetry_cache import set_device_data
from src.tools.log.logger import logger

# 📌 Telemetry Type Map
TELEMETRY_TYPE_MAP = {
    0x01: "gps",
    0x02: "imu",
    0x03: "battery"
}

# 🚀 Handle GPS data
def handle_gps_data(data: dict, src_id: int, data_type: str):
    gps_data = {
        "gps_lat": data["gps_lat"],
        "gps_lon": data["gps_lon"],
        "gps_alt": data["gps_alt"],
    }
    set_device_data(src_id, data_type, gps_data)
    logger.info(f"[TELEMETRY] Received GPS data from SRC: {src_id}")
    logger.debug(
        f"[TELEMETRY] -> LAT: {data['gps_lat']:.6f}, "
        f"LON: {data['gps_lon']:.6f}, ALT: {data['gps_alt']:.2f}"
    )

# 🚀 Handle IMU data
def handle_imu_data(data: dict, src_id: int, data_type: str):
    imu_data = {
        "imu_roll": data["imu_roll"],
        "imu_pitch": data["imu_pitch"],
        "imu_yaw": data["imu_yaw"],
    }
    set_device_data(src_id, data_type, imu_data)
    logger.info(f"[TELEMETRY] Received IMU data from SRC: {src_id}")
    logger.debug(
        f"[TELEMETRY] -> Roll: {data['imu_roll']:.2f}, "
        f"Pitch: {data['imu_pitch']:.2f}, Yaw: {data['imu_yaw']:.2f}"
    )

def handle_battery_data(data: dict, src_id: int, data_type: str):
    battery_data = {
        "voltage": data["voltage"],
        "current": data["current"],
        "level": data["level"]
    }
    set_device_data(src_id, data_type, battery_data)
    logger.info(f"[TELEMETRY] Received BATTERY data from SRC: {src_id}")
    logger.debug(
        f"[TELEMETRY] -> Voltage: {data['voltage']:.2f}, "
        f"Current: {data['current']:.2f}, Level: {data['level']:.2f}"
    )

# 🧠 Central Telemetry Handler
def handle_telemetry(payload: bytes, frame_meta: dict, interface=None):
    """
    Processes 'T' (Telemetry) type frames and updates the telemetry cache.
    """
    try:
        # 1️⃣ Parse frame metadata
        src_id = frame_meta.get("src_id")

        # 2️⃣ Deserialize telemetry payload
        data = deserialize_telemetry(payload)
        tlm_id = data.get("tlm_id")

        if not isinstance(tlm_id, int):
            raise ValueError(f"Invalid tlm_id: {tlm_id}")

        # 3️⃣ Resolve telemetry data type
        data_type = TELEMETRY_TYPE_MAP.get(tlm_id, f"unknown_{tlm_id}")

        # 4️⃣ Dispatch by telemetry type
        if data_type == "gps":
            handle_gps_data(data, src_id, data_type)
        elif data_type == "imu":
            handle_imu_data(data, src_id, data_type)
        elif tlm_id == 0x03:
            handle_battery_data(data, src_id, data_type)
        else:
            logger.warning(f"[TELEMETRY] Unknown telemetry type (tlm_id: {tlm_id}) from SRC: {src_id}")

    except ValueError as ve:
        logger.error(f"[TELEMETRY] Invalid telemetry format: {ve}")
        logger.debug(f"[TELEMETRY] Error details: {ve}", exc_info=True)

    except Exception as e:
        logger.error(f"[TELEMETRY] Failed to parse or store telemetry data: {e}")
        logger.debug(f"[TELEMETRY] Full exception: {e}", exc_info=True)
