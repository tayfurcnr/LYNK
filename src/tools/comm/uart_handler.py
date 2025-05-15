# src/tools/comm/uart_handler.py

import serial
import threading
import time
import json
import struct
from queue import Queue
import crcmod

# CRC-16-CCITT-FALSE
CRC_FUNC = crcmod.predefined.mkPredefinedCrcFun('crc-ccitt-false')

class IncompleteFrame(Exception):
    pass

class BadFrame(Exception):
    pass

class UARTHandler:
    def __init__(self, config_path="config.json"):
        self._load_config(config_path)
        self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        self.rx_queue = Queue()
        self.running = False
        self.thread = None
        self._rx_buffer = bytearray()

    def _load_config(self, path):
        with open(path, "r") as f:
            cfg = json.load(f)
            proto = cfg.get("protocol", {})
            self.start_byte    = proto["start_byte"]
            self.start_byte_2  = proto["start_byte_2"]
            self.version       = proto["version"]
            self.port          = cfg["uart"]["port"]
            self.baudrate      = cfg["uart"]["baudrate"]
            self.timeout       = cfg["uart"]["timeout"]

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
        while self.running:
            if self.ser.in_waiting:
                data = self.ser.read(self.ser.in_waiting)
                self.rx_queue.put(data)
            time.sleep(0.01)

    def send(self, data: bytes):
        if self.ser.is_open:
            self.ser.write(data)
        else:
            raise RuntimeError("UART port is not open")

    def read(self) -> bytes | None:
        # 1) Gelen tüm chunk'ları buffer'a ekle
        while not self.rx_queue.empty():
            self._rx_buffer.extend(self.rx_queue.get())

        # 2) Buffer'dan bir frame çıkarmayı dene
        try:
            frame, remaining = self._extract_frame(self._rx_buffer)
            self._rx_buffer = remaining
            return frame
        except IncompleteFrame:
            return None
        except BadFrame:
            return None

    def _extract_frame(self, buf: bytearray):
        SYNC = bytes([self.start_byte, self.start_byte_2])
        # Header: 2 sync + 1 ver + 1 type + 1 src + 1 dst + 2 len
        HEADER_LEN = 2 + 1 + 1 + 1 + 1 + 2

        # 1) Sync arama
        idx = buf.find(SYNC)
        if idx < 0:
            # Sync yoksa buffer'ı sıfırla
            return None, bytearray()

        # 2) Header tam mı?
        if len(buf) < idx + HEADER_LEN:
            raise IncompleteFrame()

        # 3) Versiyon kontrol
        ver = buf[idx+2]
        if ver != self.version:
            # Hatalı versiyon—sync'ten 1 bayt kaydır
            buf.pop(idx)
            return self._extract_frame(buf)

        # 4) Payload uzunluğunu oku
        payload_len = struct.unpack_from(">H", buf, idx+6)[0]
        total_len = HEADER_LEN + payload_len + 2  # +2 CRC

        if len(buf) < idx + total_len:
            raise IncompleteFrame()

        # 5) Frame parçasını al
        frame = bytes(buf[idx:idx+total_len])

        # 6) CRC kontrol
        crc_received = struct.unpack_from(">H", frame, HEADER_LEN + payload_len)[0]
        crc_calc = CRC_FUNC(frame[:HEADER_LEN + payload_len])
        if crc_received != crc_calc:
            # CRC hatalı—sync'ten 1 bayt kaydır
            buf.pop(idx)
            raise BadFrame()

        # 7) Kalan buffer
        remaining = buf[idx+total_len:]
        return frame, remaining
