# 📦 Test Klasörü

Bu klasörde sistemin uçtan uca testleri yer alır. Her bir `test_*.py` dosyası belirli bir iletişim senaryosunu simüle eder (komut gönderme, telemetri alma, hatalı frame vs.).

---

## 🔧 Çalıştırma Talimatı

### Yöntem 1: PYTHONPATH (Tavsiye Edilen)

Terminalde proje köküne (`root/`) gelin:

```bash
cd root
$env:PYTHONPATH="."      # Windows PowerShell için
python tests/test_send_command.py
