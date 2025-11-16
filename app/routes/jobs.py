from fastapi import APIRouter, UploadFile, File, HTTPException, Form
import uuid
import os
import shutil
import json
from app.config import UPLOAD_DIR
from app.services.redis_service import redis_client
from app.logger import get_logger

router = APIRouter(tags=["jobs"])
logger = get_logger(__name__)

@router.post("/jobs", status_code=202)
async def submit_job(
    file: UploadFile = File(...),
    diarization_json: UploadFile = File(...)
):
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(UPLOAD_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    # 1. Save uploaded files
    file_ext = os.path.splitext(file.filename)[1]
    local_media_path = os.path.join(job_dir, f"media{file_ext}")
    local_json_path = os.path.join(job_dir, "diarization.json")

    with open(local_media_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    with open(local_json_path, "wb") as f:
        shutil.copyfileobj(diarization_json.file, f)

    # 2. Initialize Job in Redis
    redis_client.create_job(job_id)

    # 3. Push to Splitter Queue
    task_payload = {
        "job_id": job_id,
        "media_path": local_media_path,
        "json_path": local_json_path,
        "job_dir": job_dir
    }
    redis_client.push_to_queue("queue:splitting", task_payload)

    logger.info(f"Job {job_id} submitted and queued.")
    return {"job_id": job_id, "status": "queued"}

@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    status = redis_client.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Parse result JSON if it exists
    if "result" in status:
        try:
            status["result"] = json.loads(status["result"])
        except:
            pass
            
    return status