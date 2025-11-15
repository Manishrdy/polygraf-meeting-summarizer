# app/routes/summary.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import os, json, re

from app.logger import get_logger
from google import genai

logger = get_logger(__name__)
router = APIRouter(tags=["summary"])

class TranscriptsEnvelope(BaseModel):
    per_person: Dict[str, List[str]] = Field(..., description="Per-person transcript map")
    class Config:
        extra = "allow"  # ignore other keys (status/saved_to/speakers/counts/etc.)

def _coerce_json(text: str) -> Dict[str, Any]:
    """Try to parse strict JSON; if not, extract the first {...} block; else wrap raw."""
    if not text:
        return {"raw": ""}

    # 1) direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) try to grab the first JSON object in the string
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            inner = text[start:end+1]
            return json.loads(inner)
    except Exception:
        pass

    # 3) fallback
    return {"raw": text}

@router.post("/summary")
def summary_from_transcripts(body: TranscriptsEnvelope) -> Dict[str, Any]:
    try:
        logger.info("POST /summary called (expects full /transcripts response).")

        per_person = body.per_person
        if not per_person or not isinstance(per_person, dict):
            logger.error("Missing or invalid per_person in request.")
            raise HTTPException(status_code=400, detail="Missing or invalid per_person in request body.")

        # --- LLM setup ---
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY/GOOGLE_API_KEY is not set.")
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY/GOOGLE_API_KEY not set.")
        model_id = os.getenv("GENAI_MODEL", "gemini-2.5-flash")

        client = genai.Client(api_key=api_key)

        # Prompt asks for STRICT JSON; we won’t pass generation_config (compat with older libs)
        prompt = {
            "instruction": (
                "Return ONLY strict JSON with keys: "
                "keypoints (array of strings, 3-7), "
                "decisions (array of strings), "
                "action_items (array of {owner, task, due_date}), "
                "per_speaker_summary (object mapping speaker -> short summary). "
                "No prose outside the JSON. Use only facts present in the input."
            ),
            "per_person_transcripts": per_person
        }

        logger.info(f"Calling model '{model_id}' for structured summary JSON (no generation_config).")
        resp = client.models.generate_content(
            model=model_id,
            contents=json.dumps(prompt, ensure_ascii=False)
        )

        text = getattr(resp, "text", "") or ""
        summary_obj = _coerce_json(text)

        logger.info("Summary generated successfully.")
        return summary_obj

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Summary generation failed.")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {e}")
