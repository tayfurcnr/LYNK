# src/tools/ack/status_codes.py

# ✅ Successful operation
STATUS_SUCCESS = 0  # The command was executed successfully.

# ❌ General error codes
STATUS_INVALID_PARAMS = 1        # The provided parameters are invalid or malformed.
STATUS_UNKNOWN_COMMAND = 2       # The command ID is not recognized.
STATUS_EXECUTION_FAILED = 3      # The command failed during execution due to an internal error.

# ⚙️ System-related status codes
STATUS_NOT_MASTER = 10           # Operation is not allowed because the device is not the master.
STATUS_MISSING_TELEMETRY = 11    # Required telemetry data is missing or unavailable.

# ⚠️ Application-level exceptions
STATUS_EXCEPTION = 99            # A general exception or unhandled error occurred.

# 🏷️ Optional: Human-readable labels for status codes
STATUS_LABELS = {
    0:  "SUCCESS",
    1:  "INVALID_PARAMS",
    2:  "UNKNOWN_COMMAND",
    3:  "EXECUTION_FAILED",
    10: "NOT_MASTER",
    11: "MISSING_TELEMETRY",
    99: "EXCEPTION"
}
