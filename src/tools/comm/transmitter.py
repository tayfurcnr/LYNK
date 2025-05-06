# src/tools/transmitter.py

import logging

logger = logging.getLogger(__name__)

def send_frame(interface, frame: bytes) -> None:
    """
    Frame verisini, verilen iletişim arayüzü (UART, RF, Wi-Fi vb.) üzerinden gönderir.

    Parameters:
        interface: CommInterface (örnek: UARTInterface)
        frame: Gönderilecek bytes verisi

    Returns:
        None
    """
    try:
        interface.send(frame)
        logger.debug(f"[TRANSMITTER] SENT | Frame Size: {len(frame)} bytes")
    except Exception as e:
        logger.error(f"[TRANSMITTER] FAILED TO SEND | Error: {e}")