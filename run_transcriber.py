from app.services.consumer import consume_diarized_segments
from app.services.transcriber import WhisperTranscriber
import os, json
from pydub.utils import which
from pydub import AudioSegment

os.environ["PATH"] += r";C:\ffmpeg-8.0-essentials_build\bin"
AudioSegment.converter = r"C:\ffmpeg-8.0-essentials_build\bin\ffmpeg.exe"
AudioSegment.ffprobe   = r"C:\ffmpeg-8.0-essentials_build\bin\ffprobe.exe"

print("ffmpeg:", which("ffmpeg"))
print("ffprobe:", which("ffprobe"))

segments = consume_diarized_segments(
    json_path="data/response.json",
    audio_path="data/bot_AkYnbDBy0YQigs48-rec_vZhODQwGYZHhi3cC.wav"
)

transcriber = WhisperTranscriber(model_name="base")
transcripts = transcriber.transcribe_segments(segments)

print(transcripts[:2])

os.makedirs("data", exist_ok=True)

with open("data/transcripts.json", "w", encoding="utf-8") as f:
    json.dump(transcripts, f, ensure_ascii=False, indent=2)

print("Saved -> data/transcripts.json")

from app.services.assembler import compose_transcripts

per_speaker, full_text = compose_transcripts(segments, transcripts)
print("Per-speaker & full transcript saved.")
