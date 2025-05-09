import socket
import struct
import threading
import time
import json
from queue import Queue
from src.core.frame_codec import load_protocol_config

class UDPHandler:
    def __init__(self, config_path="config.json"):
        self._load_config(config_path)
        _, self.terminal_byte, _ = load_protocol_config(config_path)
        self.rx_queue = Queue()
        self.running = False
        self.thread = None

        # ●●● SOCKET OLUŞTURMA ●●●
        # Singlecast için (tek hedef IP/port):
        # self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #
        # Multicast için (gruba katılmak üzere):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        # ●●● REUSEADDR ●●●
        # SO_REUSEADDR bind’ten önce gelmeli:
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # ●●● BIND İŞLEMİ ●●●
        # Singlecast’te kendi IP/port’una bind et:
        # self.sock.bind((self.local_ip, self.local_port))
        #
        # Multicast’te tüm ara yüzlerden geleni dinle:
        self.sock.bind(('', self.local_port))

        # ●●● MULTICAST GRUBUNA KATILIM ●●●
        # Sadece multicast kullanacaksan burayı yorumdan çıkar
        mreq = struct.pack(
            "4s4s",
            socket.inet_aton(self.remote_ip),   # config.json’daki multicast adres
            socket.inet_aton(self.local_ip)     # genellikle '0.0.0.0'
        )

        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)

        self.sock.setblocking(False)

    def _load_config(self, path):
        with open(path, "r") as f:
            udp_cfg = json.load(f)["udp"]
        self.local_ip     = udp_cfg["local_ip"]
        self.local_port   = udp_cfg["local_port"]
        self.remote_ip    = udp_cfg["remote_ip"]    # singlecast hedef veya multicast grup
        self.remote_port  = udp_cfg["remote_port"]

    def start(self):
        """Alıcı döngüsünü başlatır."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._rx_worker, daemon=True)
        self.thread.start()

    def stop(self):
        """Durdur ve soketi kapat."""
        self.running = False
        if self.thread:
            self.thread.join()
        self.sock.close()

    def _rx_worker(self):
        """Arka planda gelen datayı parçalar ve kuyruğa atar."""
        buffer = bytearray()
        term = bytes([self.terminal_byte])
        while self.running:
            try:
                data, addr = self.sock.recvfrom(2048)
                buffer.extend(data)
                while term in buffer:   # terminal byte
                    idx = buffer.index(term) + 1
                    frame = bytes(buffer[:idx])
                    self.rx_queue.put(frame)
                    buffer = buffer[idx:]
            except BlockingIOError:
                pass
            time.sleep(0.01)

    def read(self):
        """Kuyruktan bir frame döner, yoksa None."""
        return self.rx_queue.get() if not self.rx_queue.empty() else None

    def send(self, data: bytes):
        """
        Gönderim yapar:
        - Singlecast’te: (self.local_ip, self.local_port) → (self.remote_ip, self.remote_port)
        - Multicast’te: aynı send() çağrısı multicast grubuna gider.
        """
        self.sock.sendto(data, (self.remote_ip, self.remote_port))
