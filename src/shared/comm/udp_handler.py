# src/tools/comm/udp_handler.py

import socket
import struct
import threading
import time
from queue import Queue

from src.shared.config.manager import get_config

class UDPHandler:
    def __init__(self):
        self._load_config()
        self.rx_queue = Queue()
        self.running = False
        self.thread = None

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", self.local_port))
        self.sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_IF,
            socket.inet_aton(self.local_ip)
        )

        mreq = struct.pack(
            "4s4s",
            socket.inet_aton(self.remote_ip),
            socket.inet_aton(self.local_ip)
        )
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        self.sock.setblocking(False)

    def _load_config(self):
        cfg = get_config()
        udp_cfg = cfg.get("udp", {})
        self.local_ip    = udp_cfg["local_ip"]
        self.local_port  = udp_cfg["local_port"]
        self.remote_ip   = udp_cfg["remote_ip"]
        self.remote_port = udp_cfg["remote_port"]

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._rx_worker, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        self.sock.close()

    def _rx_worker(self):
        while self.running:
            try:
                data, _addr = self.sock.recvfrom(2048)
                if data:
                    self.rx_queue.put(data)
            except BlockingIOError:
                pass
            time.sleep(0.01)

    def read(self) -> bytes | None:
        return self.rx_queue.get() if not self.rx_queue.empty() else None

    def send(self, data: bytes):
        self.sock.sendto(data, (self.remote_ip, self.remote_port))
        print(f"[UDP SEND] {len(data)} bytes to {self.remote_ip}:{self.remote_port}")
