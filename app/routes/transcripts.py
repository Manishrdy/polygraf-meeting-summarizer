# app/routes/transcripts.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List
from pathlib import Path
import os, json

from app.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["transcripts"])

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
OUT_PATH = DATA_DIR / "per_person_transcripts.json"
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".ogg", ".flac"}

class TranscriptsIn(BaseModel):
    audio_chunks_dir: str = Field(..., description="Folder path containing audio chunks")
    diarization_json_path: str = Field(..., description="Path to diarized response.json")

class TranscriptsOut(BaseModel):
    status: str
    saved_to: str
    speakers: List[str]
    counts: Dict[str, int]
    per_person: Dict[str, List[str]]  # ← include the generated content in the response

def _load_segments(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for k in ("segments", "utterances", "items", "results"):
            v = payload.get(k)
            if isinstance(v, list):
                return v
    return []

def _extract_speaker(seg: Dict[str, Any]) -> str:
    for k in ("speaker", "speaker_id", "spk", "name", "speaker_name"):
        v = seg.get(k)
        if v not in (None, ""):
            return str(v)
    v = seg.get("speaker_uuid") or seg.get("speaker_user_uuid")
    return str(v) if v else "UNKNOWN"

def _extract_text(seg: Dict[str, Any]) -> str:
    # Try common top-level keys first
    for k in ("text", "transcript", "utterance", "content"):
        v = seg.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()

    # Then nested transcription structures
    t = seg.get("transcription")
    if isinstance(t, dict):
        v = t.get("transcript")
        if isinstance(v, str) and v.strip():
            return v.strip()
        alts = t.get("alternatives")
        if isinstance(alts, list):
            for alt in alts:
                if isinstance(alt, dict):
                    v = alt.get("transcript") or alt.get("content")
                    if isinstance(v, str) and v.strip():
                        return v.strip()

    return ""

@router.post("/transcripts", response_model=TranscriptsOut)
def build_per_person_transcripts(body: TranscriptsIn) -> TranscriptsOut:
    try:
        logger.info("POST /transcripts called.")
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        audio_dir = Path(body.audio_chunks_dir)
        diar_path = Path(body.diarization_json_path)

        # Validate paths
        if not audio_dir.exists() or not audio_dir.is_dir():
            logger.error(f"Audio folder not found: {audio_dir}")
            raise HTTPException(status_code=400, detail=f"Audio folder not found: {audio_dir}")

        audio_files = [p for p in audio_dir.iterdir() if p.suffix.lower() in AUDIO_EXTS]
        if not audio_files:
            logger.error("No audio chunks found with supported extensions.")
            raise HTTPException(status_code=400, detail="No audio chunks found (.wav/.mp3/.m4a/.ogg/.flac).")

        if not diar_path.exists() or not diar_path.is_file():
            logger.error(f"Diarization JSON not found: {diar_path}")
            raise HTTPException(status_code=400, detail=f"Diarization JSON not found: {diar_path}")

        # Load diarization JSON
        diar_json = json.loads(diar_path.read_text(encoding="utf-8"))
        segments = _load_segments(diar_json)
        if not segments:
            logger.error("Could not find segments in diarization JSON.")
            raise HTTPException(status_code=400, detail="Invalid diarization JSON: no segments/utterances/items/results.")

        # Aggregate per speaker
        per_person: Dict[str, List[str]] = {}
        counts: Dict[str, int] = {}

        for seg in segments:
            text = _extract_text(seg)
            if not text:
                continue
            speaker = _extract_speaker(seg)
            per_person.setdefault(speaker, []).append(text)
            counts[speaker] = counts.get(speaker, 0) + 1

        if not per_person:
            logger.error("No textual content extracted from diarization JSON.")
            raise HTTPException(status_code=400, detail="No text found in diarization segments.")

        # Save output to disk
        OUT_PATH.write_text(json.dumps(per_person, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"per_person_transcripts saved -> {OUT_PATH}")

        # Also return the content inline
        return TranscriptsOut(
            status="ok",
            saved_to=str(OUT_PATH),
            speakers=list(per_person.keys()),
            counts=counts,
            per_person=per_person,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to build per_person_transcripts.")
        raise HTTPException(status_code=500, detail=f"Failed to build per_person_transcripts: {e}")
