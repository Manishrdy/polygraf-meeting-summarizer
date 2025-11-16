import os
import whisper
from pydub import AudioSegment
from app.logger import get_logger

logger = get_logger(__name__)

_model = None

def get_model():
    global _model
    if _model is None:
        logger.info("Loading Whisper model (base)...")
        _model = whisper.load_model("base")
        logger.info("Whisper model loaded.")
    return _model

def transcribe_audio(file_path: str) -> str:

    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return ""

    try:
        # 1. Safety Check: Is the file empty or too short?
        # We use pydub to quickly check duration without loading the heavy model
        try:
            audio = AudioSegment.from_wav(file_path)
            if len(audio) < 100: # Less than 100ms is likely noise/empty
                logger.warning(f"Skipping {file_path}: Audio too short ({len(audio)}ms)")
                return ""
        except Exception:
            logger.warning(f"Skipping {file_path}: Could not read audio header.")
            return ""

        # 2. Transcribe
        model = get_model()
        logger.info(f"Starting transcription for: {file_path}")
        
        # fp16=False is mandatory for CPU to avoid warnings/errors
        result = model.transcribe(file_path, fp16=False)
        text = result.get("text", "").strip()
        
        logger.info(f"Transcription complete. Result: {text[:50]}...")
        return text

    except Exception as e:
        logger.error(f"CRASH PREVENTED for {file_path}: {e}")
        return ""