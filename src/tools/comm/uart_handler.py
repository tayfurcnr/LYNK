# src/tools/comm/uart_handler.py

import serial
import threading
import time
import json
from queue import Queue
from src.core.frame_codec import load_protocol_config

class UARTHandler:
    def __init__(self, config_path="config.json"):
        self._load_config(config_path)
        _, self.terminal_byte, _ = load_protocol_config(config_path)
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
        buffer = bytearray()
        term = bytes([self.terminal_byte])
        while self.running:
            if self.ser.in_waiting:
                data = self.ser.read(self.ser.in_waiting)
                buffer.extend(data)

                # terminal_byte = 0x43 (ASCII 'C') ile çerçeve sonu belirleme
                while term in buffer:
                    index = buffer.index(term) + 1
                    frame = buffer[:index]
                    self.rx_queue.put(frame)
                    buffer = buffer[index:]
            time.sleep(0.01)

    def read(self):
        if not self.rx_queue.empty():
            return self.rx_queue.get()
        return None

    def send(self, data: bytes):
        if self.ser.is_open:
            self.ser.write(data)
        else:
            raise RuntimeError("UART port is not open")