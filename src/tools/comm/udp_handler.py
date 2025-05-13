# src/tools/comm/udp_handler.py

import socket
import struct
import threading
import time
import json
from queue import Queue

class UDPHandler:
    def __init__(self, config_path="config.json"):
        self._load_config(config_path)
        # terminal_byte ve parsing buffer’ı kaldırıldı
        self.rx_queue = Queue()
        self.running = False
        self.thread = None

        # ●●● SOCKET OLUŞTURMA ●●●
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        # ●●● REUSEADDR ●●●
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # ●●● BIND İŞLEMİ ●●●
        self.sock.bind(("", self.local_port))
        self.sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_IF,
            socket.inet_aton(self.local_ip)
        )

        # ●●● MULTICAST GRUBUNA KATILIM ●●●
        mreq = struct.pack(
            "4s4s",
            socket.inet_aton(self.remote_ip),
            socket.inet_aton(self.local_ip)
        )
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)

        self.sock.setblocking(False)

    def _load_config(self, path):
        with open(path, "r") as f:
            udp_cfg = json.load(f)["udp"]
        self.local_ip    = udp_cfg["local_ip"]
        self.local_port  = udp_cfg["local_port"]
        self.remote_ip   = udp_cfg["remote_ip"]
        self.remote_port = udp_cfg["remote_port"]

    def start(self):
        """Alıcı döngüsünü başlatır."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._rx_worker, daemon=True)
        self.thread.start()

    def stop(self):
        """Alıcıyı durdurup soketi kapatır."""
        self.running = False
        if self.thread:
            self.thread.join()
        self.sock.close()

    def _rx_worker(self):
        """
        Gelen ham UDP datalarını kuyruğa ekler.
        Frame ayrımı ve CRC kontrolü parse_mesh_frame'de yapılacak.
        """
        while self.running:
            try:
                data, _addr = self.sock.recvfrom(2048)
                if data:
                    # Doğrudan ham veriyi kuyruğa bırak
                    self.rx_queue.put(data)
            except BlockingIOError:
                pass
            time.sleep(0.01)

    def read(self) -> bytes | None:
        """
        Kuyruktan bir ham UDP paketi döner.
        Üst katmanda parse_mesh_frame ile işlenecek.
        """
        return self.rx_queue.get() if not self.rx_queue.empty() else None

    def send(self, data: bytes):
        """
        build_mesh_frame ile hazırlanmış çerçeveyi direkt gönderir.
        CRC zaten içinde, ekstra bayta gerek yok.
        """
        self.sock.sendto(data, (self.remote_ip, self.remote_port))
