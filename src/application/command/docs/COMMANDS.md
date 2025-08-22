# LYNK Komutları

Bu belge, LYNK sistemi tarafından desteklenen komutları listeler, nasıl kullanılacaklarını açıklar ve yeni komutların nasıl ekleneceğine dair rehberlik sağlar.

## Komut Listesi

Aşağıda, sistemde tanımlı olan komutlar ve bunların kimlikleri (ID) ile aldıkları parametreler bulunmaktadır.

| Komut ID | Komut Adı          | Parametreler                                  | Açıklama                                      |
|----------|--------------------|-----------------------------------------------|-----------------------------------------------|
| `0x01`   | `REBOOT`           | Yok                                           | Sistemi yeniden başlatır.                     |
| `0x02`   | `SET_MODE`         | `mode` (string/int)                           | Drone'un uçuş modunu ayarlar.                 |
| `0x03`   | `TAKEOFF`          | `alt` (float) veya `alt, lat, lon, target_alt` (float) | Drone'un kalkış yapmasını sağlar.            |
| `0x04`   | `LANDING`          | Yok veya `lat, lon` (float)                   | Drone'un iniş yapmasını sağlar.              |
| `0x05`   | `GIMBAL_CTRL`      | `yaw, pitch, roll` (float)                    | Gimbal kontrol komutu.                        |
| `0x06`   | `GOTO`             | `lat, lon, alt` (float)                       | Belirtilen koordinatlara gitme komutu.        |
| `0x07`   | `FOLLOW_ME`        | `target_id` (int) veya `target_id` (int), `alt` (float) | Beni takip et modunu etkinleştirir.           |
| `0x09`   | `WAYPOINTS`        | `waypoints` (list of `lat, lon, alt` (float)) | Önceden tanımlanmış ara noktaları takip eder. |
| `0x0A`   | `TASK_RELAY`       | `task_id` (uint), `lat, lon, alt` (float)     | Görev aktarımı komutu.                        |
| `0x0B`   | `SET_SPEED`        | `speed` (float)                               | Drone'un hızını ayarlar.                      |
| `0x0C`   | `SET_DIRECTION`    | `direction` (float)                           | Drone'un yönünü ayarlar.                     |
| `0x0D`   | `SET_DRONE_ID`     | `drone_id` (uint)                             | Drone'un kimlik numarasını ayarlar.          |
| `0x0E`   | `SWARM_FORMATER`   | `formation` (string)                          | Sürü formatlama komutu.                       |
| `0x0F`   | `SWARM_LEADER`     | `leader_id` (uint)                            | Sürü lideri atama komutu.                     |
| `0x10`   | `SWARM_MERGE`      | `target_id` (uint)                            | Sürüleri birleştirme komutu.                  |
| `0x11`   | `SET_MISSION_STATUS`| `status` (string)                             | Görev durumunu ayarlar.                       |
| `0x14`   | `ACK_COMMAND`      | Yok                                           | Komut onaylama (acknowledgement) komutu.      |
| `0x15`   | `STREAM_VIDEO`     | `stream_status` (boolean)                     | Video akışını başlatır/durdurur.              |

## LYNK Mesaj Yapısı

LYNK sistemi, cihazlar arası iletişimi belirli bir çerçeve (frame) yapısı üzerinden gerçekleştirir. Her komut, bu genel mesaj yapısının "payload" (veri yükü) kısmında taşınır. Mesaj çerçevesi, `src/core/frame_codec.py` dosyasında tanımlanmıştır ve aşağıdaki genel formata sahiptir:

```
[Başlangıç Byte 1][Başlangıç Byte 2][Versiyon][Çerçeve Tipi][Kaynak ID][Hedef ID][Payload Uzunluğu][Payload...][CRC-16]
```

Açıklamalar:

*   **Başlangıç Byte 1 & 2**: Mesajın başlangıcını belirten sabit değerler.
*   **Versiyon**: Protokol versiyonu.
*   **Çerçeve Tipi**: Mesajın türünü belirtir (örn. komut, telemetri, ACK). Komutlar için özel bir tip değeri olacaktır.
*   **Kaynak ID**: Mesajı gönderen cihazın kimliği.
*   **Hedef ID**: Mesajın alıcı cihazın kimliği.
*   **Payload Uzunluğu**: `Payload` alanının byte cinsinden uzunluğu.
*   **Payload**: Asıl komut verisini içeren kısımdır. Bir komut mesajı için bu kısım, komutun ID'si ve komuta özgü parametreleri içerir. Örneğin, `SET_MODE` komutu için `Payload` içinde `SET_MODE` komut ID'si ve ayarlanacak mod değeri bulunur.
*   **CRC-16**: Mesajın bütünlüğünü doğrulamak için kullanılan 2-byte'lık döngüsel artıklık kontrolü (Cyclic Redundancy Check) değeri.

Bir komutun `Payload` içindeki yapısı ise genellikle Komut ID'si ve ardından gelen parametrelerden oluşur. Parametrelerin nasıl paketlendiği (örneğin, float, int, boolean olarak) `src/application/command/serializer/impl.py` dosyasında tanımlanır.

**Örnek Komut Mesajı (Genel Yapı):**

Diyelim ki `SET_MODE` komutunu (`0x02`) "OTOMATIK" moduna ayarlamak istiyoruz. Bu durumda `Payload` kısmı şu şekilde yapılandırılabilir:

```
[Komut ID: 0x02][Mod Değeri: "OTOMATIK" (seri hale getirilmiş hali)]
```

Bu `Payload`, yukarıda açıklanan genel LYNK mesaj çerçevesinin içine yerleştirilir ve ağ üzerinden gönderilir.

## Komutların Kullanımı

LYNK sistemindeki komutlar, belirli işlevleri tetiklemek için kullanılır. Her komutun kendine özgü bir ID'si ve adı vardır. Komutlar genellikle bir seri hale getirici (serializer) aracılığıyla oluşturulur ve bir işleyici (handler) tarafından yorumlanır.

Genel olarak, bir komutun kullanımı şu adımları içerir:
1. **Komut Oluşturma:** İlgili komutun ID'si ve gerekli parametrelerle bir komut nesnesi oluşturulur.
2. **Seri Hale Getirme (Serialization):** Oluşturulan komut nesnesi, sistemin anlayabileceği bir formata (örneğin, byte dizisi) dönüştürülür. Bu işlem genellikle `src/application/command/serializer/impl.py` içinde tanımlanan serileştiriciler tarafından yapılır.
3. **Gönderme:** Seri hale getirilmiş komut, hedef cihaza (örneğin, drone) gönderilir.
4. **İşleme (Handling):** Hedef cihaz, gelen komutu ayrıştırır ve `src/application/command/handler/impl.py` içinde tanımlanan ilgili işleyici fonksiyonunu çağırarak komutu yürütür.

Her komutun spesifik parametreleri, veri tipleri ve beklenen davranışları, `src/application/command/handler/impl.py` ve `src/application/command/serializer/impl.py` dosyalarındaki ilgili fonksiyonlarda detaylandırılmıştır. Komutların aldığı değerlerin (boolean, integer, string vb.) tam listesi için bu dosyalara başvurulmalıdır.

## Yeni Komut Ekleme

LYNK sistemine yeni bir komut eklemek için aşağıdaki adımları izlemeniz gerekmektedir:

1.  **Komut Tanımı (`definitions.py`):**
    `src/application/command/definitions.py` dosyasında `command_definitions` sözlüğüne yeni bir `CommandDefinition` ekleyin.
    ```python
    # src/application/command/definitions.py
    # ...
    command_definitions = {
        # ... mevcut komutlar ...
        0xXX: CommandDefinition(0xXX, "YENI_KOMUT_ADI", handler.yeni_komut_handler),
    }
    ```
    - `0xXX`: Yeni komut için benzersiz bir hexadecimal ID atayın.
    - `"YENI_KOMUT_ADI"`: Komutunuz için büyük harflerle, alt çizgi ile ayrılmış anlamlı bir ad belirleyin.
    - `handler.yeni_komut_handler`: Bu, komutun işlevselliğini içerecek olan işleyici fonksiyonuna bir referanstır.

2.  **Komut İşleyici (`handler/impl.py`):**
    `src/application/command/handler/impl.py` dosyasında yeni komutunuz için bir işleyici fonksiyonu oluşturun. Bu fonksiyon, komut alındığında yapılacak işlemleri tanımlar.
    ```python
    # src/application/command/handler/impl.py
    # ...
    def yeni_komut_handler(parametreler):
        # Komutun işlevselliğini buraya yazın
        print(f"Yeni komut alındı ve işleniyor: {parametreler}")
        # Gerekirse ACK veya başka bir yanıt döndürün
    ```
    - Fonksiyonun alacağı `parametreler`, komutun veri yüküne (payload) bağlı olacaktır.

3.  **Komut Seri Hale Getirici (`serializer/impl.py`):**
    Eğer yeni komutunuzun özel bir veri yükü (payload) varsa ve bu yükün seri hale getirilmesi gerekiyorsa, `src/application/command/serializer/impl.py` dosyasında bu komut için bir serileştirme ve/veya seri halden çıkarma (deserialization) mantığı eklemeniz gerekebilir.
    ```python
    # src/application/command/serializer/impl.py
    # ...
    def serialize_yeni_komut(komut_nesnesi):
        # Komut nesnesini byte dizisine dönüştürme mantığı
        pass

    def deserialize_yeni_komut(byte_dizisi):
        # Byte dizisini komut nesnesine dönüştürme mantığı
        pass
    ```
    - `dispatcher.py` dosyalarında bu yeni serileştirici/deserileştirici fonksiyonlarını kaydetmeniz gerekebilir.

4.  **Testler (İsteğe Bağlı ama Önerilir):**
    Yeni komutunuzun doğru çalıştığından emin olmak için `tests/command/` dizini altında veya uygun bir test dosyasında testler yazın.

Bu adımları takip ederek LYNK sistemine yeni komutlar ekleyebilirsiniz.