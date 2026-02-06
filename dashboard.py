from __future__ import annotations

import os
import sys
import time
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    import yaml
except Exception as exc:
    raise RuntimeError("PyYAML gerekli. 'pip install PyYAML' ile kur.") from exc

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QProcess
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


@dataclass
class NodeConfig:
    path: str
    vehicle_id: int
    team_id: int
    name: str


def load_node_configs(config_dir: str) -> List[NodeConfig]:
    configs: List[NodeConfig] = []
    for name in sorted(os.listdir(config_dir)):
        if not name.startswith("node_"):
            continue
        cfg_path = os.path.join(config_dir, name, "config.yaml")
        if not os.path.exists(cfg_path):
            continue
        with open(cfg_path, "r") as f:
            data = yaml.safe_load(f) or {}
        vehicle = data.get("vehicle", {})
        vid = int(vehicle.get("id", 0))
        tid = int(vehicle.get("team_id", 0))
        configs.append(NodeConfig(path=cfg_path, vehicle_id=vid, team_id=tid, name=name))
    return configs


class NodePanel(QWidget):
    def __init__(self, configs: List[NodeConfig], parent: QWidget | None = None):
        super().__init__(parent)
        self.configs = configs
        self.current_cfg: NodeConfig | None = None
        self._proc: Optional[QProcess] = None
        self._stdout_buf = ""

        self._build_ui()
        self._set_config_by_index(0)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        self.config_select = QComboBox()
        for cfg in self.configs:
            self.config_select.addItem(f"{cfg.name} (id={cfg.vehicle_id}, team={cfg.team_id})")
        self.config_select.currentIndexChanged.connect(self._set_config_by_index)
        header.addWidget(QLabel("Config:"))
        header.addWidget(self.config_select)

        self.status_label = QLabel("Status: stopped")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header.addWidget(self.status_label)
        layout.addLayout(header)

        info = QHBoxLayout()
        self.id_label = QLabel("ID: -")
        self.team_label = QLabel("Team: -")
        info.addWidget(self.id_label)
        info.addWidget(self.team_label)
        info.addStretch(1)
        layout.addLayout(info)

        telemetry_box = QGroupBox("Telemetry")
        t_layout = QGridLayout(telemetry_box)
        self.tlm_labels = {
            "gps": QLabel("-"),
            "imu": QLabel("-"),
            "heartbeat": QLabel("-"),
            "ping": QLabel("-"),
        }
        row = 0
        for key in ["gps", "imu", "heartbeat", "ping"]:
            t_layout.addWidget(QLabel(key.upper()), row, 0)
            t_layout.addWidget(self.tlm_labels[key], row, 1)
            row += 1
        layout.addWidget(telemetry_box)

        cmd_box = QGroupBox("Commands")
        c_layout = QGridLayout(cmd_box)

        self.takeoff_alt = QSpinBox()
        self.takeoff_alt.setRange(1, 500)
        self.takeoff_alt.setValue(30)
        takeoff_btn = QPushButton("Takeoff")
        takeoff_btn.clicked.connect(self._cmd_takeoff)

        land_btn = QPushButton("Land")
        land_btn.clicked.connect(self._cmd_land)

        arm_btn = QPushButton("Arm")
        arm_btn.clicked.connect(self._cmd_arm)

        disarm_btn = QPushButton("Disarm")
        disarm_btn.clicked.connect(self._cmd_disarm)

        self.mode_input = QLineEdit("GUIDED")
        mode_btn = QPushButton("Set Mode")
        mode_btn.clicked.connect(self._cmd_set_mode)

        c_layout.addWidget(QLabel("Takeoff Alt (m)"), 0, 0)
        c_layout.addWidget(self.takeoff_alt, 0, 1)
        c_layout.addWidget(takeoff_btn, 0, 2)
        c_layout.addWidget(land_btn, 0, 3)

        c_layout.addWidget(arm_btn, 1, 0)
        c_layout.addWidget(disarm_btn, 1, 1)
        c_layout.addWidget(QLabel("Mode"), 1, 2)
        c_layout.addWidget(self.mode_input, 1, 3)
        c_layout.addWidget(mode_btn, 1, 4)
        layout.addWidget(cmd_box)

        control = QHBoxLayout()
        start_btn = QPushButton("Start Telemetry")
        stop_btn = QPushButton("Stop Telemetry")
        start_btn.clicked.connect(lambda: self._send({"cmd": "start_telemetry"}))
        stop_btn.clicked.connect(lambda: self._send({"cmd": "stop_telemetry"}))
        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self._clear_log)
        control.addWidget(start_btn)
        control.addWidget(stop_btn)
        control.addWidget(clear_btn)
        control.addStretch(1)
        layout.addLayout(control)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(140)
        self.log.setFontFamily("Monospace")
        layout.addWidget(self.log)

        cmd_log_box = QGroupBox("Command / ACK Log")
        cmd_layout = QVBoxLayout(cmd_log_box)
        self.cmd_log = QTextEdit()
        self.cmd_log.setReadOnly(True)
        self.cmd_log.setMinimumHeight(140)
        self.cmd_log.setFontFamily("Monospace")
        cmd_layout.addWidget(self.cmd_log)
        layout.addWidget(cmd_log_box)

        tlm_log_box = QGroupBox("Telemetry Log")
        tlm_layout = QVBoxLayout(tlm_log_box)
        self.tlm_log = QTextEdit()
        self.tlm_log.setReadOnly(True)
        self.tlm_log.setMinimumHeight(140)
        self.tlm_log.setFontFamily("Monospace")
        tlm_layout.addWidget(self.tlm_log)
        layout.addWidget(tlm_log_box)

    def _set_config_by_index(self, idx: int) -> None:
        if not self.configs:
            return
        idx = max(0, min(idx, len(self.configs) - 1))
        self.current_cfg = self.configs[idx]
        self.id_label.setText(f"ID: {self.current_cfg.vehicle_id}")
        self.team_label.setText(f"Team: {self.current_cfg.team_id}")
        self.status_label.setText("Status: idle")
        self._log(f"Config selected: {self.current_cfg.path}")
        self._restart_worker()

    def _log(self, msg: str) -> None:
        ts = time.strftime("%H:%M:%S")
        self.log.append(f"{ts} | {msg}")

    def _tlm_log(self, msg: str) -> None:
        ts = time.strftime("%H:%M:%S")
        self.tlm_log.append(f"{ts} | {msg}")

    def _cmd_log(self, msg: str) -> None:
        ts = time.strftime("%H:%M:%S")
        self.cmd_log.append(f"{ts} | {msg}")

    def _clear_log(self) -> None:
        self.log.clear()
        self.tlm_log.clear()
        self.cmd_log.clear()

    def _restart_worker(self) -> None:
        self._stop_worker()
        if not self.current_cfg:
            return
        self._proc = QProcess(self)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        worker_path = os.path.join(base_dir, "dashboard_worker.py")
        self._proc.setProgram(sys.executable)
        self._proc.setArguments(["-u", worker_path, "--config", self.current_cfg.path])
        self._proc.setWorkingDirectory(base_dir)
        self._proc.readyReadStandardOutput.connect(self._on_stdout)
        self._proc.readyReadStandardError.connect(self._on_stderr)
        self._proc.started.connect(lambda: self._send({"cmd": "start_telemetry"}))
        self._proc.start()
        self.status_label.setText("Status: starting")

    def _stop_worker(self) -> None:
        if self._proc is not None:
            self._proc.kill()
            self._proc = None
        self.status_label.setText("Status: stopped")

    def _send(self, msg: Dict[str, Any]) -> None:
        if not self._proc:
            self._log("Worker not running")
            return
        data = json.dumps(msg) + "\n"
        self._proc.write(data.encode("utf-8"))

    def _on_stdout(self) -> None:
        if not self._proc:
            return
        chunk = self._proc.readAllStandardOutput().data().decode("utf-8", errors="ignore")
        self._stdout_buf += chunk
        while "\n" in self._stdout_buf:
            line, self._stdout_buf = self._stdout_buf.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            self._handle_event(line)

    def _on_stderr(self) -> None:
        if not self._proc:
            return
        chunk = self._proc.readAllStandardError().data().decode("utf-8", errors="ignore")
        for line in chunk.splitlines():
            self._log(f"[stderr] {line}")

    def _handle_event(self, line: str) -> None:
        try:
            evt = json.loads(line)
        except Exception:
            self._log(f"[raw] {line}")
            return
        etype = evt.get("event")
        if etype == "telemetry":
            name = evt.get("name")
            data = evt.get("data", {})
            if name == "gps":
                self.tlm_labels["gps"].setText(
                    f"{data.get('lat', 0):.6f}, {data.get('lon', 0):.6f}, {data.get('alt', 0):.1f}m"
                )
                self._tlm_log(f"GPS lat={data.get('lat'):.6f} lon={data.get('lon'):.6f} alt={data.get('alt'):.1f}")
            elif name == "imu":
                self.tlm_labels["imu"].setText(
                    f"r={data.get('roll', 0):.1f}, p={data.get('pitch', 0):.1f}, y={data.get('yaw', 0):.1f}"
                )
                self._tlm_log(
                    f"IMU roll={data.get('roll'):.2f} pitch={data.get('pitch'):.2f} yaw={data.get('yaw'):.2f}"
                )
            elif name == "heartbeat":
                armed = "ARMED" if data.get("is_armed") else "DISARMED"
                self.tlm_labels["heartbeat"].setText(f"mode={data.get('mode')}, {armed}")
                self._tlm_log(
                    f"HEARTBEAT mode={data.get('mode')} armed={data.get('is_armed')} gps_fix={data.get('gps_fix')}"
                )
            elif name == "ping":
                self.tlm_labels["ping"].setText(f"seq={data.get('sequence')}")
                self._tlm_log(f"PING seq={data.get('sequence')}")
            return
        if etype == "ack_received":
            ack_name = evt.get("ack_name") or f"ID={evt.get('ack_id')}"
            self._cmd_log(
                f"ACK RX | {ack_name} src={evt.get('src_id')} cmd_id={evt.get('cmd_id')} tx={evt.get('tx_id')}"
            )
            return
        if etype == "command_sent":
            self._cmd_log(f"CMD TX | {evt.get('name')} params={evt.get('params')}")
            return
        if etype == "command_received":
            self._cmd_log(f"CMD RX | src={evt.get('src_id')} id={evt.get('command_id')} tx={evt.get('tx_id')}")
            return
        if etype == "status":
            self.status_label.setText(f"Status: {evt.get('message')}")
            return
        if etype == "error":
            self._log(f"[error] {evt.get('message')}")
            return
        self._log(f"[event] {evt}")

    def _cmd_takeoff(self) -> None:
        alt = self.takeoff_alt.value()
        self._send(
            {
                "cmd": "send_command",
                "name": "FLIGHT_TAKEOFF",
                "params": {"altitude_m": alt, "min_pitch_deg": 0.0},
            }
        )

    def _cmd_land(self) -> None:
        self._send(
            {
                "cmd": "send_command",
                "name": "FLIGHT_LAND",
                "params": {"mode": 0, "has_target": False},
            }
        )

    def _cmd_arm(self) -> None:
        self._send(
            {
                "cmd": "send_command",
                "name": "FLIGHT_ARMING",
                "params": {"arm": True, "force": False},
            }
        )

    def _cmd_disarm(self) -> None:
        self._send(
            {
                "cmd": "send_command",
                "name": "FLIGHT_ARMING",
                "params": {"arm": False, "force": False},
            }
        )

    def _cmd_set_mode(self) -> None:
        mode = self.mode_input.text().strip() or "STABILIZE"
        self._send(
            {
                "cmd": "send_command",
                "name": "FLIGHT_SET_MODE",
                "params": {"mode": mode},
            }
        )


class NodeWindow(QMainWindow):
    def __init__(self, configs: List[NodeConfig]):
        super().__init__()
        self.setWindowTitle("LYNK Node Panel")
        panel = NodePanel(configs, self)
        self.setCentralWidget(panel)
        self.resize(900, 650)


class DashboardWindow(QMainWindow):
    def __init__(self, configs: List[NodeConfig]):
        super().__init__()
        self.configs = configs
        self._windows: List[NodeWindow] = []
        self.setWindowTitle("LYNK Dashboard")
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        root_layout = QVBoxLayout(central)

        toolbar = QHBoxLayout()
        add_btn = QPushButton("+ Panel")
        add_btn.clicked.connect(self._add_panel)
        add_all_btn = QPushButton("Add All")
        add_all_btn.clicked.connect(self._add_all_panels)
        toolbar.addWidget(add_btn)
        toolbar.addWidget(add_all_btn)
        toolbar.addStretch(1)
        root_layout.addLayout(toolbar)

        info = QLabel("Each panel opens in a separate window.")
        root_layout.addWidget(info)
        self.setCentralWidget(central)

    def _add_panel(self) -> None:
        if not self.configs:
            QMessageBox.warning(self, "No configs", "No node_* configs found.")
            return
        win = NodeWindow(self.configs)
        win.show()
        self._windows.append(win)

    def _add_all_panels(self) -> None:
        if not self.configs:
            QMessageBox.warning(self, "No configs", "No node_* configs found.")
            return
        for _ in self.configs:
            self._add_panel()


def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cfg_dir = os.path.join(base_dir, "configs")
    configs = load_node_configs(cfg_dir)

    app = QApplication(sys.argv)
    win = DashboardWindow(configs)
    win.resize(1100, 800)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
