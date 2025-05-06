import json
from src.handlers.mavlink.copter_handler import CopterHandler
from src.handlers.mavlink.plane_handler import PlaneHandler

SUPPORTED_VEHICLE_TYPES = {
    "PLANE":    PlaneHandler,
    "COPTER":   CopterHandler
}

def get_vehicle_handler(config_path="config.json"):
    with open(config_path, "r") as f:
        config = json.load(f)

    vehicle_type = config.get("vehicle", {}).get("type", "COPTER").upper() #DEFAULT "COPTER"
    handler_class = SUPPORTED_VEHICLE_TYPES.get(vehicle_type)

    if handler_class is None:
        raise ValueError(f"[Factory] Desteklenmeyen araç tipi: {vehicle_type}")

    print(f"[Factory] {vehicle_type} modu seçildi.")
    return handler_class(config_path)
