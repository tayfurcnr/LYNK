# src/handlers/ftp/file_handler.py

from src.serializers.ftp_serializer import (
    FTP_PHASE_IDS,
    deserialize_ftp_start,
    deserialize_ftp_chunk,
    deserialize_ftp_end
)
from src.tools.ftp.storage import open_download_stream
from src.tools.log.logger import logger
from src.tools.ack.ack_dispatcher import send_ftp_ack
from src.tools.ack.ack_tracker import register_ack

# transfer state: (src_id, dst_id) → { stream, chunks: {seq: bytes}, total: Optional[int] }
_transfers: dict[tuple[int, int], dict] = {}


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

    logger.debug(f"[FTP DEBUG] RAW payload hex={payload.hex()}")
    phase = payload[0]

    # START: yalnızca yeni transferse
    if phase == FTP_PHASE_IDS["START"] and fid not in _transfers:
        try:
            filename = deserialize_ftp_start(payload)
        except Exception as e:
            logger.error(f"[FTP] START deserialization failed: {e}")
            return
        stream = open_download_stream(filename)
        _transfers[fid] = {"stream": stream, "chunks": {}, "total": None}
        send_ftp_ack(interface, phase="START", target_id=src, success=True)
        register_ack("FTP_START", src, status=0)
        logger.info(f"[FTP] START received, filename={filename}")
        return

    # CHUNK: yalnızca transfer devam ediyorsa
    if phase == FTP_PHASE_IDS["CHUNK"] and fid in _transfers:
        try:
            seq, data = deserialize_ftp_chunk(payload)
        except Exception as e:
            logger.error(f"[FTP] CHUNK deserialization failed: {e}")
            return
        logger.debug(f"[FTP DEBUG] parsed seq={seq}, data_length={len(data)} bytes")
        transfer = _transfers[fid]
        transfer["chunks"][seq] = data
        send_ftp_ack(interface, phase="CHUNK", target_id=src, success=True, status_code=seq)
        register_ack(f"FTP_CHUNK_{seq}", src, status=0)
        logger.debug(f"[FTP] CHUNK received seq={seq}, size={len(data)} bytes")
        return

    # END: yalnızca transfer devam ediyorsa
    if phase == FTP_PHASE_IDS["END"] and fid in _transfers:
        try:
            total = deserialize_ftp_end(payload)
        except Exception as e:
            logger.error(f"[FTP] END deserialization failed: {e}")
            return
        transfer = _transfers[fid]
        transfer["total"] = total

        received = set(transfer["chunks"].keys())
        missing = set(range(total)) - received

        if missing:
            for seq in missing:
                send_ftp_ack(interface, phase="CHUNK", target_id=src, success=False, status_code=seq)
                register_ack(f"FTP_CHUNK_{seq}", src, status=1)
            logger.warning(f"[FTP] END received but missing chunks: {missing}")
        else:
            for i in range(total):
                transfer["stream"].write(transfer["chunks"][i])
            transfer["stream"].close()
            logger.info(f"[FTP] Transfer complete: {transfer['stream'].name}")
            send_ftp_ack(interface, phase="END", target_id=src, success=True)
            register_ack("FTP_END", src, status=0)
            # transfer sona erdi, state temizleniyor
            del _transfers[fid]
        return

    # yinelenen veya stale END çerçeveleri için yeniden ACK
    if phase == FTP_PHASE_IDS["END"] and fid not in _transfers:
        send_ftp_ack(interface, phase="END", target_id=src, success=True)
        logger.debug(f"[FTP] Re-ACK stale END from {src}->{dst}")
        return

    # Beklenmeyen veya yinelenen frame’leri yoksay
    logger.debug(f"[FTP] Ignoring unexpected frame: phase={phase}, fid={fid}")
