# src/tools/ftp/storage.py

"""
FTP Storage Module

Handles the creation of a local download directory and provides
a binary write stream for assembling incoming FTP file fragments.
"""

import os
import json
from pathlib import Path
from typing import IO

# === Configuration Loading ===

# Locate the project's root `config.json` (three levels above this file)
CONFIG_PATH: Path = Path(__file__).parents[3] / "config.json"

# Load the configuration dictionary
with open(CONFIG_PATH, "r", encoding="utf-8") as _cfg_file:
    _CONFIG: dict = json.load(_cfg_file)

# Determine download directory (default to 'downloads' if not set)
_DOWNLOAD_DIR: str = (
    _CONFIG.get("file_transfer", {})
           .get("download_dir")
    or "downloads"
)


def open_download_stream(filename: str) -> IO[bytes]:
    """
    Open a binary write stream for reassembling FTP-transferred file fragments.

    Ensures the download directory exists, then creates or truncates the
    specified file within that directory and returns a buffered writer.

    Args:
        filename (str): Target filename for the assembled download.

    Returns:
        io.BufferedWriter: A writable binary stream for the file.
    """
    # Create the download directory if it doesn't exist
    os.makedirs(_DOWNLOAD_DIR, exist_ok=True)

    # Build the full file path
    file_path: Path = Path(_DOWNLOAD_DIR) / filename

    # Open and return the file in write-binary mode
    return open(file_path, "wb")
