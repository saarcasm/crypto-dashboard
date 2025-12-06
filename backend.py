import asyncio
import json
import os
import httpx # New library for fetching data async
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis

app = FastAPI()

# --- SECURITY: Allow Frontend to Connect ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION ---
# It's best to read from Render's Environment Variables
# If this fails, you can paste your "rediss://..." string here as a fallback
REDIS_URL = os.getenv("REDIS_URL") 

# --- BACKGROUND TASK: The "Engine" (Fetches Prices) ---
async def fetch_prices():
    # Connect to Redis
    r = redis.from_url(REDIS_URL)
    
    # Run forever
    while True:
        try:
            # 1. Fetch Data from CoinGecko
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,dogecoin&vs_currencies=usd"
            
            # FAKE BROWSER HEADER (Crucial to avoid being blocked!)
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                data = response.json()

            # 2. Check for "Rate Limit" or Errors
            if "error" in data:
                print("API Error:", data)
            else:
                # 3. Publish to Redis
                await r.publish("crypto_stream", json.dumps(data))
                print("Updated prices:", data)
                
        except Exception as e:
            print(f"Error fetching data: {e}")
            
        # 4. Sleep for 15 seconds (Safe for Free Tier)
        await asyncio.sleep(15)

# --- STARTUP EVENT: Start the Engine ---
@app.on_event("startup")
async def startup_event():
    # This starts the fetch_prices loop in the background
    asyncio.create_task(fetch_prices())

# --- WEBSOCKET: The "Radio" (Broadcasts to Frontend) ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Connect to Redis to listen
    r = redis.from_url(REDIS_URL)
    pubsub = r.pubsub()
    await pubsub.subscribe("crypto_stream")
    
    try:
        async for message in pubsub.listen():
            if message['type'] == 'message':
                # Send data to the Frontend
                data = json.loads(message['data'])
                await websocket.send_json(data)
    except Exception as e:
        print(f"WebSocket Error: {e}")
    finally:
        await r.close()