import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
from datetime import datetime
from ta.trend import EMAIndicator, MACD, ADXIndicator, AroonIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from upstox import Upstox
import requests
import base64
from plyer import notification

# ---------------- CONFIG ----------------
API_KEY = "YOUR_UPSTOX_API_KEY"
ACCESS_TOKEN = "YOUR_UPSTOX_ACCESS_TOKEN"
SYMBOL = "NSE_INDEX|Nifty 50"
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token"
TELEGRAM_CHAT_ID = "your_chat_id"

# ---------------- STREAMLIT ----------------
st.set_page_config(page_title="Nifty 50 Live Tracker", layout="wide")
st.title("📈 Nifty 50 Live Tracker & Alerts")

placeholder = st.empty()
df = pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])

# ---------------- SOUND ALERT ----------------
def get_base64_sound(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

alert_sound = get_base64_sound("alert.mp3")

def play_sound():
    sound_html = f"""
    <audio autoplay>
        <source src="data:audio/mp3;base64,{alert_sound}" type="audio/mp3">
    </audio>
    """
    st.markdown(sound_html, unsafe_allow_html=True)

# ---------------- TELEGRAM & DESKTOP ALERTS ----------------
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=3)
    except:
        pass

def desktop_alert(title, message):
    try:
        notification.notify(title=title, message=message, timeout=5)
    except:
        pass

# ---------------- UPSTOX ----------------
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

u.set_on_quote_update(event_handler_quote_update)
u.subscribe(u.get_instrument_by_symbol('NSE_INDEX', 'Nifty 50'), u.QUOTE)
u.start_websocket(False)

# ---------------- INDICATORS ----------------
def compute_indicators(df):
    df = df.copy()
    if len(df) < 50:
        return df
    df["EMA20"] = EMAIndicator(df["close"], window=20).ema_indicator()
    df["EMA50"] = EMAIndicator(df["close"], window=50).ema_indicator()
    df["RSI"] = RSIIndicator(df["close"], window=14).rsi()
    macd = MACD(df["close"])
    df["MACD"] = macd.macd()
    df["MACD_Hist"] = macd.macd_diff()
    df["ADX"] = ADXIndicator(df["high"], df["low"], df["close"], window=14).adx()
    aroon = AroonIndicator(df["close"], window=14)
    df["Aroon_Up"] = aroon.aroon_up()
    df["Aroon_Down"] = aroon.aroon_down()
    bb = BollingerBands(df["close"], window=20, window_dev=2)
    df["BB_High"] = bb.bollinger_hband()
    df["BB_Low"] = bb.bollinger_lband()
    return df

def detect_signals(df):
    if len(df) < 50:
        return "Waiting for data..."
    last = df.iloc[-1]
    signals = []
    # Trend detection
    if last["EMA20"] > last["EMA50"]:
        signals.append("Bullish Trend")
    else:
        signals.append("Bearish Trend")
    # Bollinger breakout
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
    fig.update_layout(height=600, margin=dict(l=0,r=0,t=0,b=0))
    return fig

prev_signal = None

while True:
    df_ind = compute_indicators(df)
    signals = detect_signals(df_ind)
    
    with placeholder.container():
        col1, col2 = st.columns(2)
        if len(df_ind) > 0:
            col1.metric("Last Price", f"{df_ind['close'].iloc[-1]:.2f}")
        col2.metric("Signal", signals)
        if len(df_ind) > 0:
            st.plotly_chart(plot_candlestick(df_ind), use_container_width=True)
        
        # Alert logic
        if signals != "Waiting for data..." and signals != prev_signal:
            if "Breakout" in signals or "Breakdown" in signals:
                play_sound()
                send_telegram_alert(f"Nifty 50 Alert: {signals}")
                desktop_alert("Nifty 50 Signal", signals)
            prev_signal = signals


    time.sleep(10)
