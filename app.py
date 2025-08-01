import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
from datetime import datetime
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
import requests
import os

# ---------------- CONFIG ----------------
API_KEY = os.environ.get("API_KEY") or st.secrets["API_KEY"]
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN") or st.secrets["ACCESS_TOKEN"]
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or st.secrets["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") or st.secrets["TELEGRAM_CHAT_ID"]

SYMBOL = "NSE_INDEX|Nifty 50"

st.set_page_config(page_title="Nifty 50 Live Tracker", layout="wide")
st.title("📈 Nifty 50 Live Tracker – Streamlit Cloud")

placeholder = st.empty()
df = pd.DataFrame(columns=["datetime","open","high","low","close","volume"])
prev_signal = None

# ---------------- ALERT FUNCTIONS ----------------
def send_telegram_alert(message):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        try:
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=3)
        except:
            pass

def play_sound():
    sound_html = """
    <audio autoplay>
        <source src="https://www.soundjay.com/buttons/sounds/beep-07.mp3" type="audio/mp3">
    </audio>
    """
    st.markdown(sound_html, unsafe_allow_html=True)

# ---------------- PRICE FETCH (REST API POLLING) ----------------
def fetch_nifty_price():
    try:
        url = "https://api.upstox.com/v2/market-quote/ltp?symbol=NSE_INDEX|Nifty 50"
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        resp = requests.get(url, headers=headers, timeout=5)
        data = resp.json()
        price_data = data['data'].get("NSE_INDEX|Nifty 50")
        if price_data and 'last_price' in price_data:
            return float(price_data['last_price'])
        else:
            return "Market Closed"
    except:
        return None

# ---------------- INDICATORS ----------------
def compute_indicators(df):
    df = df.copy()
    if len(df) < 20:
        return df
    df["EMA20"] = EMAIndicator(df["close"], window=20).ema_indicator()
    df["EMA50"] = EMAIndicator(df["close"], window=50).ema_indicator()
    df["RSI"] = RSIIndicator(df["close"], window=14).rsi()
    macd = MACD(df["close"])
    df["MACD"] = macd.macd()
    df["MACD_Hist"] = macd.macd_diff()
    bb = BollingerBands(df["close"], window=20, window_dev=2)
    df["BB_High"] = bb.bollinger_hband()
    df["BB_Low"] = bb.bollinger_lband()
    return df

def detect_signals(df):
    if len(df) < 20:
        return None
    last = df.iloc[-1]
    if not isinstance(last["close"], (int, float, np.number)):
        return None
    signals = []
    if last["EMA20"] > last["EMA50"]:
        signals.append
