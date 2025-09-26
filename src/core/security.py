from fastapi import Header, HTTPException, Depends
from dotenv import load_dotenv
import os

load_dotenv()

async def api_key_auth(x_api_key: str = Header(None)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

# Additional validation can be added here if needed, e.g., rate limiting or JWT in future expansions. 