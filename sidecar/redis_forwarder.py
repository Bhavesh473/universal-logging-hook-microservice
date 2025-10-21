from fastapi import FastAPI, Request, HTTPException # pyright: ignore[reportMissingImports]
import redis.asyncio as aioredis  # pyright: ignore[reportMissingImports] # Top import - no duplicate
import os
import uuid
import json
import datetime
from typing import Optional
import uvicorn  # pyright: ignore[reportMissingImports] # Moved to top - fixes lint warning!

# For type checking only
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from redis.asyncio import Redis  # pyright: ignore[reportMissingImports] # Only for mypy/pyright
else:
    Redis = aioredis.Redis  # Runtime fallback (avoid NameError)

app = FastAPI()

# Environment variables
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379")
STREAM_KEY = os.environ.get("STREAM_KEY", "logs:stream")
SECRET = os.environ.get("REPLAY_SHARED_TOKEN", "mysecret")

redis_client: Optional[Redis] = None  # Now Redis is defined at runtime

@app.on_event("startup")
async def startup():
    global redis_client
    # from_url is SYNCHRONOUS - DO NOT AWAIT
    redis_client = aioredis.from_url(
        REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    # Ping is async - await it
    try:
        await redis_client.ping()
        print(f"Connected to Redis: {REDIS_URL}")
    except Exception as e:
        print(f"Redis ping failed on startup: {e}")
    print(f"Forwarding to stream: {STREAM_KEY}")

@app.on_event("shutdown")
async def shutdown():
    global redis_client
    if redis_client:
        await redis_client.close()

@app.post("/forward")
async def forward(request: Request):
    try:
        log_data = await request.json()
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="Invalid JSON")
   
    # COMMENTED OUT - No auth needed for internal Docker network
    # token = request.headers.get("x-replay-token") or request.headers.get("authorization")
    # if token != SECRET:
    #     raise HTTPException(status_code=401, detail="Unauthorized")
   
    event_id = log_data.get("event_id") or str(uuid.uuid4())
    
    try:
        timestamp = log_data.get("timestamp") or datetime.datetime.utcnow().isoformat()
        session_id = log_data.get("session_id", "") or log_data.get("request_id", "")
        source = log_data.get("source", "unknown")
        level = log_data.get("level", "INFO")
        payload = log_data
        
        await redis_client.xadd(
            STREAM_KEY,
            {
                "event_id": event_id,
                "timestamp": timestamp,
                "session_id": session_id,
                "source": source,
                "level": level,
                "payload": json.dumps(payload, ensure_ascii=False)
            }
        )
        
        print(f"Forwarded: {event_id} from {source} - Keys: {list(payload.keys())[:3]}")
        return {"status": "accepted", "event_id": event_id}
        
    except Exception as ex:
        print(f"Error forwarding: {ex}")
        raise HTTPException(status_code=500, detail=str(ex))

@app.get("/health")
async def health():
    try:
        await redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as ex:
        raise HTTPException(status_code=503, detail=f"Redis unavailable: {ex}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8200)