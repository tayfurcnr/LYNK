from __future__ import annotations
# src/shared/comm/interface_factory.py

from typing import Literal
from src.shared.config.manager import get_config
from src.shared.comm.interfaces import UARTInterface, UDPInterface
from src.shared.comm.mock_handler import MockUARTHandler
from src.shared.comm.uart_handler import UARTHandler
from src.shared.comm.udp_handler import UDPHandler
from src.shared.log.logger import logger

# Global singleton cache
_interface_instance = None

def create_interface():
    global _interface_instance

    if _interface_instance is not None:
        return _interface_instance

    cfg = get_config()
    comm_type: Literal["UART", "MOCK_UART", "UDP"] = cfg \
        .get("interface", {}) \
        .get("comm_type", "UART") \
        .upper()

    if comm_type == "UART":
        logger.info("[FACTORY] Initializing UART interface...")
        handler = UARTHandler()
        handler.start()
        _interface_instance = UARTInterface(handler)
        return _interface_instance

    if comm_type == "MOCK_UART":
        logger.info("[FACTORY] Initializing MOCK UART interface...")
        handler = MockUARTHandler()
        handler.start()
        _interface_instance = UARTInterface(handler)
        return _interface_instance

    if comm_type == "UDP":
        logger.info("[FACTORY] Initializing UDP interface...")
        handler = UDPHandler()
        handler.start()
        _interface_instance = UDPInterface(handler)
        return _interface_instance

    raise ValueError(f"[FACTORY] Unsupported comm_type in config: {comm_type}")
