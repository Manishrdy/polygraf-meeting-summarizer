from fastapi import FastAPI
from app.logger import logger
from app.routes.transcripts import router as transcripts_router
from app.routes.summary import router as summary_router

app = FastAPI(title="Polygraf Audio Summarizer")
logger.info("FastAPI app created.")

app.include_router(transcripts_router)
app.include_router(summary_router)

@app.get("/health")
def health():
    logger.info("Health check OK.")
    return {"status": "ok"}

@app.on_event("startup")
def startup():
    logger.info("Backend started successfully.")
