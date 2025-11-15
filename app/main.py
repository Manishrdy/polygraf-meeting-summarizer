from fastapi import FastAPI
from app.routes import transcript, summary
from app.logger import logger

app = FastAPI(title="Polygraf Audio Summarizer")

app.include_router(transcript.router)
app.include_router(summary.router)

@app.on_event("startup")
def startup():
    logger.info("Backend started successfully.")
