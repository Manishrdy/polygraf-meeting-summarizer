import whisper
from app.logger import logger
from app.config import WHISPER_MODEL

class Transcriber:
    def __init__(self):
        self.model = whisper.load_model(WHISPER_MODEL)

    def transcribe(self, audio_path: str):
        logger.info(f"Transcribing {audio_path}")
        result = self.model.transcribe(audio_path)
        return result["text"]
