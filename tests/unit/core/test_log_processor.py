import pytest
from datetime import datetime
from src.core.log_processor import process_log
from src.core.api_server import LogEntry

def test_process_log_valid():
    log = LogEntry(level="info", message="test", source="app", metadata={"key": "value"})
    processed = process_log(log)
    assert processed.level == "INFO"
    assert isinstance(processed.timestamp, datetime)
    assert processed.sequence_id > 0  # Assuming Redis is mocked or running
    assert processed.metadata == {"key": "value"}

def test_process_log_invalid():
    with pytest.raises(ValueError):
        process_log(LogEntry(level=123, message="test", source="app"))  # Invalid type for level 
        