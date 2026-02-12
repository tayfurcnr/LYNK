#!/usr/bin/env python3
"""
LYNK NEXUS | Simplified MAVLink Gateway
"""
from __future__ import annotations
import sys
import os
import time
import socket
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QTextEdit, QLabel, QPushButton, QLineEdit, QFrame)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QColor, QFont

import lynk

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(base_dir)

# --- BACKEND ---

class VehicleConnection:
    def __init__(self, vehicle_id, qgc_port, gw_port, lynk_interface, log_callback):
        self.vehicle_id = vehicle_id
        self.qgc_port = qgc_port
        self.gw_port = gw_port
        self.interface = lynk_interface
        self.log = log_callback
        self.running = True
        self.packet_count = 0
        self.last_packet_time = 0
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.sock.bind(("127.0.0.1", self.gw_port))
        except Exception as e:
            self.log(f"Bind Failed: Vehicle {vehicle_id} on {self.gw_port}: {e}")
            self.running = False
            return

        self.sock.settimeout(0.1)
        self.qgc_addr = ("127.0.0.1", self.qgc_port)
        
        self.thread = threading.Thread(target=self._qgc_to_lynk_loop, daemon=True)
        self.thread.start()

    def _qgc_to_lynk_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(8192)
                if data:
                    self.packet_count += 1
                    self.last_packet_time = time.time()
                    lynk.mavlink.send_mavlink(interface=self.interface, payload=data, dst=self.vehicle_id, system_id=255, component_id=1)
            except socket.timeout:
                continue
            except OSError as e:
                if e.errno == 9:
                    break
                if self.running:
                    break
            except:
                break

    def send_to_qgc(self, payload):
        if not self.running:
            return
        try:
            self.sock.sendto(payload, self.qgc_addr)
            self.packet_count += 1
            self.last_packet_time = time.time()
        except:
            pass

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except:
            pass

class GatewayWorker(QThread):
    log_signal = pyqtSignal(str)
    new_vehicle_signal = pyqtSignal(int, int, int)
    stats_signal = pyqtSignal(int, int, float)

    def __init__(self, qgc_start, gw_start):
        super().__init__()
        self.qgc_start = qgc_start
        self.gw_start = gw_start
        self.connections = {}
        self.next_idx = 0
        self.running = True

    def run(self):
        config_path = os.path.join(base_dir, "configs", "node_0", "config.yaml")
        try:
            lynk.config.load_config(config_path)
            self.interface = lynk.create_interface()
            self.interface.start()
            self.log_signal.emit("[OK] LYNK Interface Started")
        except Exception as e:
            self.log_signal.emit(f"[ERROR] LYNK Error: {e}")
            return
            
        try:
            lynk.mavlink.clear_mavlink_callbacks()
        except:
            pass
        lynk.mavlink.on_mavlink_received(self.handle_incoming_mavlink)

        while self.running:
            raw = self.interface.read()
            if raw:
                try:
                    frame = lynk.codec.parse_mesh_frame(raw)
                    lynk.router.route_frame(frame, self.interface)
                except:
                    pass
            
            for vehicle_id, conn in self.connections.items():
                self.stats_signal.emit(vehicle_id, conn.packet_count, conn.last_packet_time)
                
            time.sleep(0.01)
        
        self.interface.stop()

    def handle_incoming_mavlink(self, payload, tunnel_meta, frame_meta):
        if not self.running:
            return
        vehicle_id = frame_meta['src_id']
        if vehicle_id not in self.connections:
            self._create_connection(vehicle_id)
        if vehicle_id in self.connections:
            self.connections[vehicle_id].send_to_qgc(payload)

    def _create_connection(self, vehicle_id):
        idx = self.next_idx
        while True:
            q_port = self.qgc_start + idx
            g_port = self.gw_start + idx
            if self._is_port_free(g_port):
                break
            idx += 1
        
        conn = VehicleConnection(vehicle_id, q_port, g_port, self.interface, lambda m: self.log_signal.emit(m))
        if conn.running:
            self.connections[vehicle_id] = conn
            self.next_idx = idx + 1
            self.new_vehicle_signal.emit(vehicle_id, q_port, g_port)
            self.log_signal.emit(f"[OK] Vehicle {vehicle_id} -> QGC:{q_port} | GW:{g_port}")

    def _is_port_free(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return True
            except:
                return False

    def stop(self):
        self.running = False
        self.wait()
        for c in self.connections.values():
            c.stop()
        self.connections.clear()

# --- UI ---

class NexusWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LYNK NEXUS")
        self.resize(900, 600)
        self.setStyleSheet("background-color:#0a0a0a; color:#e0e0e0; font-family:Consolas;")
        
        self.worker = None

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        header = QLabel("LYNK NEXUS | MAVLink Gateway")
        header.setStyleSheet("font-size:18px; font-weight:bold; color:#00e5ff; padding:10px;")
        layout.addWidget(header)

        # Controls
        ctrl = QFrame()
        ctrl.setStyleSheet("background:#111; border:1px solid #222; border-radius:8px; padding:10px;")
        ctrl_layout = QHBoxLayout(ctrl)
        
        ctrl_layout.addWidget(QLabel("QGC Port:"))
        self.inp_qgc = QLineEdit("14550")
        self.inp_qgc.setFixedWidth(80)
        self.inp_qgc.setStyleSheet("background:#1a1a1a; border:1px solid #333; padding:5px; border-radius:4px;")
        ctrl_layout.addWidget(self.inp_qgc)
        
        ctrl_layout.addWidget(QLabel("GW Port:"))
        self.inp_gw = QLineEdit("15550")
        self.inp_gw.setFixedWidth(80)
        self.inp_gw.setStyleSheet("background:#1a1a1a; border:1px solid #333; padding:5px; border-radius:4px;")
        ctrl_layout.addWidget(self.inp_gw)
        
        self.btn_start = QPushButton("START GATEWAY")
        self.btn_start.setStyleSheet("background:#00e5ff; color:#000; font-weight:bold; padding:8px 16px; border-radius:5px;")
        self.btn_start.clicked.connect(self.start_gateway)
        ctrl_layout.addWidget(self.btn_start)
        
        ctrl_layout.addStretch()
        layout.addWidget(ctrl)

        # Vehicle Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Vehicle ID", "QGC Port", "GW Port", "Packets", "Status"])
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0a0a;
                border: 1px solid #333;
                border-radius: 8px;
                gridline-color: #1a1a1a;
            }
            QTableWidget::item {
                padding: 8px;
                color: #e0e0e0;
                border-bottom: 1px solid #151515;
            }
            QTableWidget::item:alternate {
                background-color: #0f0f0f;
            }
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #00e5ff;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #00e5ff;
                font-weight: bold;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
        """)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 100)
        layout.addWidget(self.table)

        # Console
        console_label = QLabel("System Console:")
        console_label.setStyleSheet("font-weight:bold; color:#888;")
        layout.addWidget(console_label)
        
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("background:#050505; border:1px solid #222; color:#ccc; font-family:Consolas; font-size:11px;")
        self.console.setMaximumHeight(150)
        layout.addWidget(self.console)

    def start_gateway(self):
        if self.worker:
            self.log("Gateway already running!")
            return
            
        try:
            qgc = int(self.inp_qgc.text())
            gw = int(self.inp_gw.text())
        except ValueError:
            self.log("Invalid port numbers!")
            return

        self.worker = GatewayWorker(qgc, gw)
        self.worker.log_signal.connect(self.log)
        self.worker.new_vehicle_signal.connect(self.add_vehicle)
        self.worker.stats_signal.connect(self.update_stats)
        self.worker.start()
        
        self.btn_start.setEnabled(False)
        self.inp_qgc.setEnabled(False)
        self.inp_gw.setEnabled(False)
        self.log(f"Gateway started (QGC:{qgc}+ | GW:{gw}+)")

    def log(self, msg):
        import datetime
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.console.append(f"[{ts}] {msg}")

    def add_vehicle(self, vid, q, g):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        vid_item = QTableWidgetItem(f"UNIT #{vid}")
        vid_item.setForeground(QColor("#00e5ff"))
        self.table.setItem(row, 0, vid_item)
        
        self.table.setItem(row, 1, QTableWidgetItem(str(q)))
        self.table.setItem(row, 2, QTableWidgetItem(str(g)))
        self.table.setItem(row, 3, QTableWidgetItem("0"))
        
        status_item = QTableWidgetItem("WAITING")
        status_item.setForeground(QColor("#888888"))
        self.table.setItem(row, 4, status_item)

    def update_stats(self, vid, count, last_time):
        for row in range(self.table.rowCount()):
            vid_text = self.table.item(row, 0).text()
            if f"#{vid}" in vid_text:
                self.table.item(row, 3).setText(f"{count:,}")
                
                # Update status based on last packet time
                status_item = self.table.item(row, 4)
                if last_time == 0:
                    status_item.setText("WAITING")
                    status_item.setForeground(QColor("#888888"))
                else:
                    elapsed = time.time() - last_time
                    if elapsed < 2:
                        status_item.setText("ONLINE")
                        status_item.setForeground(QColor("#00ff88"))
                    elif elapsed < 10:
                        status_item.setText("STALE")
                        status_item.setForeground(QColor("#ffd000"))
                    else:
                        status_item.setText("OFFLINE")
                        status_item.setForeground(QColor("#ff4444"))
                break

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NexusWindow()
    window.show()
    sys.exit(app.exec_())
