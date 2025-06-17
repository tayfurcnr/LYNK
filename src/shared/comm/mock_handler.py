# src/tools/comm/mock_handler.py

"""
Mock UART Handler

Simulates a UART transport for testing purposes by capturing sent frames
and providing them back via a read buffer.
"""

from typing import List, Optional


class MockUARTHandler:
    """
    In-memory UART handler that records outgoing frames and allows
    injected or looped-back frames to be read.
    """

    def __init__(self) -> None:
        # Frames available to read (injection or loopback)
        self.buffer: List[bytes] = []
        # Frames that have been sent
        self._outbox: List[bytes] = []

    def start(self) -> None:
        """Initialize the mock UART (no-op beyond logging)."""
        print("[MockUART] ✅ Başlatıldı")

    def stop(self) -> None:
        """Shut down the mock UART (no-op beyond logging)."""
        print("[MockUART] ⛔ Durduruldu")

    def send(self, frame: bytes) -> None:
        """
        "Send" a frame by recording it and echoing it into the read buffer.

        Args:
            frame (bytes): The raw frame to send.
        """
        print(f"[MockUART] 📤 Gönderildi: {frame.hex()}")
        self._outbox.append(frame)
        # Loop back for immediate read in tests
        self.buffer.append(frame)

    def inject_frame(self, frame: bytes) -> None:
        """
        Inject an external frame into the read buffer.

        Args:
            frame (bytes): The raw frame to inject.
        """
        self.buffer.append(frame)

    def read(self) -> Optional[bytes]:
        """
        Read the next available frame, if any.

        Returns:
            bytes or None: The next frame, or None if the buffer is empty.
        """
        if self.buffer:
            return self.buffer.pop(0)
        return None
