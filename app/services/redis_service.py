import json
import redis
from app.config import REDIS_HOST, REDIS_PORT, REDIS_DB
from app.logger import get_logger

logger = get_logger(__name__)


class RedisService:
    def __init__(self):
        try:
            self.client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
            self.client.ping()
            logger.info(f"Connected to redis at {REDIS_HOST}:{REDIS_PORT}")
        except Exception as error:
            logger.error(f"Failed to connect to redis: {error}")

    def push_to_queue(self, queue_name, payload):
        try:
            body = json.dumps(payload)
            self.client.rpush(queue_name, body)
        except Exception as error:
            logger.error(f"Error pushing to queue {queue_name}: {error}")

    def pop_from_queue(self, queue_name, timeout=0):
        try:
            item = self.client.blpop(queue_name, timeout=timeout)
            if item:
                _, value = item
                return json.loads(value)
        except Exception as error:
            logger.error(f"Error popping from queue {queue_name}: {error}")
        return None

    def create_job(self, job_id):
        data = {
            "status": "queued",
            "created_at": "now",
            "total_chunks": 0,
            "processed_chunks": 0,
        }
        self.client.hset(f"job:{job_id}", mapping=data)

    def update_status(self, job_id, status, **extra):
        data = {"status": status}
        data.update(extra)
        self.client.hset(f"job:{job_id}", mapping=data)

    def get_job_status(self, job_id):
        return self.client.hgetall(f"job:{job_id}")

    def increment_processed_count(self, job_id):
        return self.client.hincrby(f"job:{job_id}", "processed_chunks", 1)

    def save_transcript_chunk(self, job_id, chunk_data):
        body = json.dumps(chunk_data)
        self.client.rpush(f"job:{job_id}:transcripts", body)

    def get_all_transcripts(self, job_id):
        key = f"job:{job_id}:transcripts"
        items = self.client.lrange(key, 0, -1)
        return [json.loads(item) for item in items]

    def save_final_summary(self, job_id, summary):
        body = json.dumps(summary)
        self.client.hset(f"job:{job_id}", "result", body)


redis_client = RedisService()