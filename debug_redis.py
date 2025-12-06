import redis
import sys

# --- PASTE YOUR UPSTASH URL HERE ---
# It must start with "rediss://" (note the 'ss' for SSL)
REDIS_URL = "rediss://default:Aaa7AAIncDI2N2I1ZmRiZTYzNDM0NDc3YTJkZDlhNTdhMGY3ZjkzZHAyNDI2ODM@noble-mollusk-42683.upstash.io:6379"

print(f"🩺 Starting Connection Doctor...")
print(f"🎯 Target: {REDIS_URL.split('@')[-1]}") # Prints just the endpoint part

try:
    # 1. Attempt Basic Connection
    print("1️⃣  Attempting to connect...", end=" ")
    r = redis.from_url(
        REDIS_URL, 
        socket_timeout=5,
        # This line fixes 90% of Mac/Windows SSL issues:
        ssl_cert_reqs=None 
    )
    
    # 2. Test Ping (Actually sends data)
    r.ping()
    print("✅ SUCCESS!")
    
    # 3. Test Write/Read
    print("2️⃣  Testing Write/Read permission...", end=" ")
    r.set('test_key', 'Hello from Laptop')
    value = r.get('test_key')
    
    if value.decode('utf-8') == 'Hello from Laptop':
        print("✅ SUCCESS!")
        print("\n🎉 GREAT NEWS: Your internet AND credentials are working.")
        print("👉 The issue is likely in your producer code logic, not the connection.")
    else:
        print("❌ Write succeeded but Read failed (Weird!)")

except redis.exceptions.AuthenticationError:
    print("\n❌ AUTHENTICATION ERROR")
    print("👉 Your Password or Username is wrong.")
    print("Check the string between 'default:' and '@'.")

except redis.exceptions.TimeoutError:
    print("\n❌ TIMEOUT ERROR")
    print("👉 The server didn't respond in 5 seconds.")
    print("1. Are you on a School/Office Wifi? (They block Port 6379)")
    print("2. Is the URL correct? (Check for spaces)")

except redis.exceptions.ConnectionError as e:
    print(f"\n❌ CONNECTION ERROR: {e}")
    if "certificate verify failed" in str(e):
        print("👉 SSL CERTIFICATE ISSUE. (Common on Macs)")
        print("Fix: Add 'ssl_cert_reqs=None' to your redis.from_url() arguments.")
    elif "nodename nor servname" in str(e):
        print("👉 URL ERROR. The domain name doesn't exist.")
        print("Check if you pasted the REST URL (http) instead of TCP URL.")

except Exception as e:
    print(f"\n❌ UNEXPECTED ERROR: {e}")