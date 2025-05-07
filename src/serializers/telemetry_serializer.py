import struct

def serialize_telemetry(tlm_id: int, *params) -> bytes:
    """
    Telemetri verilerini binary formatta serialize eder.

    Parameters:
        tlm_id (int): Telemetry Type ID (e.g., GPS, IMU)
        *params (tuple): Parametreler (örneğin, [lat, lon, alt])

    Returns:
        bytes: Serialleşmiş telemetry verisi
    """
    # İlk olarak, tlm_id'yi serialize ediyoruz
    serialized_data = struct.pack(">B", tlm_id)  # tlm_id'yi tek bir byte olarak serialize et

    # Parametreleri serialize ediyoruz (tüm parametreler float olarak kabul edilir, diğer türler için genişletilebilir)
    for param in params:
        serialized_data += struct.pack(">f", param)  # Her parametreyi float olarak serialize ediyoruz

    return serialized_data


def deserialize_telemetry(payload: bytes) -> dict:
    """
    Binary (byte) verisini anlamlı telemetry verilerine dönüştürür.

    Parameters:
        payload (bytes): Serialleşmiş telemetry verisi

    Returns:
        dict: Parsed telemetry data (e.g., tlm_id, gps_lat, gps_lon, gps_alt)
    """
    # İlk olarak, tlm_id'yi çözümlüyoruz
    tlm_id, = struct.unpack(">B", payload[:1])  # İlk byte'ı tlm_id olarak alıyoruz
    
    # Geriye kalan veriyi float olarak çözümlüyoruz (bu örnek tüm verilerin float olduğunu varsayar)
    data = struct.unpack(f">{len(payload[1:]) // 4}f", payload[1:])  # Geriye kalanları float olarak çöz

    # Sonuç dictionary'sini tlm_id'ye göre oluşturuyoruz
    result = {"tlm_id": tlm_id}
    
    # Eğer tlm_id GPS verisi ise
    if tlm_id == 0x01:  # GPS verisi
        result.update({
            "lat": data[0],
            "lon": data[1],
            "alt": data[2],
        })
    
    # IMU verisi gibi başka türler eklemek için aşağıdaki gibi genişletebilirsiniz
    elif tlm_id == 0x02:  # IMU verisi
        result.update({
            "roll": data[0],
            "pitch": data[1],
            "yaw": data[2],
        })
    
    elif tlm_id == 0x03:  # BATTERY verisi
        result.update({
            "voltage": data[0],
            "current": data[1],
            "level": data[2],
        })
    return result
