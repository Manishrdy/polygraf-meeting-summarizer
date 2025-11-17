import os
import sys
import json
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from google import genai
from app.services.redis_service import redis_client
from app.logger import get_logger
from app.config import GEMINI_API_KEY, GEMINI_MODEL_NAME, GEMINI_PROMPT_INSTRUCTION


logger = get_logger("worker-summarizer")

def check_gemini_api(GEMINI_API_KEY):
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set.")
        return
    logger.info(f"Gemini ai model anme: {GEMINI_MODEL_NAME}")
    return genai.Client(api_key=GEMINI_API_KEY)


def run_summarizer():

    logger.info("Inside worker summariser")

    client = check_gemini_api(GEMINI_API_KEY)

    while True:
        try:
            task = redis_client.removeFromQueue("queue:summary", timeout=0)

            if not task:
                continue

            job_id = task["job_id"]
            logger.info(f"Summarizing current job: {str(job_id)}")

            transcripts_list = redis_client.getTranscripts(job_id)

            per_person = {}
            for transcript in transcripts_list:
                speaker = transcript["speaker"]
                speaker_text = transcript["text"]

                stripped_text = speaker_text.strip()
                if stripped_text:
                    if speaker not in per_person:
                        per_person[speaker] = []
                    per_person[speaker].append(speaker_text)

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
                summary_object = json.loads(summary_text)
            except Exception:

                try:
                    a = summary_text.find("{")
                    b = summary_text.rfind("}")
                    if a != -1 and b != -1:
                        summary_object = json.loads(summary_text[a:b + 1])
                    else:
                        summary_object = {"raw": summary_text}
                except Exception:
                    summary_object = {"raw": summary_text}

            redis_client.save_summary(job_id, summary_object)
            redis_client.statusUpdate(job_id, "complete")

            logger.info(f"Job with id {job_id} completed")

        except Exception as e:
            logger.error(f"Summarizer worker failed: {str(e)}")
            
            if 'job_id' in locals():
                redis_client.statusUpdate(job_id, "failed", error=str(e))
            time.sleep(1)

run_summarizer()
