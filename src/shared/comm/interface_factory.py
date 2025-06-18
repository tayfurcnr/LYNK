# src/shared/comm/interface_factory.py

"""
Communication Interface Factory

Reads the 'comm_type' setting from config (via config.manager) and initializes the
corresponding communication handler and interface wrapper.
"""

from typing import Literal

from src.shared.config.manager import get_config
from src.shared.comm.interfaces import UARTInterface, UDPInterface
from src.shared.comm.mock_handler import MockUARTHandler
from src.shared.comm.uart_handler import UARTHandler
from src.shared.comm.udp_handler import UDPHandler
from src.shared.log.logger import logger


def create_interface():
    """
    Instantiate and return the appropriate communication interface
    based on the 'interface.comm_type' value in the configuration.

    Supports:
      - UART
      - MOCK_UART
      - UDP

    Returns:
        UARTInterface | UDPInterface: Wrapper over the selected handler.

    Raises:
        ValueError: If 'comm_type' is missing or unsupported.
    """
    cfg = get_config()

    comm_type: Literal["UART", "MOCK_UART", "UDP"] = cfg \
        .get("interface", {}) \
        .get("comm_type", "UART") \
        .upper()

    if comm_type == "UART":
        logger.info("[FACTORY] Initializing UART interface...")
        handler = UARTHandler()
        handler.start()
        return UARTInterface(handler)

    if comm_type == "MOCK_UART":
        logger.info("[FACTORY] Initializing MOCK UART interface...")
        handler = MockUARTHandler()
        handler.start()
        return UARTInterface(handler)

    if comm_type == "UDP":
        logger.info("[FACTORY] Initializing UDP interface...")
        handler = UDPHandler()
        handler.start()
        return UDPInterface(handler)

    raise ValueError(f"[FACTORY] Unsupported comm_type in config: {comm_type}")
