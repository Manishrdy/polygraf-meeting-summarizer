import os
from dotenv import load_dotenv

load_dotenv()


APP_NAME = "Polygraf Audio Backend"
APP_ENV = os.getenv("APP_ENV", "development")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))

LOG_FILE = os.path.join(LOG_DIR, "backend.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

if not GEMINI_API_KEY:
    print("Gemini api key is missing from .env")

print(f"[Config loaded]: app-{APP_NAME} - env={APP_ENV} - model={GEMINI_MODEL_NAME}")