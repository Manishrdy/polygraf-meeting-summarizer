# run_summary.py
import json
import os

# Ensure your package structure exposes app.services.summary
from app.services.summarizer import GeminiSummarizer

def main():
    app_env = os.getenv("APP_ENV", "development")
    model_id = os.getenv("GENAI_MODEL")  # optional override, otherwise config is used
    if model_id:
        os.environ["GEMINI_MODEL_NAME"] = model_id  # if app.config reads from env

    # Mirror your previous runner's banner
    print(f"[Config loaded]: app-Polygraf Audio Backend - env={app_env} - model={os.getenv('GEMINI_MODEL_NAME', 'auto')}")

    with open("data/per_speaker_transcripts.json", "r", encoding="utf-8") as f:
        per_speaker = json.load(f)
    with open("data/full_transcript.txt", "r", encoding="utf-8") as f:
        full_text = f.read()

    GeminiSummarizer().summarize(per_speaker, full_text)
    print("Saved -> data/summary.txt")

if __name__ == "__main__":
    main()
