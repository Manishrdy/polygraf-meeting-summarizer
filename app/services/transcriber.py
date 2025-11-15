import os
import whisper
from app.logger import get_logger

logger = get_logger()

class WhisperTranscriber:
    def __init__(self, model_name="base"):
        self.model = whisper.load_model(model_name)
        logger.info(f"Loaded Whisper model: {model_name}")

    def transcribe_segments(self, segments):
        logger.info(f"Segments returned: {len(segments)}")
        print(f"Segments returned: {len(segments)}")

        results = []
        for idx, seg in enumerate(segments, 1):
            audio_path = seg.get("file_path")
            try:
                if not audio_path or not os.path.exists(audio_path):
                    logger.error(f"Missing audio file for segment {idx}: {audio_path}")
                    continue

                # Force CPU-friendly settings; language hint to reduce blanks
                result = self.model.transcribe(
                    audio_path,
                    fp16=False,
                    language="en",
                    task="transcribe",
                    verbose=False
                )
                text = (result.get("text") or "").strip()

                results.append({
                    "speaker": seg.get("speaker", "Unknown"),
                    "text": text
                })
                logger.info(f"Transcribed: {seg.get('speaker','Unknown')} -> {audio_path} (chars={len(text)})")

                

            except Exception as e:
                logger.error(f"Transcription error for {audio_path}: {e}")
        return results
