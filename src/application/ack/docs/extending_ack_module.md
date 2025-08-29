# Yeni Metotlar Ekleme: ACK Modülü

Bu dökümantasyon, `src/ack` klasörü altında yeni metotların nasıl ekleneceğini adım adım açıklamaktadır. ACK modülü, sistemdeki onay (acknowledgement) mesajlarının işlenmesinden sorumludur.

## Genel Yapı

`src/ack` modülü genellikle aşağıdaki alt klasörleri içerir:

*   `definitions/`: ACK tanımlamalarını (ID'ler, isimler vb.) içerir.
*   `handler/`: Gelen ACK mesajlarını işleyen metotları içerir.
*   `serializer/`: ACK mesajlarını serileştiren/deserileştiren metotları içerir.
*   `tools/`: ACK ile ilgili yardımcı araçlar ve fonksiyonlar içerir.

Yeni bir ACK metodu eklerken, genellikle ilgili `impl.py` dosyasına metodu tanımlamanız ve ardından `definitions.py` dosyasında bu metodu kaydetmeniz gerekir.

## Adım 1: Metodu `src/ack/handler/impl.py` Dosyasına Ekleme

Yeni ACK handler metodunuzu `src/ack/handler/impl.py` dosyasına eklemelisiniz. Bu dosya, ACK mesajlarının ana iş mantığını barındırır.

### Örnek: `src/ack/handler/impl.py` dosyasına yeni bir ACK handler metodu ekleme

Diyelim ki yeni bir `ACK_TIMEOUT` durumu için bir handler eklemek istiyorsunuz.

```python
# src/ack/handler/impl.py

from src.tools.log.logger import logger

def ack_ok(data: dict, src_id: int):
    logger.debug(f"[ACK] ACK_OK received from SRC: {src_id}")
    logger.debug(f"[ACK] → Data: {data}")

def ack_error(data: dict, src_id: int):
    logger.error(f"[ACK] ACK_ERROR received from SRC: {src_id}")
    logger.debug(f"[ACK] → Data: {data}")

def ack_busy(data: dict, src_id: int):
    logger.warning(f"[ACK] ACK_BUSY received from SRC: {src_id}")
    logger.debug(f"[ACK] → Data: {data}")

def ack_invalid_cmd(data: dict, src_id: int):
    logger.error(f"[ACK] ACK_INVALID_CMD received from SRC: {src_id}")
    logger.debug(f"[ACK] → Data: {data}")

def unknown(data: dict, src_id: int, ack_id: int):
    logger.warning(f"[ACK] Unknown ACK ID {ack_id} from SRC: {src_id}")
    logger.debug(f"[ACK] → Data: {data}")

def ack_timeout(data: dict, src_id: int):
    logger.warning(f"[ACK] ACK_TIMEOUT received from SRC: {src_id}")
    logger.debug(f"[ACK] → Data: {data}")
```

## Adım 2: Metodu `src/ack/definitions.py` Dosyasına Kaydetme

Yeni eklediğiniz ACK metodunun sistem tarafından tanınabilmesi için, `src/ack/definitions.py` dosyasına bir tanım eklemeniz gerekmektedir. Bu tanım, genellikle bir ID'yi metodunuzla eşleştirir.

### Örnek: `src/ack/definitions.py` dosyasını güncelleme

`ACK_TIMEOUT` için bir ID tanımlayın ve bunu `ack_definitions` sözlüğüne ekleyin.

```python
# src/ack/definitions.py

from dataclasses import dataclass
import src.ack.handler.impl as ack_handler

@dataclass
class AckDefinition:
    id: int
    name: str
    handler: callable

ACK_OK = 0x00
ACK_ERROR = 0x01
ACK_BUSY = 0x02
ACK_INVALID_CMD = 0x03
ACK_TIMEOUT = 0x04 # Yeni ACK ID'si

ack_definitions = {
    ACK_OK: AckDefinition(ACK_OK, "ACK_OK", ack_handler.ack_ok),
    ACK_ERROR: AckDefinition(ACK_ERROR, "ACK_ERROR", ack_handler.ack_error),
    ACK_BUSY: AckDefinition(ACK_BUSY, "ACK_BUSY", ack_handler.ack_busy),
    ACK_INVALID_CMD: AckDefinition(ACK_INVALID_CMD, "ACK_INVALID_CMD", ack_handler.ack_invalid_cmd),
    ACK_TIMEOUT: AckDefinition(ACK_TIMEOUT, "ACK_TIMEOUT", ack_handler.ack_timeout), # Yeni tanım
}
```

## Özet

Yeni bir ACK metodu eklemek için:

1.  `src/ack/handler/impl.py` dosyasına yeni fonksiyonunuzu ekleyin.
2.  `src/ack/definitions.py` dosyasına, yeni fonksiyonunuzu bir ID ile eşleştiren bir tanım ekleyin. Bu, sistemin gelen ACK mesajlarını doğru fonksiyona yönlendirmesini sağlar.