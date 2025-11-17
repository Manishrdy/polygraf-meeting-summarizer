import json
import redis
from app.config import REDIS_HOST, REDIS_PORT, REDIS_DB
from app.logger import get_logger

logger = get_logger(__name__)

logger.info("Inside app.services.redis_service")


class RedisService:
    def __init__(self):
        host, redis_port,db, decode_responses = REDIS_HOST, REDIS_PORT, REDIS_DB, True
        self.client = redis.Redis(host=host, port=redis_port, db=db, decode_responses=decode_responses)

        self.client.ping()

        logger.info(f"Redis connection successful {REDIS_HOST}:{REDIS_PORT}")
    
    def get_job_status(self, job_id):
        key_repr = f"job:{job_id}"
        job_id_status = self.client.hgetall(key_repr)
        return job_id_status

    def increment_processed_count(self, job_id):
        key_repr = f"job:{job_id}"
        incr_val = self.client.hincrby(key_repr, "processed_chunks", 1)
        return incr_val

    def jobCreation(self, job_id):
        job_key = f"Job:{job_id}"
        self.client.hset(job_key, mapping={
            "status": "queued",
            "createdAt": "now",
            "total_chunks": 0,
            "processed_chunks": 0,
        })

    def pushIntoQueue(self, queue_name, payload):
        body = json.dumps(payload)
        self.client.rpush(queue_name, body)

    def statusUpdate(self, job_id, status, **extra):
        data = {
            "status": status
        }
        data.update(extra)

        job_key = f"job:{job_id}"
        self.client.hset(job_key, mapping=data)

    def removeFromQueue(self, queue_name, timeout=0):
        item = self.client.blpop(queue_name, timeout=timeout)

        if not item:
            return None
        else:
            void, value = item
            return json.loads(value)

    def saveTranscriptsFromChunks(self, job_id, chunk_data):
        body = json.dumps(chunk_data)
        # logger.info(f"In saveTranscriptsFromChunks {body}")
        job_transcripts_key = f"job:{job_id}:transcripts"
        self.client.rpush(job_transcripts_key, body)

    def getTranscripts(self, job_id):
        job_transcripts_key = f"job:{job_id}:transcripts"
        items = self.client.lrange(job_transcripts_key, 0, -1)

        res = []
        for item in items:
            res.append(json.loads(item))
        
        return res

    def save_summary(self, job_id, summary):
        body = json.dumps(summary)
        job_key = f"job:{job_id}"
        self.client.hset(job_key, "result", body)


redis_client = RedisService()