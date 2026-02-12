# LYNK Examples Library

Bu klasör, LYNK sistemini bir kütüphane gibi kullanarak uygulamanıza nasıl entegre edebileceğinizi gösteren çalışabilir kod örnekleri içerir.

## Dizin Yapısı

```
examples/
├── telemetry/
│   └── basic_flow.py      # Telemetri gönderme (GPS, Battery)
├── command/
│   └── vehicle_control.py # Komut gönderme (Arm, Takeoff)
└── event/
    ├── system_events.py   # Sistem olayları (Battery Low)
    └── custom_events.py   # Özel olaylar (Custom Event)
```

## Nasıl Çalıştırılır?

Proje kök dizininde olduğunuzdan emin olun ve scriptleri çağırın:

```bash
# Telemetri Örneği
python3 examples/telemetry/basic_flow.py

# Komut Örneği
python3 examples/command/vehicle_control.py

# Olay Sistemi Örneği
python3 examples/event/system_events.py
```

## İçerik Detayları

### Telemetri (`telemetry/basic_flow.py`)
Araçtan yer istasyonuna veya ağdaki diğer düğümlere periyodik veri göndermeyi gösterir.
- **Kullanılanlar:** `send_tlm_battery`, `send_tlm_gps`, `send_tlm_heartbeat`.

### Komut (`command/vehicle_control.py`)
Bir Yer İstasyonu (GCS) gibi davranarak araca komut göndermeyi gösterir.
- **Kullanılanlar:** `cmd_flight_arming`, `cmd_flight_takeoff`, `cmd_flight_land`.

### Olaylar (`event/`)
- **`system_events.py`**: Kritik durumları bildirmek için tanımlı sistem olaylarını (BATTERY_LOW, GPS_DEGRADED) kullanmayı gösterir.
- **`custom_events.py`**: Protokolde tanımlı olmayan, uygulamaya özel durumları bildirmek için esnek yapı (EVENT_CUSTOM).
