from fastapi import FastAPI
from app.logger import logger
from app.routes.jobs import router as jobs_router

app = FastAPI(title="Polygraf Audio Summarizer (Async)")
logger.info("FastAPI app created (Async Mode).")

# Register the new Jobs router
app.include_router(jobs_router)

@app.get("/health")
def health():
    return {"status": "ok"}