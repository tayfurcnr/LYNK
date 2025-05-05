import json
from src.tools.interfaces import UARTInterface, UDPInterface
from mock_uart import MockUARTHandler
from src.handlers.uart_handler import UARTHandler
from src.handlers.udp_handler import UDPHandler
from src.tools.logger import logger

def create_interface(config_path="config.json"):
    """
    config.json'daki comm_type değerine göre uygun handler ve interface oluşturur.
    """
    with open(config_path, "r") as f:
        cfg = json.load(f)
        comm_type = cfg.get("interface", {}).get("comm_type", "UART").upper()

    if comm_type == "UART":
        logger.info("[FACTORY] Initializing UART interface...")
        uart_handler = UARTHandler(config_path)
        uart_handler.start()
        return UARTInterface(uart_handler)
    
    elif comm_type == "MOCK_UART":
        logger.info("[FACTORY] Initializing MOCK UART interface...")
        mock_handler = MockUARTHandler()
        mock_handler.start()
        return UARTInterface(mock_handler)
    
    elif comm_type == "UDP":
        logger.info("[FACTORY] Initializing UDP interface...")
        udp_handler = UDPHandler(config_path)
        udp_handler.start()
        return UDPInterface(udp_handler)

    else:
        raise ValueError(f"Unsupported comm_type in config.json: {comm_type}")
