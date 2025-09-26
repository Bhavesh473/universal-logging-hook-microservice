import pytest
from src.core.storage import enqueue_log, persist_logs_from_queue, create_checkpoint
from src.core.api_server import ProcessedLog
from datetime import datetime

@pytest.fixture
def sample_processed_log():
    return ProcessedLog(level="INFO", message="test", source="app", timestamp=datetime.utcnow(), sequence_id=1)

def test_enqueue_and_persist(sample_processed_log):
    enqueue_log(sample_processed_log)
    persist_logs_from_queue()  # Assumes DB/Redis running; use mocks for isolation
    # Query DB to verify (placeholder; add SQLAlchemy session fixture)
    # assert logs_collection.count_documents({"sequence_id": 1}) == 1  # For Mongo; adapt for Postgres

def test_create_checkpoint():
    checkpoint_id = create_checkpoint()
    assert isinstance(checkpoint_id, str)  