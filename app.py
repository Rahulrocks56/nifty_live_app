import streamlit as st
import threading
import time
import requests
from upstox_api.api import *  # Provided by upstox-python-sdk

# ==============================
# Load secrets
# ==============================
UPSTOX_API_KEY = st.secrets["UPSTOX_API_KEY"]
UPSTOX_ACCESS_TOKEN = st.secrets["UPSTOX_ACCESS_TOKEN"]
TELEGRAM_BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

EXCHANGE = 'NSE_INDEX'  # Nifty index
SYMBOL = 'Nifty 50'     # Instrument symbol

if 'last_price' not in st.session_state:
    st.session_state.last_price = None
if 'ws_running' not in st.session_state:
    st.session_state.ws_running = False

# ==============================
# Telegram alert function
# ==============================
def send_telegram_message(msg: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print("Telegram error:", e)

# ==============================
# WebSocket live feed handler
# ==============================
def start_websocket():
    u = Upstox(UPSTOX_API_KEY, UPSTOX_ACCESS_TOKEN)

    def event_handler(msg):
        if 'ltp' in msg:
            st.session_state.last_price = msg['ltp']
            if st.session_state.last_price > 23000:
                send_telegram_message(
                    f"🚀 Nifty crossed 23000! LTP: {st.session_state.last_price}"
                )

    def error_handler(err):
        print("WebSocket Error:", err)

    instrument = u.get_instrument_by_symbol(EXCHANGE, SYMBOL)
    u.set_on_quote_update(event_handler)
    u.set_on_quote_update_error(error_handler)
    u.subscribe(instrument, LiveFeedType.LTP)

    print("✅ WebSocket started...")
    while True:
        time.sleep(1)

# ==============================
# Start WebSocket in background
# ==============================
if not st.session_state.ws_running:
    thread = threading.Thread(target=start_websocket, daemon=True)
    thread.start()
    st.session_state.ws_running = True

# ==============================
# Streamlit UI
# ==============================
st.title("📈 Live Nifty Tracker")
st.subheader("💹 Multi-Leg Options Hedge")

if st.session_state.last_price:
    st.metric("Last Price", st.session_state.last_price)
else:
    st.warning("Waiting for live market data...")
