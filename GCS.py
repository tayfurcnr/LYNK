import sys, json, os, threading, time
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QUrl, QDateTime, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel

import src.tools.comm.interface_factory       as iface
import src.tools.telemetry.telemetry_cache    as cache
import src.tools.telemetry.telemetry_dispatcher as disp
import src.tools.command.command_dispatcher   as cmd
import src.core.frame_codec                   as codec
import src.core.frame_router                  as router

# Config
with open("config.json","r") as f:
    MY_SRC_ID = json.load(f)["vehicle"]["id"]

# JS ↔ Python bridge that emits a signal on click
class JSHandler(QObject):
    coordsChanged = pyqtSignal(float, float)
    def __init__(self):
        super().__init__()
        self.lat = None
        self.lon = None

    @pyqtSlot(float, float)
    def setCoords(self, lat, lon):
        self.lat, self.lon = lat, lon
        self.coordsChanged.emit(lat, lon)

class GroundStation(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LYNK Ground Station")
        self.resize(1200, 800)

        # Interface
        self.interface = iface.create_interface()
        self.interface.start()

        self.current_dst = None
        self.prep = None

        # Map HTML
        self.map_file = os.path.abspath("map.html")
        self._write_map_html()

        # Build UI
        self._build_ui()

        # Background loops
        self._start_comm_loops()
        # UI timers
        self._start_cache_timer()
        self._start_telemetry_timer()

    def _write_map_html(self):
        html = """
<!DOCTYPE html><html><head>
<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
<style>html,body,#map{height:100%;margin:0}</style>
</head><body><div id="map"></div><script>
var map = L.map('map').setView([37,35],13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19}).addTo(map);
// containers for markers
window.droneMarkers = {};
window.clickMarker = null;

new QWebChannel(qt.webChannelTransport,function(ch){
  window.pyHandler = ch.objects.pyHandler;
  map.on('click', function(e){
    if(window.clickMarker) map.removeLayer(window.clickMarker);
    window.clickMarker = L.marker(e.latlng, {icon: L.icon({iconUrl:'https://maps.gstatic.com/mapfiles/api-3/images/spotlight-poi-dotless_hdpi.png'})}).addTo(map);
    window.pyHandler.setCoords(e.latlng.lat, e.latlng.lng);
  });
});
</script></body></html>
"""
        with open(self.map_file, 'w', encoding='utf-8') as f:
            f.write(html)

    def _build_ui(self):
        root = QtWidgets.QWidget()
        self.setCentralWidget(root)
        h = QtWidgets.QHBoxLayout(root)

        # Left panel
        left = QtWidgets.QVBoxLayout()
        h.addLayout(left, 1)
        self.dst_combo = QtWidgets.QComboBox()
        self.dst_combo.addItem("Select Drone...", None)
        self.dst_combo.currentIndexChanged.connect(self._on_dst_changed)
        left.addWidget(self.dst_combo)

        # Command buttons
        for key, label in [('T','Takeoff'), ('G','Goto'),
                           ('L','Landing'), ('W','Waypoints')]:
            btn = QtWidgets.QPushButton(label)
            btn.clicked.connect(lambda _, k=key: self._prepare(k))
            left.addWidget(btn)

        # Params
        self.param_box = QtWidgets.QGroupBox("Parameters")
        self.param_form = QtWidgets.QFormLayout(self.param_box)
        left.addWidget(self.param_box)
        self.coord_label = None   # will be QLabel
        left.addStretch()
        send = QtWidgets.QPushButton("Send Command")
        send.clicked.connect(self._send)
        left.addWidget(send)

        # Right panel: map + log
        right = QtWidgets.QVBoxLayout()
        h.addLayout(right, 3)

        # Map
        self.map_view = QWebEngineView()
        self.jsHandler = JSHandler()
        self.jsHandler.coordsChanged.connect(self._on_map_click)
        ch = QWebChannel(self.map_view.page())
        ch.registerObject("pyHandler", self.jsHandler)
        self.map_view.page().setWebChannel(ch)
        self.map_view.load(QUrl.fromLocalFile(self.map_file))
        right.addWidget(self.map_view, 5)

        # Log
        self.log = QtWidgets.QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(150)
        right.addWidget(self.log, 1)

    def _prepare(self, key):
        # clear old form
        while self.param_form.count():
            self.param_form.removeRow(0)
        self.prep = key

        # center on first cached drone
        data = cache.get_all_cached_data()
        for sid, vals in data.items():
            if int(sid)!=MY_SRC_ID and 'gps' in vals:
                gps = vals['gps']
                lat = gps.get('gps_lat') or gps.get('lat')
                lon = gps.get('gps_lon') or gps.get('lon')
                if lat is not None and lon is not None:
                    # add/update drone marker in JS
                    js = f"""
if (window.droneMarkers['{sid}']) {{
  map.removeLayer(window.droneMarkers['{sid}']);
}}
window.droneMarkers['{sid}'] = L.circleMarker([{lat},{lon}], {{color:'green'}}).addTo(map);
map.setView([{lat},{lon}],15);
"""
                    self.map_view.page().runJavaScript(js)
                    break

        # build form
        # common coord label
        self.coord_label = QtWidgets.QLabel("click map")
        self.param_form.addRow("Clicked Lat/Lon:", self.coord_label)

        if key in ('T','G','W'):
            sb = QtWidgets.QDoubleSpinBox(); sb.setRange(0,10000)
            self.param_form.addRow("Altitude (m):", sb)

        if key=='W':
            # waypoint list show
            self.wp_list = []
            self.param_form.addRow("Waypoints:", QtWidgets.QLabel("click multiple"))

    def _on_map_click(self, lat, lon):
        # update coord label
        if self.coord_label:
            self.coord_label.setText(f"{lat:.6f}, {lon:.6f}")

    def _send(self):
        if not self.prep:
            return
        dst = self.current_dst
        if dst is None:
            QtWidgets.QMessageBox.warning(self, "No drone", "Select a drone first")
            return
        lat, lon = self.jsHandler.lat, self.jsHandler.lon
        ts = QDateTime.currentDateTime().toString("hh:mm:ss")

        if self.prep=='T':
            alt = self.param_form.itemAt(1, QtWidgets.QFormLayout.FieldRole).widget().value()
            cmd.cmd_takeoff(self.interface,
                takeoff_alt=alt, target_lat=lat, target_lon=lon,
                src=MY_SRC_ID, dst=dst)
            self.log.append(f"[{ts}] TAKEOFF → Dr{dst} @({lat:.5f},{lon:.5f}) alt={alt}")

        elif self.prep=='G':
            alt = self.param_form.itemAt(1, QtWidgets.QFormLayout.FieldRole).widget().value()
            cmd.cmd_goto(self.interface,
                target_lat=lat, target_lon=lon, target_alt=alt,
                src=MY_SRC_ID, dst=dst)
            self.log.append(f"[{ts}] GOTO → Dr{dst} @({lat:.5f},{lon:.5f}) alt={alt}")

        elif self.prep=='L':
            cmd.cmd_landing(self.interface, src=MY_SRC_ID, dst=dst)
            self.log.append(f"[{ts}] LAND → Dr{dst} @({lat:.5f},{lon:.5f})")

        elif self.prep=='W':
            alt = self.param_form.itemAt(1, QtWidgets.QFormLayout.FieldRole).widget().value()
            # collect clicks: assume user can click multiple times; for simplicity
            # here just last clicked
            wp = [(lat, lon, alt)]
            cmd.cmd_waypoints(self.interface, waypoints=wp, src=MY_SRC_ID, dst=dst)
            self.log.append(f"[{ts}] WAYPOINTS → Dr{dst} {wp}")

        # reset
        self.prep = None
        self.coord_label = None

    def _start_comm_loops(self):
        def tel_loop():
            while True:
                if not self.current_dst:
                    time.sleep(1)
                    continue
                dst = self.current_dst
                disp.send_tlm_gps(self.interface, lat=37, lon=35, alt=100, dst=dst, src=MY_SRC_ID)
                disp.send_tlm_imu(self.interface, roll=1, pitch=2, yaw=3, dst=dst, src=MY_SRC_ID)
                disp.send_tlm_battery(self.interface, voltage=11, current=2, level=90, dst=dst, src=MY_SRC_ID)
                disp.send_tlm_heartbeat(self.interface, mode="AUTO", health="OK",
                                        is_armed=True, gps_fix=True, sat_count=10,
                                        dst=dst, src=MY_SRC_ID)
                time.sleep(1)
        def recv_loop():
            while True:
                raw = self.interface.read()
                if raw:
                    try:
                        f = codec.parse_mesh_frame(raw)
                        router.route_frame(f, self.interface)
                    except:
                        pass
                time.sleep(0.05)
        threading.Thread(target=tel_loop, daemon=True).start()
        threading.Thread(target=recv_loop, daemon=True).start()

    def _start_cache_timer(self):
        t = QtCore.QTimer(self); t.setInterval(2000)
        t.timeout.connect(self._update_cache)
        t.start(); self.cache_timer = t

    def _start_telemetry_timer(self):
        t = QtCore.QTimer(self); t.setInterval(2000)
        t.timeout.connect(self._update_map)
        t.start(); self.tel_timer = t

    def _update_cache(self):
        D = cache.get_all_cached_data()
        ids = [int(k) for k in D if int(k)!=MY_SRC_ID]
        old = self.current_dst
        self.dst_combo.blockSignals(True)
        self.dst_combo.clear()
        self.dst_combo.addItem("Select Drone...", None)
        for i in sorted(ids):
            self.dst_combo.addItem(f"Drone {i}", i)
        self.dst_combo.blockSignals(False)
        if old in ids:
            idx = self.dst_combo.findData(old)
            self.dst_combo.setCurrentIndex(idx)
            self.current_dst = old
        else:
            self.current_dst = None
            self.dst_combo.setCurrentIndex(0)
        self.log.append(f"[{QDateTime.currentDateTime().toString('hh:mm:ss')}] CACHE: {json.dumps(D)}")

    def _update_map(self):
        if not self.current_dst:
            return
        D = cache.get_all_cached_data().get(str(self.current_dst), {})
        gps = D.get('gps', {})
        lat = gps.get('gps_lat') or gps.get('lat')
        lon = gps.get('gps_lon') or gps.get('lon')
        if lat is not None and lon is not None:
            # update drone marker
            js = f"""
if (window.droneMarkers['{self.current_dst}']) {{
    map.removeLayer(window.droneMarkers['{self.current_dst}']);
}}
window.droneMarkers['{self.current_dst}'] = L.circleMarker([{lat},{lon}],{{color:'green'}}).addTo(map);
"""
            self.map_view.page().runJavaScript(js)
            ts = QDateTime.currentDateTime().toString("hh:mm:ss")
            self.log.append(f"[{ts}] GPS Drone {self.current_dst}: {lat:.6f},{lon:.6f}")

    def _on_dst_changed(self, idx):
        self.current_dst = self.dst_combo.itemData(idx)

    def closeEvent(self, e):
        self.cache_timer.stop(); self.tel_timer.stop(); self.interface.stop()
        super().closeEvent(e)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    gs = GroundStation()
    gs.show()
    sys.exit(app.exec_())
