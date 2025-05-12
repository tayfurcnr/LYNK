# src/handlers/ftp/file_handler.py

from src.serializers.ftp_serializer import (
    deserialize_ftp_start,
    deserialize_ftp_chunk,
    deserialize_ftp_end
)
from src.tools.ftp.storage import open_download_stream
from src.tools.log.logger import logger
from src.tools.ack.ack_dispatcher import send_ftp_ack
from src.tools.ack.ack_tracker import register_ack

# transfer state: (src_id, dst_id) → { stream, chunks: {seq: bytes}, total: Optional[int] }
_transfers = {}

def handle_file(payload: bytes, frame_dict: dict, interface):
    """
    FTP transfer için gelen frame’leri işler:
    - START: dosya adı → stream aç → START-ACK
    - CHUNK: seq → buffer’a ekle → CHUNK-ACK
    - END: total → eksikleri NACK / tamamsa yaz → END-ACK
    """
    src = frame_dict["src_id"]
    dst = frame_dict["dst_id"]
    fid = (src, dst)

    # 1) START frame
    if fid not in _transfers:
        filename = deserialize_ftp_start(payload)
        stream = open_download_stream(filename)
        _transfers[fid] = {
            "stream": stream,
            "chunks": {},
            "total": None
        }
        # START-ACK
        send_ftp_ack(interface,
                     phase="START",
                     target_id=src,
                     success=True)
        register_ack("FTP_START", src, status=0)
        logger.info(f"[FTP] START received, filename={filename}")
        return

    # 2) END frame
    # payload uzunluğu 4 bayt olunca END mesajı
    if len(payload) == 4:
        total = deserialize_ftp_end(payload)
        transfer = _transfers[fid]
        transfer["total"] = total

        received = set(transfer["chunks"].keys())
        missing = set(range(total)) - received

        if missing:
            # Eksik seq’leri NACK ile bildir
            for seq in missing:
                send_ftp_ack(interface,
                             phase="CHUNK",
                             target_id=src,
                             success=False,
                             status_code=seq)
                register_ack(f"FTP_CHUNK_{seq}", src, status=1)
            logger.warning(f"[FTP] END received but missing chunks: {missing}")
        else:
            # Tüm parçaları sırayla yaz ve tamamla
            for i in range(total):
                transfer["stream"].write(transfer["chunks"][i])
            transfer["stream"].close()
            logger.info(f"[FTP] Transfer complete: {transfer['stream'].name}")
            # END-ACK
            send_ftp_ack(interface,
                         phase="END",
                         target_id=src,
                         success=True)
            register_ack("FTP_END", src, status=0)
            del _transfers[fid]

        return

    # 3) CHUNK frame
    seq, data = deserialize_ftp_chunk(payload)
    _transfers[fid]["chunks"][seq] = data
    # CHUNK-ACK
    send_ftp_ack(interface,
                 phase="CHUNK",
                 target_id=src,
                 success=True,
                 status_code=seq)
    register_ack(f"FTP_CHUNK_{seq}", src, status=0)
    logger.debug(f"[FTP] Chunk received seq={seq}, size={len(data)} bytes")
