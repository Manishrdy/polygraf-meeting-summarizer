import os
import json
import re
from pydub import AudioSegment
from app.logger import get_logger
from app.config import DATA_DIR

logger = get_logger()

logger.info("Inside consumer from app.routes.services")

def consume_diarized_segments(json_path, audio_path):
    output_dir = os.path.join(DATA_DIR, "sample_audio")
    os.makedirs(output_dir, exist_ok=True)

    with open(json_path, "r", encoding="utf-8") as json_file:
        diarization_data = json.load(json_file)

    if not diarization_data:
        logger.warning("No diarized segments found")
        return []

    full_audio = AudioSegment.from_wav(audio_path)

    def safe_name(name):
        cleaned = name.strip()
        return re.sub(r"[^A-Za-z0-9_\-]+", "_", cleaned)

    anchor_ms = min(int(segment.get("timestamp_ms", 0)) for segment in diarization_data)
    segments_info = []
    logger.info(f"Loaded {len(diarization_data)} diarized segments from {json_path}")

    for i, segment in enumerate(diarization_data):
        try:
            speaker = segment.get("speaker_name", "unknown")
            start_ms = int(segment.get("timestamp_ms", 0))
            duration_ms = int(segment.get("duration_ms", 0))

            if duration_ms <= 0:
                continue

            start_rel = max(0, start_ms - anchor_ms)
            end_rel = start_rel + duration_ms

            clip = full_audio[start_rel:end_rel].set_frame_rate(16000).set_channels(1)
            if len(clip) <= 0:
                continue

            output_file = os.path.join(output_dir, f"{safe_name(speaker)}_{i}.wav")
            clip.export(output_file, format="wav")

            segments_info.append({
                "index": i,
                "speaker": speaker,
                "file_path": output_file,
                "start": start_ms,
                "end": start_ms + duration_ms,
                "duration_ms": duration_ms,
                "text": segment.get("transcription", {}).get("transcript", "")
            })

            logger.info(f"Extracted {speaker} - {output_file} (dur={len(clip)}ms)")
        except Exception as error:
            logger.error(f"Error processing segment {i}: {error}")

    logger.info(f"Finished splitting into {len(segments_info)} audio chunks")
    return segments_info
