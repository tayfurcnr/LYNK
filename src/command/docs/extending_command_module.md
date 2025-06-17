# Yeni Metotlar Ekleme: Command Modülü

Bu dökümantasyon, `src/command` klasörü altında yeni metotların nasıl ekleneceğini adım adım açıklamaktadır. Command modülü, sisteme gönderilen komutların işlenmesinden sorumludur.

## Genel Yapı

`src/command` modülü genellikle aşağıdaki alt klasörleri içerir:

*   `definitions/`: Komut tanımlamalarını (ID'ler, isimler vb.) içerir.
*   `handler/`: Gelen komutları işleyen metotları içerir.
*   `serializer/`: Komutları serileştiren/deserileştiren metotları içerir.
*   `tools/`: Komutlarla ilgili yardımcı araçlar ve fonksiyonlar içerir.

Yeni bir komut metodu eklerken, genellikle ilgili `impl.py` dosyasına metodu tanımlamanız ve ardından `definitions.py` dosyasında bu metodu kaydetmeniz gerekir.

## Adım 1: Metodu `src/command/handler/impl.py` Dosyasına Ekleme

Yeni komut handler metodunuzu `src/command/handler/impl.py` dosyasına eklemelisiniz. Bu dosya, komutların ana iş mantığını barındırır.

### Örnek: `src/command/handler/impl.py` dosyasına yeni bir Command handler metodu ekleme

Yeni bir `SET_HOME` komutu eklemek istediğinizi varsayalım.

```python
# src/command/handler/impl.py

from src.tools.log.logger import logger
from src.ack.tools.dispatcher import send_ack_ok, send_ack_error, send_ack_invalid_cmd
import struct

def reboot(cmd_id, params, src_id, interface):
    logger.info("[COMMAND] SENT | CMD: REBOOT")
    send_ack_ok(interface, "Command executed successfully", dst=src_id)

def set_mode(cmd_id, params, src_id, interface):
    if params:
        mode = params[0]
        logger.info(f"[COMMAND] SENT | CMD: SET_MODE | MODE: {mode}")
        send_ack_ok(interface, f"Mode set to {mode}", dst=src_id)
    else:
        logger.warning("[COMMAND] INVALID PARAMS | CMD: SET_MODE")
        send_ack_invalid_cmd(interface, "Missing mode parameter for SET_MODE", dst=src_id)

def takeoff(cmd_id, params, src_id, interface):
    if len(params) == 4:
        alt = struct.unpack(">f", params)[0]
        logger.info(f"[COMMAND] SENT | CMD: TAKEOFF | ALT: {alt:.2f} m")
        send_ack_ok(interface, f"Takeoff initiated to {alt:.2f}m", dst=src_id)
    elif len(params) == 16:
        alt, lat, lon, target_alt = struct.unpack(">ffff", params)
        logger.info(f"[COMMAND] SENT | CMD: TAKEOFF | ALT: {alt:.2f} m | TARGET: {lat:.6f}, {lon:.6f}, {target_alt:.2f} m")
        send_ack_ok(interface, f"Takeoff initiated to {alt:.2f}m, target {lat:.6f}, {lon:.6f}, {target_alt:.2f}m", dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: TAKEOFF | PRM LEN: {len(params)}")
        send_ack_invalid_cmd(interface, f"Invalid parameters for TAKEOFF. Expected 4 or 16 bytes, got {len(params)}", dst=src_id)

def landing(cmd_id, params, src_id, interface):
    if len(params) == 0:
        logger.info("[COMMAND] SENT | CMD: LANDING | MODE: LOCAL")
        send_ack_ok(interface, "Landing initiated (local)", dst=src_id)
    elif len(params) == 8:
        lat, lon = struct.unpack(">ff", params)
        logger.info(f"[COMMAND] SENT | CMD: LANDING | TARGET: LAT={lat:.6f}, LON={lon:.6f}")
        send_ack_ok(interface, f"Landing initiated to target {lat:.6f}, {lon:.6f}", dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: LANDING | PRM LEN: {len(params)}")
        send_ack_invalid_cmd(interface, f"Invalid parameters for LANDING. Expected 0 or 8 bytes, got {len(params)}", dst=src_id)

def gimbal(cmd_id, params, src_id, interface):
    if len(params) == 12:
        yaw, pitch, roll = struct.unpack(">fff", params)
        logger.info(f"[COMMAND] SENT | CMD: GIMBAL_CTRL | YAW: {yaw}, PITCH: {pitch}, ROLL: {roll}")
        send_ack_ok(interface, f"Gimbal control set to YAW: {yaw}, PITCH: {pitch}, ROLL: {roll}", dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: GIMBAL_CTRL | PRM LEN: {len(params)}")
        send_ack_invalid_cmd(interface, f"Invalid parameters for GIMBAL_CTRL. Expected 12 bytes, got {len(params)}", dst=src_id)

def goto(cmd_id, params, src_id, interface):
    if len(params) == 12:
        lat, lon, alt = struct.unpack(">fff", params)
        logger.info(f"[COMMAND] SENT | CMD: GOTO | TARGET: LAT={lat}, LON={lon}, ALT={alt}")
        send_ack_ok(interface, f"GoTo command issued to LAT={lat}, LON={lon}, ALT={alt}", dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: GOTO | PRM LEN: {len(params)}")
        send_ack_invalid_cmd(interface, f"Invalid parameters for GOTO. Expected 12 bytes, got {len(params)}", dst=src_id)

def follow_me(cmd_id, params, src_id, interface):
    if len(params) == 8:
        target_id, alt = struct.unpack(">if", params)
        logger.info(f"[COMMAND] SENT | CMD: FOLLOW_ME | TARGET: {target_id} | ALT: {alt}")
        send_ack_ok(interface, f"Follow Me command issued for target {target_id} at ALT: {alt}", dst=src_id)
    elif len(params) == 4:
        target_id, = struct.unpack(">i", params)
        logger.info(f"[COMMAND] SENT | CMD: FOLLOW_ME | TARGET: {target_id}")
        send_ack_ok(interface, f"Follow Me command issued for target {target_id}", dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FOLLOW_ME | PRM LEN: {len(params)}")
        send_ack_invalid_cmd(interface, f"Invalid parameters for FOLLOW_ME. Expected 4 or 8 bytes, got {len(params)}", dst=src_id)

def waypoints(cmd_id, params, src_id, interface):
    if len(params) >= 12:
        waypoints = []
        for i in range(0, len(params), 12):
            lat, lon, alt = struct.unpack(">fff", params[i:i+12])
            waypoints.append((lat, lon, alt))
        logger.info(f"[COMMAND] SENT | CMD: WAYPOINTS | COUNT: {len(waypoints)} | DATA: {waypoints}")
        send_ack_ok(interface, f"Waypoints command issued with {len(waypoints)} waypoints", dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: WAYPOINTS | PRM LEN: {len(params)}")
        send_ack_invalid_cmd(interface, f"Invalid parameters for WAYPOINTS. Expected multiple of 12 bytes, got {len(params)}", dst=src_id)

def set_home(cmd_id, params, src_id, interface):
    if len(params) == 8:
        lat, lon = struct.unpack(">ff", params)
        logger.info(f"[COMMAND] SENT | CMD: SET_HOME | LAT: {lat:.6f}, LON: {lon:.6f}")
        send_ack_ok(interface, f"Home location set to LAT={lat:.6f}, LON={lon:.6f}", dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: SET_HOME | PRM LEN: {len(params)}")
        send_ack_invalid_cmd(interface, f"Invalid parameters for SET_HOME. Expected 8 bytes, got {len(params)}", dst=src_id)
```

## Adım 2: Metodu `src/command/definitions.py` Dosyasına Kaydetme

Yeni eklediğiniz komut metodunun sistem tarafından tanınabilmesi için, `src/command/definitions.py` dosyasına bir tanım eklemeniz gerekmektedir. Bu tanım, genellikle bir ID'yi metodunuzla eşleştirir.

### Örnek: `src/command/definitions.py` dosyasını güncelleme

`SET_HOME` için bir ID tanımlayın ve bunu `command_definitions` sözlüğüne ekleyin.

```python
# src/command/definitions.py

from dataclasses import dataclass
import src.command.handler.impl as command_handler

@dataclass
class CommandDefinition:
    id: int
    name: str
    handler: callable

CMD_REBOOT = 0x00
CMD_SET_MODE = 0x01
CMD_TAKEOFF = 0x02
CMD_LANDING = 0x03
CMD_GIMBAL_CTRL = 0x04
CMD_GOTO = 0x05
CMD_FOLLOW_ME = 0x06
CMD_WAYPOINTS = 0x07
CMD_SET_HOME = 0x08 # Yeni Command ID'si

command_definitions = {
    CMD_REBOOT: CommandDefinition(CMD_REBOOT, "REBOOT", command_handler.reboot),
    CMD_SET_MODE: CommandDefinition(CMD_SET_MODE, "SET_MODE", command_handler.set_mode),
    CMD_TAKEOFF: CommandDefinition(CMD_TAKEOFF, "TAKEOFF", command_handler.takeoff),
    CMD_LANDING: CommandDefinition(CMD_LANDING, "LANDING", command_handler.landing),
    CMD_GIMBAL_CTRL: CommandDefinition(CMD_GIMBAL_CTRL, "GIMBAL_CTRL", command_handler.gimbal),
    CMD_GOTO: CommandDefinition(CMD_GOTO, "GOTO", command_handler.goto),
    CMD_FOLLOW_ME: CommandDefinition(CMD_FOLLOW_ME, "FOLLOW_ME", command_handler.follow_me),
    CMD_WAYPOINTS: CommandDefinition(CMD_WAYPOINTS, "WAYPOINTS", command_handler.waypoints),
    CMD_SET_HOME: CommandDefinition(CMD_SET_HOME, "SET_HOME", command_handler.set_home), # Yeni tanım
}
```

## Özet

Yeni bir komut metodu eklemek için:

1.  `src/command/handler/impl.py` dosyasına yeni fonksiyonunuzu ekleyin.
2.  `src/command/definitions.py` dosyasına, yeni fonksiyonunuzu bir ID ile eşleştiren bir tanım ekleyin. Bu, sistemin gelen komutları doğru fonksiyona yönlendirmesini sağlar.