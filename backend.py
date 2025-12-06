import asyncio
import json
from fastapi import FastAPI, WebSocket
import redis.asyncio as redis # Use the async version of redis

app = FastAPI()

# --- CONFIGURATION ---
# PASTE YOUR UPSTASH URL HERE
REDIS_URL = "rediss://default:Aaa7AAIncDI2N2I1ZmRiZTYzNDM0NDc3YTJkZDlhNTdhMGY3ZjkzZHAyNDI2ODM@noble-mollusk-42683.upstash.io:6379"

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Connect to Redis
    r = redis.from_url(REDIS_URL)
    pubsub = r.pubsub()
    await pubsub.subscribe("crypto_stream") 

    try:
        async for message in pubsub.listen():
            # Redis sends initial 'subscribe' confirmation messages, ignore them
            if message['type'] == 'message':
                data = json.loads(message['data'])
                await websocket.send_json(data)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await r.close()

@app.get("/")
def home():
    return {"message": "Redis Crypto Backend is Running!"}