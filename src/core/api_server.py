from fastapi import FastAPI, Depends, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session
import os

from .log_processor import process_log
from .storage import enqueue_log, get_db, CheckpointDB, LogEntryDB, create_checkpoint

app = FastAPI(title="Universal Logging Hook")

class LogEntry(BaseModel):
    level: str  # e.g., "INFO", "ERROR"
    message: str
    source: str  # e.g., "app1"
    metadata: dict = {}  # Optional extra data

class ProcessedLog(LogEntry):
    timestamp: datetime
    sequence_id: int

async def api_key_auth(x_api_key: str = Header(None)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")

@app.post("/logs")
async def receive_log(log: LogEntry, background_tasks: BackgroundTasks, auth: str = Depends(api_key_auth)):
    processed = process_log(log)
    enqueue_log(processed)
    background_tasks.add_task(persist_logs_from_queue)
    return {"status": "enqueued"}

@app.post("/checkpoint")
async def trigger_checkpoint(db: Session = Depends(get_db)):
    checkpoint_id = create_checkpoint()
    return {"checkpoint_id": checkpoint_id}

@app.get("/replay/{checkpoint_id}")
async def replay_logs(checkpoint_id: str, db: Session = Depends(get_db)):
    checkpoint = db.query(CheckpointDB).filter(CheckpointDB.checkpoint_id == checkpoint_id).first()
    if not checkpoint:
        return {"error": "Checkpoint not found"}
    logs = db.query(LogEntryDB).filter(LogEntryDB.sequence_id > checkpoint.last_sequence).order_by(LogEntryDB.sequence_id.asc()).all()
    return {"logs": [{"level": log.level, "message": log.message, "source": log.source, "timestamp": log.timestamp, "sequence_id": log.sequence_id, "metadata": log.metadata} for log in logs]} 