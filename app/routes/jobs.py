from fastapi import APIRouter, UploadFile, File, HTTPException, Form
import uuid
import os
import shutil
import json
from app.config import UPLOAD_DIR
from app.services.redis_service import redis_client
from app.logger import get_logger
from typing import List, Dict, Any

router = APIRouter(tags=["jobs"])
logger = get_logger(__name__)

logger.info("-- Inside app.routes.jobs --")

def format_transcripts(transcripts_list):
    logger.info("Inside format_transcripts in app.routes.jobs")

    people = {}
    how_many = {}
    speakers = []

    for transcript in transcripts_list:
        person = transcript.get("speaker", "Unknown")
        words = transcript.get("text", "")
        if words.strip() != "":
            if person not in people:
                people[person] = []
            people[person].append(words)
            if person in how_many:
                how_many[person] = how_many[person] + 1
            else:
                how_many[person] = 1

    for p in people:
        speakers.append(p)

    logger.info(
        {
            "per_person": people,
            "speakers": speakers,
            "counts": how_many
        }
    )
    return {
        "per_person": people, 
        "speakers": speakers, 
        "counts": how_many
    }


@router.post("/jobs", status_code=202)
async def submit_job(file: UploadFile = File(...), diarization_json: UploadFile = File(...)):

    logger.info("-- Inside submit_job in app.routes.jobs --")

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(UPLOAD_DIR, job_id)
    if not os.path.exists(job_dir):
        os.makedirs(job_dir, exist_ok=True)

    file_ext = os.path.splitext(file.filename)[1]
    local_media_path = os.path.join(job_dir, f"media{file_ext}")
    local_json_path = os.path.join(job_dir, "diarization.json")

    media_contents = b""
    json_contents = b""

    try:
        logger.info(f"Job {job_id}: Receiving media file {file.filename}...")
        media_contents = await file.read()
        logger.info(f"Job {job_id}: Media file size: {len(media_contents)}")

        with open(local_media_path, "wb") as media_file:
            media_file.write(media_contents)
        logger.info(f"Job {job_id}: Media file saved to {local_media_path}")

        logger.info(f"Job {job_id}: Receiving JSON file {diarization_json.filename}...")
        json_contents = await diarization_json.read()
        logger.info(f"Job {job_id}: JSON file size read: {len(json_contents)}")

        with open(local_json_path, "wb") as json_file:
            json_file.write(json_contents)
        logger.info(f"Job {job_id}: JSON file saved to {local_json_path}")

    except Exception as e:
        logger.error(f"Failed to save files in submit_job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded files")

    if len(media_contents) == 0 or len(json_contents) == 0:
        logger.error(f"Job {job_id} failed, Empty files or no files")
        raise HTTPException(status_code=400, detail="Empty files or no files")

    redis_client.create_job(job_id)

    task_payload = {}
    task_payload["job_id"] = job_id
    task_payload["media_path"] = local_media_path
    task_payload["json_path"] = local_json_path
    task_payload["job_dir"] = job_dir
    logger.info(f"task_payload: {task_payload}")

    redis_client.push_to_queue("queue:splitting", task_payload)

    logger.info(f"Job {job_id} submitted and in queued")
    return {"job_id": job_id, "status": "queued"}

@router.get("/jobs/{job_id}")
def get_job_status(job_id):

    logger.info("-- Inside get_job_status in app.routes.jobs --")

    job_data = redis_client.get_job_status(job_id)
    if not job_data:
        logger.error(f"Job data not found; {job_data}")
        raise HTTPException(status_code=404, detail="Job not found")
    
    logger.info(f"job_data: {job_data}")
    job_status = job_data.get("status")

    if job_status == "complete":
        logger.info(f"Job {job_id} is complete")

        transcripts_list = redis_client.get_all_transcripts(job_id)
        formatted_transcripts = format_transcripts(transcripts_list)
        
        summary = {}
        if "result" in job_data:
            try:
                summary = json.loads(job_data["result"])
            except:
                summary = {
                    "raw": job_data["result"]
                }
        
        final_response = {
            "job_id": job_id,
            "status": "complete",
            "summary": summary,
            **formatted_transcripts
        }
        return final_response
    
    return job_data