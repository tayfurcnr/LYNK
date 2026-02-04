import os
import sys
import lz4.block
import struct

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.core.frame_codec import build_mesh_frame
from src.shared.config.manager import load_config

# Initialize config
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
config_path = os.path.join(base_dir, 'configs/config.yaml')
load_config(config_path)

def run_demo():
    # Örnek 1: Çok boşluklu/tekrarlı bir veri (Görev Listesi/Log gibi)
    # 256 byte'lık tekrarlı veri
    payload_compressible = b"WAYPOINT_ID:1;LAT:41.0082;LON:28.9784;ALT:100.0|" * 5
    orig_len = len(payload_compressible)
    
    frame_compressed = build_mesh_frame('C', 1, 2, payload_compressible)
    comp_wire_len = len(frame_compressed)
    
    # Hesaplama yapalım (Header 11 + Seq 4 + CRC 2 = 17 byte temel overhead)
    # Sıkıştırılmışta ek olarak 4 byte orijinal boyut bilgisi var.
    
    print("=== LYNK Payload Compression Demo ===")
    print(f"Senaryo: Tekrarlı Veri (256 Byte Görev Listesi)")
    print(f"Orijinal Payload: {orig_len} bytes")
    print(f"Toplam Paket (Wire): {comp_wire_len} bytes")
    print(f"Net Kazanç: {orig_len + 17 - comp_wire_len} bytes")
    print(f"Sıkıştırma Oranı: %{((orig_len + 17 - comp_wire_len) / (orig_len + 17)) * 100:.1f}")
    print("-" * 40)

    # Örnek 2: Rastgele veri (Şifreli veya gürültülü veri gibi)
    payload_random = os.urandom(200)
    frame_random = build_mesh_frame('T', 1, 2, payload_random)
    random_wire_len = len(frame_random)
    
    print(f"Senaryo: Rastgele Veri (200 Byte)")
    print(f"Orijinal Payload: {len(payload_random)} bytes")
    print(f"Toplam Paket (Wire): {random_wire_len} bytes")
    print(f"Durum: Sıkıştırma yapılmadı (Smart Detection)")
    print("-" * 40)

if __name__ == "__main__":
    run_demo()
