import uuid
import os
import shutil
import json
from app.config import UPLOAD_DIR
from app.services.redis_service import redis_client
from app.logger import get_logger
from fastapi import APIRouter, UploadFile, File, HTTPException, Form


router = APIRouter(tags=["jobs"])
logger = get_logger(__name__)

logger.info("-- Inside app.routes.jobs --")

def format_transcripts(transcripts_list):

    if not transcripts_list:
        return {}

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
    job_path = os.path.join(UPLOAD_DIR, job_id)

    if not os.path.exists(job_path):
        os.makedirs(job_path, exist_ok=True)

    file_extension = os.path.splitext(file.filename)[1]
    local_media_path = os.path.join(job_path, f"media{file_extension}")
    local_json_path = os.path.join(job_path, "diarization.json")

    media_contents = b""
    json_contents = b""

    try:
        media_contents = await file.read()
        with open(local_media_path, "wb") as media_file:
            media_file.write(media_contents)

        json_contents = await diarization_json.read()

        with open(local_json_path, "wb") as json_file:
            json_file.write(json_contents)
    except Exception as e:
        logger.error(f"Failed to save files {job_id}: {e}")
        reason = "Failed to save uploaded files"
        raise HTTPException(status_code=500, detail=reason)

    if not media_contents or not json_contents == 0:
        logger.error(f"Job {job_id} failed. No files found")
        reason = "There were no files found"
        raise HTTPException(status_code=400, detail=reason)

    redis_client.jobCreation(job_id)

    payload = {}
    payload["job_id"] = job_id
    payload["media_path"] = local_media_path
    payload["json_path"] = local_json_path
    payload["job_dir"] = job_path

    logger.info(f"Task payloadd: {payload}")
    redis_client.pushIntoQueue("queue:splitting", payload)
    return {"job_id": job_id, "status": "queued"} 

@router.get("/jobs/{job_id}")
def get_job_status(job_id):

    logger.info("-- Inside get_job_status in app.routes.jobs --")

    job_data = redis_client.get_job_status(job_id)
    logger.info(f"job_data: {job_data}")

    if not job_data:
        logger.error(f"Job data not found; {job_data}")
        reason = f"Job with {job_id}, not found"
        raise HTTPException(status_code=404, detail=reason)
    
    job_status = job_data.get("status")
    if job_status == "complete":
        logger.info(f"{job_id} is completed")

        transcripts_list = redis_client.getTranscripts(job_id)
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