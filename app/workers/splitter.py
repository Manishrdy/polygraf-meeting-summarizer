import os
import time
import sys
# Add project root to path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.services.redis_service import redis_client
from app.services.audio_extractor import extract_audio
from app.services.consumer import consume_diarized_segments
from app.logger import get_logger

logger = get_logger("worker-splitter")

def run_splitter():
    logger.info("Splitter Worker Started. Listening on 'queue:splitting'...")
    
    while True:
        try:
            # Blocking pop (wait until a job arrives)
            task = redis_client.pop_from_queue("queue:splitting", timeout=0)
            if not task:
                continue

            job_id = task["job_id"]
            media_path = task["media_path"]
            json_path = task["json_path"]
            
            logger.info(f"Processing Job {job_id}")
            redis_client.update_status(job_id, "processing_audio")

            # 1. Extract Audio if video
            audio_path = media_path
            if media_path.lower().endswith(".mp4"):
                audio_path = media_path.replace(".mp4", ".wav")
                extract_audio(media_path, audio_path)

            # 2. Split Audio based on Diarization
            # Note: consume_diarized_segments currently saves to DATA_DIR/sample_audio
            segments = consume_diarized_segments(json_path, audio_path)
            
            total_chunks = len(segments)
            redis_client.update_status(job_id, "transcribing", total_chunks=total_chunks)
            logger.info(f"Job {job_id}: Split into {total_chunks} chunks.")

            if total_chunks == 0:
                 # Handle edge case of no speech
                 redis_client.update_status(job_id, "failed", error="No segments found")
                 continue

            # 3. Push each chunk to Transcription Queue
            for segment in segments:
                payload = {
                    "job_id": job_id,
                    "chunk_path": segment["file_path"],
                    "speaker": segment["speaker"],
                    "start_ms": segment["start"],
                    "duration_ms": segment["duration_ms"]
                }
                redis_client.push_to_queue("queue:transcription", payload)

        except Exception as e:
            logger.exception(f"Splitter Worker Failed: {e}")
            if 'job_id' in locals():
                redis_client.update_status(job_id, "failed", error=str(e))
            time.sleep(1)

if __name__ == "__main__":
    run_splitter()