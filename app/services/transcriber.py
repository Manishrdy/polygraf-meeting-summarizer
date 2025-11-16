import whisper
from app.logger import get_logger

logger = get_logger(__name__)
_model = None

def get_model():
    global _model
    if _model is None:
        logger.info("Loading Whisper model")
        _model = whisper.load_model("base")
        logger.info("Whisper model loaded successfully.")
    return _model

def transcribe_audio(file_path: str) -> str:
    try:
        model = get_model()
        logger.info(f"Starting transcription for: {file_path}")
        
        # The transcribe function returns a dictionary, we just need the text
        result = model.transcribe(file_path)
        text = result.get("text", "").strip()
        
        logger.info(f"Transcription complete. Result: {text[:50]}...")
        return text
    except Exception as e:
        logger.error(f"Failed to transcribe {file_path}: {e}")
        return ""