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
from streamlit_autorefresh import st_autorefresh
import math
from scipy.stats import norm

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

# Black-Scholes pricing
def black_scholes_call_price(S, K, T, r, sigma):
    d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    return S*norm.cdf(d1) - K*math.exp(-r*T)*norm.cdf(d2)

def black_scholes_put_price(S, K, T, r, sigma):
    d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    return K*math.exp(-r*T)*norm.cdf(-d2) - S*norm.cdf(-d1)

def long_option_strategy_profit(spot, call_strike, put_strike, call_premium, put_premium, call_lots, put_lots):
    call_iv = max(spot - call_strike, 0)
    put_iv = max(put_strike - spot, 0)
    long_call_pl = (call_iv - call_premium) * call_lots
    long_put_pl = (put_iv - put_premium) * put_lots
    return long_call_pl + long_put_pl

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
tab1, tab2 = st.tabs(["📈 Live Tracker", "💹 Multi-Leg Options Hedge"])

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

        if signals and signals != st.session_state.prev_signal and ltp:
            if "Breakout" in signals or "Breakdown" in signals:
                play_sound()
                send_telegram_alert(f"Nifty 50 Alert: {signals}")
            st.session_state.prev_signal = signals

# -------- TAB 2: MULTI-LEG OPTION BUY STRATEGY --------
with tab2:
    st.subheader("Dynamic Hedged Nifty 50 Options (Only Buying)")

    if len(df_ind) < 20 or signals is None:
        st.info("Not enough data to suggest a trade.")
    else:
        last_price = df_ind['close'].iloc[-1]
        atm_strike = round(last_price / 50) * 50

        # Assume 1-week expiry
        T = 7/365
        r = 0.05
        sigma = 0.18  # IV approx

        # Approx option premiums
        call_premium = black_scholes_call_price(last_price, atm_strike, T, r, sigma)
        put_premium = black_scholes_put_price(last_price, atm_strike, T, r, sigma)

        call_lots = st.number_input("Number of Call Lots", min_value=0, max_value=5, value=1)
        put_lots = st.number_input("Number of Put Lots", min_value=0, max_value=5, value=1)
        lot_size = 50

        net_premium = (call_premium*call_lots + put_premium*put_lots)
        max_loss = net_premium * lot_size

        st.write(f"**Max Loss:** ₹{max_loss:.2f} (limited to premium paid)")
        st.write("**Max Profit:** Unlimited if market moves sharply")

        # Spot slider
        spot = st.slider("Nifty 50 Spot Price", int(atm_strike*0.9), int(atm_strike*1.1), int(last_price))
        pl = long_option_strategy_profit(spot, atm_strike, atm_strike, call_premium, put_premium, call_lots, put_lots)
        st.metric("P/L at Spot", f"₹{pl*lot_size:.2f} per lot combination")

        st.info(f"""
        **Trade Setup: Multi-leg Option Hedge**
        - Buy {call_lots}x Nifty50 {atm_strike} CE ≈ ₹{call_premium*lot_size*call_lots:.2f}
        - Buy {put_lots}x Nifty50 {atm_strike} PE ≈ ₹{put_premium*lot_size*put_lots:.2f}
        - Total Cost ≈ ₹{net_premium*lot_size:.2f}
        - Max Loss = Total Premium Paid
        - Unlimited Profit if market moves significantly up or down
        """)
