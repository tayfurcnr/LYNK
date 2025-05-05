class MockUARTHandler:
    def __init__(self):
        self.buffer = []   # Gelen frame’ler için
        self._outbox = []  # Gönderilen frame’leri tutmak için

    def start(self):
        print("[MockUART] ✅ Başlatıldı")

    def stop(self):
        print("[MockUART] ⛔ Durduruldu")

    def send(self, frame: bytes):
        print(f"[MockUART] 📤 Gönderildi: {frame.hex()}")
        self._outbox.append(frame)
        self.buffer.append(frame)  # Test ortamında geri okunabilir olması için

    def inject_frame(self, frame: bytes):
        self.buffer.append(frame)

    def read(self):
        if self.buffer:
            return self.buffer.pop(0)
        return None
