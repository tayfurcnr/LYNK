# Command Extension Guide

## Command Categories

The LYNK toolkit categorizes commands into four main functional areas:
- **System** (IDs 1-10): Basic node management (Reboot, ID settings).
- **Flight** (IDs 21-40): Vehicle control (Mode, Arming, Takeoff, Goto, Land).
- **Mission** (IDs 41-60): Autonomous operations (Upload, Control).
- **Swarm** (IDs 61-80): Multi-agent coordination (Formation, Leader, Spacing).

## Adding a New Command

LYNK uses a **schema-first** approach. The system automatically handles serialization, dispatching, and discovery based on your Protobuf definitions.

### 1. Define the Protobuf Message

Create a new `.proto` file in `msg/command/`.

**Example: `msg/command/camera_capture.proto`**
```protobuf
syntax = "proto3";
package lynk.command;

message CameraCapture {
  uint32 camera_id = 1;
  bool video_mode = 2;
  uint32 duration_sec = 3;
}
```

### 2. Register in the Envelope

Update `msg/command/command_envelope.proto` to include your new message in the `oneof payload`.

**`msg/command/command_envelope.proto`:**
```protobuf
import "msg/command/camera_capture.proto";

message CommandEnvelope {
  uint32 cmd_id = 255;
  
  oneof payload {
    // ... existing commands
    CameraCapture camera_capture = 71;  // Assign a unique ID (tag)
  }
}
```

### 3. Compile Protobufs

Run the setup script to generate the Python classes:
```bash
python3 setup.py protos
```

### 4. Implement the Handler (Optional)

Handlers react to incoming commands. If you need special logic, create a function in `lynk/application/command/handler/impl.py`.

**Note**: If you skip this step, the system will use a **Default Bridge Handler** that automatically:
- ✅ Acknowledges the command (`send_ack_success`).
- ✅ Logs the data for bridge forwarding.
- ✅ Prepares it for ROS integration.

**Example `lynk/application/command/handler/impl.py` (if custom logic is needed):**
```python
def camera_capture(cmd_id, params, src_id, interface):
    # This overrides the default bridge handler
```

### 5. Send the Command (Automatic!)

You can now use the generic `send_command` function. It uses introspection to find the schema by name.

```python
import lynk.application.command.tools.dispatcher as cmd

# Automatic parameter mapping and validation
cmd.send_command(
    interface, 
    "CAMERA_CAPTURE", 
    camera_id=1, 
    video_mode=True, 
    duration_sec=10,
    dst=0x12 # Target Node ID
)
```

## Advanced Features

### Type-Safe Senders
For IDE autocompletion and strict typing, you can add a specialized wrapper in `tools/dispatcher.py`:

```python
def send_cmd_camera_capture(interface, camera_id: int, dst: int):
    # Uses the generic builder under the hood
    frame = build_cmd_frame("CAMERA_CAPTURE", {"camera_id": camera_id}, dst)
    send_frame(interface, frame)
```

## Best Practices

- **ID Conflicts**: Ensure the tag numbers in `CommandEnvelope` are unique.
- **Handler Naming**: The handler function name **must** match the field name in the Protobuf envelope (snake_case).
- **ACKs**: Always send an ACK back to the source to confirm execution.
- **Validation**: Validate parameters inside the handler before taking physical actions.
