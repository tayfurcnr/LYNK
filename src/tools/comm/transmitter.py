# src/tools/comm/transmitter.py

import logging

logger = logging.getLogger(__name__)

def send_frame(interface, frame: bytes) -> None:
    """
    Send a raw frame over the specified communication interface.

    Args:
        interface: CommInterface instance (e.g., UARTInterface, UDPInterface).
        frame (bytes): Byte sequence to transmit.

    Returns:
        None
    """
    try:
        interface.send(frame)
        logger.debug(f"[TRANSMITTER] SENT | Frame size: {len(frame)} bytes")
    except Exception as e:
        logger.error(f"[TRANSMITTER] FAILED TO SEND | Error: {e}")
