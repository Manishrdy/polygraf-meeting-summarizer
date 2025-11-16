import redis
import json
from app.config import REDIS_HOST, REDIS_PORT, REDIS_DB
from app.logger import get_logger

logger = get_logger(__name__)

class RedisService:
    def __init__(self):
        try:
            # decode_responses=True ensures we get Strings back, not Bytes
            self.client = redis.Redis(
                host=REDIS_HOST, 
                port=REDIS_PORT, 
                db=REDIS_DB, 
                decode_responses=True
            )
            self.client.ping()
            logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # We don't raise here to allow app to start, but workers will fail if Redis is down
            pass

    # --- Queue Operations ---
    def push_to_queue(self, queue_name: str, payload: dict):
        """
        Push a JSON task to the tail of a queue.
        """
        try:
            self.client.rpush(queue_name, json.dumps(payload))
        except Exception as e:
            logger.error(f"Error pushing to queue {queue_name}: {e}")

    def pop_from_queue(self, queue_name: str, timeout=0):
        """
        Blocking pop from the head of a queue. 
        Waits forever if timeout=0, or returns None after timeout seconds.
        """
        try:
            # blpop returns a tuple: (queue_name, data)
            result = self.client.blpop(queue_name, timeout=timeout)
            if result:
                return json.loads(result[1])
        except Exception as e:
            logger.error(f"Error popping from queue {queue_name}: {e}")
        return None

    # --- Job State Management ---
    def create_job(self, job_id: str):
        """Initialize a job entry in Redis Hash."""
        self.client.hset(f"job:{job_id}", mapping={
            "status": "queued",
            "created_at": "now", # Placeholder for simple timestamp
            "total_chunks": 0,
            "processed_chunks": 0
        })

    def update_status(self, job_id: str, status: str, **kwargs):
        """Update job status and optionally other fields (like error messages)."""
        data = {"status": status}
        data.update(kwargs)
        self.client.hset(f"job:{job_id}", mapping=data)

    def get_job_status(self, job_id: str):
        """Retrieve all fields for a job."""
        return self.client.hgetall(f"job:{job_id}")

    def increment_processed_count(self, job_id: str):
        """Atomically increment the processed chunks counter."""
        return self.client.hincrby(f"job:{job_id}", "processed_chunks", 1)

    # --- Result Storage ---
    def save_transcript_chunk(self, job_id: str, chunk_data: dict):
        """
        Append a transcribed chunk to a dedicated list for this job.
        We use a List structure: job:{id}:transcripts
        """
        self.client.rpush(f"job:{job_id}:transcripts", json.dumps(chunk_data))

    def get_all_transcripts(self, job_id: str):
        """Retrieve all transcribed chunks."""
        raw_list = self.client.lrange(f"job:{job_id}:transcripts", 0, -1)
        return [json.loads(item) for item in raw_list]

    def save_final_summary(self, job_id: str, summary: dict):
        """Save the final JSON summary into the job hash."""
        self.client.hset(f"job:{job_id}", "result", json.dumps(summary))

# Singleton instance to be imported elsewhere
redis_client = RedisService()