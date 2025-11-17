import os
import sys
import json
import time
from google import genai

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.services.redis_service import redis_client
from app.logger import get_logger
from app.config import GEMINI_API_KEY, GEMINI_MODEL_NAME, GEMINI_PROMPT_INSTRUCTION

logger = get_logger("worker-summarizer")

def run_summarizer():

    logger.info("Summarizer worker on 'queue:summary'")

    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set.")
        return
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    logger.info("using gemini model: " + str(GEMINI_MODEL_NAME))

    while True:
        try:
            task = redis_client.pop_from_queue("queue:summary", timeout=0)

            if not task:
                continue

            job_id = task["job_id"]
            logger.info("Summarizing Job " + str(job_id))

            transcripts_list = redis_client.get_all_transcripts(job_id)

            per_person = {}
            for transcript in transcripts_list:
                spk = transcript["speaker"]
                txt = transcript["text"]
                if txt.strip():
                    per_person.setdefault(spk, []).append(txt)

            prompt_payload = {
                "instruction": GEMINI_PROMPT_INSTRUCTION,
                "per_person_transcripts": per_person
            }

            resp = client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=json.dumps(prompt_payload, ensure_ascii=False)
            )

            summary_text = getattr(resp, "text", "")

            try:
                summary_obj = json.loads(summary_text)
            except Exception:
                try:
                    a = summary_text.find("{")
                    b = summary_text.rfind("}")
                    if a != -1 and b != -1:
                        summary_obj = json.loads(summary_text[a:b + 1])
                    else:
                        summary_obj = {"raw": summary_text}
                except Exception:
                    summary_obj = {"raw": summary_text}

            redis_client.save_final_summary(job_id, summary_obj)
            redis_client.update_status(job_id, "complete")

            logger.info("Job " + str(job_id) + " Completed Successfully.")

        except Exception as e:
            logger.exception("Summarizer Worker Failed: " + str(e))
            
            if 'job_id' in locals():
                redis_client.update_status(job_id, "failed", error=str(e))
            time.sleep(1)

run_summarizer()
