import uvicorn
from core.api_server import app  # Import from core
from core.storage import persist_logs_from_queue  # Imported for reference, used in background

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 