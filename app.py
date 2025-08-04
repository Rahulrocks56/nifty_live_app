import streamlit as st
import threading
import asyncio
from datetime import datetime

# Upstox SDK setup
from upstox_client import Configuration, ApiClient
from upstox_client.api import get_profile_api, get_market_api
from upstox_client.rest import ApiException

# Import WebSocket feed and quote cache
from nifty_ws import subscribe_feed, latest_quotes  # Make sure this file exists

# ───────────── Streamlit UI Setup ─────────────
st.set_page_config(page_title="📈 Nifty 50 Dashboard", layout="wide")
st.title("📊 Nifty 50 Breakout Tracker")

# ───────────── Secrets ─────────────
ACCESS_TOKEN = st.secrets["ACCESS_TOKEN"]

# ───────────── Upstox API Client ─────────────
config = Configuration()
config.access_token = ACCESS_TOKEN
client = ApiClient(configuration=config)

# ───────────── Profile Info ─────────────
try:
    profile_api = get_profile_api.GetProfileApi(client)
    profile = profile_api.get_profile()
    st.subheader("👤 User Profile")
    st.json(profile.to_dict())
except ApiException as e:
    st.error(f"Profile API Error: {e}")

# ───────────── Market Status ─────────────
try:
    market_api = get_market_api.GetMarketApi(client)
    status = market_api.get_market_status()
    st.subheader("📈 Market Status")
    st.json(status.to_dict())
except ApiException as e:
    st.error(f"Market API Error: {e}")

# ───────────── WebSocket Feed Start ─────────────
st.subheader("🔄 Live Feed")

def run_ws():
    asyncio.run(subscribe_feed())

if st.button("Start WebSocket Feed"):
    st.success("Listening to live quotes...")
    threading.Thread(target=run_ws, daemon=True).start()

# ───────────── Live Quote Display ─────────────
if latest_quotes:
    st.subheader("💹 Latest Prices & Breakouts")
    for symbol, info in latest_quotes.items():
        ltp = info.get("ltp", "--")
        ts = info.get("timestamp", "--")
        alert = info.get("alert", None)
        st.metric(label=symbol, value=f"₹{ltp}", delta=alert or "—", help=f"Updated: {ts}")
else:
    st.info("Quotes will appear once the feed starts...")

# ───────────── Footer ─────────────
st.markdown("---")
st.caption("Made by Rahul • Powered by Upstox SDK & Streamlit")
