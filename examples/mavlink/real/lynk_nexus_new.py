#!/usr/bin/env python3
"""
LYNK NEXUS | Next-Gen MAVLink Gateway Interface
Powered by PyQt6 & LYNK Mesh Network
"""
from __future__ import annotations
import sys
import os
import time
import socket
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QTextEdit, QLabel, QHeaderView, QFrame, QPushButton,
                             QLineEdit, QStackedWidget, QListWidget, 
                             QListWidgetItem, QGraphicsDropShadowEffect, QSizeGrip, QGroupBox,
                             QSplitter, QAbstractItemView, QComboBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer, QSize, QPoint, QRect, QPropertyAnimation
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QBrush, QPen, QColorConstants, QCursor, QAction

import lynk

# Ensure LYNK is importable
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(base_dir)

# --- THEME CONSTANTS ---
C_BG_DARK     = QColor("#050505")
C_BG_PANEL    = QColor("#0f0f0f")
C_ACCENT_CYAN = QColor("#00e5ff")
C_ACCENT_RED  = QColor("#ff2a2a")
C_TEXT_MAIN   = QColor("#e0e0e0")
C_TEXT_DIM    = QColor("#666666")
FONT_MAIN     = "Segoe UI"
FONT_MONO     = "Consolas"

# --- CUSTOM WIDGETS ---

class Card(QFrame):
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            QFrame#Card {
                background-color: #0f0f0f;
                border: 1px solid #1e1e1e;
                border-radius: 14px;
            }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        if title:
            t = QLabel(title)
            t.setStyleSheet("color:#9a9a9a; font-weight:800; letter-spacing:1px; font-size:10px;")
            lay.addWidget(t)
        self.body = QVBoxLayout()
        self.body.setSpacing(10)
        lay.addLayout(self.body)

class StatPill(QFrame):
    def __init__(self, label: str, value: str = "-", parent=None):
        super().__init__(parent)
        self.setObjectName("StatPill")
        self.setStyleSheet("""
            QFrame#StatPill {
                background-color: #0b0b0b;
                border: 1px solid #1f1f1f;
                border-radius: 12px;
            }
            QLabel { color: #e0e0e0; }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(2)

        self.lbl = QLabel(label.upper())
        self.lbl.setStyleSheet("color:#6f6f6f; font-size:9px; font-weight:800; letter-spacing:1px;")
        self.val = QLabel(value)
        self.val.setStyleSheet(f"color:{C_ACCENT_CYAN.name()}; font-size:16px; font-weight:900;")
        lay.addWidget(self.lbl)
        lay.addWidget(self.val)

    def setValue(self, v: str, color: QColor | None = None):
        self.val.setText(v)
        if color:
            self.val.setStyleSheet(f"color:{color.name()}; font-size:16px; font-weight:900;")

class ModernSwitch(QWidget):
    toggled = pyqtSignal(bool)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(56, 30)
        self._checked = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._anim = QPropertyAnimation(self, b"pos")  # placeholder
        self._t = 0.0

    def isChecked(self): return self._checked

    def setChecked(self, checked: bool):
        if self._checked == checked:
            return
        self._checked = checked
        self.update()
        self.toggled.emit(checked)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()

        track = QColor("#2a2a2a")
        if self._checked:
            track = QColor("#00353a")

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(r, 15, 15)

        # glow line
        if self._checked:
            p.setBrush(QColor(0, 229, 255, 60))
            p.drawRoundedRect(QRect(2, 2, r.width()-4, r.height()-4), 13, 13)

        knob_x = 28 if self._checked else 4
        p.setBrush(QColor("#ffffff"))
        p.drawEllipse(knob_x, 4, 22, 22)

class StatusBadge(QLabel):
    def __init__(self, text="OFFLINE", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(100, 28)
        self.setFont(QFont(FONT_MAIN, 9, QFont.Weight.Bold))
        self.update_status(False)

    def update_status(self, active):
        if active:
            self.setText("ONLINE")
            self.setStyleSheet(f"""
                color: {C_ACCENT_CYAN.name()};
                background-color: #002222;
                border: 1px solid {C_ACCENT_CYAN.name()};
                border-radius: 14px;
            """)
        else:
            self.setText("OFFLINE")
            self.setStyleSheet(f"""
                color: {C_ACCENT_RED.name()};
                background-color: #220000;
                border: 1px solid {C_ACCENT_RED.name()};
                border-radius: 14px;
            """)

class SidebarButton(QPushButton):
    def __init__(self, text, icon_char, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setFixedHeight(50)
        self.setFont(QFont(FONT_MAIN, 10, QFont.Weight.Bold))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.icon_char = icon_char
        
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        if self.isChecked():
            p.setBrush(QColor("#1a1a1a"))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRect(self.rect())
            
            # Active Indicator
            p.setBrush(C_ACCENT_CYAN)
            p.drawRect(0, 0, 3, 50)
            
            text_color = C_ACCENT_CYAN
        elif self.underMouse():
            p.setBrush(QColor("#111"))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRect(self.rect())
            text_color = QColor("#fff")
        else:
            text_color = C_TEXT_DIM

        # Icon & Text
        p.setPen(text_color)
        p.setFont(QFont(FONT_MAIN, 14))
        p.drawText(20, 32, self.icon_char)
        
        p.setFont(QFont(FONT_MAIN, 10, QFont.Weight.Bold))
        p.drawText(50, 30, self.text())

class VehicleList(QListWidget):
    vehicle_selected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("VehicleList")
        self.setSpacing(6)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setStyleSheet("""
            QListWidget#VehicleList {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background-color: #0f0f0f;
                border: 1px solid #1e1e1e;
                border-radius: 12px;
                padding: 10px;
                color: #cfcfcf;
            }
            QListWidget::item:selected {
                border: 1px solid #00e5ff;
                background-color: #071a1c;
            }
        """)
        self.itemSelectionChanged.connect(self._emit_selected)

    def _emit_selected(self):
        it = self.currentItem()
        if not it:
            return
        vid = it.data(Qt.ItemDataRole.UserRole)
        if vid is not None:
            self.vehicle_selected.emit(int(vid))

# --- BACKEND LOGIC ---

class VehicleConnection:
    """Manages a local UDP bridge for a specific Vehicle ID."""
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
            self.log(f"<span style='color: #888'>Bind Success: Vehicle {vehicle_id} on UDP {self.gw_port}</span>")
        except Exception as e:
            self.log(f"<span style='color: #ff2a2a'>Bind Failed: Vehicle {vehicle_id} on {self.gw_port}: {e}</span>")
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
                    
                    lynk.mavlink.send_mavlink(
                        interface=self.interface,
                        payload=data,
                        dst=self.vehicle_id,
                        system_id=255, 
                        component_id=1
                    )
            except socket.timeout:
                continue
            except OSError as e:
                if e.errno == 9:  # Bad file descriptor (socket closed during shutdown)
                    break
                if self.running:
                    self.log(f"⚠️ Error in QGC loop for Vehicle {self.vehicle_id}: {e}")
                break
            except Exception as e:
                if self.running:
                    self.log(f"⚠️ Error in QGC loop for Vehicle {self.vehicle_id}: {e}")
                break

    def send_to_qgc(self, payload):
        if not self.running:
            return
        try:
            self.sock.sendto(payload, self.qgc_addr)
            self.packet_count += 1
            self.last_packet_time = time.time()
        except OSError as e:
            if e.errno == 9:
                pass
            else:
                self.log(f"⚠️ Could not send to QGC for Vehicle {self.vehicle_id}: {e}")
        except Exception as e:
            self.log(f"⚠️ Could not send to QGC for Vehicle {self.vehicle_id}: {e}")

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except:
            pass
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
            self.log_signal.emit("<span style='color: #00ffcc'><b>LYNK INTERFACE</b></span> <span style='color: #888'>INITIALIZED</span>")
        except Exception as e:
            self.log_signal.emit(f"<span style='color: #ff2a2a'><b>LYNK ERROR</b></span> {e}")
            return
            
        # Clear old callbacks to prevent conflicts on restart
        try:
            lynk.mavlink.clear_mavlink_callbacks()
        except AttributeError:
            pass  # Older LYNK version without clear function
            
        lynk.mavlink.on_mavlink_received(self.handle_incoming_mavlink)

        while self.running:
            raw = self.interface.read()
            if raw:
                try:
                    frame = lynk.codec.parse_mesh_frame(raw)
                    lynk.router.route_frame(frame, self.interface)
                except Exception:
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
            self.log_signal.emit(f"<span style='color: #00ffcc'><b>NEW VEHICLE DETECTED</b></span> <span style='color: #fff'>ID {vehicle_id}</span> <span style='color: #444'>(QGC:{q_port} | GW:{g_port})</span>")

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
        # Interface is stopped in run() when loop exits

# --- MAIN WINDOW ---

class NexusWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LYNK NEXUS")
        self.resize(1280, 780)

        self.worker = None
        self.drone_rows = {}
        self.vehicle_meta = {}
        self._selected_vid = None
        self._start_time = time.time()

        self.setup_ui()
        self.apply_theme()

        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self._tick_ui)
        self.ui_timer.start(500)

    def apply_theme(self):
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {C_BG_DARK.name()}; }}
            QWidget {{ font-family: '{FONT_MAIN}'; color: {C_TEXT_MAIN.name()}; }}

            QLineEdit {{
                background-color: #0b0b0b;
                border: 1px solid #232323;
                border-radius: 10px;
                padding: 10px 12px;
                color: {C_TEXT_MAIN.name()};
                font-weight: 600;
            }}
            QLineEdit:focus {{ border: 1px solid {C_ACCENT_CYAN.name()}; }}

            QTextEdit {{
                background-color: #070707;
                border: 1px solid #1f1f1f;
                border-radius: 12px;
                padding: 10px;
                font-family: '{FONT_MONO}';
            }}

            QPushButton {{
                background-color: #0f0f0f;
                border: 1px solid #262626;
                border-radius: 12px;
                padding: 10px 12px;
                font-weight: 800;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                border: 1px solid #3a3a3a;
                background-color: #121212;
            }}
            QPushButton:pressed {{
                background-color: #0b0b0b;
            }}

            QComboBox {{
                background-color: #0b0b0b;
                border: 1px solid #232323;
                border-radius: 10px;
                padding: 8px 10px;
            }}
        """)

    def setup_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_lay = QHBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        sidebar = QFrame()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet("background-color:#0b0b0b; border-right:1px solid #1c1c1c;")
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(18, 18, 18, 18)
        sb.setSpacing(14)

        brand = QLabel("LYNK  NEXUS")
        brand.setStyleSheet(f"font-size:22px; font-weight:1000; color:{C_ACCENT_CYAN.name()}; letter-spacing:3px;")
        sb.addWidget(brand)

        sub = QLabel("NEXT-GEN MAVLINK GATEWAY")
        sub.setStyleSheet("color:#5a5a5a; font-weight:800; letter-spacing:2px; font-size:10px;")
        sb.addWidget(sub)
        sb.addSpacing(14)

        self.btn_dash = SidebarButton("MISSION CONTROL", "❖")
        self.btn_dash.setChecked(True)
        self.btn_dash.clicked.connect(lambda: self.switch_page(0))
        sb.addWidget(self.btn_dash)

        self.btn_conf = SidebarButton("SETTINGS", "⚙")
        self.btn_conf.clicked.connect(lambda: self.switch_page(1))
        sb.addWidget(self.btn_conf)

        sb.addStretch()

        self.lbl_ver = QLabel("v2.4.0-RC")
        self.lbl_ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_ver.setStyleSheet("color:#343434; font-size:10px; font-weight:800;")
        sb.addWidget(self.lbl_ver)

        root_lay.addWidget(sidebar)

        content = QWidget()
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(22, 18, 22, 18)
        content_lay.setSpacing(14)

        top = QFrame()
        top.setStyleSheet("background:#0b0b0b; border:1px solid #1c1c1c; border-radius:16px;")
        top_l = QHBoxLayout(top)
        top_l.setContentsMargins(16, 12, 16, 12)
        top_l.setSpacing(12)

        self.page_title = QLabel("MISSION CONTROL")
        self.page_title.setStyleSheet("font-size:16px; font-weight:900; letter-spacing:1px; color:#ffffff;")
        top_l.addWidget(self.page_title)

        top_l.addStretch()

        self.pill_uptime = StatPill("Uptime", "-")
        self.pill_online = StatPill("Online", "0")
        self.pill_packets = StatPill("Packets", "0")
        top_l.addWidget(self.pill_uptime)
        top_l.addWidget(self.pill_online)
        top_l.addWidget(self.pill_packets)

        self.gw_toggle = ModernSwitch()
        self.gw_toggle.toggled.connect(self.toggle_gateway)
        top_l.addWidget(self.gw_toggle)

        self.gw_status = StatusBadge()
        top_l.addWidget(self.gw_status)

        content_lay.addWidget(top)

        self.pages = QStackedWidget()
        content_lay.addWidget(self.pages)
        root_lay.addWidget(content)

        # Page 0: Mission Control
        p0 = QWidget()
        p0_lay = QVBoxLayout(p0)
        p0_lay.setContentsMargins(0, 0, 0, 0)
        p0_lay.setSpacing(14)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

        upper = QSplitter(Qt.Orientation.Horizontal)
        upper.setChildrenCollapsible(False)

        left_card = Card("VEHICLES")
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("Search vehicle id (e.g. 1, 2, 42)…")
        self.inp_search.textChanged.connect(self._filter_vehicle_list)
        left_card.body.addWidget(self.inp_search)

        self.vehicle_list = VehicleList()
        self.vehicle_list.vehicle_selected.connect(self._on_vehicle_selected)
        left_card.body.addWidget(self.vehicle_list)

        upper.addWidget(left_card)

        self.detail_card = Card("VEHICLE DETAILS")
        self.lbl_detail_title = QLabel("No vehicle selected")
        self.lbl_detail_title.setStyleSheet("font-size:18px; font-weight:1000; color:#ffffff;")
        self.detail_card.body.addWidget(self.lbl_detail_title)

        detail_stats_row = QHBoxLayout()
        self.dv_qgc = StatPill("QGC Port", "-")
        self.dv_gw  = StatPill("GW Port", "-")
        self.dv_pkt = StatPill("Total Packets", "-")
        self.dv_st  = StatPill("Status", "-")
        detail_stats_row.addWidget(self.dv_qgc)
        detail_stats_row.addWidget(self.dv_gw)
        detail_stats_row.addWidget(self.dv_pkt)
        detail_stats_row.addWidget(self.dv_st)
        self.detail_card.body.addLayout(detail_stats_row)

        act_row = QHBoxLayout()
        self.btn_copy = QPushButton("COPY QGC PORT")
        self.btn_copy.clicked.connect(self._copy_qgc_port)
        self.btn_ping = QPushButton("PING (LOG)")
        self.btn_ping.clicked.connect(self._ping_selected)
        act_row.addWidget(self.btn_copy)
        act_row.addWidget(self.btn_ping)
        act_row.addStretch()
        self.detail_card.body.addLayout(act_row)

        upper.addWidget(self.detail_card)
        upper.setStretchFactor(0, 1)
        upper.setStretchFactor(1, 2)

        splitter.addWidget(upper)

        logs_card = Card("SYSTEM LOGS")
        tools = QHBoxLayout()
        self.cmb_level = QComboBox()
        self.cmb_level.addItems(["ALL", "INFO", "WARN", "ERROR"])
        self.cmb_level.currentTextChanged.connect(self._apply_log_filter)
        self.inp_log_search = QLineEdit()
        self.inp_log_search.setPlaceholderText("Search in logs…")
        self.inp_log_search.textChanged.connect(self._apply_log_filter)

        self.btn_clear = QPushButton("CLEAR")
        self.btn_clear.clicked.connect(lambda: self.console.clear())

        tools.addWidget(self.cmb_level)
        tools.addWidget(self.inp_log_search, 1)
        tools.addWidget(self.btn_clear)
        logs_card.body.addLayout(tools)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMinimumHeight(220)
        logs_card.body.addWidget(self.console)

        splitter.addWidget(logs_card)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        p0_lay.addWidget(splitter)
        self.pages.addWidget(p0)

        # Page 1: Settings
        p1 = QWidget()
        p1_lay = QVBoxLayout(p1)
        p1_lay.setContentsMargins(0, 0, 0, 0)
        p1_lay.setSpacing(14)

        net = Card("NETWORK SETTINGS")
        row = QHBoxLayout()

        col1 = QVBoxLayout()
        col1.addWidget(QLabel("QGC Listen Port (Start Range)"))
        self.inp_qgc = QLineEdit("14550")
        col1.addWidget(self.inp_qgc)

        col2 = QVBoxLayout()
        col2.addWidget(QLabel("Gateway Listen Port (Start Range)"))
        self.inp_gw = QLineEdit("15550")
        col2.addWidget(self.inp_gw)

        row.addLayout(col1)
        row.addLayout(col2)
        net.body.addLayout(row)

        p1_lay.addWidget(net)
        p1_lay.addStretch()
        self.pages.addWidget(p1)

    def switch_page(self, idx):
        self.pages.setCurrentIndex(idx)
        if idx == 0:
            self.page_title.setText("MISSION CONTROL")
            self.btn_dash.setChecked(True)
            self.btn_conf.setChecked(False)
        else:
            self.page_title.setText("SETTINGS")
            self.btn_dash.setChecked(False)
            self.btn_conf.setChecked(True)

    def toggle_gateway(self, active):
        if active:
            try:
                qgc = int(self.inp_qgc.text())
                gw = int(self.inp_gw.text())
            except ValueError:
                self.log("❌ Invalid Ports", level="ERROR")
                self.gw_toggle.setChecked(False)
                return

            self.worker = GatewayWorker(qgc, gw)
            self.worker.log_signal.connect(lambda m: self.log(m, level="INFO", raw_html=True))
            self.worker.new_vehicle_signal.connect(self.add_vehicle)
            self.worker.stats_signal.connect(self.update_stats)
            self.worker.finished.connect(self.worker_finished)
            self.worker.start()

            self.gw_status.update_status(True)
            self.inp_qgc.setEnabled(False)
            self.inp_gw.setEnabled(False)
            self.log(f"GATEWAY STARTED (QGC:{qgc}+ | GW:{gw}+)", level="INFO")
        else:
            if self.worker:
                self.worker.stop()

    def worker_finished(self):
        self.gw_status.update_status(False)
        self.inp_qgc.setEnabled(True)
        self.inp_gw.setEnabled(True)
        self.log("GATEWAY STOPPED", level="WARN")
        
        # Clear vehicle state for clean restart
        self.vehicle_meta.clear()
        self.vehicle_list.clear()
        self._selected_vid = None
        self.lbl_detail_title.setText("No vehicle selected")
        
        self.worker = None

    def log(self, msg, level="INFO", raw_html=False):
        import datetime
        ts = datetime.datetime.now().strftime("%H:%M:%S")

        tag_color = {
            "INFO": "#00e5ff",
            "WARN": "#ffd000",
            "ERROR": "#ff2a2a",
        }.get(level, "#888")

        if raw_html:
            line = f"<span style='color:#444'>[{ts}]</span> <span style='color:{tag_color}; font-weight:900'>[{level}]</span> {msg}"
        else:
            safe = str(msg).replace("<", "&lt;").replace(">", "&gt;")
            line = f"<span style='color:#444'>[{ts}]</span> <span style='color:{tag_color}; font-weight:900'>[{level}]</span> <span style='color:#cfcfcf'>{safe}</span>"

        self.console.append(line)
        self.console.verticalScrollBar().setValue(self.console.verticalScrollBar().maximum())

    def add_vehicle(self, vid, q, g):
        if vid in self.vehicle_meta:
            return

        self.vehicle_meta[vid] = {"q": q, "g": g, "count": 0, "last": 0.0}

        item = QListWidgetItem(f"UNIT #{vid}")
        item.setData(Qt.ItemDataRole.UserRole, vid)
        self.vehicle_list.addItem(item)

        self.log(f"NEW VEHICLE: ID {vid} (QGC:{q} | GW:{g})", level="INFO")

        if self._selected_vid is None:
            self.vehicle_list.setCurrentItem(item)

        self._refresh_top_pills()

    def update_stats(self, vid, count, last_time):
        if vid not in self.vehicle_meta:
            return
        self.vehicle_meta[vid]["count"] = count
        self.vehicle_meta[vid]["last"] = last_time

        if self._selected_vid == vid:
            self._render_vehicle_detail(vid)

        self._refresh_top_pills()

    def _on_vehicle_selected(self, vid: int):
        self._selected_vid = vid
        self._render_vehicle_detail(vid)

    def _render_vehicle_detail(self, vid: int):
        m = self.vehicle_meta.get(vid)
        if not m:
            self.lbl_detail_title.setText("No vehicle selected")
            return

        self.lbl_detail_title.setText(f"UNIT #{vid}")

        self.dv_qgc.setValue(str(m["q"]), C_TEXT_MAIN)
        self.dv_gw.setValue(str(m["g"]), C_TEXT_MAIN)
        self.dv_pkt.setValue(f"{m['count']:,}", C_ACCENT_CYAN)

        elapsed = time.time() - (m["last"] or 0)
        if m["last"] == 0:
            self.dv_st.setValue("WAITING", QColor("#888"))
        elif elapsed < 2:
            self.dv_st.setValue("ONLINE", C_ACCENT_CYAN)
        elif elapsed < 10:
            self.dv_st.setValue("STALE", QColor("#ffd000"))
        else:
            self.dv_st.setValue("LOST", C_ACCENT_RED)

    def _refresh_top_pills(self):
        total_packets = 0
        online = 0
        now = time.time()
        for vid, m in self.vehicle_meta.items():
            total_packets += int(m.get("count", 0))
            last = m.get("last", 0) or 0
            if last and (now - last) < 2:
                online += 1

        self.pill_online.setValue(str(online), C_ACCENT_CYAN if online else QColor("#888"))
        self.pill_packets.setValue(f"{total_packets:,}", C_ACCENT_CYAN)

    def _tick_ui(self):
        up = int(time.time() - self._start_time)
        h = up // 3600
        m = (up % 3600) // 60
        s = up % 60
        self.pill_uptime.setValue(f"{h:02d}:{m:02d}:{s:02d}", QColor("#cfcfcf"))

        if self._selected_vid is not None:
            self._render_vehicle_detail(self._selected_vid)

    def _filter_vehicle_list(self, text: str):
        text = text.strip().lower()
        for i in range(self.vehicle_list.count()):
            it = self.vehicle_list.item(i)
            vid = str(it.data(Qt.ItemDataRole.UserRole))
            it.setHidden(text not in vid and text not in it.text().lower())

    def _apply_log_filter(self):
        pass

    def _copy_qgc_port(self):
        if self._selected_vid is None:
            return
        q = self.vehicle_meta.get(self._selected_vid, {}).get("q")
        if q is None:
            return
        QApplication.clipboard().setText(str(q))
        self.log(f"Copied QGC port: {q}", level="INFO")

    def _ping_selected(self):
        if self._selected_vid is None:
            return
        self.log(f"PING requested for UNIT #{self._selected_vid} (UI only)", level="INFO")

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NexusWindow()
    window.show()
    sys.exit(app.exec())
