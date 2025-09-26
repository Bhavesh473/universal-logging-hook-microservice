import redis
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from datetime import datetime
from .api_server import ProcessedLog

load_dotenv()

# PostgreSQL setup
DATABASE_URL = os.getenv("POSTGRES_URI")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class LogEntryDB(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String, index=True)
    message = Column(String)
    source = Column(String, index=True)
    metadata = Column(JSON)  # JSONB for flexible data
    timestamp = Column(DateTime(timezone=True))
    sequence_id = Column(Integer, index=True)

class CheckpointDB(Base):
    __tablename__ = "checkpoints"
    id = Column(Integer, primary_key=True, index=True)
    checkpoint_id = Column(String, unique=True)
    last_sequence = Column(Integer)
    timestamp = Column(DateTime(timezone=True), default=func.now())

# Create tables (run once)
Base.metadata.create_all(bind=engine)

# Redis setup (unchanged)
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    decode_responses=True
)

QUEUE_KEY = "log_queue"
SEQUENCE_KEY = "log_sequence"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def enqueue_log(processed_log: ProcessedLog):
    redis_client.rpush(QUEUE_KEY, processed_log.json())

def persist_logs_from_queue():
    db = next(get_db())
    try:
        while redis_client.llen(QUEUE_KEY) > 0:
            log_json = redis_client.lpop(QUEUE_KEY)
            log_data = ProcessedLog.parse_raw(log_json).dict()
            db_log = LogEntryDB(
                level=log_data['level'],
                message=log_data['message'],
                source=log_data['source'],
                metadata=log_data.get('metadata', {}),
                timestamp=log_data['timestamp'],
                sequence_id=log_data['sequence_id']
            )
            db.add(db_log)
            db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def create_checkpoint():
    last_sequence = int(redis_client.get(SEQUENCE_KEY) or 0)
    checkpoint_id = str(datetime.utcnow())
    db = next(get_db())
    try:
        db_checkpoint = CheckpointDB(
            checkpoint_id=checkpoint_id,
            last_sequence=last_sequence
        )
        db.add(db_checkpoint)
        db.commit()
        return checkpoint_id
    finally:
        db.close() 