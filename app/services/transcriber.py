import os
import whisper
from pydub import AudioSegment
from app.logger import get_logger

logger = get_logger(__name__)
LOADED_MODEL = None

def load_model_once():
    global LOADED_MODEL
    if LOADED_MODEL is None:
        LOADED_MODEL = whisper.load_model("base")
        logger.info("Whisper model loaded")
    return LOADED_MODEL

def transcribe_audio(file_path):
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return ""

    try:
        audio = AudioSegment.from_wav(file_path)
    except Exception:
        logger.warning(f"Skipping {file_path}: Can't read audio")
        return ""

    if len(audio) < 100:
        logger.warning(f"Skipping {file_path}: Audio too short ({len(audio)})")
        return ""

    try:
        model = load_model_once()
        logger.info(f"Starting transcription for: {file_path}")
        result = model.transcribe(file_path, fp16=False)
        text = result.get("text", "").strip()
        logger.info(f"Transcription complete. Result: {text[:50]}...")
        return text
    except Exception as exc:
        logger.error(f"CRASH PREVENTED for {file_path}: {exc}")
        return ""
