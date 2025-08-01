import pandas as pd
import time
from datetime import datetime
from ta.trend import EMAIndicator
from ta.volatility import BollingerBands
from upstox_api.api import Upstox
import requests
import threading

# Config
API_KEY = "YOUR_UPSTOX_API_KEY"
ACCESS_TOKEN = "YOUR_UPSTOX_ACCESS_TOKEN"
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token"
TELEGRAM_CHAT_ID = "your_chat_id"

df = pd.DataFrame(columns=["datetime","open","high","low","close","volume"])
u = Upstox(API_KEY, ACCESS_TOKEN)
u.get_master_contract('NSE_INDEX')

def event_handler_quote_update(msg):
    global df
    ts = datetime.now()
    ltp = msg['ltp']
    df = pd.concat([df, pd.DataFrame([{
        "datetime": ts,
        "open": ltp,
        "high": ltp,
        "low": ltp,
        "close": ltp,
        "volume": msg.get('volume',0)
    }])], ignore_index=True)
    df = df.tail(200)

def start_websocket():
    u.set_on_quote_update(event_handler_quote_update)
    u.subscribe(u.get_instrument_by_symbol('NSE_INDEX', 'Nifty 50'), u.QUOTE)
    u.start_websocket(False)

def compute_indicators(df):
    df = df.copy()
    if len(df) < 50:
        return df
    df["EMA20"] = EMAIndicator(df["close"], window=20).ema_indicator()
    df["EMA50"] = EMAIndicator(df["close"], window=50).ema_indicator()
    bb = BollingerBands(df["close"], window=20, window_dev=2)
    df["BB_High"] = bb.bollinger_hband()
    df["BB_Low"] = bb.bollinger_lband()
    return df

def detect_signals(df):
    if len(df) < 50:
        return None
    last = df.iloc[-1]
    signals = []
    if last["EMA20"] > last["EMA50"]:
        signals.append("Bullish Trend")
    else:
        signals.append("Bearish Trend")
    if last["close"] > last["BB_High"]:
        signals.append("⚡ Breakout!")
    elif last["close"] < last["BB_Low"]:
        signals.append("⚠ Breakdown!")
    return " | ".join(signals)

def send_telegram_alert(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})

threading.Thread(target=start_websocket, daemon=True).start()
prev_signal = None
print("🚀 Alert bot started. Running 24/7...")

while True:
    df_ind = compute_indicators(df)
    signal = detect_signals(df_ind)
    if signal and signal != prev_signal:
        if "Breakout" in signal or "Breakdown" in signal:
            send_telegram_alert(f"Nifty 50 Alert: {signal}")
            print(f"[{datetime.now()}] ALERT SENT: {signal}")
        prev_signal = signal
    time.sleep(10)