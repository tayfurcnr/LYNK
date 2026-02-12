#!/usr/bin/env python3
"""
LYNK NEXUS | Next-Gen MAVLink Gateway Interface
Powered by PyQt6 & LYNK Mesh Network
"""
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

class ModernToggle(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._checked = False

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        self._checked = checked
        self.update()
        self.toggled.emit(checked)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Track
        track_color = C_ACCENT_CYAN if self._checked else QColor("#333")
        p.setBrush(track_color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, 60, 32, 16, 16)
        
        # Knob
        knob_x = 32 if self._checked else 4
        p.setBrush(QColor("#fff"))
        p.drawEllipse(knob_x, 4, 24, 24)

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
        p.setFont(QFont(FONT_MAIN, 14)) # Icon Font
        p.drawText(20, 32, self.icon_char)
        
        p.setFont(QFont(FONT_MAIN, 10, QFont.Weight.Bold)) # Text Font
        p.drawText(50, 30, self.text())

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
            if e.errno == 9: # Bad file descriptor (socket closed)
                pass
            else:
                self.log(f"⚠️ Could not send to QGC for Vehicle {self.vehicle_id}: {e}")
        except Exception as e:
            self.log(f"⚠️ Could not send to QGC for Vehicle {self.vehicle_id}: {e}")

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
            self.log_signal.emit("<span style='color: #00ffcc'><b>LYNK INTERFACE</b></span> <span style='color: #888'>INITIALIZED</span>")
        except Exception as e:
            self.log_signal.emit(f"<span style='color: #ff2a2a'><b>LYNK ERROR</b></span> {e}")
            return
            
        lynk.mavlink.on_mavlink_received(self.handle_incoming_mavlink)

        while self.running:
            # ... (unchanged loop logic) ... 
            # Note: I need to replace the content correctly around existing logic
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
        self.connections.clear() # Clear connections to prevent callbacks

# --- MAIN WINDOW ---

class NexusWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LYNK NEXUS")
        self.resize(1100, 750)
        
        # Frameless Window Setup
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.worker = None
        self.setup_ui()
        self.apply_theme()

    def apply_theme(self):
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {C_BG_DARK.name()}; }}
            QWidget {{ font-family: '{FONT_MAIN}'; color: {C_TEXT_MAIN.name()}; }}
            
            /* Inputs */
            QLineEdit {{ 
                background-color: #111; border: 1px solid #333; border-radius: 4px; 
                padding: 8px; color: {C_ACCENT_CYAN.name()}; font-family: '{FONT_MONO}'; font-weight: bold;
            }}
            QLineEdit:focus {{ border: 1px solid {C_ACCENT_CYAN.name()}; }}
            
            /* Table */
            QTableWidget {{ 
                background-color: {C_BG_PANEL.name()}; border: none; gridline-color: #222;
            }}
            QHeaderView::section {{ 
                background-color: #111; color: #888; padding: 10px; border: none; 
                font-weight: bold; font-size: 11px; letter-spacing: 1px;
            }}
            QTableWidget::item {{ padding: 5px; }}
            
            /* Logs */
            QTextEdit {{ 
                background-color: #080808; color: #00ff00; font-family: '{FONT_MONO}'; border: 1px solid #222;
            }}
            
            /* GroupBox */
            QGroupBox {{ 
                border: 1px solid #333; border-radius: 6px; margin-top: 25px; 
                color: #888; font-weight: bold; font-size: 10px;
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 15px; padding: 0 5px; }}
        """)

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- SIDEBAR ---
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"background-color: {C_BG_PANEL.name()}; border-right: 1px solid #222;")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 30, 0, 20)
        sb_layout.setSpacing(10)
        
        # Logo Area
        logo = QLabel("LYNK NEXUS")
        logo.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {C_ACCENT_CYAN.name()}; letter-spacing: 2px; padding-left: 20px;")
        sb_layout.addWidget(logo)
        
        lbl_sub = QLabel("MESH GATEWAY")
        lbl_sub.setStyleSheet("font-size: 10px; color: #555; font-weight: bold; letter-spacing: 3px; padding-left: 22px;")
        sb_layout.addWidget(lbl_sub)
        
        sb_layout.addSpacing(40)
        
        # Nav Buttons
        self.btn_dash = SidebarButton("DASHBOARD", "❖")
        self.btn_dash.setChecked(True)
        self.btn_dash.clicked.connect(lambda: self.switch_page(0))
        sb_layout.addWidget(self.btn_dash)
        
        self.btn_conf = SidebarButton("CONFIGURATION", "⚙")
        self.btn_conf.clicked.connect(lambda: self.switch_page(1))
        sb_layout.addWidget(self.btn_conf)
        
        sb_layout.addStretch()
        
        # Version
        ver = QLabel("v2.4.0-RC")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet("color: #333; font-size: 10px;")
        sb_layout.addWidget(ver)
        
        main_layout.addWidget(sidebar)

        # --- CONTENT AREA ---
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(20)
        
        # Top Bar
        top_bar = QHBoxLayout()
        
        # Page Title
        self.page_title = QLabel("MISSION DASHBOARD")
        self.page_title.setStyleSheet("font-size: 18px; color: #fff; font-weight: 600;")
        top_bar.addWidget(self.page_title)
        
        top_bar.addStretch()
        
        # Gateway Logic Controls (On Top as requested)
        self.gw_toggle = ModernToggle()
        self.gw_toggle.toggled.connect(self.toggle_gateway)
        top_bar.addWidget(self.gw_toggle)
        
        self.gw_status = StatusBadge()
        top_bar.addWidget(self.gw_status)
        
        content_layout.addLayout(top_bar)
        
        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("background-color: #222;")
        content_layout.addWidget(div)

        # Pages Stack
        self.pages = QStackedWidget()
        
        # [PAGE 0] Dashboard
        p_dash = QWidget()
        l_dash = QVBoxLayout(p_dash)
        l_dash.setContentsMargins(0, 0, 0, 0)
        l_dash.setSpacing(20)
        
        # Vehicle Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["VEHICLE ID", "QGC PORT", "GATEWAY PORT", "TOTAL PACKETS", "STATUS"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setStyleSheet("alternate-background-color: #0c0c0c;")
        l_dash.addWidget(self.table)
        
        # Console
        grp_log = QGroupBox("SYSTEM EVENT LOG")
        l_log = QVBoxLayout(grp_log)
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(180)
        l_log.addWidget(self.console)
        l_dash.addWidget(grp_log)
        
        self.pages.addWidget(p_dash)
        
        # [PAGE 1] Configuration
        p_conf = QWidget()
        l_conf = QVBoxLayout(p_conf)
        l_conf.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        grp_net = QGroupBox("NETWORK SETTINGS")
        l_net = QVBoxLayout(grp_net)
        l_net.setContentsMargins(20, 30, 20, 30)
        l_net.setSpacing(20)
        
        # Port inputs
        row_ports = QHBoxLayout()
        
        box_q = QVBoxLayout()
        box_q.addWidget(QLabel("QGC Listen Port (Start Range)"))
        self.inp_qgc = QLineEdit("14550")
        box_q.addWidget(self.inp_qgc)
        row_ports.addLayout(box_q)
        
        box_g = QVBoxLayout()
        box_g.addWidget(QLabel("Gateway Listen Port (Start Range)"))
        self.inp_gw = QLineEdit("15550")
        box_g.addWidget(self.inp_gw)
        row_ports.addLayout(box_g)
        
        l_net.addLayout(row_ports)
        l_conf.addWidget(grp_net)
        
        self.pages.addWidget(p_conf)
        
        content_layout.addWidget(self.pages)
        main_layout.addWidget(content_area)

        # Internal State
        self.drone_rows = {}

    def switch_page(self, idx):
        self.pages.setCurrentIndex(idx)
        if idx == 0:
            self.page_title.setText("MISSION DASHBOARD")
            self.btn_dash.setChecked(True)
            self.btn_conf.setChecked(False)
        else:
            self.page_title.setText("SYSTEM CONFIGURATION")
            self.btn_dash.setChecked(False)
            self.btn_conf.setChecked(True)

    def toggle_gateway(self, active):
        if active:
            try:
                qgc = int(self.inp_qgc.text())
                gw = int(self.inp_gw.text())
            except ValueError:
                self.log("❌ Invalid Ports")
                self.gw_toggle.setChecked(False)
                return

            self.worker = GatewayWorker(qgc, gw)
            self.worker.log_signal.connect(self.log)
            self.worker.new_vehicle_signal.connect(self.add_vehicle)
            self.worker.stats_signal.connect(self.update_stats)
            self.worker.finished.connect(self.worker_finished)
            self.worker.start()
            
            self.gw_status.update_status(True)
            self.inp_qgc.setEnabled(False)
            self.inp_gw.setEnabled(False)
            self.log(f"<span style='color: #00ffcc'><b>GATEWAY STARTED</b></span> <span style='color: #888'>(QGC: {qgc}+ | GW: {gw}+)</span>")
        else:
            if self.worker:
                self.worker.stop()

    def worker_finished(self):
        self.gw_status.update_status(False)
        self.inp_qgc.setEnabled(True)
        self.inp_gw.setEnabled(True)
        self.log("<span style='color: #ff2a2a'><b>GATEWAY STOPPED</b></span>")
        self.worker = None

    def log(self, msg):
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.console.append(f"<span style='color: #444'>[{timestamp}]</span> {msg}")
        self.console.verticalScrollBar().setValue(self.console.verticalScrollBar().maximum())

    def add_vehicle(self, vid, q, g):
        if vid in self.drone_rows: return
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        params = [
            (f"UNIT #{vid}", C_ACCENT_CYAN, True),
            (str(q), C_TEXT_MAIN, False),
            (str(g), C_TEXT_MAIN, False),
            ("0", C_TEXT_MAIN, False),
            ("SYNC...", C_TEXT_DIM, False)
        ]
        
        for c, (txt, color, bold) in enumerate(params):
            item = QTableWidgetItem(txt)
            item.setForeground(color)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if bold: item.setFont(QFont(FONT_MAIN, 9, QFont.Weight.Bold))
            self.table.setItem(row, c, item)
            
        self.drone_rows[vid] = row

    def update_stats(self, vid, count, last_time):
        if vid not in self.drone_rows: return
        row = self.drone_rows[vid]
        
        self.table.item(row, 3).setText(f"{count:,}")
        
        elapsed = time.time() - last_time
        s_item = self.table.item(row, 4)
        
        if elapsed < 2:
            s_item.setText("ONLINE")
            s_item.setForeground(C_ACCENT_CYAN)
        elif elapsed < 10:
            s_item.setText("STALE")
            s_item.setForeground(QColor("#ffff00"))
        else:
            s_item.setText("LOST")
            s_item.setForeground(C_ACCENT_RED)

    def closeEvent(self, event):
        if self.worker: self.worker.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NexusWindow()
    window.show()
    sys.exit(app.exec())
