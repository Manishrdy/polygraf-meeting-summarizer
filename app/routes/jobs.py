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


def _format_transcripts(transcripts_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Helper function to process the raw transcript list into the desired
    per_person, counts, and speakers format.
    """
    per_person: Dict[str, List[str]] = {}
    counts: Dict[str, int] = {}
    
    for t in transcripts_list:
        spk = t.get("speaker", "Unknown")
        txt = t.get("text", "")
        if txt.strip():
            per_person.setdefault(spk, []).append(txt)
            counts[spk] = counts.get(spk, 0) + 1
            
    speakers = list(per_person.keys())
    return {"per_person": per_person, "speakers": speakers, "counts": counts}


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

    try:
        logger.info(f"Job {job_id}: Receiving media file {file.filename}...")
        media_contents = await file.read()
        logger.info(f"Job {job_id}: Media file size read: {len(media_contents)} bytes")
        
        with open(local_media_path, "wb") as f:
            f.write(media_contents)
        logger.info(f"Job {job_id}: Media file saved to {local_media_path}")

        logger.info(f"Job {job_id}: Receiving JSON file {diarization_json.filename}...")
        json_contents = await diarization_json.read()
        logger.info(f"Job {job_id}: JSON file size read: {len(json_contents)} bytes")

        with open(local_json_path, "wb") as f:
            f.write(json_contents)
        logger.info(f"Job {job_id}: JSON file saved to {local_json_path}")

    except Exception as e:
        logger.error(f"Failed to save files for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded files.")
    
    if len(media_contents) == 0 or len(json_contents) == 0:
        logger.error(f"Job {job_id} failed: Uploaded files were empty.")
        raise HTTPException(status_code=400, detail="Uploaded files are empty.")

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
    job_data = redis_client.get_job_status(job_id)
    if not job_data:
        raise HTTPException(status_code=4404, detail="Job not found")
    
    job_status = job_data.get("status")

    # --- THIS IS THE NEW FINAL RESPONSE ---
    if job_status == "complete":
        logger.info(f"Job {job_id} is complete. Formatting final response.")
        
        # 1. Fetch and format transcripts
        transcripts_list = redis_client.get_all_transcripts(job_id)
        formatted_transcripts = _format_transcripts(transcripts_list)
        
        # 2. Fetch summary
        summary = {}
        if "result" in job_data:
            try:
                summary = json.loads(job_data["result"])
            except:
                summary = {"raw": job_data["result"]}
        
        # 3. Combine and return
        final_response = {
            "job_id": job_id,
            "status": "complete",
            "summary": summary,
            **formatted_transcripts # This adds 'per_person', 'speakers', and 'counts'
        }
        return final_response
    
    # --- Otherwise, just return the progress status ---
    return job_data