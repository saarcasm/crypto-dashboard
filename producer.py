import time
import json
import ccxt
import pandas as pd
import redis

# --- CONFIGURATION ---
# PASTE YOUR UPSTASH URL HERE
REDIS_URL = "rediss://default:Aaa7AAIncDI2N2I1ZmRiZTYzNDM0NDc3YTJkZDlhNTdhMGY3ZjkzZHAyNDI2ODM@noble-mollusk-42683.upstash.io:6379"

def connect_redis():
    """Connects to Redis with 'Keep-Alive' settings to prevent timeouts"""
    return redis.from_url(
        REDIS_URL,
        decode_responses=True,       # Automatically decode bytes to strings
        socket_timeout=10,           # Wait 10s before giving up
        socket_connect_timeout=10,
        socket_keepalive=True,       # TCP Keepalive to keep connection open
        health_check_interval=30,    # Ping every 30s to stay alive
        retry_on_timeout=True        # Auto-reconnect if dropped
    )

# Initial Connection
try:
    r = connect_redis()
    r.ping() # Test connection
    print("✅ Connected to Upstash Redis (Hardened Mode)!")
except Exception as e:
    print(f"❌ Failed to connect: {e}")
    exit()

exchange = ccxt.binance({'enableRateLimit': True})
COINS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'DOGE/USDT']

def calculate_rsi(prices, period=14):
    series = pd.Series(prices)
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

print(f"🚀 Producer running... Tracking: {COINS}")

while True:
    try:
        for symbol in COINS:
            # 1. Fetch Data
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=50)
            closes = [candle[4] for candle in ohlcv]
            current_price = closes[-1]
            current_timestamp = ohlcv[-1][0]
            
            # 2. Calculate RSI
            current_rsi = calculate_rsi(closes)
            if pd.isna(current_rsi): current_rsi = 50.0

            data = {
                'symbol': symbol,
                'price': current_price,
                'rsi': current_rsi,
                'timestamp': current_timestamp
            }
            
            # 3. Publish (Protected Block)
            try:
                r.publish('crypto_stream', json.dumps(data))
                print(f"📡 Sent {symbol}: ${current_price}")
            except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
                print("⚠️ Connection lost... Reconnecting.")
                r = connect_redis() # Re-establish connection
                time.sleep(1)

        time.sleep(2)
        
    except Exception as e:
        print(f"Main Loop Error: {e}")
        time.sleep(5)