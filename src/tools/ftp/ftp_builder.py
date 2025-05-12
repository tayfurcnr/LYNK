# src/tools/ftp/ftp_builder.py

"""
FTP Builder Module

Implements a reliable, FTP‐like file transfer over the mesh network:
  1) START frame (filename)
  2) CHUNK frames (with retries and ACK tracking)
  3) END frame (total chunk count)
"""

import os
import math
import time
import json
from pathlib import Path
from typing import Any, Protocol

from src.core.frame_codec import build_mesh_frame, parse_mesh_frame
from src.core.frame_router import route_frame
from src.serializers.ftp_serializer import (
    serialize_ftp_start,
    serialize_ftp_chunk,
    serialize_ftp_end
)
from src.tools.log.logger import logger
from src.tools.ack.ack_tracker import clear_ack, get_ack_status

# === Load FTP settings from project root config.json ===
CONFIG_PATH: Path = Path(__file__).parents[3] / "config.json"
with open(CONFIG_PATH, "r", encoding="utf-8") as _cfg_file:
    _CONFIG: dict[str, Any] = json.load(_cfg_file)

_ftp_cfg = _CONFIG["file_transfer"]
PKT_SIZE: int    = _ftp_cfg["packet_size"]
TIMEOUT_MS: int  = _ftp_cfg["timeout_ms"]
MAX_RETRIES: int = _ftp_cfg["max_retries"]


class SendableInterface(Protocol):
    """
    Protocol for interfaces that support send() and read() or uart.read().
    """
    def send(self, frame: bytes) -> None: ...
    def read(self) -> bytes | None: ...


def send_ftp_file(
    interface: SendableInterface,
    filepath: str,
    src: int,
    dst: int
) -> None:
    """
    Perform a chunked file transfer with acknowledgments.

    Args:
        interface (SendableInterface): Communication interface instance.
        filepath (str): Path to the local file to transfer.
        src (int): Source device ID.
        dst (int): Destination device ID.

    Raises:
        RuntimeError: If any step fails after MAX_RETRIES or timeout.
    """
    # Read entire file and compute number of chunks
    with open(filepath, "rb") as f:
        data = f.read()

    total_chunks = math.ceil(len(data) / PKT_SIZE)
    timeout_secs = TIMEOUT_MS / 1000.0
    filename = os.path.basename(filepath)

    # --- 1) START frame ---
    start_key = "FTP_START"
    clear_ack(start_key, dst)
    start_payload = serialize_ftp_start(filename)
    start_frame = build_mesh_frame('F', src, dst, payload=start_payload)
    interface.send(start_frame)
    logger.info(f"[FTP] START sent | filename={filename}")

    # Wait for START-ACK
    start_time = time.time()
    while time.time() - start_time < timeout_secs:
        raw = interface.read() if not hasattr(interface, 'uart') else interface.uart.read()
        if raw:
            frm = parse_mesh_frame(raw)
            route_frame(frm, interface)
            if get_ack_status(start_key, dst) == 0:
                clear_ack(start_key, dst)
                logger.debug("[FTP] START ACK received")
                break
        time.sleep(0.01)
    else:
        raise RuntimeError("[FTP] START not ACKed within timeout")

    # --- 2) CHUNK frames ---
    for seq in range(total_chunks):
        chunk_data = data[seq * PKT_SIZE : (seq + 1) * PKT_SIZE]
        chunk_key = f"FTP_CHUNK_{seq}"
        clear_ack(chunk_key, dst)

        # send with retries
        for attempt in range(1, MAX_RETRIES + 1):
            chunk_payload = serialize_ftp_chunk(seq, chunk_data)
            chunk_frame   = build_mesh_frame('F', src, dst, payload=chunk_payload)
            interface.send(chunk_frame)
            logger.debug(f"[FTP] CHUNK {seq} sent (attempt {attempt})")

            # pump incoming
            start_t = time.time()
            while time.time() - start_t < timeout_secs:
                raw = interface.read() if not hasattr(interface, 'uart') else interface.uart.read()
                if raw:
                    frm = parse_mesh_frame(raw)
                    route_frame(frm, interface)
                # check ACK
                status = get_ack_status(chunk_key, dst)
                if status is not None:
                    break
                time.sleep(0.01)

            if status == 0:
                clear_ack(chunk_key, dst)
                logger.debug(f"[FTP] CHUNK {seq} ACKed")
                break
            else:
                clear_ack(chunk_key, dst)
                logger.warning(f"[FTP] CHUNK {seq} failed (status={status}), retrying")
        else:
            raise RuntimeError(f"[FTP] CHUNK {seq} failed after {MAX_RETRIES} attempts")

    # --- 3) END frame ---
    end_key = "FTP_END"
    clear_ack(end_key, dst)
    end_payload = serialize_ftp_end(total_chunks)
    end_frame = build_mesh_frame('F', src, dst, payload=end_payload)
    interface.send(end_frame)
    logger.info(f"[FTP] END sent | total_chunks={total_chunks}")

    # Wait for END-ACK
    start_time = time.time()
    while time.time() - start_time < timeout_secs:
        raw = interface.read() if not hasattr(interface, 'uart') else interface.uart.read()
        if raw:
            frm = parse_mesh_frame(raw)
            route_frame(frm, interface)
            if get_ack_status(end_key, dst) == 0:
                clear_ack(end_key, dst)
                logger.debug("[FTP] END ACK received")
                return
        time.sleep(0.01)
    raise RuntimeError("[FTP] END not ACKed within timeout")
