# Yeni Metotlar Ekleme: Telemetry Modülü

Bu dökümantasyon, `src/telemetry` klasörü altında yeni telemetri tiplerinin nasıl ekleneceğini adım adım açıklamaktadır. Telemetry modülü, sistemden gelen telemetri verilerinin işlenmesinden ve serileştirilmesinden/deserileştirilmesinden sorumludur.

## Genel Yapı

`src/telemetry` modülü genellikle aşağıdaki alt klasörleri içerir:

*   `definitions/`: Telemetri tanımlamalarını (ID'ler, isimler vb.) içerir.
*   `handler/`: Gelen telemetri verilerini işleyen metotları içerir.
*   `serializer/`: Telemetri verilerini serileştiren/deserileştiren metotları içerir.
*   `tools/`: Telemetri ile ilgili yardımcı araçlar ve fonksiyonlar içerir.

Yeni bir telemetri tipi eklerken, ilgili `handler/impl.py` dosyasına handler metodunu, `serializer/impl.py` dosyasına serileştirme ve deserileştirme metotlarını tanımlamanız ve ardından `definitions.py` dosyasında bu telemetri tipini kaydetmeniz gerekir.

## Adım 1: Metodu `src/telemetry/handler/impl.py` Dosyasına Ekleme

Yeni telemetri handler metodunuzu `src/telemetry/handler/impl.py` dosyasına eklemelisiniz. Bu dosya, telemetri verilerinin ana iş mantığını barındırır.

### Örnek: `src/telemetry/handler/impl.py` dosyasına yeni bir Telemetry handler metodu ekleme

Yeni bir `ENVIRONMENT_DATA` telemetri verisi eklemek istediğinizi varsayalım.

```python
# src/telemetry/handler/impl.py

from src.telemetry.tools.cache import set_device_data
from src.tools.log.logger import logger

def gps(data: dict, src_id: int):
    gps = {
        "lat": data["lat"],
        "lon": data["lon"],
        "alt": data["alt"],
    }
    set_device_data(src_id, "gps", gps)
    logger.debug(f"[TELEMETRY] GPS received from SRC: {src_id}")
    logger.debug(f"[TELEMETRY] → LAT: {gps['lat']:.6f}, LON: {gps['lon']:.6f}, ALT: {gps['alt']:.2f}")

def imu(data: dict, src_id: int):
    imu = {
        "roll": data["roll"],
        "pitch": data["pitch"],
        "yaw": data["yaw"],
    }
    set_device_data(src_id, "imu", imu)
    logger.debug(f"[TELEMETRY] IMU received from SRC: {src_id}")
    logger.debug(f"[TELEMETRY] → Roll: {imu['roll']:.2f}, Pitch: {imu['pitch']:.2f}, Yaw: {imu['yaw']:.2f}")

def battery(data: dict, src_id: int):
    battery = {
        "voltage": data["voltage"],
        "current": data["current"],
        "level": data["level"]
    }
    set_device_data(src_id, "battery", battery)
    logger.debug(f"[TELEMETRY] BATTERY received from SRC: {src_id}")
    logger.debug(f"[TELEMETRY] → V: {battery['voltage']:.2f}V, I: {battery['current']:.2f}A, Level: {battery['level']:.1f}%")

def heartbeat(data: dict, src_id: int):
    hb = {
        "mode": data["mode"],
        "health": data["health"],
        "is_armed": data["is_armed"],
        "gps_fix": data["gps_fix"],
        "sat_count": data["sat_count"]
    }
    set_device_data(src_id, "heartbeat", hb)
    logger.debug(f"[TELEMETRY] HEARTBEAT received from SRC: {src_id}")
    logger.debug(f"[TELEMETRY] → MODE: {hb['mode']}, HEALTH: {hb['health']}, ARMED: {hb['is_armed']}, GPS_FIX: {hb['gps_fix']}, SATS: {hb['sat_count']}")

def unknown(data: dict, src_id: int, tlm_id: int):
    logger.warning(f"[TELEMETRY] Unknown telemetry ID {tlm_id} from SRC: {src_id}")

def environment_data(data: dict, src_id: int):
    env_data = {
        "temperature": data["temp"],
        "humidity": data["hum"],
        "pressure": data["press"]
    }
    set_device_data(src_id, "environment", env_data)
    logger.debug(f"[TELEMETRY] ENVIRONMENT_DATA received from SRC: {src_id}")
    logger.debug(f"[TELEMETRY] → Temp: {env_data['temperature']:.1f}°C, Hum: {env_data['humidity']:.1f}%, Press: {env_data['pressure']:.2f}hPa")
```

## Adım 2: Metodu `src/telemetry/serializer/impl.py` Dosyasına Ekleme

Yeni telemetri tipiniz için verileri serileştirecek ve deserileştirecek metotları `src/telemetry/serializer/impl.py` dosyasına eklemelisiniz.

### Örnek: `src/telemetry/serializer/impl.py` dosyasına yeni serileştirme/deserileştirme metotları ekleme

`ENVIRONMENT_DATA` için serileştirme ve deserileştirme metotları ekleyelim.

```python
# src/telemetry/serializer/impl.py

import struct

# -----------------------------------------------
# TELEMETRY SERIALIZATION FUNCTIONS
# -----------------------------------------------

def serialize_gps(lat: float, lon: float, alt: float) -> bytes:
    return struct.pack(">3f", lat, lon, alt)

def deserialize_gps(data: bytes) -> dict:
    lat, lon, alt = struct.unpack(">3f", data)
    return {"lat": lat, "lon": lon, "alt": alt}

def serialize_imu(roll: float, pitch: float, yaw: float) -> bytes:
    return struct.pack(">3f", roll, pitch, yaw)

def deserialize_imu(data: bytes) -> dict:
    roll, pitch, yaw = struct.unpack(">3f", data)
    return {"roll": roll, "pitch": pitch, "yaw": yaw}

def serialize_battery(voltage: float, current: float, level: float) -> bytes:
    return struct.pack(">3f", voltage, current, level)

def deserialize_battery(data: bytes) -> dict:
    voltage, current, level = struct.unpack(">3f", data)
    return {"voltage": voltage, "current": current, "level": level}

def serialize_heartbeat(mode: str, health: str, is_armed: bool, gps_fix: bool, sat_count: int) -> bytes:
    return (
        mode.encode("utf-8")[:32].ljust(32, b'\x00') +
        health.encode("utf-8")[:32].ljust(32, b'\x00') +
        struct.pack(">??B", is_armed, gps_fix, sat_count)
    )

def deserialize_heartbeat(data: bytes) -> dict:
    mode = data[:32].decode("utf-8").rstrip('\x00')
    health = data[32:64].decode("utf-8").rstrip('\x00')
    is_armed, gps_fix, sat_count = struct.unpack(">??B", data[64:67])
    return {
        "mode": mode,
        "health": health,
        "is_armed": is_armed,
        "gps_fix": gps_fix,
        "sat_count": sat_count
    }

def serialize_environment_data(temperature: float, humidity: float, pressure: float) -> bytes:
    return struct.pack(">fff", temperature, humidity, pressure)

def deserialize_environment_data(data: bytes) -> dict:
    temperature, humidity, pressure = struct.unpack(">fff", data)
    return {"temp": temperature, "hum": humidity, "press": pressure}
```

## Adım 3: Metodu `src/telemetry/definitions.py` Dosyasına Kaydetme

Yeni eklediğiniz telemetri tipinin sistem tarafından tanınabilmesi için, `src/telemetry/definitions.py` dosyasına bir tanım eklemeniz gerekmektedir. Bu tanım, bir ID'yi handler, serileştirme ve deserileştirme metotlarınızla eşleştirir.

### Örnek: `src/telemetry/definitions.py` dosyasını güncelleme

`ENVIRONMENT_DATA` için bir ID tanımlayın ve bunu `telemetry_definitions` sözlüğüne ekleyin.

```python
# src/telemetry/definitions.py

from collections import namedtuple
import src.telemetry.handler.impl as handler
import src.telemetry.serializer.impl as codec

TelemetryDefinition = namedtuple("TelemetryDefinition", ["id", "name", "handler", "serialize", "deserialize"])

telemetry_definitions = {
    0x01: TelemetryDefinition(0x01, "GPS",       handler.gps,       codec.serialize_gps,       codec.deserialize_gps),
    0x02: TelemetryDefinition(0x02, "IMU",       handler.imu,       codec.serialize_imu,       codec.deserialize_imu),
    0x03: TelemetryDefinition(0x03, "BATTERY",   handler.battery,   codec.serialize_battery,   codec.deserialize_battery),
    0x04: TelemetryDefinition(0x04, "HEARTBEAT", handler.heartbeat, codec.serialize_heartbeat, codec.deserialize_heartbeat),
    0x05: TelemetryDefinition(0x05, "ENVIRONMENT_DATA", handler.environment_data, codec.serialize_environment_data, codec.deserialize_environment_data), # Yeni tanım
}
```

## Özet

Yeni bir telemetri tipi eklemek için:

1.  `src/telemetry/handler/impl.py` dosyasına yeni handler fonksiyonunuzu ekleyin.
2.  `src/telemetry/serializer/impl.py` dosyasına yeni serileştirme ve deserileştirme fonksiyonlarınızı ekleyin.
3.  `src/telemetry/definitions.py` dosyasına, yeni telemetri tipinizi bir ID ile eşleştiren bir tanım ekleyin. Bu tanım, handler, serileştirme ve deserileştirme fonksiyonlarınızı içermelidir.