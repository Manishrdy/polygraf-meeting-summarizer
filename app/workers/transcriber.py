import os
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.services.redis_service import redis_client
from app.services.transcriber import transcribe_audio, load_model
from app.logger import get_logger



logger = get_logger("worker-transcriber")
logger.info("Inside workers.transcriber function")

def run_transcriber():

    m = load_model()

    if m is None:
        logger.info("no model loaded")
        time.sleep(1)

    while True:

        task = None

        try:
            task_name = "queue:transcription"
            task = redis_client.removeFromQueue(task_name, timeout=0)
        except Exception as e:
            logger.exception(f"Error on processing queue: {e}")
            time.sleep(1)

        if not task:
            time.sleep(0.01)
            continue

        job_id = task["job_id"]
        chunk_path = task["chunk_path"]
        speaker = task["speaker"]

        try:
            text = transcribe_audio(chunk_path)
        except Exception as e:
            logger.exception(f"Error while transcribing chunks: {e}")
            text = ""

        chunk_data = {}
        chunk_data["speaker"] = speaker
        chunk_data["text"] = text
        chunk_data["timestamp_ms"] = task.get("start_ms")

        try:
            redis_client.saveTranscriptsFromChunks(job_id, chunk_data)
            new_count = redis_client.increment_processed_count(job_id)

        except Exception as e:
            logger.exception(f"Couldn't save chunks: {e}")
            continue

        job_info = redis_client.get_job_status(job_id)
        total_chunks = job_info.get("total_chunks")

        if not total_chunks:
            total_chunks = 0
        
        total_chunks = int(total_chunks)
    
        if new_count >= total_chunks and total_chunks != 0:
            try:
                redis_client.statusUpdate(job_id, "summarizing")
                redis_client.pushIntoQueue("queue:summary", {"job_id": job_id})
            except Exception as e:
                logger.exception(f"Cant push summar into redis: {e}")
        time.sleep(0.001)

run_transcriber()