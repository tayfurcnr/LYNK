# src/serializers/telemetry_serializer.py

import struct

def serialize_telemetry(device_id: int, gps_lat: float, gps_lon: float, gps_alt: float) -> bytes:
    """
    Cihazın GPS verilerini binary formatta serialize eder.

    Parameters:
        device_id (int): Cihaz ID'si
        gps_lat (float): GPS enlem
        gps_lon (float): GPS boylam
        gps_alt (float): Yükseklik

    Returns:
        bytes: Serialleşmiş telemetry verisi
    """
    # >Bfff: > : Big-endian, B : unsigned char (1 byte), f : float (4 bytes)
    return struct.pack(">Bfff", device_id, gps_lat, gps_lon, gps_alt)

def deserialize_telemetry(payload: bytes) -> dict:
    """
    Binary (byte) verisini anlamlı telemetry verilerine dönüştürür.

    Parameters:
        payload (bytes): Serialleşmiş telemetry verisi

    Returns:
        dict: device_id, gps_lat, gps_lon, gps_alt
    """
    if len(payload) != 13:
        raise ValueError("Telemetry payload uzunluğu geçersiz (beklenen 13 byte)")
    
    # >Bfff: > : Big-endian, B : unsigned char (1 byte), f : float (4 bytes)
    device_id, gps_lat, gps_lon, gps_alt = struct.unpack(">Bfff", payload)
    
    return {
        "device_id": device_id,
        "gps_lat": gps_lat,
        "gps_lon": gps_lon,
        "gps_alt": gps_alt
    }
