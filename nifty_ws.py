import websockets
import asyncio
import json
from datetime import datetime

# 🔁 Latest quotes dictionary shared with Streamlit
latest_quotes = {}

# 📌 Add your symbols here
NIFTY_SYMBOLS = ["NSE_INDEX_NIFTY", "NSE_STOCK_RELIANCE", "NSE_STOCK_INFOSYS"]

# 🛠️ Subscription request formatting (customize as needed)
def build_subscribe_request(symbols):
    return json.dumps({
        "guid": "rahul-streamlit-nifty",
        "method": "sub",
        "data": {"symbols": symbols}
    })

# 📡 WebSocket listener
async def subscribe_feed():
    uri = "wss://api.upstox.com/feed/websocket"  # Replace if your endpoint differs
    async with websockets.connect(uri) as ws:
        await ws.send(build_subscribe_request(NIFTY_SYMBOLS))
        
        while True:
            try:
                message = await ws.recv()
                data = json.loads(message)

                if data.get("type") == "quote":
                    symbol = data["data"].get("symbol")
                    ltp = data["data"].get("ltp")
                    ts = datetime.now().strftime("%H:%M:%S")

                    # 💥 Custom breakout logic (placeholder)
                    alert = "🔺 Breakout" if ltp and ltp > 2500 else None

                    # 🚀 Update live quotes dictionary
                    latest_quotes[symbol] = {"ltp": ltp, "timestamp": ts, "alert": alert}
            except Exception as e:
                print(f"WebSocket Error: {e}")
                continue