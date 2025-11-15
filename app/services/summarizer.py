import os
import json
from typing import Any, Dict
from google import genai
from app.logger import get_logger
from app.config import GEMINI_API_KEY, GEMINI_MODEL_NAME, DATA_DIR

logger = get_logger()


def _select_model(config_name: str | None) -> str:

    name = (config_name or "").strip()
    if not name:
        return "gemini-2.5-flash"
    if name.startswith("gemini-1."):
        logger.warning(f"Model '{name}' is deprecated; using 'gemini-2.5-flash'.")
        return "gemini-2.5-flash"
    return name


class GeminiSummarizer:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = _select_model(GEMINI_MODEL_NAME)
        logger.info(f"Gemini model loaded: {self.model}")

    def _build_prompt(self, per_speaker: Dict[str, Any], full_text: str) -> str:
        return f"""You are Polygraf's meeting summarizer. Produce a concise, factual, structured report.

Sections (JSON keys):
- key_points: 3–5 bullets
- decisions: bullets
- action_items: bullets with owner and due if mentioned
- per_speaker_summary: dict of speaker -> 1–3 sentence summary

Rules:
- No hallucinations. If info is missing, use "Unassigned" / "Date not specified".

PER_SPEAKER (JSON):
{json.dumps(per_speaker, ensure_ascii=False)}

FULL_TRANSCRIPT:
{full_text}
"""

    def summarize(self, per_speaker: Dict[str, Any], full_text: str) -> Dict[str, str]:
        prompt = self._build_prompt(per_speaker, full_text)

        resp = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        # Preferred accessor on google-genai responses
        text = getattr(resp, "text", "") or ""
        if not text:
            # Fallback parse
            try:
                parts = resp.candidates[0].content.parts
                text = "".join(getattr(p, "text", "") for p in parts)
            except Exception:
                text = str(resp)

        os.makedirs(DATA_DIR, exist_ok=True)
        out_path = os.path.join(DATA_DIR, "summary.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text.strip())
        logger.info(f"Summary saved -> {out_path}")
        return {"summary": text.strip(), "path": out_path}
