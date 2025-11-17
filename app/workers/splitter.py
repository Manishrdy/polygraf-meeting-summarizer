import os
import time
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.services.redis_service import redis_client
# from app.services.audio_extractor import extract_audio
from app.services.consumer import consume_diarized_segments
from app.logger import get_logger

logger = get_logger("worker-splitter")

def run_splitter():
    logger.info("Inside splitter, on queue:splitting")

    while True:
        try:
            task = redis_client.pop_from_queue("queue:splitting", timeout=0)
            if not task:
                continue

            job_id = task["job_id"]
            media_path = task["media_path"]
            json_path = task["json_path"]

            logger.info(f"Processing job: {job_id}")
            logger.info(f"Processing media_path: {media_path}")
            logger.info(f"Processing json_path: {json_path}")

            redis_client.update_status(job_id, "processing_audio")

            if not media_path.lower().endswith(".wav"):
                error_msg = "Only .wav media files are supported"
                logger.error(f"Job {job_id}: {error_msg}")

                redis_client.update_status(job_id, "failed", error=error_msg)
                continue
            
            # audio_path = media_path
            # if media_path.lower().endswith(".mp4"):
            #     audio_path = media_path.replace(".mp4", ".wav")
            #     extract_audio(media_path, audio_path)

            segments = consume_diarized_segments(json_path, media_path)

            total_chunks = len(segments)
            redis_client.update_status(job_id, "transcribing", total_chunks=total_chunks)
            logger.info(f"Job {job_id}: split into {total_chunks} chunks")

            if total_chunks == 0:
                redis_client.update_status(job_id, "failed", error="No segments found")
                continue

            for segment in segments:
                payload = {
                    "job_id": job_id,
                    "chunk_path": segment["file_path"],
                    "speaker": segment["speaker"],
                    "start_ms": segment["start"],
                    "duration_ms": segment["duration_ms"],
                }
                logger.info(f"Payload in run_splitter: {payload}")

                redis_client.push_to_queue("queue:transcription", payload)
        except Exception as e:
            logger.exception(f"Splitter worker failed: {e}")
            if "job_id" in locals():
                redis_client.update_status(job_id, "failed", error=str(e))
            time.sleep(1)

run_splitter()