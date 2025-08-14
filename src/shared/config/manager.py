from __future__ import annotations
# src/shared/config/manager.py

import json

_config = None
_config_path = None

def load_config(path: str = "config.json"):
    global _config, _config_path
    with open(path, "r") as f:
        _config = json.load(f)
        _config_path = path


def get_config():
    if _config is None:
        raise RuntimeError("Config not loaded. Call load_config(path) first.")
    return _config


def get_config_path():
    if _config_path is None:
        raise RuntimeError("Config path not available. Did you call load_config(path)?")
    return _config_path


def get(key_path: str, default=None):
    """
    get("udp.local_ip") -> returns nested config value or default
    """
    keys = key_path.split(".")
    value = _config
    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default
