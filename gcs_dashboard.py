from __future__ import annotations

import os
import sys
import time
import threading
from typing import Any, Dict, List

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Ensure generated protobuf package can import nested msg.* modules
_proto_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lynk", "shared", "proto")
if _proto_dir not in sys.path:
    sys.path.insert(0, _proto_dir)

import lynk.shared.comm.interface_factory as iface
from lynk.shared.config import manager as cfg_manager
from lynk.application.command.serializer.dispatcher import _get_cmd_map
from lynk.application.command.tools import dispatcher as cmd_dispatcher
from lynk.application.command.serializer.dispatcher import deserialize_command
from lynk.application.ack.serializer.dispatcher import deserialize_ack
from lynk.application.ack.definitions import ack_definitions
from lynk.application.result.serializer.dispatcher import deserialize_result
from lynk.application.command.tools.dispatcher import get_tx_cmd_name
import lynk.core.frame_codec as codec
from lynk.core.frame_codec import parse_mesh_frame
from lynk.shared.utils.dedupe import DedupeCache


class ReaderThread(QThread):
    event = pyqtSignal(str)

    def __init__(self, interface):
        super().__init__()
        self._iface = interface
        self._stop = threading.Event()
        self._ack_dedupe = DedupeCache(ttl_sec=2.0)

    def stop(self):
        self._stop.set()

    def run(self):
        while not self._stop.is_set():
            try:
                data = self._iface.read()
                if not data:
                    time.sleep(0.01)
                    continue
                frame = parse_mesh_frame(data)
                ftype = frame.get("frame_type")
                if isinstance(ftype, int):
                    ftype = chr(ftype)
                src_id = frame.get("src_id")
                dst_id = frame.get("dst_id")

                if ftype == "A":
                    ack = deserialize_ack(frame.get("payload", b""))
                    ack_id = ack.get("ack_id")
                    ack_name = ack_definitions.get(ack_id).name if ack_id in ack_definitions else f"ACK_{ack_id}"
                    tx_id = ack.get("transaction_id")
                    tx_name = get_tx_cmd_name(tx_id) if tx_id else None
                    key = (tx_id, src_id, ack_id)
                    if not self._ack_dedupe.allow(key):
                        continue
                    label = f"[ACK] {ack_name}"
                    if tx_name:
                        label += f" FOR {tx_name}"
                    self.event.emit(f"{label} | SRC:{src_id} -> DST:{dst_id} | TX:{tx_id}")
                elif ftype == "C":
                    cmd = deserialize_command(frame.get("payload", b""))
                    cmd_id = cmd.get("command_id")
                    tx_id = cmd.get("transaction_id")
                    tx_name = get_tx_cmd_name(tx_id) or f"CMD_ID:{cmd_id}"
                    self.event.emit(f"[CMD] RECV {tx_name} | SRC:{src_id} -> DST:{dst_id} | TX:{tx_id}")
                elif ftype == "R":
                    res = deserialize_result(frame.get("payload", b""))
                    tx_id = res.get("transaction_id")
                    status = res.get("status")
                    tx_name = get_tx_cmd_name(tx_id) if tx_id else None
                    label = f"[RESULT] {status}"
                    if tx_name:
                        label += f" FOR {tx_name}"
                    self.event.emit(f"{label} | SRC:{src_id} -> DST:{dst_id} | TX:{tx_id}")
            except Exception as exc:
                self.event.emit(f"[READER] {exc}")
                time.sleep(0.05)


class GcsDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LYNK GCS Dashboard")
        self.resize(1200, 720)

        self.interface = None
        self.reader = None
        self.commands = self._load_commands()
        self.last_params: Dict[str, Dict[str, Any]] = {}

        self._init_ui()
        self._load_config_and_start()

    def closeEvent(self, event):
        try:
            if self.reader:
                self.reader.stop()
                self.reader.wait(1000)
            if self.interface:
                self.interface.stop()
        finally:
            event.accept()

    def _load_commands(self) -> List[Dict[str, Any]]:
        cmd_map = _get_cmd_map()
        out = []
        for cmd_id, (field_name, params) in cmd_map.items():
            out.append({
                "id": cmd_id,
                "name": field_name.upper(),
                "params": params,
            })
        out.sort(key=lambda x: x["name"])
        return out

    def _init_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)

        # Left panel: command list
        left = QVBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search command...")
        self.search.textChanged.connect(self._render_commands)
        self.list = QListWidget()
        self.list.itemClicked.connect(self._select_command)
        left.addWidget(self.search)
        left.addWidget(self.list)

        # Middle panel: send form
        middle = QVBoxLayout()
        self.selected_label = QLabel("Selected: none")
        middle.addWidget(self.selected_label)

        send_box = QGroupBox("Quick Send")
        form = QFormLayout(send_box)
        self.dst = QSpinBox()
        self.dst.setMaximum(255)
        self.dst.setValue(255)
        self.dst_team = QLineEdit()
        self.ack_timeout = QLineEdit("2.0")
        self.max_retries = QSpinBox()
        self.max_retries.setMaximum(10)
        self.retry_interval = QLineEdit("2.0")
        self.wait_ack = QComboBox()
        self.wait_ack.addItems(["False", "True"])

        form.addRow("DST", self.dst)
        form.addRow("TEAM_ID", self.dst_team)
        form.addRow("ACK Timeout", self.ack_timeout)
        form.addRow("Max Retries", self.max_retries)
        form.addRow("Retry Interval", self.retry_interval)
        form.addRow("Wait for ACK", self.wait_ack)

        self.param_form = QGroupBox("Parameters")
        self.param_layout = QFormLayout(self.param_form)

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self._send_command)

        middle.addWidget(send_box)
        middle.addWidget(self.param_form)
        middle.addWidget(self.send_btn)

        # Right panel: activity
        right = QVBoxLayout()
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        right.addWidget(QLabel("Activity"))
        right.addWidget(self.log)

        layout.addLayout(left, 2)
        layout.addLayout(middle, 2)
        layout.addLayout(right, 3)

        self._render_commands()

    def _render_commands(self):
        self.list.clear()
        q = self.search.text().strip().lower()
        for cmd in self.commands:
            if q and q not in cmd["name"].lower():
                continue
            item = QListWidgetItem(f"{cmd['name']} (ID {cmd['id']})")
            item.setData(Qt.UserRole, cmd)
            self.list.addItem(item)

    def _select_command(self, item: QListWidgetItem):
        cmd = item.data(Qt.UserRole)
        self.selected = cmd
        self.selected_label.setText(f"Selected: {cmd['name']}")

        # Build param inputs
        for i in reversed(range(self.param_layout.count())):
            w = self.param_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        saved = self.last_params.get(cmd["name"], {})
        self.param_inputs = {}
        for p in cmd["params"]:
            le = QLineEdit(str(saved.get(p, "")))
            self.param_layout.addRow(p, le)
            self.param_inputs[p] = le

    def _send_command(self):
        if not hasattr(self, "selected") or not self.selected:
            QMessageBox.warning(self, "No command", "Select a command first.")
            return

        params = {}
        for k, w in self.param_inputs.items():
            v = w.text().strip()
            if v == "":
                continue
            # simple type casting
            if v.lower() == "true":
                params[k] = True
            elif v.lower() == "false":
                params[k] = False
            else:
                try:
                    if "." in v:
                        params[k] = float(v)
                    else:
                        params[k] = int(v)
                except Exception:
                    params[k] = v

        self.last_params[self.selected["name"]] = params.copy()

        dst_team = self.dst_team.text().strip()
        dst_team_id = None
        if dst_team:
            try:
                dst_team_id = int(dst_team)
            except ValueError:
                QMessageBox.warning(self, "Invalid input", "Team ID must be a valid integer.")
                return

        try:
            ack_timeout_val = float(self.ack_timeout.text() or 2.0)
            retry_interval_val = float(self.retry_interval.text() or 2.0)
        except ValueError:
            QMessageBox.warning(self, "Invalid input", "Timeout and interval must be valid numbers.")
            return

        try:
            cmd_dispatcher.send_command(
                self.interface,
                self.selected["name"],
                dst=self.dst.value(),
                dst_team_id=dst_team_id,
                wait_for_ack=self.wait_ack.currentText() == "True",
                ack_timeout=ack_timeout_val,
                max_retries=int(self.max_retries.value()),
                retry_interval=retry_interval_val,
                src=codec.load_device_id(),
                **params,
            )
            self._append_log(f"[SEND] {self.selected['name']} -> DST {self.dst.value()}")
        except Exception as exc:
            QMessageBox.critical(self, "Send failed", str(exc))

    def _append_log(self, line: str):
        self.log.append(line)

    def _load_config_and_start(self):
        cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs", "node_0", "config.yaml")
        if not os.path.exists(cfg_path):
            QMessageBox.critical(self, "Config missing", cfg_path)
            return
        try:
            cfg_manager.load_config(cfg_path)
        except Exception as e:
            QMessageBox.critical(self, "Config load failed", str(e))
            return
        self.interface = iface.create_interface()
        self.interface.start()
        self.reader = ReaderThread(self.interface)
        self.reader.event.connect(self._append_log)
        self.reader.start()


def main():
    app = QApplication(sys.argv)
    win = GcsDashboard()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
