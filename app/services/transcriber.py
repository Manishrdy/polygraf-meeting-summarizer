import os
import whisper
from pydub import AudioSegment
from app.logger import get_logger

logger = get_logger(__name__)

def load_model():
    model = whisper.load_model("base")
    logger.info("Whisper model loaded")
    return model

def transcribe_audio(file_path):
    logger.info(f"Inside transcribe_audio adn file_path: {file_path}")
    
    if not os.path.exists(file_path):
        logger.warning(f"File not found {file_path}")
        return ""

    model = load_model()
    res = model.transcribe(file_path, fp16=False)
    text = res.get("text", "").strip()

    logger.info(f"Transcription: {text[:50]}")
    return text