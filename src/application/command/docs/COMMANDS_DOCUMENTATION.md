# LYNK Komut Dokümantasyonu

Bu belge, LYNK sistemi tarafından desteklenen komutları listeler, nasıl kullanılacaklarını açıklar ve sisteme yeni komutların nasıl ekleneceğine dair rehberlik sağlar.

## LYNK Mesaj Yapısı

LYNK sistemi, cihazlar arası iletişimi belirli bir çerçeve (frame) yapısı üzerinden gerçekleştirir. Her komut, bu genel mesaj yapısının "payload" (veri yükü) kısmında taşınır. Mesaj çerçevesi, `src/core/frame_codec.py` dosyasında tanımlanmıştır ve aşağıdaki genel formata sahiptir:

```
[Başlangıç Byte 1][Başlangıç Byte 2][Versiyon][Çerçeve Tipi][Kaynak ID][Hedef ID][Payload Uzunluğu][Payload...][CRC-16]
```

Bir komutun `Payload` içindeki yapısı ise genellikle **Komut ID'si (1 byte)** ve ardından gelen **parametrelerden** oluşur. Parametrelerin nasıl paketlendiği `src/application/command/tools/builder.py` dosyasında, nasıl çözüldüğü ise `src/application/command/handler/impl.py` dosyasında tanımlanır.

---

## Komut Listesi ve Detayları

Aşağıda, sistemde tanımlı olan komutlar, kimlikleri (ID), aldıkları parametreler ve açıklamaları bulunmaktadır. Parametreler, komutun payload'ı içinde nasıl kodlandığını gösterir.

| Komut ID | Komut Adı | Parametreler (Kodlama) | Açıklama |
|----------|--------------------|----------------------------------------------------------------|------------------------------------------------------------------------------|
| `0x01` | `REBOOT` | Yok | Hedef sistemi yeniden başlatır. |
| `0x02` | `SET_MODE` | `mode` (UTF-8 String) | Aracın uçuş modunu ayarlar (örn: "GUIDED", "LAND"). |
| `0x03` | `TAKEOFF` | `takeoff_alt` (float32) | Aracın belirtilen irtifaya kalkış yapmasını sağlar. |
| `0x04` | `LANDING` | Yok | Aracın mevcut pozisyonuna iniş yapmasını sağlar. |
| `0x06` | `GOTO` | `lat, lon, alt` (float32) | Aracı belirtilen global koordinatlara yönlendirir. |
| `0x0B` | `SET_SPEED` | `speed` (float32) | Aracın yer hızını (m/s) ayarlar. |
| `0x0C` | `SET_DIRECTION` | `direction` (float32) | Aracın yönünü (yaw) derece cinsinden ayarlar. |
| `0x0D` | `SET_DRONE_ID` | `drone_id` (uint32) | Aracın kimlik numarasını (ID) kalıcı olarak değiştirir. |
| `0x0E` | `SWARM_FORMATER` | `formation` (UTF-8 String) | Sürü için formasyon tipini belirler (örn: "line"). |
| `0x0F` | `SWARM_LEADER` | `leader_id` (uint32) | Sürü liderinin ID'sini atar. |
| `0x11` | `SET_MISSION_STATUS`| `status` (UTF-8 String) | Görev durumunu ayarlar (örn: "PAUSE", "RESUME"). |
| `0x15` | `STREAM_VIDEO` | `status` (bool/uint8) | Video akışını başlatır (`1`) veya durdurur (`0`). |
| `0x16` | `ARM_DISARM` | `arm` (bool/uint8) | Aracı arm (`1`) veya disarm (`0`) eder. |
| `0x29` | `MISSION_UPLOAD` | JSON String | Görev planı/waypoint listesini yükler. |
| `0x2A` | `MISSION_CONTROL` | JSON String | Görev yürütme durumunu kontrol eder (START, PAUSE, RESUME, ABORT). |

### Kullanım Örnekleri (Python)

Bu örnekler, `src.application.command.tools.dispatcher` modülündeki fonksiyonların nasıl kullanılacağını gösterir. `interface` objesi, donanım haberleşmesini sağlayan bir nesnedir.

```python
import src.application.command.tools.dispatcher as cmd

# Örnek bir interface ve ID'ler
# interface = ...
MY_SRC_ID = 1
OTHER_DST_ID = 2

# REBOOT
cmd.cmd_reboot(interface, dst=OTHER_DST_ID, src=MY_SRC_ID)

# SET_MODE
cmd.cmd_set_mode(interface, mode="GUIDED", dst=OTHER_DST_ID, src=MY_SRC_ID)

# ARM_DISARM (Arm)
cmd.cmd_arm_disarm(interface, arm=True, dst=OTHER_DST_ID, src=MY_SRC_ID)

# TAKEOFF
cmd.cmd_takeoff(interface, takeoff_alt=10.0, dst=OTHER_DST_ID, src=MY_SRC_ID)

# SET_SPEED
cmd.cmd_set_speed(interface, speed=15.0, dst=OTHER_DST_ID, src=MY_SRC_ID)

# GOTO
cmd.cmd_goto(interface, target_lat=37.001, target_lon=35.002, target_alt=20.0, dst=OTHER_DST_ID, src=MY_SRC_ID)

# SET_DIRECTION
cmd.cmd_set_direction(interface, direction=90.0, dst=OTHER_DST_ID, src=MY_SRC_ID)

# LANDING
cmd.cmd_landing(interface, dst=OTHER_DST_ID, src=MY_SRC_ID)

# ARM_DISARM (Disarm)
cmd.cmd_arm_disarm(interface, arm=False, dst=OTHER_DST_ID, src=MY_SRC_ID)

# SET_DRONE_ID (Yeni ID: 5)
cmd.cmd_set_drone_id(interface, drone_id=5, dst=OTHER_DST_ID, src=MY_SRC_ID)

# STREAM_VIDEO (Başlat)
cmd.cmd_stream_video(interface, status=True, dst=OTHER_DST_ID, src=MY_SRC_ID)

# MISSION_UPLOAD
waypoints_example = [
    {"seq": 0, "command": "TAKEOFF", "lat": 0.0, "lon": 0.0, "alt": 10.0},
    {"seq": 1, "command": "WAYPOINT", "lat": 37.001, "lon": 35.002, "alt": 20.0, "hold_time": 5.0},
    {"seq": 2, "command": "LAND", "lat": 37.001, "lon": 35.002, "alt": 0.0}
]
cmd.cmd_mission_upload(interface, mission_id=101, waypoints=waypoints_example, dst=OTHER_DST_ID, src=MY_SRC_ID)

# MISSION_CONTROL (Start)
cmd.cmd_mission_control(interface, action="START", start_index=0, dst=OTHER_DST_ID, src=MY_SRC_ID)

# MISSION_CONTROL (Abort)
cmd.cmd_mission_control(interface, action="ABORT", abort_mode="RTL", dst=OTHER_DST_ID, src=MY_SRC_ID)

```

---

## Yeni Komut Ekleme

LYNK sistemine yeni bir komut eklemek için 4 ana adım bulunmaktadır. Örnek olarak `SET_HOME` adında, `lat` ve `lon` parametreleri alan yeni bir komut ekleyelim.

### Adım 1: Komut Tanımı (`definitions.py`)

`src/application/command/definitions.py` dosyasında `command_definitions` sözlüğüne yeni komutunuzu ekleyin. Benzersiz bir ID seçtiğinizden emin olun.

```python
# src/application/command/definitions.py

import src.application.command.handler.impl as handler

# ... (diğer tanımlar)

command_definitions = {
    # ... (mevcut komutlar)
    0x16: CommandDefinition(0x16, "ARM_DISARM",  handler.arm_disarm),
    
    # Yeni komutumuz
    0x17: CommandDefinition(0x17, "SET_HOME", handler.set_home),
}
```

### Adım 2: Komut İşleyici (`handler/impl.py`)

`src/application/command/handler/impl.py` dosyasında yeni komutunuz için bir işleyici (handler) fonksiyonu oluşturun. Bu fonksiyon, gelen ham `params` byte dizisini çözer, ilgili işlemi yapar ve komut bilgilerini `set_last_command` ile önbelleğe kaydeder. Önbelleğe kaydetme, komutun ROS tarafında doğru şekilde işlenmesi için kritik öneme sahiptir.

```python
# src/application/command/handler/impl.py

import struct
from src.shared.log.logger import logger
from src.application.ack.tools.dispatcher import send_ack_ok, send_ack_invalid_cmd
from src.application.command.tools.cache import set_last_command

# ... (diğer handler'lar)

def set_home(cmd_id, params, src_id, interface):
    # Parametrelerin 8 byte (2 x float) olup olmadığını kontrol et
    if len(params) == 8:
        # ">ff" formatıyla byte'ları iki float değere çöz
        lat, lon = struct.unpack(">ff", params)
        
        # ROS tarafında kullanılacak olan çözülmüş parametreleri bir sözlük yap
        parsed = {"lat": lat, "lon": lon}
        
        # Logla ve önbelleğe al
        logger.info(f"[COMMAND] SENT | CMD: SET_HOME | LAT: {lat:.6f}, LON: {lon:.6f}")
        set_last_command(cmd_id, params, parsed)
        
        # Göndericiye OK onayı gönder
        send_ack_ok(interface, f"Home location set to LAT={lat:.6f}, LON={lon:.6f}", dst=src_id)
    else:
        # Hatalı parametre durumunda uyarı ver ve INVALID_CMD onayı gönder
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: SET_HOME | PRM LEN: {len(params)}")
        send_ack_invalid_cmd(interface, f"Invalid parameters for SET_HOME. Expected 8 bytes, got {len(params)}", dst=src_id)

```

### Adım 3: Komut Oluşturucu (`tools/builder.py`)

Komutu gönderecek tarafın işini kolaylaştırmak için `src/application/command/tools/builder.py` dosyasına bir "builder" fonksiyonu ekleyin. Bu fonksiyon, parametreleri alır ve onları paketleyerek tam bir komut çerçevesi (frame) oluşturur.

```python
# src/application/command/tools/builder.py

import struct
from typing import Optional

# ... (diğer builder'lar)

def build_cmd_set_home(
    lat: float,
    lon: float,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> bytes:
    """
    Build a SET_HOME command frame.
    """
    # Parametreleri ">ff" formatıyla byte dizisine paketle
    params = struct.pack(">ff", lat, lon)
    # 0x17 ID'si ile genel komut çerçevesini oluştur
    return build_cmd_frame(0x17, params, dst, src)
```

### Adım 4: Komut Gönderici (`tools/dispatcher.py`)

Son olarak, `src/application/command/tools/dispatcher.py` dosyasına, az önce yazdığınız builder'ı çağıran ve komutu arayüze gönderen yüksek seviye bir "dispatcher" fonksiyonu ekleyin.

```python
# src/application/command/tools/dispatcher.py

from src.application.command.tools.builder import (
    # ...
    build_cmd_set_home  # Yeni builder'ı import et
)
from src.shared.comm.transmitter import send_frame
from src.shared.log.logger import logger

# ... (diğer dispatcher'lar)

def cmd_set_home(
    interface: SendableInterface,
    lat: float,
    lon: float,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    """
    Send a SET_HOME command.
    """
    # Builder ile komut çerçevesini oluştur
    frame = build_cmd_set_home(lat, lon, dst, src)
    # Çerçeveyi gönder
    send_frame(interface, frame)
    # Bilgilendirme logu at
    logger.info(f"[COMMAND] SENT | SET_HOME(lat={lat:.6f}, lon={lon:.6f}) -> DST: {dst}")

```

Bu dört adımı tamamladıktan sonra, `SET_HOME` komutunuz sistemin her yerinden `cmd_set_home(...)` fonksiyonu çağrılarak kullanılabilir ve alıcı cihaz tarafından doğru bir şekilde işlenebilir hale gelir.
