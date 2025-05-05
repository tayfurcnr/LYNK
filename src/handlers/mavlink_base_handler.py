import json
from pymavlink import mavutil

class MAVLinkBaseHandler:
    def __init__(self, config_file: str = 'config.json'):
        with open(config_file, 'r') as f:
            cfg = json.load(f)

        ap_cfg   = cfg['ardupilot_uart']
        port     = ap_cfg['port']
        baudrate = ap_cfg['baudrate']

        self.master = mavutil.mavlink_connection(port, baud=baudrate)
        print(f"[MAVLinkBaseHandler] Bağlantı açıldı: port={port}, baud={baudrate}")

    def send_gimbal_control(self, yaw: float, pitch: float, roll: float):
        self.master.mav.command_long_send(
            1, 0,
            mavutil.mavlink.MAV_CMD_USER_1,
            0,
            yaw, pitch, roll, 0, 0, 0, 0
        )
        print(f"[MAVLinkBaseHandler] GIMBAL → Yaw={yaw}, Pitch={pitch}, Roll={roll}")

    def send_waypoints(self, waypoints: list[tuple[float, float, float]]):
        for idx, (lat, lon, alt) in enumerate(waypoints, start=1):
            self.master.mav.mission_item_send(
                1, 0,
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                0,
                0, 0, 0, 0, 0, 0,
                lat, lon, alt
            )
            print(f"[MAVLinkBaseHandler] WAYPOINT {idx} → LAT={lat}, LON={lon}, ALT={alt}")
        print(f"[MAVLinkBaseHandler] Toplam {len(waypoints)} waypoint gönderildi.")

    def send_generic_command(self, command_id: int, params: tuple):
        self.master.mav.command_long_send(
            1, 0,
            command_id,
            0,
            *params
        )
        print(f"[MAVLinkBaseHandler] GENERIC CMD → ID={command_id}, params={params}")
