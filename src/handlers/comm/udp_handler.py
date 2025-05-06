import socket
import threading
import time
import json
from queue import Queue

class UDPHandler:
    def __init__(self, config_path="config.json"):
        self._load_config(config_path)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.local_ip, self.local_port))
        self.sock.setblocking(False)

        self.rx_queue = Queue()
        self.running = False
        self.thread = None

    def _load_config(self, path):
        with open(path, "r") as f:
            cfg = json.load(f)
            try:
                udp_cfg = cfg["udp"]
                self.local_ip = udp_cfg["local_ip"]
                self.local_port = udp_cfg["local_port"]
                self.remote_ip = udp_cfg["remote_ip"]
                self.remote_port = udp_cfg["remote_port"]
            except KeyError as e:
                raise ValueError(f"config.json içinde eksik UDP parametresi: {e}")

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._rx_worker, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        self.sock.close()

    def _rx_worker(self):
        buffer = bytearray()
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                buffer.extend(data)

                while b'\x43' in buffer:  # ASCII 'C' terminal byte
                    index = buffer.index(0x43) + 1
                    frame = buffer[:index]
                    self.rx_queue.put(frame)
                    buffer = buffer[index:]

            except BlockingIOError:
                pass

            time.sleep(0.01)

    def read(self):
        if not self.rx_queue.empty():
            return self.rx_queue.get()
        return None

    def send(self, data: bytes):
        self.sock.sendto(data, (self.remote_ip, self.remote_port))
