from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from typing import Any, Dict, Optional

# Ensure generated protobuf imports like "from msg.telemetry import ..." resolve
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROTO_DIR = os.path.join(BASE_DIR, "src", "shared", "proto")
if PROTO_DIR not in sys.path:
    sys.path.insert(0, PROTO_DIR)


def _emit(event: str, **data: Any) -> None:
    payload = {"event": event, **data}
    print(json.dumps(payload, ensure_ascii=False), flush=True)


class TelemetrySender:
    def __init__(self, interface):
        self.interface = interface
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []

    def start(self) -> None:
        self.stop()
        self._stop.clear()
        self._threads = [
            threading.Thread(target=self._loop_gps, daemon=True),
            threading.Thread(target=self._loop_imu, daemon=True),
            threading.Thread(target=self._loop_heartbeat, daemon=True),
            threading.Thread(target=self._loop_ping, daemon=True),
        ]
        for t in self._threads:
            t.start()

    def stop(self) -> None:
        self._stop.set()
        for t in self._threads:
            t.join(timeout=0.2)
        self._threads.clear()

    def _loop_gps(self) -> None:
        import random
        from src.application.telemetry.tools.dispatcher import send_tlm_gps
        while not self._stop.is_set():
            lat = 37.0 + random.uniform(-0.01, 0.01)
            lon = 35.0 + random.uniform(-0.01, 0.01)
            alt = 100.0 + random.uniform(-5, 5)
            send_tlm_gps(self.interface, lat=lat, lon=lon, alt=alt)
            _emit("telemetry", name="gps", data={"lat": lat, "lon": lon, "alt": alt})
            time.sleep(0.2)  # 5 Hz

    def _loop_imu(self) -> None:
        import random
        from src.application.telemetry.tools.dispatcher import send_tlm_imu
        while not self._stop.is_set():
            roll = random.uniform(-5, 5)
            pitch = random.uniform(-5, 5)
            yaw = random.uniform(0, 360)
            send_tlm_imu(self.interface, roll=roll, pitch=pitch, yaw=yaw)
            _emit("telemetry", name="imu", data={"roll": roll, "pitch": pitch, "yaw": yaw})
            time.sleep(0.5)  # 2 Hz

    def _loop_heartbeat(self) -> None:
        import random
        from src.application.telemetry.tools.dispatcher import send_tlm_heartbeat
        while not self._stop.is_set():
            mode = "STABILIZE"
            health = "OK"
            is_armed = bool(random.getrandbits(1))
            gps_fix = True
            sat_count = random.randint(8, 15)
            send_tlm_heartbeat(
                self.interface,
                mode=mode,
                health=health,
                is_armed=is_armed,
                gps_fix=gps_fix,
                sat_count=sat_count,
            )
            _emit(
                "telemetry",
                name="heartbeat",
                data={
                    "mode": mode,
                    "health": health,
                    "is_armed": is_armed,
                    "gps_fix": gps_fix,
                    "sat_count": sat_count,
                },
            )
            time.sleep(0.2)  # 5 Hz

    def _loop_ping(self) -> None:
        import random
        from src.application.telemetry.tools.dispatcher import send_tlm_ping
        while not self._stop.is_set():
            send_tlm_ping(self.interface)
            _emit("telemetry", name="ping", data={"sequence": random.randint(1, 9999)})
            time.sleep(1.0)  # 1 Hz


class Worker:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.interface = None
        self.sender: Optional[TelemetrySender] = None
        self._stop = threading.Event()

    def start(self) -> None:
        from src.shared.config.manager import load_config
        load_config(self.config_path)

        from src.shared.comm.interface_factory import create_interface
        self.interface = create_interface()
        self.sender = TelemetrySender(self.interface)

        threading.Thread(target=self._rx_loop, daemon=True).start()
        threading.Thread(target=self._stdin_loop, daemon=True).start()

        _emit("status", message=f"Loaded config: {self.config_path}")

    def _stdin_loop(self) -> None:
        while not self._stop.is_set():
            line = sys.stdin.readline()
            if not line:
                self._stop.set()
                break
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except Exception:
                _emit("error", message=f"Invalid JSON: {line[:200]}")
                continue
            self._handle_cmd(msg)

    def _handle_cmd(self, msg: Dict[str, Any]) -> None:
        cmd = msg.get("cmd")
        if cmd == "start_telemetry":
            if self.sender:
                self.sender.start()
                _emit("status", message="Telemetry started")
            return
        if cmd == "stop_telemetry":
            if self.sender:
                self.sender.stop()
                _emit("status", message="Telemetry stopped")
            return
        if cmd == "send_command":
            name = msg.get("name")
            params = msg.get("params", {})
            if not name:
                _emit("error", message="send_command missing name")
                return
            self._send_command(name, params)
            return

    def _send_command(self, name: str, params: Dict[str, Any]) -> None:
        from src.application.command.tools.dispatcher import send_command
        try:
            send_command(self.interface, name, **params)
            _emit("command_sent", name=name, params=params)
        except Exception as exc:
            _emit("error", message=f"send_command failed: {exc}")

    def _rx_loop(self) -> None:
        from src.core.frame_codec import parse_mesh_frame
        from src.core.frame_router import route_frame
        from src.application.ack.serializer.dispatcher import deserialize_ack
        from src.application.command.serializer.dispatcher import deserialize_command
        from src.application.telemetry.serializer.dispatcher import deserialize_telemetry

        while not self._stop.is_set():
            try:
                raw = self.interface.read()
                if not raw:
                    time.sleep(0.001)
                    continue
                try:
                    frame = parse_mesh_frame(raw)
                except Exception:
                    continue

                frame_type = frame.get("frame_type")
                if isinstance(frame_type, int):
                    frame_type = chr(frame_type)

                if frame_type == "A":
                    try:
                        data = deserialize_ack(frame.get("payload", b""))
                        ack_name = None
                        try:
                            from src.application.ack.definitions import ack_definitions
                            defn = ack_definitions.get(data.get("ack_id"))
                            ack_name = defn.name if defn else None
                        except Exception:
                            ack_name = None
                        _emit(
                            "ack_received",
                            src_id=frame.get("src_id"),
                            dst_id=frame.get("dst_id"),
                            ack_id=data.get("ack_id"),
                            ack_name=ack_name,
                            tx_id=data.get("transaction_id"),
                            cmd_id=data.get("cmd_id"),
                        )
                    except Exception:
                        pass

                if frame_type == "C":
                    try:
                        data = deserialize_command(frame.get("payload", b""))
                        _emit(
                            "command_received",
                            src_id=frame.get("src_id"),
                            dst_id=frame.get("dst_id"),
                            command_id=data.get("command_id"),
                            tx_id=data.get("transaction_id"),
                        )
                    except Exception:
                        pass

                if frame_type == "T":
                    try:
                        data = deserialize_telemetry(frame.get("payload", b""))
                        _emit(
                            "telemetry_received",
                            src_id=frame.get("src_id"),
                            name=data.get("tlm_id"),
                            data=data,
                        )
                    except Exception:
                        pass

                route_frame(frame, self.interface)
            except Exception:
                time.sleep(0.01)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to node config")
    args = parser.parse_args()

    worker = Worker(args.config)
    worker.start()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
