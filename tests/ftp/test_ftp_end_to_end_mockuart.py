# tests/ftp/test_ftp_end_to_end_mockuart.py

import os
import sys
import pytest

# Proje kökünü bulun ve src klasörünü path'e ekleyin
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from src.tools.comm.interface_factory import create_interface
from src.core.frame_codec           import parse_mesh_frame
from src.core.frame_router          import route_frame
from src.tools.ftp.ftp_builder      import send_ftp_file
import src.tools.ftp.storage as storage

def test_ftp_end_to_end_mockuart(tmp_path, monkeypatch):
    # Çalışma dizinini proje köküne çekelim
    monkeypatch.chdir(PROJECT_ROOT)

    # 1) Mock UART interface
    interface = create_interface()

    # 2) Test edilecek küçük bir dosyayı oluştur
    test_data = b"Merhaba Mock FTP!"
    # tests/ftp altına yazıyoruz
    file_path = os.path.join(PROJECT_ROOT, "tests", "ftp", "hello.txt")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(test_data)

    # 3) FTP transferi başlat (loopback: src=1, dst=1)
    send_ftp_file(interface, filepath=file_path, src=1, dst=1)

    # 4) MockUARTHandler.buffer’ındaki tüm frame’leri işle
    while True:
        raw = interface.uart.read()
        if not raw:
            break
        frame_dict = parse_mesh_frame(raw)
        route_frame(frame_dict, interface)

    # 5) İndirilen dosyanın storage._DOWNLOAD_DIR içinde oluştuğunu kontrol et
    download_dir     = storage._DOWNLOAD_DIR
    downloaded_path  = os.path.join(download_dir, "hello.txt")

    assert os.path.isfile(downloaded_path), \
        f"Dosya {downloaded_path} içinde bulunamadı!"
    with open(downloaded_path, "rb") as f:
        received = f.read()
    assert received == test_data, "İndirilen dosya içeriği orijinalle eşleşmiyor!"
