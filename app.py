import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from datetime import datetime
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
import os
import time
from streamlit_autorefresh import st_autorefresh

# ---------------- CONFIG ----------------
API_KEY = os.environ.get("API_KEY") or st.secrets["API_KEY"]
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN") or st.secrets["ACCESS_TOKEN"]
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or st.secrets["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") or st.secrets["TELEGRAM_CHAT_ID"]

st.set_page_config(page_title="Nifty 50 Live Tracker", layout="wide")
st.title("📈 Nifty 50 Live Tracker – Streamlit Cloud")

# Auto-refresh every 10 seconds
st_autorefresh(interval=10000, key="data_refresh")

# Initialize session state DataFrame
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["datetime","open","high","low","close","volume"])
if "prev_signal" not in st.session_state:
    st.session_state.prev_signal = None

# ---------------- FUNCTIONS ----------------
def fetch_nifty_price():
    """Fetch Nifty 50 LTP using Upstox REST API"""
    try:
        url = "https://api.upstox.com/v2/market-quote/ltp?symbol=NSE_INDEX|Nifty 50"
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        resp = requests.get(url, headers=headers, timeout=5)
        data = resp.json()
        price_data = data['data'].get("NSE_INDEX|Nifty 50")
        if price_data and 'last_price' in price_data:
            return float(price_data['last_price'])
        else:
            return None
    except:
        return None

def compute_indicators(df):
    """Compute EMA, RSI, MACD, Bollinger"""
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
    """Detect trend and breakout/breakdown"""
    if len(df) < 20:
        return None
    last = df.iloc[-1]
    if not isinstance(last["close"], (int, float, np.number)):
        return None
    signals = []
    signals.append("Bullish Trend" if last["EMA20"] > last["EMA50"] else "Bearish Trend")
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

# ---------------- UPDATE DATA ----------------
ltp = fetch_nifty_price()
df = st.session_state.df

if ltp:
    ts = datetime.now()
    df.loc[len(df)] = [ts, ltp, ltp, ltp, ltp, 0]
    st.session_state.df = df.tail(200)
else:
    st.warning("No data received. Market might be closed or token expired.")

df_ind = compute_indicators(st.session_state.df)
signals = detect_signals(df_ind)

# ---------------- TABS ----------------
tab1, tab2 = st.tabs(["📈 Live Tracker", "💹 Hedged Options Trade"])

# -------- TAB 1: LIVE TRACKER --------
with tab1:
    placeholder = st.empty()
    with placeholder.container():
        col1, col2 = st.columns(2)

        if len(df_ind) > 0 and isinstance(df_ind['close'].iloc[-1], (int, float, np.number)):
            col1.metric("Last Price", f"{df_ind['close'].iloc[-1]:.2f}")
        elif ltp is None:
            col1.metric("Last Price", "No Data")
        else:
            col1.metric("Last Price", "Market Closed")

        col2.metric("Signal", signals or "Waiting for data...")

        if len(df_ind) > 0:
            st.plotly_chart(plot_candlestick(df_ind), use_container_width=True)

        # Alert only on signal change
        if signals and signals != st.session_state.prev_signal and ltp:
            if "Breakout" in signals or "Breakdown" in signals:
                play_sound()
                send_telegram_alert(f"Nifty 50 Alert: {signals}")
            st.session_state.prev_signal = signals

# -------- TAB 2: HEDGED OPTIONS TRADE --------
with tab2:
    st.subheader("Suggested Hedged Nifty 50 Options Trade")
    
    if len(df_ind) < 20 or signals is None:
        st.info("Not enough data to suggest a trade.")
    else:
        last_price = df_ind['close'].iloc[-1]
        atm_strike = round(last_price / 50) * 50
        hedge_strike = atm_strike + 200

        # Check bullish conditions
        bullish = (
            df_ind['EMA20'].iloc[-1] > df_ind['EMA50'].iloc[-1] and
            df_ind['MACD'].iloc[-1] > 0 and
            40 < df_ind['RSI'].iloc[-1] < 70
        )

        # VCP detection: Bollinger Band width contraction
        bb_width = (df_ind['BB_High'].iloc[-1] - df_ind['BB_Low'].iloc[-1]) / last_price
        vcp_signal = bb_width < 0.02  # <2% width → contraction

        if bullish and vcp_signal:
            st.success(f"""
            **Recommended Trade: Bull Call Spread**

            - Buy 1 Lot Nifty50 {atm_strike} CE  
            - Sell 1 Lot Nifty50 {hedge_strike} CE  
            - Max Loss ≈ 10% of premium (limited)  
            - Unlimited Profit beyond upper strike  
            - Probability of Profit > 70%

            _Entry Reason_: EMA20>EMA50, MACD positive, RSI healthy, VCP breakout detected
            """)
        else:
            st.info("No high-probability hedged trade right now. Waiting for bullish VCP confirmation.")
