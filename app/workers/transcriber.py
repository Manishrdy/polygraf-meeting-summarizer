import os
import sys
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.services.redis_service import redis_client
from app.services.transcriber import transcribe_audio, get_model
from app.logger import get_logger

logger = get_logger("worker-transcriber")

def run_transcriber():
    # Pre-load model into memory ONCE at startup
    logger.info("Loading Whisper model...")
    get_model() 
    logger.info("Transcriber Worker Started. Listening on 'queue:transcription'...")

    while True:
        try:
            task = redis_client.pop_from_queue("queue:transcription", timeout=0)
            if not task:
                continue

            job_id = task["job_id"]
            chunk_path = task["chunk_path"]
            speaker = task["speaker"]

            # 1. Transcribe
            text = transcribe_audio(chunk_path)

            # 2. Save Partial Result to Redis
            chunk_data = {
                "speaker": speaker,
                "text": text,
                "timestamp_ms": task.get("start_ms")
            }
            redis_client.save_transcript_chunk(job_id, chunk_data)

            # 3. Increment Progress
            new_count = redis_client.increment_processed_count(job_id)
            
            # 4. Check Completion
            job_info = redis_client.get_job_status(job_id)
            total_chunks = int(job_info.get("total_chunks", 0))

            logger.info(f"Job {job_id}: Processed {new_count}/{total_chunks}")

            if new_count >= total_chunks:
                logger.info(f"Job {job_id}: All chunks processed. Queueing for summary.")
                redis_client.update_status(job_id, "summarizing")
                redis_client.push_to_queue("queue:summary", {"job_id": job_id})

        except Exception as e:
            logger.exception(f"Transcriber Worker Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    run_transcriber()