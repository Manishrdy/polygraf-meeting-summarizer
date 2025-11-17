import os
import json
import re
from pydub import AudioSegment
from app.logger import get_logger
from app.config import DATA_DIR

logger = get_logger()
logger.info("Inside consumer from app.routes.services")

output_path = os.path.join(DATA_DIR, "sample_audio")
os.makedirs(output_path, exist_ok=True)

def read_file(json_path):
    if not json_path:
        return 
    
    with open(json_path, "r", encoding="utf-8") as json_file:
        diarization_data = json.load(json_file)
    
    if not diarization_data:
        logger.error("No diarized segments found")
        return []

    return diarization_data

def consume_diarized_segments(json_path, audio_path):

    logger.info(f"Check json path: {json_path}")
    logger.path(f"Check for .wav audio file: {json_path}")

    diarization_data = read_file(json_path)
    full_audio = AudioSegment.from_wav(audio_path)

    timestamps = []
    for seg in diarization_data:
        timestamps.append(int(seg.get("timestamp_ms", 0)))
    anchor_ms = min(timestamps)

    segments_data = []
    logger.info(f"Total {len(diarization_data)} segments")

    for i, segment in enumerate(diarization_data):
        try:
            speaker = segment.get("speaker_name", "unknown")
            start_time = int(segment.get("timestamp_ms", 0))
            duration_time = int(segment.get("duration_ms", 0))

            if duration_time <= 0:
                continue

            start = max(0, start_time - anchor_ms)
            end = start + duration_time

            clip = full_audio[start:end].set_frame_rate(16000).set_channels(1)
            if len(clip) <= 0:
                continue
            
            filename = f"{speaker}_{i}.wav"
            output_file = os.path.join(output_path, filename)

            clip.export(output_file, format="wav")
            segments_data.append({
                "index": i,
                "speaker": speaker,
                "file_path": output_file,
                "start": start_time,
                "end": start_time + duration_time,
                "duration_ms": duration_time,
                "text": segment.get("transcription", {}).get("transcript", "")
            })
            logger.info(f"Extracted {speaker} - {output_file} duration: {len(clip)}ms")
        except Exception as e:
            logger.error(f"Error processing segment {i}: {e}")

    logger.info(f"Finished spliting into {len(segments_data)} audio chunks")
    return segments_data
