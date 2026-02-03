import sys
import os
import signal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTextEdit, QLabel, QGridLayout, QScrollArea, QFrame,
    QLineEdit, QCheckBox, QTabWidget, QStackedWidget
)
from PyQt5.QtCore import QProcess, Qt, pyqtSignal, QObject, QTimer, QPointF, QRectF
from PyQt5.QtGui import QFont, QColor, QTextCursor, QPalette, QLinearGradient, QBrush, QPainter, QPen, QRadialGradient
import re
import time
import math

class NodeWorker(QObject):
    log_signal = pyqtSignal(str)
    traffic_signal = pyqtSignal(int, int, str) # src, dst, type
    finished_signal = pyqtSignal(int)

    def __init__(self, config_path, node_id):
        super().__init__()
        self.config_path = config_path
        self.node_id = node_id
        self.process = None
        self.log_buffer = [] # Buffer for performance

    def start(self):
        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.finished.connect(self.handle_finished)
        
        # Determine the root directory (assuming current file is in tests/)
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        main_script = os.path.join(root_dir, "main.py")
        
        self.process.setWorkingDirectory(root_dir)
        self.process.start("python3", [main_script, "--config", self.config_path])

    def handle_output(self):
        data = self.process.readAllStandardOutput().data().decode(errors='ignore')
        self.log_buffer.append(data)
        # Parse traffic immediately for mesh reactivity
        self.parse_traffic(data)

    def flush_logs(self):
        if self.log_buffer:
            all_text = "".join(self.log_buffer)
            self.log_signal.emit(all_text)
            self.log_buffer = []

    def parse_traffic(self, text):
        # 1. Sent Traffic (Telemetry/Ping/Commands)
        # Patterns: [SEND] GPS -> ... -> DST: 255, [SEND] HEARTBEAT -> DST: 1
        for match in re.finditer(r"\[SEND\] .*? -> DST: (\d+)", text):
            dst = int(match.group(1))
            self.traffic_signal.emit(int(self.node_id), dst, "DATA_SENT")

        # 2. Received Telemetry 
        # Patterns: [RECV TELEMETRY] SRC 1, [RECV TELEMETRY] From SRC 1
        for match in re.finditer(r"\[RECV TELEMETRY\] (?:From )?SRC (\d+)", text):
            src = int(match.group(1))
            self.traffic_signal.emit(src, int(self.node_id), "TLM_RECV")

        # 3. Received Commands
        # Patterns: [RECV COMMAND] SRC 1, [RECV CMD] SRC: 1, [RECV COMMAND] From SRC 5
        for match in re.finditer(r"\[RECV (?:COMMAND|CMD)\] (?:From )?SRC(?::)? (\d+)", text):
            src = int(match.group(1))
            self.traffic_signal.emit(src, int(self.node_id), "CMD_RECV")

        # 4. Team Update Detection
        for match in re.finditer(r"Team ID updated to: (\d+)", text):
            new_team = int(match.group(1))
            self.traffic_signal.emit(int(self.node_id), new_team, "TEAM_UPDATE")

    def handle_finished(self, exit_code):
        self.finished_signal.emit(exit_code)

    def stop(self):
        if self.process and self.process.state() == QProcess.Running:
            self.process.terminate()
            if not self.process.waitForFinished(2000):
                self.process.kill()

    def send_command(self, cmd_char):
        if self.process and self.process.state() == QProcess.Running:
            self.process.write(cmd_char.encode() + b"\n")

class MeshTopologyWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.nodes = {} # node_id: {pos: QPointF, team: int, last_seen: float}
        self.traffic = [] # list of {src, dst, time, type}
        self.total_packets = 0
        self.dragged_node = None
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50) # 20 FPS is plenty for monitoring
        
        self.setMinimumHeight(600)
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        for nid, data in self.nodes.items():
            if (event.pos() - data["pos"]).manhattanLength() < 20:
                self.dragged_node = nid
                break

    def mouseMoveEvent(self, event):
        if self.dragged_node is not None:
            self.nodes[self.dragged_node]["pos"] = QPointF(event.pos())
            self.update()

    def mouseReleaseEvent(self, event):
        self.dragged_node = None

    def update_node(self, node_id, team_id):
        if node_id not in self.nodes:
            # Random initial position based on team
            angle = (node_id * 137.5) % 360
            dist = 150 if team_id != 0 else 50
            if team_id == 1: angle = 0 + (node_id * 30)
            elif team_id == 2: angle = 180 + (node_id * 30)
            
            x = 400 + dist * math.cos(math.radians(angle))
            y = 300 + dist * math.sin(math.radians(angle))
            self.nodes[node_id] = {"pos": QPointF(x, y), "team": team_id, "last_seen": time.time()}
        else:
            self.nodes[node_id]["team"] = team_id
            self.nodes[node_id]["last_seen"] = time.time()

    def add_traffic(self, src, dst, t_type):
        self.total_packets += 1
        self.traffic.append({
            "src": src, 
            "dst": dst, 
            "time": time.time(), 
            "type": t_type
        })
        # Limit traffic history to prevent memory leak and slow iteration
        if len(self.traffic) > 100:
            self.traffic = self.traffic[-100:]
        # Keep only recent traffic
        if len(self.traffic) > 50:
            self.traffic.pop(0)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor("#0d0d0f"))
        
        w, h = self.width(), self.height()
        
        # Draw Grid Lines
        grid_pen = QPen(QColor(255, 255, 255, 15)) # Very subtle white
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        grid_size = 40
        for x in range(0, w, grid_size):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, grid_size):
            painter.drawLine(0, y, w, y)

        # Draw connections
        now = time.time()
        for t in self.traffic[:]:
            age = now - t["time"]
            if age > 1.5: # Reduced persistence for performance
                self.traffic.remove(t)
                continue
            
            if t["src"] in self.nodes and (t["dst"] in self.nodes or t["dst"] == 255):
                p1 = self.nodes[t["src"]]["pos"]
                
                # If broadcast, draw to all or center
                if t["dst"] == 255 or t["dst"] == 0:
                    # Draw a pulse from src
                    opacity = int(120 * (1 - age/1.5))
                    pen = QPen(QColor(79, 195, 247, opacity))
                    pen.setWidth(1) # Thinner for performance
                    painter.setPen(pen)
                    r = 5 + age * 30 # Simple, tight pulse
                    painter.drawEllipse(p1, r, r)
                elif t["dst"] in self.nodes:
                    p2 = self.nodes[t["dst"]]["pos"]
                    # Increased transparency for telemetry (lower base opacity)
                    base_opacity = 150 if "CMD" in t["type"] else 80
                    opacity = int(base_opacity * (1 - age/1.5))
                    color = QColor(255, 183, 77, opacity) if "CMD" in t["type"] else QColor(129, 199, 132, opacity)
                    pen = QPen(color)
                    pen.setWidth(1)
                    painter.setPen(pen)
                    painter.drawLine(p1, p2)
                    
                    if age < 0.8: # Shorter lived dot
                        progress = age / 0.8
                        dot_pos = p1 + (p2 - p1) * progress
                        painter.setBrush(color)
                        painter.drawEllipse(dot_pos, 3, 3)

        # Draw nodes
        for nid, data in self.nodes.items():
            pos = data["pos"]
            team = data["team"]
            
            # Team colors
            color = QColor("#4fc3f7") if team == 1 else (QColor("#81c784") if team == 2 else QColor("#9e9e9e"))
            
            # Draw Drone Shape (X-Frame)
            pen = QPen(color)
            pen.setWidth(2)
            painter.setPen(pen)
            
            s = 10 # Half-size of the drone arms
            # Arms
            painter.drawLine(int(pos.x() - s), int(pos.y() - s), int(pos.x() + s), int(pos.y() + s))
            painter.drawLine(int(pos.x() + s), int(pos.y() - s), int(pos.x() - s), int(pos.y() + s))
            
            # Rotors (Small circles at ends of arms)
            painter.setBrush(QColor(40, 40, 40))
            for dx, dy in [(-s, -s), (s, -s), (-s, s), (s, s)]:
                painter.drawEllipse(QPointF(pos.x() + dx, pos.y() + dy), 4, 4)

            # Core / Center Node
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(pos, 5, 5)
            
            # Label - Centered below drone icon
            painter.setPen(QColor("#ffffff"))
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            id_rect = QRectF(pos.x() - 40, pos.y() + 12, 80, 12)
            painter.drawText(id_rect, Qt.AlignCenter, f"ID: {nid}")
            
            painter.setFont(QFont("Arial", 7))
            team_txt = "SOLO" if team == 0 else f"TEAM {team}"
            team_rect = QRectF(pos.x() - 40, pos.y() + 24, 80, 12)
            painter.drawText(team_rect, Qt.AlignCenter, team_txt)

class NodeCard(QFrame):
    traffic_signal = pyqtSignal(int, int, str)
    def __init__(self, node_id, config_path):
        super().__init__()
        self.node_id = node_id
        self.config_path = config_path
        self.worker = NodeWorker(config_path, node_id)
        self.worker.traffic_signal.connect(self.traffic_signal.emit)
        self.worker.finished_signal.connect(self.on_process_finished)
        self.init_ui()

    def init_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setLineWidth(1)
        self.setStyleSheet("""
            NodeCard {
                background-color: #1a1a1c; 
                color: #e0e0e0; 
                border-radius: 15px; 
                border: 1px solid #333333;
            }
            NodeCard:hover {
                border: 1px solid #4fc3f7;
            }
            QPushButton {
                background-color: #2b2b2b;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                padding: 6px;
                font-size: 10px;
                font-weight: bold;
                color: #cccccc;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border: 1px solid #555555;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #4fc3f7;
                color: #000000;
            }
            QLineEdit {
                background-color: #0d0d0d;
                border: 1px solid #333333;
                border-radius: 6px;
                color: #4fc3f7;
                padding: 4px;
                font-family: 'Courier New';
                font-weight: bold;
            }
            QTabWidget::pane {
                border: 1px solid #2b2b2b;
                background-color: #0d0d0d;
                border-radius: 8px;
                margin-top: -1px;
            }
            QTabBar::tab {
                background-color: #1a1a1c;
                color: #666666;
                padding: 6px 15px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 9px;
                font-weight: bold;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #0d0d0d;
                color: #4fc3f7;
                border: 1px solid #2b2b2b;
                border-bottom: none;
            }
            QCheckBox {
                spacing: 5px;
                color: #888888;
                font-size: 9px;
            }
            QCheckBox::indicator {
                width: 12px;
                height: 12px;
                border-radius: 3px;
                background-color: #2b2b2b;
                border: 1px solid #3d3d3d;
            }
            QCheckBox::indicator:checked {
                background-color: #4fc3f7;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel(f"NODE {self.node_id}")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(title)

        # Get Team ID from config (simplified parsing)
        team_id = "?"
        try:
            import yaml
            with open(self.config_path, 'r') as f:
                cfg = yaml.safe_load(f)
                team_id = cfg.get("vehicle", {}).get("team_id", "?")
        except: pass
        
        team_label = QLabel(f"{f'TEAM {team_id}' if team_id != 0 else 'SOLO'}")
        team_color = "#4fc3f7" if team_id == 1 else ("#81c784" if team_id == 2 else "#9e9e9e")
        team_label.setStyleSheet(f"color: {team_color}; font-weight: bold; font-size: 10px;")
        header_layout.addWidget(team_label)
        
        header_layout.addStretch()

        self.scroll_lock = QCheckBox("Auto-Scroll")
        self.scroll_lock.setChecked(True)
        self.scroll_lock.setStyleSheet("font-size: 9px;")
        header_layout.addWidget(self.scroll_lock)

        self.status_label = QLabel("STOPPED")
        self.status_label.setStyleSheet("color: #ff5555; font-weight: bold; background-color: rgba(255, 85, 85, 0.1); padding: 2px 8px; border-radius: 10px;")
        header_layout.addWidget(self.status_label)

        self.toggle_tabs_btn = QPushButton("LOGS")
        self.toggle_tabs_btn.setCheckable(True)
        self.toggle_tabs_btn.setChecked(True)
        self.toggle_tabs_btn.setStyleSheet("max-width: 50px; font-size: 8px; background: #333333;")
        self.toggle_tabs_btn.clicked.connect(self.toggle_tabs)
        header_layout.addWidget(self.toggle_tabs_btn)

        self.toggle_ctrls_btn = QPushButton("CTRLS")
        self.toggle_ctrls_btn.setCheckable(True)
        self.toggle_ctrls_btn.setChecked(True)
        self.toggle_ctrls_btn.setStyleSheet("max-width: 50px; font-size: 8px; background: #333333;")
        self.toggle_ctrls_btn.clicked.connect(self.toggle_controls)
        header_layout.addWidget(self.toggle_ctrls_btn)
        
        layout.addLayout(header_layout)
        layout.addSpacing(5)
        
        # 1. Log Area - Tabbed
        self.tabs = QTabWidget()
        self.log_all = self._create_log_area()
        self.log_tlm = self._create_log_area()
        self.log_cmd = self._create_log_area()
        self.log_sys = self._create_log_area()

        self.tabs.addTab(self.log_all, "ALL")
        self.tabs.addTab(self.log_tlm, "TLM")
        self.tabs.addTab(self.log_cmd, "CMD")
        self.tabs.addTab(self.log_sys, "SYS")
        
        layout.addWidget(self.tabs)
        
        # 2. Controls Area (Quick Actions) - Grouped in a toggleable container
        self.ctrl_container = QWidget()
        ctrl_layout_main = QVBoxLayout(self.ctrl_container)
        ctrl_layout_main.setContentsMargins(0, 5, 0, 5)
        ctrl_layout_main.setSpacing(5)

        # Basic Controls
        basic_row = QHBoxLayout()
        self.start_btn = QPushButton("START")
        self.start_btn.setMinimumHeight(35)
        self.start_btn.setStyleSheet("background-color: #44aa44; border: none; padding: 5px; font-size: 11px;")
        self.start_btn.clicked.connect(self.toggle_process)
        basic_row.addWidget(self.start_btn)
        
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Key (B)")
        self.cmd_input.setMaxLength(1)
        self.cmd_input.setFixedWidth(80)
        self.cmd_input.returnPressed.connect(self.send_custom_cmd)
        basic_row.addWidget(self.cmd_input)
        ctrl_layout_main.addLayout(basic_row)
        
        # Quick Actions Layouts
        for grp_cmds in [
            [("ARM", "X", "#ff9800"), ("DISARM", "Y", "#795548"), ("GUIDED", "C", None)],
            [("TAKEOFF", "T", "#2196f3"), ("LAND", "L", "#607d8b"), ("PING", "B", None)],
            [("GLOBAL PING", "V", "#9c27b0"), ("TGT TEAM 2", "Z", "#e91e63")]
        ]:
            row = QHBoxLayout()
            for label, cmd, color in grp_cmds:
                btn = QPushButton(f"{label} ({cmd})")
                if color: btn.setStyleSheet(f"background-color: {color}; color: white;")
                btn.clicked.connect(lambda _, c=cmd: self.worker.send_command(c))
                row.addWidget(btn)
            ctrl_layout_main.addLayout(row)

        # Telemetry Toggles
        tlm_row = QHBoxLayout()
        tlm_row.addWidget(QLabel("Tlm:"))
        self.toggles = {}
        for name, key in [("GPS", "7"), ("IMU", "8"), ("BAT", "9"), ("HB", "0"), ("BARO", "-"), ("PING", "=")]:
            cb = QCheckBox(name)
            cb.setChecked(True)
            cb.setStyleSheet("QCheckBox { font-size: 9px; }")
            cb.toggled.connect(lambda _, k=key: self.send_toggle_if_running(k))
            tlm_row.addWidget(cb)
            self.toggles[name] = cb
        ctrl_layout_main.addLayout(tlm_row)

        layout.addWidget(self.ctrl_container)
        
        self.setLayout(layout)
        
        # Connect Worker
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished_signal.connect(self.on_process_finished)

    def _create_log_area(self):
        area = QTextEdit()
        area.setReadOnly(True)
        area.setUndoRedoEnabled(False)
        area.document().setMaximumBlockCount(1000)
        area.setFont(QFont("Courier New", 9))
        area.setStyleSheet("""
            QTextEdit {
                background-color: #0d0d0d; 
                color: #dcdcdc; 
                border: none;
                selection-background-color: #4fc3f7;
                selection-color: #000000;
            }
        """)
        # Custom ScrollBar Styling
        area.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: #1a1a1c;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #3d3d3d;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4fc3f7;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        return area

    def send_toggle_if_running(self, key):
        if self.worker.process and self.worker.process.state() == QProcess.Running:
            self.worker.send_command(key)

    def toggle_process(self):
        if self.start_btn.text() == "START":
            self.log_all.clear()
            self.log_tlm.clear()
            self.log_cmd.clear()
            self.log_sys.clear()
            self.worker.start()
            self.start_btn.setText("STOP")
            self.start_btn.setStyleSheet("background-color: #aa4444; color: white; border: none; padding: 5px;")
            self.status_label.setText("RUNNING")
            self.status_label.setStyleSheet("color: #55ff55; font-weight: bold; background-color: rgba(85, 255, 85, 0.1); padding: 2px 8px; border-radius: 10px;")
        else:
            self.worker.stop()

    def on_process_finished(self, exit_code):
        self.start_btn.setText("START")
        self.start_btn.setStyleSheet("background-color: #44aa44; color: white; border: none; padding: 5px;")
        self.status_label.setText("STOPPED")
        self.status_label.setStyleSheet("color: #ff5555; font-weight: bold; background-color: rgba(255, 85, 85, 0.1); padding: 2px 8px; border-radius: 10px;")
        self.append_log(f"\n[SYSTEM] Process finished with exit code {exit_code}")

    def append_log(self, text):
        # Colorize and route lines
        lines = text.split("\n")
        
        # Batch updates by target tab to minimize DOM operations
        tab_updates = {
            self.log_all: [],
            self.log_tlm: [],
            self.log_cmd: [],
            self.log_sys: []
        }

        for line in lines:
            if not line.strip(): continue
            
            color = "#dcdcdc"
            targets = [self.log_all]

            if "[SEND]" in line or "[RECV TELEMETRY]" in line:
                color = "#4fc3f7" if "[SEND]" in line else "#81c784"
                targets.append(self.log_tlm)
            elif "[RECV COMMAND]" in line or "[CMD]" in line or "[COMMAND] SENT" in line:
                color = "#fff176" if "[RECV COMMAND]" in line else "#ffb74d"
                targets.append(self.log_cmd)
            elif "[ERROR]" in line or "[SYSTEM]" in line or "[SYS]" in line or "IGNORED" in line:
                if "[ERROR]" in line: color = "#e57373"
                elif "[SYSTEM]" in line or "[SYS]" in line: color = "#ba68c8"
                else: color = "#9e9e9e"
                targets.append(self.log_sys)

            html = f'<span style="color: {color};">{line}</span><br>'
            for t in targets:
                tab_updates[t].append(html)

        # Apply batched updates efficiently
        for t, content_list in tab_updates.items():
            if not content_list: continue
            
            # Disable updates while inserting to prevent flicker and CPU spikes
            t.setUpdatesEnabled(False)
            t.insertHtml("".join(content_list))
            if self.scroll_lock.isChecked():
                t.moveCursor(QTextCursor.End)
            t.setUpdatesEnabled(True)

    def send_custom_cmd(self):
        cmd = self.cmd_input.text().upper()
        if cmd:
            self.worker.send_command(cmd)
            self.cmd_input.clear()

    def toggle_tabs(self, checked):
        self.tabs.setVisible(checked)
        self.toggle_tabs_btn.setText("LOGS" if checked else "LOGS+")

    def toggle_controls(self, checked):
        self.ctrl_container.setVisible(checked)
        self.toggle_ctrls_btn.setText("CTRLS" if checked else "CTRLS+")

class LynkTestPlatform(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LYNK Multi-Node Test Platform")
        self.resize(1200, 800)
        self.setStyleSheet("background-color: #121212; color: #ffffff;")
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.main_layout = QVBoxLayout()
        
        # ... Top Bar ...
        self.setup_top_bar()
        
        # Main Tab Widget for Fleet vs Mesh
        self.main_tabs = QTabWidget()
        self.main_tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #333333; background: #121212; }
            QTabBar::tab { background: #1a1a1c; color: #888888; padding: 10px 30px; font-weight: bold; border-top-left-radius: 8px; border-top-right-radius: 8px;}
            QTabBar::tab:selected { background: #4fc3f7; color: #000000; }
        """)

        # Tab 1: Fleet Control
        self.fleet_widget = QWidget()
        fleet_vlayout = QVBoxLayout()
        
        # Global Tlm Toggles in Fleet View
        self.setup_global_tlm_bar(fleet_vlayout)
        
        # Scroll Area for Nodes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_widget.setLayout(self.grid_layout)
        scroll.setWidget(self.grid_widget)
        fleet_vlayout.addWidget(scroll)
        self.fleet_widget.setLayout(fleet_vlayout)
        
        # Tab 2: Mesh Topology with Sidebar
        self.mesh_tab_widget = QWidget()
        mesh_hlayout = QHBoxLayout()
        
        self.mesh_widget = MeshTopologyWidget()
        mesh_hlayout.addWidget(self.mesh_widget, 4) # Take 80%
        
        # Stats Sidebar
        stats_panel = QFrame()
        stats_panel.setFixedWidth(250)
        stats_panel.setStyleSheet("background-color: #1a1a1c; border-left: 1px solid #333333; border-radius: 0;")
        stats_layout = QVBoxLayout()
        
        stats_title = QLabel("NETWORK STATS")
        stats_title.setStyleSheet("color: #4fc3f7; font-weight: bold; font-size: 14px; margin-bottom: 20px;")
        stats_layout.addWidget(stats_title)
        
        self.stat_active_nodes = QLabel("Active Nodes: 0")
        self.stat_total_packets = QLabel("Total Packets: 0")
        self.stat_team_ratio = QLabel("Team Ratio: (1/2/S) 0/0/0")
        
        stat_style = "color: #dcdcdc; font-size: 11px; margin-bottom: 10px;"
        self.stat_active_nodes.setStyleSheet(stat_style)
        self.stat_total_packets.setStyleSheet(stat_style)
        self.stat_team_ratio.setStyleSheet(stat_style)
        
        stats_layout.addWidget(self.stat_active_nodes)
        stats_layout.addWidget(self.stat_total_packets)
        stats_layout.addWidget(self.stat_team_ratio)
        stats_layout.addStretch()
        
        hint_label = QLabel("🚀 Protip:\nDrag nodes with mouse\nto rearrange mesh.")
        hint_label.setStyleSheet("color: #666666; font-size: 10px; font-style: italic;")
        stats_layout.addWidget(hint_label)
        
        stats_panel.setLayout(stats_layout)
        mesh_hlayout.addWidget(stats_panel)
        
        self.mesh_tab_widget.setLayout(mesh_hlayout)
        
        self.main_tabs.addTab(self.fleet_widget, "📍 FLEET CONTROL")
        self.main_tabs.addTab(self.mesh_tab_widget, "🕸️ MESH TOPOLOGY")
        
        self.main_layout.addWidget(self.main_tabs)
        
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)
        
        self.nodes = [] # List of NodeCard objects
        self.loaded_node_ids = set()
        
        self.load_nodes()
        
        self.discovery_timer = QTimer()
        self.discovery_timer.timeout.connect(self.load_nodes)
        self.discovery_timer.start(5000)

        # Throttled Stats Update Timer (1Hz)
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_network_stats)
        self.stats_timer.start(1000)

        # Log Flush Timer (10Hz)
        self.flush_timer = QTimer()
        self.flush_timer.timeout.connect(self.flush_all_logs)
        self.flush_timer.start(100)

    def setup_top_bar(self):
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(10, 10, 10, 10)
        
        title_label = QLabel("LYNK DASHBOARD")
        title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title_label.setStyleSheet("color: #4fc3f7; letter-spacing: 2px;")
        top_bar.addWidget(title_label)
        
        top_bar.addStretch()
        
        btn_style = """
            QPushButton {
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 8px;
                font-size: 11px;
                border: 1px solid rgba(255,255,255,0.1);
            }
        """
        
        start_all = QPushButton("START ALL")
        start_all.setStyleSheet(btn_style + "background-color: #2e7d32; color: white;")
        start_all.clicked.connect(self.start_all_nodes)
        top_bar.addWidget(start_all)
        
        stop_all = QPushButton("STOP ALL")
        stop_all.setStyleSheet(btn_style + "background-color: #c62828; color: white;")
        stop_all.clicked.connect(self.stop_all_nodes)
        top_bar.addWidget(stop_all)

        top_bar.addSpacing(20)

        global_arm = QPushButton("GLOBAL ARM (X)")
        global_arm.setStyleSheet(btn_style + "background-color: #ef6c00; color: white;")
        global_arm.clicked.connect(lambda: self.broadcast_command("X"))
        top_bar.addWidget(global_arm)

        global_disarm = QPushButton("GLOBAL DISARM (Y)")
        global_disarm.setStyleSheet(btn_style + "background-color: #4e342e; color: white;")
        global_disarm.clicked.connect(lambda: self.broadcast_command("Y"))
        top_bar.addWidget(global_disarm)

        global_land = QPushButton("GLOBAL LAND (L)")
        global_land.setStyleSheet(btn_style + "background-color: #455a64; color: white;")
        global_land.clicked.connect(lambda: self.broadcast_command("L"))
        top_bar.addWidget(global_land)

        clear_all = QPushButton("CLEAR LOGS")
        clear_all.setStyleSheet(btn_style + "background-color: #333333; color: #aaaaaa;")
        clear_all.clicked.connect(self.clear_all_logs)
        top_bar.addWidget(clear_all)

        refresh_btn = QPushButton("REFRESH NODES")
        refresh_btn.setStyleSheet(btn_style + "background-color: #00838f; color: white;")
        refresh_btn.clicked.connect(self.load_nodes)
        top_bar.addWidget(refresh_btn)
        
        self.main_layout.addLayout(top_bar)

    def setup_global_tlm_bar(self, parent_layout):
        global_tlm_layout = QHBoxLayout()
        global_tlm_layout.addWidget(QLabel("Global Tlm Toggles:"))
        types = [("GPS", "7"), ("IMU", "8"), ("BAT", "9"), ("HB", "0"), ("BARO", "-"), ("PING", "=")]
        for name, key in types:
            btn = QPushButton(name)
            btn.setStyleSheet("max-width: 60px; font-size: 9px; background: #2b2b2b;")
            btn.clicked.connect(lambda _, k=key: self.broadcast_command(k))
            global_tlm_layout.addWidget(btn)
        global_tlm_layout.addStretch()
        parent_layout.addLayout(global_tlm_layout)

    def handle_traffic(self, src, dst, t_type):
        if t_type == "TEAM_UPDATE":
            self.mesh_widget.update_node(src, dst) # src=node_id, dst=new_team
        else:
            self.mesh_widget.add_traffic(src, dst, t_type)
        # update_network_stats call removed -> now handled by 1Hz timer

    def update_network_stats(self):
        active_count = len(self.mesh_widget.nodes)
        total_p = self.mesh_widget.total_packets
        
        t1 = sum(1 for n in self.mesh_widget.nodes.values() if n["team"] == 1)
        t2 = sum(1 for n in self.mesh_widget.nodes.values() if n["team"] == 2)
        ts = sum(1 for n in self.mesh_widget.nodes.values() if n["team"] == 0)
        
        self.stat_active_nodes.setText(f"Active Nodes: {active_count}")
        self.stat_total_packets.setText(f"Total Packets: {total_p}")
        self.stat_team_ratio.setText(f"Team Ratio (1/2/S): {t1} / {t2} / {ts}") 

    def load_nodes(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        configs_dir = os.path.join(root_dir, "configs")
        
        # Look for node_X directories
        if os.path.exists(configs_dir):
            subdirs = sorted([d for d in os.listdir(configs_dir) if os.path.isdir(os.path.join(configs_dir, d)) and d.startswith("node_")])
            
            new_nodes_found = False
            for d in subdirs:
                try:
                    # Robust parsing: matches 'node_1', 'node_2 copy', 'node_123'
                    match = re.search(r"node_(\d+)", d)
                    if not match: continue
                    node_id_int = int(match.group(1))
                except (ValueError, IndexError):
                    continue # Skip invalid directory names
                
                if node_id_int in self.loaded_node_ids:
                    continue # Skip already loaded
                
                cfg_path = os.path.join(configs_dir, d, "config.yaml")
                if os.path.exists(cfg_path):
                    new_nodes_found = True
                    card = NodeCard(str(node_id_int), cfg_path)
                    card.traffic_signal.connect(self.handle_traffic)
                    
                    # Also register node in mesh at startup
                    try:
                        import yaml
                        with open(cfg_path, 'r') as f:
                            cfg = yaml.safe_load(f)
                            tid = cfg.get("vehicle", {}).get("team_id", 0)
                            self.mesh_widget.update_node(node_id_int, tid)
                    except: pass

                    # Add to Grid layout dynamically
                    idx = len(self.nodes)
                    self.grid_layout.addWidget(card, idx // 2, idx % 2)
                    self.nodes.append(card)
                    self.loaded_node_ids.add(node_id_int)
            
            if new_nodes_found:
                self.update_network_stats()
                print(f"[SYSTEM] Discovery: New nodes loaded. Total: {len(self.nodes)}")

    def start_all_nodes(self):
        for node in self.nodes:
            if node.start_btn.text() == "START":
                node.toggle_process()

    def stop_all_nodes(self):
        for node in self.nodes:
            if node.start_btn.text() == "STOP":
                node.toggle_process()

    def broadcast_command(self, cmd):
        for node in self.nodes:
            node.worker.send_command(cmd)

    def flush_all_logs(self):
        for node in self.nodes:
            node.worker.flush_logs()

    def clear_all_logs(self):
        for node in self.nodes:
            node.log_all.clear()
            node.log_tlm.clear()
            node.log_cmd.clear()
            node.log_sys.clear()

    def closeEvent(self, event):
        self.stop_all_nodes()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = LynkTestPlatform()
    window.show()
    sys.exit(app.exec_())
