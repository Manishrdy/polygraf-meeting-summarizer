import os
import sys
import json
import time
from google import genai
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.services.redis_service import redis_client
from app.logger import get_logger
# Import all the config vars we need
from app.config import GEMINI_API_KEY, GEMINI_MODEL_NAME, GEMINI_PROMPT_INSTRUCTION

logger = get_logger("worker-summarizer")

# Helper to clean JSON from LLM
def _coerce_json(text: str):
    try:
        return json.loads(text)
    except:
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                return json.loads(text[start:end+1])
        except:
            return {"raw": text}

def run_summarizer():
    logger.info("Summarizer Worker Started. Listening on 'queue:summary'...")
    
    # --- THIS IS THE FIX ---
    # We check for the key at runtime, not module-level, so the app can load.
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set. Summarizer worker cannot start.")
        return # Exit the worker gracefully if no key
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    logger.info(f"Summarizer worker connected to Gemini with model: {GEMINI_MODEL_NAME}")

    while True:
        try:
            task = redis_client.pop_from_queue("queue:summary", timeout=0)
            if not task:
                continue

            job_id = task["job_id"]
            logger.info(f"Summarizing Job {job_id}...")

            # 1. Fetch all transcripts from Redis
            transcripts_list = redis_client.get_all_transcripts(job_id)
            
            # 2. Reformat for the Prompt
            per_person = {}
            for t in transcripts_list:
                spk = t["speaker"]
                txt = t["text"]
                if txt.strip():
                    per_person.setdefault(spk, []).append(txt)

            prompt_payload = {
                "instruction": GEMINI_PROMPT_INSTRUCTION,
                "per_person_transcripts": per_person
            }

            # 3. Call LLM
            resp = client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=json.dumps(prompt_payload, ensure_ascii=False)
            )
            
            summary_obj = _coerce_json(getattr(resp, "text", ""))

            # 4. Save Final Result
            redis_client.save_final_summary(job_id, summary_obj)
            redis_client.update_status(job_id, "complete")
            logger.info(f"Job {job_id} Completed Successfully.")

        except Exception as e:
            logger.exception(f"Summarizer Worker Failed: {e}")
            if 'job_id' in locals():
                redis_client.update_status(job_id, "failed", error=str(e))
            time.sleep(1)

# Note: The 'RuntimeError' from line 45 is now gone.

if __name__ == "__main__":
    run_summarizer()