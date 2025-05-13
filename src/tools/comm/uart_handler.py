# src/tools/comm/uart_handler.py

import serial
import threading
import time
import json
from queue import Queue

class UARTHandler:
    def __init__(self, config_path="config.json"):
        self._load_config(config_path)
        # artık terminal_byte yok
        self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        self.rx_queue = Queue()
        self.running = False
        self.thread = None

    def _load_config(self, path):
        with open(path, "r") as f:
            cfg = json.load(f)
            try:
                uart_cfg = cfg["uart"]
                self.port = uart_cfg["port"]
                self.baudrate = uart_cfg["baudrate"]
                self.timeout = uart_cfg["timeout"]
            except KeyError as e:
                raise ValueError(f"config.json içinde eksik UART parametresi: {e}")

    def start(self):
        if not self.ser.is_open:
            self.ser.open()
        self.running = True
        self.thread = threading.Thread(target=self._rx_worker, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        if self.ser.is_open:
            self.ser.close()

    def _rx_worker(self):
        """
        Gelen tüm ham byte'ları kuyruğa ekliyoruz.
        Frame ayrımı ve CRC kontrolü parse_mesh_frame'de yapılacak.
        """
        while self.running:
            if self.ser.in_waiting:
                data = self.ser.read(self.ser.in_waiting)
                # doğrudan ham veriyi kuyruğa bırak
                self.rx_queue.put(data)
            time.sleep(0.01)

    def read(self) -> bytes | None:
        """
        Kuyruktan bir seferde okunan ham veriyi döner.
        Üst katmanda parse_mesh_frame ile işlenecek.
        """
        if not self.rx_queue.empty():
            return self.rx_queue.get()
        return None

    def send(self, data: bytes):
        """
        build_mesh_frame ile hazırlanmış çerçeveyi direkt yollar.
        CRC zaten içinde, ekstra bayta gerek yok.
        """
        if self.ser.is_open:
            self.ser.write(data)
        else:
            raise RuntimeError("UART port is not open")
