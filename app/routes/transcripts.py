from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List
from pathlib import Path
import os
import json
import concurrent.futures

from app.logger import get_logger
from app.services.transcriber import transcribe_audio

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
    per_person: Dict[str, List[str]]

def process_single_file(audio_file: Path, diar_data: List[Dict]) -> Dict:
    """
    Helper function to be run in a separate thread.
    Returns a dict with {speaker: str, text: str} or None if failed.
    """
    try:
        filename_stem = audio_file.stem
        # Filename format expected: "SpeakerName_Index.wav"
        parts = filename_stem.rsplit('_', 1)

        if len(parts) < 2 or not parts[1].isdigit():
            return None
        
        index = int(parts[1])

        # Look up speaker
        speaker_name = "Unknown"
        if 0 <= index < len(diar_data):
            speaker_name = diar_data[index].get("speaker_name", "Unknown")
        
        # Transcribe (Heavy Operation)
        text = transcribe_audio(str(audio_file))
        
        if text:
            return {"speaker": speaker_name, "text": text}
    except Exception as e:
        logger.error(f"Error in thread for {audio_file.name}: {e}")
    
    return None

@router.post("/transcripts", response_model=TranscriptsOut)
def build_per_person_transcripts(body: TranscriptsIn) -> TranscriptsOut:
    try:
        logger.info("POST /transcripts called - Starting CONCURRENT transcription.")
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        audio_dir = Path(body.audio_chunks_dir)
        diar_path = Path(body.diarization_json_path)

        # 1. Validation
        if not audio_dir.exists() or not audio_dir.is_dir():
            raise HTTPException(status_code=400, detail=f"Audio folder not found: {audio_dir}")
        if not diar_path.exists() or not diar_path.is_file():
            raise HTTPException(status_code=400, detail=f"Diarization JSON not found: {diar_path}")

        # 2. Load Diarization Data
        try:
            diar_data = json.loads(diar_path.read_text(encoding="utf-8"))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid diarization JSON.")

        # 3. Find Audio Files
        audio_files = [p for p in audio_dir.iterdir() if p.suffix.lower() in AUDIO_EXTS]
        if not audio_files:
            raise HTTPException(status_code=400, detail="No audio chunks found.")

        # Sort to maintain some logical order before processing
        audio_files.sort(key=lambda p: p.name)

        per_person: Dict[str, List[str]] = {}
        counts: Dict[str, int] = {}

        # 4. Concurrent Execution
        # We use a ThreadPoolExecutor. The max_workers defaults to 5 * num_cpus, 
        # which is usually fine for I/O + some CPU tasks like this.
        # Adjust max_workers if your CPU throttles (e.g., max_workers=4)
        logger.info(f"Processing {len(audio_files)} files in parallel...")
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(process_single_file, f, diar_data): f 
                for f in audio_files
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_file):
                result = future.result()
                if result:
                    spk = result["speaker"]
                    txt = result["text"]
                    per_person.setdefault(spk, []).append(txt)
                    counts[spk] = counts.get(spk, 0) + 1

        # 5. Save Output
        OUT_PATH.write_text(json.dumps(per_person, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"Transcription complete. Saved to {OUT_PATH}")

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
        logger.exception("Fatal error in /transcripts")
        raise HTTPException(status_code=500, detail=str(e))