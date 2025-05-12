# src/tools/ack/status_codes.py

"""
Status Codes Module

Defines standardized status codes for ACK/NACK responses and provides
human-readable labels for each code.
"""

from typing import Final, Dict

# === Status code definitions ===

# ✅ Success
STATUS_SUCCESS: Final[int] = 0  
"""Operation completed successfully."""

# ❌ General errors
STATUS_INVALID_PARAMS: Final[int]    = 1  
"""Parameters provided to the command are invalid or malformed."""
STATUS_UNKNOWN_COMMAND: Final[int]    = 2  
"""The specified command ID is not recognized."""
STATUS_EXECUTION_FAILED: Final[int]   = 3  
"""The command failed during execution due to an internal error."""

# ⚙️ System-level restrictions
STATUS_NOT_MASTER: Final[int]         = 10  
"""Operation not allowed because this device is not the master."""
STATUS_MISSING_TELEMETRY: Final[int]  = 11  
"""Required telemetry data is missing or unavailable."""

# ⚠️ Application-level exception
STATUS_EXCEPTION: Final[int]          = 99  
"""A general or unhandled exception occurred."""

# === Mapping to human-readable labels ===
STATUS_LABELS: Final[Dict[int, str]] = {
    STATUS_SUCCESS:         "SUCCESS",
    STATUS_INVALID_PARAMS:  "INVALID_PARAMS",
    STATUS_UNKNOWN_COMMAND: "UNKNOWN_COMMAND",
    STATUS_EXECUTION_FAILED:"EXECUTION_FAILED",
    STATUS_NOT_MASTER:      "NOT_MASTER",
    STATUS_MISSING_TELEMETRY:"MISSING_TELEMETRY",
    STATUS_EXCEPTION:       "EXCEPTION",
}
