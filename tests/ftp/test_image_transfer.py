# tests/ftp/test_ftp_transfer_desktop_file.py

import os
import sys
import pytest

# Proje kökünü ve src klasörünü ekle
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from src.tools.comm.interface_factory import create_interface
from src.core.frame_codec           import parse_mesh_frame
from src.core.frame_router          import route_frame
from src.tools.ftp.ftp_builder      import send_ftp_file
import src.tools.ftp.storage as storage

def test_transfer_desktop_example_png(monkeypatch):
    # Çalışma dizinini proje köküne çekelim (göreli yollar için)
    monkeypatch.chdir(PROJECT_ROOT)

    # 1) Masaüstündeki dosya yolu
    source_file = r"C:\Users\KAIROS\Desktop\example.png"
    assert os.path.isfile(source_file), f"Kaynak dosya bulunamadı: {source_file}"

    # 2) Kaynak içeriği oku
    original_data = open(source_file, "rb").read()

    # 3) Mock UART interface
    interface = create_interface()

    # 4) FTP transferini başlat (loopback: src=1, dst=1)
    send_ftp_file(interface, filepath=source_file, src=1, dst=1)

    # 5) Gelen tüm frame'leri işleyelim
    while True:
        raw = interface.uart.read()
        if not raw:
            break
        frm = parse_mesh_frame(raw)
        route_frame(frm, interface)

    # 6) İndirilen dosyanın konumunu al
    download_dir    = storage._DOWNLOAD_DIR
    downloaded_file = os.path.join(download_dir, "example.png")

    # 7) Dosyanın varlığını ve içeriğini kontrol et
    assert os.path.isfile(downloaded_file), \
        f"İndirilen dosya bulunamadı: {downloaded_file}"
    received = open(downloaded_file, "rb").read()
    assert received == original_data, "İndirilen dosya orijinalle eşleşmiyor!"
