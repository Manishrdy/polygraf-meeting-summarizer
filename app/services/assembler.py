import os, json
from app.logger import get_logger
from app.config import DATA_DIR

logger = get_logger()

def compose_transcripts(segments, transcripts):
    
    paired = []
    for i, seg in enumerate(segments):
        txt = transcripts[i]["text"] if i < len(transcripts) else ""
        paired.append({
            "index": seg["index"],
            "speaker": seg["speaker"],
            "start": seg["start"],
            "text": txt
        })
    paired.sort(key=lambda x: x["start"])

    per_speaker = {}
    for row in paired:
        if not row["text"]:
            continue
        per_speaker.setdefault(row["speaker"], []).append(row["text"])

    full_lines = [f"{row['speaker']}: {row['text']}" for row in paired if row["text"]]
    full_text = "\n".join(full_lines)

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, "per_speaker_transcripts.json"), "w", encoding="utf-8") as f:
        json.dump(per_speaker, f, ensure_ascii=False, indent=2)
    with open(os.path.join(DATA_DIR, "full_transcript.txt"), "w", encoding="utf-8") as f:
        f.write(full_text)

    logger.info("Wrote per_speaker_transcripts.json and full_transcript.txt")
    return per_speaker, full_text