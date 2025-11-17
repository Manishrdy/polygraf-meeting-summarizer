from fastapi import FastAPI
from app.logger import logger
from app.routes.jobs import router as jobs_router

app = FastAPI()
logger.info("Fast api started")

app.include_router(jobs_router)

@app.get("/health")
def health():
    return {"status": "ok"}