from __future__ import annotations
# lynk/shared/config/manager.py

import os
import json
try:
    import yaml
except ImportError:
    # PyYAML yüklü değilse, sadece JSON desteği ile devam et
    yaml = None

_config = None
_config_path = None

def load_config(path: str):
    """
    Yapılandırmayı bir JSON veya YAML dosyasından yükler.
    Dosya türü uzantıya göre belirlenir (.json, .yaml, .yml).
    """
    global _config, _config_path
    _, ext = os.path.splitext(path)
    ext = ext.lower()

    with open(path, "r") as f:
        if ext in ['.yaml', '.yml']:
            if yaml is None:
                raise ImportError("YAML support requires PyYAML. Please 'pip install PyYAML'")
            _config = yaml.safe_load(f)
        elif ext == '.json':
            _config = json.load(f)
        else:
            raise ValueError(f"Unsupported config file format: {ext}. Use .json, .yaml, or .yml")
        _config_path = path


def get_config():
    if _config is None:
        raise RuntimeError("Config not loaded. Call load_config(path) first.")
    return _config


def get_config_path():
    if _config_path is None:
        raise RuntimeError("Config path not available. Did you call load_config(path)?")
    return _config_path


def save_config():
    """
    Saves the current in-memory config back to the original file path.
    Supports both YAML and JSON based on file extension.
    """
    global _config, _config_path
    if _config is None or _config_path is None:
        return False

    try:
        _, ext = os.path.splitext(_config_path)
        ext = ext.lower()

        with open(_config_path, "w") as f:
            if ext in ['.yaml', '.yml']:
                if yaml is None:
                    raise ImportError("YAML support missing")
                yaml.safe_dump(_config, f, default_flow_style=False, sort_keys=False)
            elif ext == '.json':
                json.dump(_config, f, indent=2)
            else:
                return False
        return True
    except Exception as e:
        print(f"[CONFIG] Failed to save config: {e}")
        return False


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
