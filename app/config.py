import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "Polygraf Audio Backend"
APP_ENV = os.getenv("APP_ENV", "development")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

##################Gemini api data and prompt.#########################

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GENAI_MODEL", "gemini-2.5-flash")

DEFAULT_PROMPT = (
    "Return ONLY strict JSON with keys: "
    "keypoints (array of strings, 3-7), "
    "decisions (array of strings), "
    "action_items (array of {owner, task, due_date}), "
    "per_speaker_summary (object mapping speaker -> short summary). "
    "No prose outside the JSON. Use only facts present in the input."
)
GEMINI_PROMPT_INSTRUCTION = os.getenv("GEMINI_PROMPT_INSTRUCTION", DEFAULT_PROMPT)
if not GEMINI_API_KEY:
    print(f"Warning: GEMINI_API_KEY not found in .env file.")

#####################################################################


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))

LOG_FILE = os.path.join(LOG_DIR, "backend.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

print(f"[Config loaded]: app-{APP_NAME} - env={APP_ENV} - redis={REDIS_HOST}:{REDIS_PORT}")