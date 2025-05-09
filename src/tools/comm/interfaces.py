# src/tools/interfaces.py
class CommInterface:
    def send(self, data: bytes):
        raise NotImplementedError()

    def read(self) -> bytes:
        raise NotImplementedError()

    def start(self):
        """Başlat (örn. socket bind veya uart.open)."""
        pass

    def stop(self):
        """Durdur (örn. socket.close veya uart.close)."""
        pass


class UARTInterface(CommInterface):
    def __init__(self, uart_handler):
        self.uart = uart_handler

    def send(self, data: bytes):
        self.uart.send(data)

    def read(self) -> bytes:
        return self.uart.read()

    def start(self):
        self.uart.start()

    def stop(self):
        self.uart.stop()


class UDPInterface(CommInterface):
    def __init__(self, udp_handler):
        self.udp = udp_handler

    def send(self, data: bytes):
        self.udp.send(data)

    def read(self) -> bytes:
        return self.udp.read()

    def start(self):
        self.udp.start()

    def stop(self):
        self.udp.stop()
