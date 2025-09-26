from datetime import datetime
from pydantic import ValidationError
from .api_server import LogEntry, ProcessedLog
from .storage import redis_client

SEQUENCE_KEY = "log_sequence"

def process_log(log: LogEntry) -> ProcessedLog:
    try:
        # Normalize: Ensure level uppercase, add timestamp
        normalized_level = log.level.upper()
        timestamp = datetime.utcnow()
        sequence_id = redis_client.incr(SEQUENCE_KEY)
        return ProcessedLog(
            level=normalized_level,
            message=log.message,
            source=log.source,
            metadata=log.metadata,
            timestamp=timestamp,
            sequence_id=sequence_id
        )
    except ValidationError as e:
        raise ValueError(f"Invalid log: {e}") 