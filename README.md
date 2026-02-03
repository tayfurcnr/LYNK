<p align="center">
  <img src="docs/logo-v2.png" alt="LYNK Logo" width="1200"/>
</p>

# 🧠 LYNK – Layered Your-Node Kernel

**LYNK** is a modular and layered communication kernel designed for autonomous systems and multi-drone networks. It provides low-latency, reliable, and scalable communication between nodes using a handler-based infrastructure. LYNK supports multiple communication types such as UART, UDP, and simulated MOCK interfaces, making it suitable for both hardware deployment and testing environments.

---

## 🚀 Key Features

- 📡 **Communication Types:** UART, UDP, MOCK (for testing)
- 🧠 **Protocol Logic:** Start/terminal bytes, versioning, and structured device addressing
- 🛡️ **Fleet Management:** Multi-team support with Team ID filtering and "Solo" mode
- 📦 **Message Types:** Command, Telemetry, ACK/NACK, and Swarm messages
- 🧱 **Modular Design:** Handler-Serializer-Tool architecture for easy extensibility
- 🧪 **Testable:** Fully compatible with `pytest`, supporting mock-based tests

---

## 📁 Project Structure

```plaintext
lynk-root/
├── configs/                  # Vehicle and team configurations
│   ├── config.yaml           # Master / Default config
│   ├── node_1/               # Node 1 specific settings
│   └── ...
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
├── docs/                     # Technical reports and diagrams
├── logs/                     # Log files (system.log)
│
├── src/                      # 🧠 LYNK Core Kernel
│   ├── core/                 # Frame routing and encoding
│   ├── application/          # ACK, Command, Telemetry modules
│   └── shared/               # Interfaces (UDP/UART), config, and logging
│
├── main.py                   # 🧪 Node Emulator & CLI Test Tool
└── tests/                    # 🏁 Automated Pytest Suite (Modular)
```

---

## ⚙️ Installation

```bash
git clone https://github.com/tayfurcnr/LYNK.git
cd lynk-root
pip install -r requirements.txt
```

---

## 🛡️ Fleet Management & Team Logic

LYNK implements a sophisticated filtering and routing system based on **Team IDs** and **Vehicle IDs**.

### Team Categorization:
- 🔵 **Team 1 / 🟢 Team 2**: Standard mission teams. Nodes in these teams ignore all traffic from other teams to reduce network noise.
- ⚪ **Solo Mode (Team 0)**: Nodes assigned to Team 0 act as independent agents. They ignore multi-team traffic but remain part of the global command chain.

### Communication Rules:
1. **Intra-Team**: Standard telemetry and commands are routed within the same Team ID.
2. **Global (Broadcast)**: Frames sent with **Team ID 0** are treated as "Global" and are accepted by **all nodes** regardless of their own Team ID.
3. **Targeted**: Commands can be sent to specific `dst_id` values. If the Team ID matches or is 0, the node processes the command.

### Dynamic Reconfiguration:
You can change a node's identity at runtime using keyboard shortcuts in `main.py`:
- `I`: Toggle **Vehicle ID** (e.g., between 5 and 10).
- `E`: Toggle **Team ID** (Cycle: Team 1 → Team 2 → SOLO 0).

---

## 🧪 Testing with Node Emulator

Since `main.py` is a test emulator, you can use it to simulate nodes:

Update the `config.yaml` file in the `configs/` directory to select the interface type:

```yaml
interface:
  comm_type: "UDP"  # or "UART", "MOCK_UART"
```

To run a simulated node:

```bash
# Using default configs/config.yaml
python3 main.py

# Using a specific node config
python3 main.py --config configs/node_1/config.yaml
```

---

## 🏁 Automated Tests

Run all tests with:

```bash
pytest tests/
```

Each test submodule is fully independent and can be run standalone. For example:

```bash
pytest tests/ack/test_ack_multithread.py
```

---

## 🧠 Developer Guide

- To **add a new frame type**:
  - Create a serializer in `src/application/<frame_type>/serializer/`
  - Implement a handler in `src/application/<frame_type>/handler/`
  - Register the handler in `src/core/frame_router.py`
- **Dynamic ID Management**: Use `src.shared.config.manager.get_config()` to update `id` or `team_id` at runtime. The `FrameRouter` and Transmitter always pull the latest values from this shared config.
- Use `src/shared/comm/mock_handler.py` for local testing
- Use `src/shared/log/logger.py` to log all frame activity to `logs/system.log`

---

## 🤝 Contributing

1. Fork the repository
2. Create a new feature branch
3. Add your changes and tests
4. Make sure all tests pass with `pytest`
5. Submit a Pull Request (PR)

We recommend formatting your code with [`black`](https://black.readthedocs.io/) before committing.
