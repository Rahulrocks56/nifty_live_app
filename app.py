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

SYMBOL = "NSE_INDEX|Nifty 50"  # Symbol for REST polling

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

def plot_candlestick(df):
    fig = go.Figure(data=[go.Candlestick(
        x=df['datetime'],
        open=df['open'], high=df['high'],
        low=df['low'], close=df['close']
    )])
    if "EMA20" in df.columns:
        fig.add_trace(go.Scatter(x=df['datetime'], y=df['EMA20'], line=dict(color='blue',width=1), name='EMA20'))
    if "EMA50" in df.columns:
        fig.add_trace(go.Scatter(x=df['datetime'], y=df['EMA50'], line=dict(color='orange',width=1), name='EMA50'))
    fig.update_layout(height=600, xaxis_rangeslider_visible=False, template='plotly_dark')
    return fig

# ---------------- STREAMLIT LOOP ----------------
st.info("App is running in free mode (REST polling every 10s, not WebSocket real-time)")

while True:
    ltp = fetch_nifty_price()
    if ltp:
        ts = datetime.now()
        df.loc[len(df)] = [ts, ltp, ltp, ltp, ltp, 0]
        df = df.tail(200)
    
    df_ind = compute_indicators(df)
    signals = detect_signals(df_ind)

    with placeholder.container():
        col1, col2 = st.columns(2)
        if len(df_ind) > 0:
            col1.metric("Last Price", f"{df_ind['close'].iloc[-1]:.2f}")
        col2.metric("Signal", signals or "Waiting for data...")

        if len(df_ind) > 0:
            st.plotly_chart(plot_candlestick(df_ind), use_container_width=True)

        # Send alerts only when signal changes
        if signals and signals != prev_signal:
            if "Breakout" in signals or "Breakdown" in signals:
                play_sound()
                send_telegram_alert(f"Nifty 50 Alert: {signals}")
            prev_signal = signals

    time.sleep(10)


