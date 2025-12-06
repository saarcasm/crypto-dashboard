import asyncio
import json
import os
import httpx 
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis

app = FastAPI()

# --- SECURITY ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIS_URL = os.getenv("REDIS_URL") 

# --- HELPER: Fetch from Binance (More Reliable) ---
async def get_price(client, symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        resp = await client.get(url)
        data = resp.json()
        return float(data['price'])
    except:
        return 0

# --- THE ENGINE ---
async def fetch_prices():
    if not REDIS_URL:
        return

    r = redis.from_url(REDIS_URL)
    
    while True:
        try:
            async with httpx.AsyncClient() as client:
                # 1. Fetch prices from Binance (No API Key needed)
                btc = await get_price(client, "BTCUSDT")
                eth = await get_price(client, "ETHUSDT")
                sol = await get_price(client, "SOLUSDT")
                doge = await get_price(client, "DOGEUSDT")

            # 2. Format exactly like CoinGecko (so Frontend doesn't break)
            data = {
                "bitcoin": {"usd": btc},
                "ethereum": {"usd": eth},
                "solana": {"usd": sol},
                "dogecoin": {"usd": doge}
            }

            # 3. Publish
            await r.publish("crypto_stream", json.dumps(data))
            print("Updated prices:", data) 
                
        except Exception as e:
            print(f"Error: {e}")
            
        # 4. Sleep for 3 seconds (Binance is fast!)
        await asyncio.sleep(3)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(fetch_prices())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    r = redis.from_url(REDIS_URL)
    pubsub = r.pubsub()
    await pubsub.subscribe("crypto_stream")
    try:
        async for message in pubsub.listen():
            if message['type'] == 'message':
                await websocket.send_json(json.loads(message['data']))
    except:
        pass
    finally:
        await r.close()