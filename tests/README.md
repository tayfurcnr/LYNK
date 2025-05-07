# LYNK Test Suite

This folder contains the test structure for the **LYNK** project.

---

## 📁 Structure Overview

Tests are organized by feature/module and are placed under their respective subfolders:

```
tests/
├── ack/
│   └── test_ack_multithread.py       # Tests multi-threaded ACK handling
├── command/
├── telemetry/
├── swarm/
├── comm/
├── integration/
│   └── test_lynk_integration.py      # End-to-end system test using telemetry and commands
└── core/
```

---

## 🧪 Example: `test_lynk_integration.py`

This file contains an integration test for the LYNK system. It:
- Sends sample telemetry data from multiple simulated drones
- Dispatches a command (`cmd_takeoff`)
- Processes incoming frames via the LYNK routing system
- Verifies telemetry cache entries and ACK results

You can change the test scenario or add new telemetry/command types by modifying this script.

---

## ⚙️ How to Run Tests

First, make sure `pytest` is installed:

```bash
pip install pytest
```

Run **all tests** from the project root:

```bash
pytest tests/
```

Run a **specific test file**:

```bash
pytest tests/integration/test_lynk_integration.py
```

---

## 🖨️ Show Print Output

By default, `pytest` captures all `print()` outputs.  
To **see print statements live**, add the `-s` flag:

```bash
pytest -s tests/integration/test_lynk_integration.py
```

Or combine with verbose output:

```bash
pytest -s -v tests/
```

---

## 🎛️ Other Useful Options

- `-v`: Verbose mode (shows each test function name)
- `-k "keyword"`: Run only tests that match the keyword
- `--maxfail=1`: Stop after the first failure
- `--tb=short`: Shorter traceback output

Example:

```bash
pytest -k "takeoff" --maxfail=1 --tb=short
```

---

## 🧠 Tips

- Each subfolder includes an `__init__.py` to ensure modular test discovery.
- Use `MockUARTHandler` or other mock interfaces to simulate environments.
- Log files are created in `logs/system.log` for review if `logger` is enabled.

---
