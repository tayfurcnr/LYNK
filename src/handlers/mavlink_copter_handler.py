import time
from pymavlink import mavutil
from src.handlers.mavlink_base_handler import MAVLinkBaseHandler

class CopterHandler(MAVLinkBaseHandler):
    def arm(self):
        print("[CopterHandler] ARM komutu gönderiliyor...")
        self.master.arducopter_arm()

    def set_guided_mode(self):
        self.master.set_mode(4)  # GUIDED
        print("[CopterHandler] GUIDED moda geçildi.")

    def send_takeoff(self,
                    takeoff_alt: float,
                    target_lat: float = 0.0,
                    target_lon: float = 0.0,
                    target_alt: float = None):
        """
        Copter için kalkış komutu gönderir.
        :param takeoff_alt: Kalkış sonrası hedef irtifa
        :param target_lat: Hedef enlem (opsiyonel)
        :param target_lon: Hedef boylam (opsiyonel)
        :param target_alt: Hedef irtifa (opsiyonel, verilmezse takeoff_alt kullanılır)
        """
        self.set_guided_mode()
        time.sleep(1)
        self.arm()
        time.sleep(1)

        # Hedef irtifa verilmemişse takeoff_alt kullan
        final_alt = target_alt if target_alt is not None else takeoff_alt

        self.master.mav.command_long_send(
            1, 0,
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
            0,
            0, 0, 0, 0,
            0, 0, takeoff_alt
        )
        print(f"[CopterHandler] TAKEOFF komutu gönderildi: {takeoff_alt} m → Hedef: ({target_lat}, {target_lon}, {final_alt})")

    def send_goto(self, lat: float, lon: float, alt: float, speed: float = 5.0):
        self.set_guided_mode()
        time.sleep(1)
        lat_scaled = int(lat * 1e7)
        lon_scaled = int(lon * 1e7)
        self.master.mav.command_int_send(
            target_system=self.master.target_system,
            target_component=self.master.target_component,
            frame=mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
            command=mavutil.mavlink.MAV_CMD_DO_REPOSITION,
            current=0,
            autocontinue=0,
            param1=speed,
            param2=0,
            param3=0,
            param4=0,
            x=lat_scaled,
            y=lon_scaled,
            z=alt
        )
        print(f"[CopterHandler] GOTO → LAT={lat}, LON={lon}, ALT={alt}")