from __future__ import annotations
# src/tools/comm/udp_handler.py

import socket
import struct
import threading
import time
from collections import deque
from queue import Queue, Full
from typing import Optional, List, Tuple

from src.shared.config.manager import get_config


class UDPHandler:
    def __init__(self):
        self._load_config()

        # Tek öğelik kuyruk: her zaman en güncel paket
        self.rx_queue = Queue(maxsize=1)
        self.running = False
        self.thread = None

        # --- ZAMAN PENCERELİ TAMPU ---
        # Eleman: (ts_sec: float, data: bytes)
        self._win: deque[Tuple[float, bytes]] = deque()
        self._win_bytes: int = 0
        self._win_lock = threading.Lock()

        # UDP soketi
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, 'SO_REUSEPORT'):
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        # Kernel RX tamponunu büyüt (OS tavanına kadar). Config'ten gelebilir.
        if self.rcvbuf_bytes and self.rcvbuf_bytes > 0:
            try:
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, int(self.rcvbuf_bytes))
            except Exception:
                pass  # OS sınırına takılırsa sessiz geç

        self.sock.bind(("", self.local_port))
        self.sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_IF,
            socket.inet_aton(self.local_ip)
        )

        mreq = struct.pack("4s4s",
                           socket.inet_aton(self.remote_ip),
                           socket.inet_aton(self.local_ip))
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        self.sock.setblocking(False)

    def _load_config(self):
        cfg = get_config()
        udp_cfg = cfg.get("udp", {})

        self.local_ip        = udp_cfg["local_ip"]
        self.local_port      = udp_cfg["local_port"]
        self.remote_ip       = udp_cfg["remote_ip"]
        self.remote_port     = udp_cfg["remote_port"]

        # Zaman penceresi ve toplam pencere bayt limiti (opsiyonel)
        self.window_sec      = float(udp_cfg.get("window_sec", 1.0))         # son 1 saniye
        self.max_window_bytes= int(udp_cfg.get("max_window_bytes", 2_000_000))  # ~2 MB

        # Soket receive buffer (opsiyonel): örn. 4*1024*1024
        self.rcvbuf_bytes    = int(udp_cfg.get("rcvbuf_bytes", 4 * 1024 * 1024))

        # Idle bekleme (ms cinsinden): 1 ms önerilir
        self.idle_sleep_sec  = float(udp_cfg.get("idle_sleep_sec", 0.001))

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._rx_worker, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        self.sock.close()

    # --- helper: en günceli kuyruğa koy, doluysa eskiyi at ---
    def _enqueue_latest(self, data: bytes) -> None:
        try:
            self.rx_queue.put_nowait(data)
        except Full:
            try:
                _ = self.rx_queue.get_nowait()  # eskiyi at
            except Exception:
                pass
            self.rx_queue.put_nowait(data)
        # Zaman pencereli tampuya da ekle
        self._win_add(data)

    # --- ZAMAN PENCERESİ YARDIMCILARI ---
    def _win_prune_time(self, cutoff: float) -> None:
        while self._win and self._win[0][0] < cutoff:
            _, d = self._win.popleft()
            self._win_bytes -= len(d)

    def _win_prune_bytes(self) -> None:
        if self.max_window_bytes <= 0:
            return
        while self._win and self._win_bytes > self.max_window_bytes:
            _, d = self._win.popleft()
            self._win_bytes -= len(d)

    def _win_add(self, data: bytes) -> None:
        now = time.time()
        with self._win_lock:
            self._win.append((now, data))
            self._win_bytes += len(data)
            self._win_prune_time(now - self.window_sec)
            self._win_prune_bytes()

    def read_window(self, seconds: Optional[float] = None) -> List[bytes]:
        """
        Son 'seconds' saniyedeki TÜM paketleri döndürür (kopya).
        seconds None ise self.window_sec kullanılır.
        """
        if seconds is None:
            seconds = self.window_sec
        cutoff = time.time() - float(seconds)
        out: List[bytes] = []
        with self._win_lock:
            self._win_prune_time(cutoff)
            out.extend(d for _, d in self._win)
        return out

    def read_and_clear_window(self, seconds: Optional[float] = None) -> List[bytes]:
        """
        Son 'seconds' saniyelik pencereyi döndürür ve buffer’dan temizler.
        """
        if seconds is None:
            seconds = self.window_sec
        cutoff = time.time() - float(seconds)
        out: List[bytes] = []
        with self._win_lock:
            self._win_prune_time(cutoff)
            while self._win:
                _, d = self._win.popleft()
                self._win_bytes -= len(d)
                out.append(d)
        return out

    def _rx_worker(self):
        while self.running:
            try:
                # Drain loop: bu turda sokette bekleyen TÜM paketleri çek
                got_any = False
                while True:
                    try:
                        # Büyük datagramlar için 65535
                        data, _addr = self.sock.recvfrom(65535)
                    except BlockingIOError:
                        break
                    if not data:
                        break
                    got_any = True
                    self._enqueue_latest(data)

                # Paket yoksa kısa uyku; varsa hemen bir sonraki tura geç
                if not got_any:
                    time.sleep(self.idle_sleep_sec)
            except Exception:
                # Sessiz geç veya throttle'lı log ekleyebilirsiniz
                time.sleep(max(self.idle_sleep_sec, 0.001))

    def read(self) -> bytes | None:
        """
        Kuyruğu tüketir ve en SON paketi döndürür (her zaman en güncel).
        """
        last = None
        while not self.rx_queue.empty():
            try:
                last = self.rx_queue.get_nowait()
            except Exception:
                break
        return last

    def send(self, data: bytes):
        self.sock.sendto(data, (self.remote_ip, self.remote_port))
        # print(f"[UDP SEND] {len(data)} bytes to {self.remote_ip}:{self.remote_port}")
