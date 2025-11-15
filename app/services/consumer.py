import os
import json
import re
from pydub import AudioSegment
from app.logger import get_logger
from app.config import DATA_DIR

logger = get_logger()

def _safe_name(name: str) -> str:
    # keep alnum, underscore, hyphen; replace others with underscore
    return re.sub(r"[^A-Za-z0-9_\-]+", "_", name.strip())

def consume_diarized_segments(json_path: str, audio_path: str):
    """
    Reads diarized JSON + .wav audio, aligns timestamps relative to the earliest
    segment, exports 16k mono WAV chunks, and returns segment metadata.
    """
    output_dir = os.path.join(DATA_DIR, "sample_audio")
    os.makedirs(output_dir, exist_ok=True)

    with open(json_path, "r", encoding="utf-8") as f:
        diarization_data = json.load(f)

    if not diarization_data:
        logger.warning("No diarized segments found.")
        return []

    # Load base audio once
    full_audio = AudioSegment.from_wav(audio_path)

    # Use earliest timestamp as anchor (not just index 0)
    anchor_ms = min(int(s.get("timestamp_ms", 0)) for s in diarization_data)

    segments_info = []
    logger.info(f"Loaded {len(diarization_data)} diarized segments from {json_path}")

    for idx, segment in enumerate(diarization_data):
        try:
            speaker = segment.get("speaker_name", "Unknown")
            start_ms = int(segment.get("timestamp_ms", 0))
            duration_ms = int(segment.get("duration_ms", 0))
            if duration_ms <= 0:
                logger.warning(f"Skip idx={idx} ({speaker}): non-positive duration {duration_ms}ms")
                continue

            # Align to audio start and guard negatives
            start_rel = max(0, start_ms - anchor_ms)
            end_rel = start_rel + duration_ms

            # Slice and normalize to 16k mono PCM
            clip = full_audio[start_rel:end_rel].set_frame_rate(16000).set_channels(1)
            if len(clip) <= 0:
                logger.warning(f"Skip idx={idx} ({speaker}): empty slice [{start_rel}:{end_rel}]")
                continue

            safe_speaker = _safe_name(speaker)
            output_file = os.path.join(output_dir, f"{safe_speaker}_{idx}.wav")
            clip.export(output_file, format="wav")

            segments_info.append({
                "index": idx,
                "speaker": speaker,
                "file_path": output_file,
                "start": start_ms,
                "end": start_ms + duration_ms,
                "duration_ms": duration_ms,
                "text": segment.get("transcription", {}).get("transcript", "")
            })

            logger.info(f"Extracted {speaker} -> {output_file} (dur={len(clip)}ms)")

        except Exception as e:
            logger.error(f"Error processing segment {idx}: {e}")

    logger.info(f"Finished splitting into {len(segments_info)} audio chunks.")
    return segments_info
