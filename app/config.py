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

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
LOG_FILE = os.path.join(LOG_DIR, "backend.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

if not GEMINI_API_KEY:
    # print("Gemini api key is missing from .env")
    raise ValueError("Gemini api key is missing from .env")

print(f"[Config loaded]: app-{APP_NAME} - env={APP_ENV} - redis={REDIS_HOST}:{REDIS_PORT}. db={REDIS_DB}")