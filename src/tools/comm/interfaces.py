# src/tools/interfaces.py
import socket

class CommInterface:
    def send(self, data: bytes):
        raise NotImplementedError()

    def read(self) -> bytes:
        raise NotImplementedError()


class UARTInterface(CommInterface):
    def __init__(self, uart):
        self.uart = uart

    def send(self, data: bytes):
        self.uart.send(data)

    def read(self) -> bytes:
        return self.uart.read()

class UDPInterface(CommInterface):
    def __init__(self, udp):
        self.udp = udp

    def send(self, data: bytes):
        self.udp.send(data)

    def read(self) -> bytes:
        return self.udp.read()