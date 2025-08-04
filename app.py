import streamlit as st
import threading
import asyncio
from datetime import datetime

# ✅ Correct imports based on SDK v2.17.0 structure
from upstox_client import Configuration, ApiClient
from upstox_client.api.get_profile_api import GetProfileApi
from upstox_client.api.get_market_api import GetMarketApi
from upstox_client.rest import ApiException

# ✅ Your WebSocket module (make sure nifty_ws.py defines these)
from nifty_ws import subscribe_feed, latest_quotes

# ─────────────────────────────────────
# 🔐 Load your access token from secrets
ACCESS_TOKEN = st.secrets["ACCESS_TOKEN"]

# ✅ Configure Upstox API client
config = Configuration()
config.access_token = ACCESS_TOKEN
client = ApiClient(configuration=config)

# ─────────────────────────────────────
# 📊 Streamlit UI Setup
st.set_page_config(page_title="📈 Nifty 50 Tracker", layout="wide")
st.title("📡 Nifty 50 Live Dashboard")

# 👤 Profile Section
try:
    profile_api = GetProfileApi(client)
    profile = profile_api.get_profile()
    st.subheader("👤 User Profile")
    st.json(profile.to_dict())
except ApiException as e:
    st.error(f"Profile API Error: {e}")

# 📈 Market Status
try:
    market_api = GetMarketApi(client)
    status = market_api.get_market_status()
    st.subheader("📅 Market Status")
    st.json(status.to_dict())
except ApiException as e:
    st.error(f"Market Status API Error: {e}")

# ─────────────────────────────────────
# 🚀 Start WebSocket Feed
def run_ws():
    asyncio.run(subscribe_feed())

st.subheader("🔄 WebSocket Feed")
if st.button("Start Feed"):
    st.success("WebSocket feed started!")
    threading.Thread(target=run_ws, daemon=True).start()

# 💹 Display Live Quotes and Breakout Alerts
if latest_quotes:
    st.subheader("📈 Live Prices & Alerts")
    for symbol, info in latest_quotes.items():
        ltp = info.get("ltp", "--")
        ts = info.get("timestamp", "--")
        alert = info.get("alert", None)
        st.metric(label=symbol, value=f"₹{ltp}", delta=alert or "—", help=f"Updated: {ts}")
else:
    st.info("Waiting for quotes... Start the feed to see live data.")

# ─────────────────────────────────────
# 🧭 Footer
st.markdown("---")
st.caption("Made by Rahul • Powered by Upstox SDK & Streamlit")
