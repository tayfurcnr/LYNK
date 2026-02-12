# LYNK Sistemi Kullanım Kılavuzu

Bu belge, LYNK kütüphanesini nasıl kuracağınızı, kullanacağınızı ve temel özellikleri nasıl test edeceğinizi anlatır.

## 1. Kurulum (Installation)

### Paketi Tanıtma
Proje kök dizininde aşağıdaki komutu çalıştırarak `lynk` paketini "editable" modda kurun:

```bash
pip install -e .
```

### Protobuf Derleme
Mesaj tanımlarını Python koduna çevirmek için:

```bash
python3 setup.py protos
```

## 2. Temiz Kullanım (Simplified API)

Artık tüm işlemleri tek bir satırla yapabilirsiniz:

```python
import lynk

# 1. Konfigürasyonu yükle
lynk.config.load_config("configs/config.yaml")

# 2. Bağlantı arayüzünü oluştur
interface = lynk.create_interface()

# 3. Hazırsınız!
```

## 3. Komut Gönderimi (Commands)

```python
# 10 metreye kalkış komutu
lynk.command.cmd_flight_takeoff(interface, altitude_m=10.0, dst=1)
```

## 4. Telemetri Gönderimi (Telemetry)

```python
# Batarya bilgisi gönder
lynk.telemetry.send_tlm_battery(interface, voltage=12.6, level=98.0, dst=1)
```

## 5. MAVLink Tünelleme (Tunneling)

Farklı sistemleri LYNK mesh ağı üzerinden konuşturmak için ham MAVLink paketleri taşıyabilirsiniz:

```python
raw_mavlink = b"\xFD\x09..." # Ham MAVLink baytları
lynk.mavlink.send_mavlink(interface, raw_mavlink, dst=2)
```

## 6. Dinleme ve Olaylar (Events & Callbacks)

Gelen MAVLink paketlerini yakalamak için:

```python
def on_msg(payload, meta, frame):
    print(f"Gelen mesaj: {payload}")

lynk.mavlink.on_mavlink_received(on_msg)
```

---
> [!NOTE]
> Daha fazla örnek için `examples/` klasöründeki dosyaları inceleyebilirsiniz.
