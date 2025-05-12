# src/tools/comm/interface_factory.py

"""
Communication Interface Factory

Reads the 'comm_type' setting from config.json and initializes the
corresponding communication handler and interface wrapper.
"""

import json
from pathlib import Path
from typing import Any, Dict, Literal, Union

from src.tools.comm.interfaces import UARTInterface, UDPInterface
from src.tools.comm.mock_handler import MockUARTHandler
from src.tools.comm.uart_handler import UARTHandler
from src.tools.comm.udp_handler import UDPHandler
from src.tools.log.logger import logger


def create_interface(config_path: Union[str, Path] = "config.json"):
    """
    Instantiate and return the appropriate communication interface
    based on the 'interface.comm_type' value in the configuration.

    Supports:
      - UART
      - MOCK_UART
      - UDP

    Args:
        config_path (str | Path): Path to the JSON configuration file.

    Returns:
        UARTInterface | UDPInterface: Wrapper over the selected handler.

    Raises:
        ValueError: If 'comm_type' is missing or unsupported.
    """
    # Load configuration
    with open(config_path, "r", encoding="utf-8") as f:
        cfg: Dict[str, Any] = json.load(f)

    comm_type: Literal["UART", "MOCK_UART", "UDP"] = cfg \
        .get("interface", {}) \
        .get("comm_type", "UART") \
        .upper()

    if comm_type == "UART":
        logger.info("[FACTORY] Initializing UART interface...")
        handler = UARTHandler(config_path)
        handler.start()
        return UARTInterface(handler)

    if comm_type == "MOCK_UART":
        logger.info("[FACTORY] Initializing MOCK UART interface...")
        handler = MockUARTHandler()
        handler.start()
        return UARTInterface(handler)

    if comm_type == "UDP":
        logger.info("[FACTORY] Initializing UDP interface...")
        handler = UDPHandler(config_path)
        handler.start()
        return UDPInterface(handler)

    # Unsupported comm_type
    raise ValueError(f"Unsupported comm_type in '{config_path}': {comm_type}")
