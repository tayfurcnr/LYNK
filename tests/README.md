# LYNK Test Suite

This folder contains the test structure for the **LYNK** project.

## Structure Overview

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

## Example: `test_lynk_integration.py`

This file contains an integration test for the LYNK system. It:
- Sends sample telemetry data from multiple simulated drones
- Dispatches a command (`cmd_takeoff`)
- Processes incoming frames via the LYNK routing system
- Verifies telemetry cache entries and ACK results

You can change the test scenario or add new telemetry types and command types by modifying this script.

## How to Run All Tests

Make sure `pytest` is installed:

```bash
pip install pytest
```

Run tests from the project root:

```bash
pytest tests/
```

Run a specific test file:

```bash
pytest tests/integration/test_lynk_integration.py
```

## Output

By default, `pytest` will show output as `PASSED`, `FAILED`, or `SKIPPED` for each test function.
You can add `print()` statements in test files to observe telemetry content or ACK responses.

---

For advanced usage, you can install `pytest` plugins like `pytest-cov` for coverage or `pytest-xdist` for parallel test runs.
