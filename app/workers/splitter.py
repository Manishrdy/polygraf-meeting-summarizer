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

    print("Inside app.workers.splitter.py function")

    while True:
        try:
            task = redis_client.removeFromQueue("queue:splitting", timeout=0)
            logger.info(f"Task from queue splitting - {task}")

            if not task:
                continue

            job_id = task["job_id"]
            media_path = task["media_path"]
            json_path = task["json_path"]

            logger.info(f"Processing job: {job_id}")
            logger.info(f"Cehcking media_path: {media_path}")
            logger.info(f"View json_path: {json_path}")

            redis_client.statusUpdate(job_id, "processing_audio")

            if not media_path.lower().endswith(".wav"):
                logger.error("Currenly only .wav audio files are supported.")

                redis_client.statusUpdate(job_id, "failed", error="Only .wav files are allowed")
                continue
            
            # audio_path = media_path
            # if media_path.lower().endswith(".mp4"):
            #     audio_path = media_path.replace(".mp4", ".wav")
            #     extract_audio(media_path, audio_path)

            segments = consume_diarized_segments(json_path, media_path)

            overall_chunks = len(segments)
            redis_client.statusUpdate(job_id, "transcribing", total_chunks=overall_chunks)
            logger.info(f"Job {job_id}: split into {overall_chunks} chunks")

            if overall_chunks == 0:
                redis_client.statusUpdate(job_id, "failed", error="segments not found")
                continue

            for i in segments:
                payload = {
                    "job_id": job_id,
                    "chunk_path": i["file_path"],
                    "speaker": i["speaker"],
                    "start_ms": i["start"],
                    "duration_ms": i["duration_ms"],
                }
                logger.info(f"Payload: {payload}")

                redis_client.pushIntoQueue("queue:transcription", payload)
        except Exception as e:
            logger.error(f"Splitter worker failed duw to: {e}")

            if "job_id" in locals():
                error = str(e)
                redis_client.statusUpdate(job_id, "failed", error=error)

            time.sleep(1)

run_splitter()