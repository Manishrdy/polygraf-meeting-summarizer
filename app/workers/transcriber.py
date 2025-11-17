import os
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app.services.redis_service import redis_client
from app.services.transcriber import transcribe_audio, get_model
from app.logger import get_logger

logger = get_logger("worker-transcriber")

def run_transcriber():

    m = get_model()
    if m is None:
        logger.info("no model")
        time.sleep(1)

    logger.info("Transcriber on 'queue:transcription")

    while True:

        task = None
        try:
            task = redis_client.pop_from_queue("queue:transcription", timeout=0)
        except Exception as weird:
            logger.exception("queue error %s" % weird)
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
            logger.exception(e)
            text = ""

        chunk_data = {}
        chunk_data["speaker"] = speaker
        chunk_data["text"] = text
        chunk_data["timestamp_ms"] = task.get("start_ms")

        try:
            redis_client.save_transcript_chunk(job_id, chunk_data)
            new_count = redis_client.increment_processed_count(job_id)
        except Exception as badsave:
            logger.exception("cant save chunk: %s" % badsave)
            continue

        job_info = redis_client.get_job_status(job_id)
        total_chunks = job_info.get("total_chunks")

        if not total_chunks:
            total_chunks = 0
        
        total_chunks = int(total_chunks)
        logger.info("Job " + str(job_id) + ": processed " + str(new_count) + "/" + str(total_chunks))
    
        if new_count >= total_chunks and total_chunks != 0:
            try:
                redis_client.update_status(job_id, "summarizing")
                redis_client.push_to_queue("queue:summary", {"job_id": job_id})
            except Exception as meh:
                logger.exception("cant push summary %s" % meh)
        time.sleep(0.001)

run_transcriber()