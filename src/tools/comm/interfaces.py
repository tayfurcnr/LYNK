# src/tools/comm/interfaces.py

"""
Communication Interface Abstractions

Defines a common API for communication handlers and provides concrete
wrappers for UART and UDP transports.
"""

class CommInterface:
    """
    Base class for communication interfaces. Concrete implementations must
    support starting, stopping, sending, and reading raw byte data.
    """

    def start(self):
        """
        Initialize the transport (e.g., open UART port or bind UDP socket).
        """
        pass

    def stop(self):
        """
        Shut down the transport (e.g., close UART port or socket).
        """
        pass

    def send(self, data: bytes):
        """
        Transmit raw bytes over the interface.

        Args:
            data (bytes): The payload to send.
        """
        raise NotImplementedError()

    def read(self) -> bytes:
        """
        Read raw bytes from the interface, if available.

        Returns:
            bytes: The received payload.
        """
        raise NotImplementedError()


class UARTInterface(CommInterface):
    """
    Wraps a UART handler to conform to CommInterface.
    """

    def __init__(self, uart_handler):
        """
        Args:
            uart_handler: Instance providing start(), stop(), send(), read().
        """
        self.uart = uart_handler

    def start(self):
        """Start the UART handler."""
        self.uart.start()

    def stop(self):
        """Stop the UART handler."""
        self.uart.stop()

    def send(self, data: bytes):
        """Send data via UART."""
        self.uart.send(data)

    def read(self) -> bytes:
        """Read data from UART."""
        return self.uart.read()


class UDPInterface(CommInterface):
    """
    Wraps a UDP handler to conform to CommInterface.
    """

    def __init__(self, udp_handler):
        """
        Args:
            udp_handler: Instance providing start(), stop(), send(), read().
        """
        self.udp = udp_handler

    def start(self):
        """Start the UDP handler."""
        self.udp.start()

    def stop(self):
        """Stop the UDP handler."""
        self.udp.stop()

    def send(self, data: bytes):
        """Send data via UDP."""
        self.udp.send(data)

    def read(self) -> bytes:
        """Read data from UDP."""
        return self.udp.read()