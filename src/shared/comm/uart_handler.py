from __future__ import annotations
# src/shared/comm/uart_handler.py

import threading
import time
import struct
from queue import Queue
from serial import Serial, SerialException
import crcmod

from src.shared.log.logger import logger
from src.shared.config.manager import get_config

# CRC-16-CCITT-FALSE
CRC_FUNC = crcmod.predefined.mkPredefinedCrcFun('crc-ccitt-false')

class IncompleteFrame(Exception):
    pass

class BadFrame(Exception):
    pass

class UARTHandler:
    def __init__(self):
        self._load_config()
        self.ser = Serial(self.port, self.baudrate, timeout=self.timeout)
        self.rx_queue = Queue()
        self.running = False
        self.thread = None
        self._rx_buffer = bytearray()

    def _load_config(self):
        cfg = get_config()
        proto = cfg.get("protocol", {})
        self.start_byte   = proto["start_byte"]
        self.start_byte_2 = proto["start_byte_2"]
        self.version      = proto["version"]

        uart_cfg = cfg.get("uart", {})
        self.port     = uart_cfg["port"]
        self.baudrate = uart_cfg["baudrate"]
        self.timeout  = uart_cfg["timeout"]

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
            try:
                if self.ser.in_waiting:
                    data = self.ser.read_all()
                    if data:
                        self.rx_queue.put(data)
                time.sleep(0.01)
            except SerialException as e:
                if "device reports readiness to read but returned no data" in str(e):
                    # This specific error is ignored as per user request.
                    # Note: This may hide an underlying issue like multi-access on the port.
                    pass
                else:
                    logger.error(f"[UARTHandler] Read error: {e}")

    def send(self, data: bytes) -> bool:
        if not self.ser.is_open:
            try:
                self.ser.open()
            except SerialException as e:
                logger.error(f"[UARTHandler] UART port open failed: {e}")
                return False
        try:
            self.ser.write(data)
            return True
        except SerialException as e:
            logger.error(f"[UARTHandler] UART write error: {e}")
            return False

    def read(self) -> bytes | None:
        while not self.rx_queue.empty():
            self._rx_buffer.extend(self.rx_queue.get())

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
        # start1(1) + start2(1) + ver(1) + type(1) + team(1) + src(1) + dst(1) + hop(1) + flags(1) + len(2)
        HEADER_LEN = 11

        idx = buf.find(SYNC)
        if idx < 0:
            return None, bytearray()

        if len(buf) < idx + HEADER_LEN:
            raise IncompleteFrame()

        ver = buf[idx + 2]
        if ver != self.version:
            buf.pop(idx)
            return self._extract_frame(buf)

        payload_len = struct.unpack_from(">H", buf, idx + 9)[0]
        total_len = HEADER_LEN + payload_len + 2  # CRC

        if len(buf) < idx + total_len:
            raise IncompleteFrame()

        frame = bytes(buf[idx:idx + total_len])

        crc_received = struct.unpack_from(">H", frame, HEADER_LEN + payload_len)[0]
        crc_calc = CRC_FUNC(frame[:HEADER_LEN + payload_len])
        if crc_received != crc_calc:
            buf.pop(idx)
            raise BadFrame()

        remaining = buf[idx + total_len:]
        return frame, remaining
