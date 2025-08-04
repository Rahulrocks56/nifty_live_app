import streamlit as st
import threading
import asyncio
from datetime import datetime

# ✅ Upstox SDK imports (correct paths for SDK v2.17.0)
from upstox_client import Configuration, ApiClient
from upstox_client.api.get_profile_api import GetProfileApi
from upstox_client.api.get_market_api import GetMarketApi
from upstox_client.rest import ApiException

# ✅ WebSocket module (you must have nifty_ws.py with subscribe_feed and latest_quotes defined)
from nifty_ws import subscribe_feed, latest_quotes

# ─────────────────────────────────────
# 🔐 Load secrets from Streamlit config
ACCESS_TOKEN = st.secrets["ACCESS_TOKEN"]

# 🎛 Configure Upstox client
config = Configuration()
config.access_token = ACCESS_TOKEN
client = ApiClient(configuration=config)

# ─────────────────────────────────────
# 📊 UI Setup
st.set_page_config(page_title="📈 Nifty 50 Tracker", layout="wide")
st.title("📡 Real-Time Nifty 50 Dashboard")

# ─────────────────────────────────────
# 👤 Display user profile
try:
    profile_api = GetProfileApi(client)
    profile = profile_api.get_profile()
    st.subheader("👤 User Info")
    st.json(profile.to_dict())
except ApiException as e:
    st.error(f"Profile API Error: {e}")

# 📈 Display market status
try:
    market_api = GetMarketApi(client)
    status = market_api.get_market_status()
    st.subheader("🕒 Market Status")
    st.json(status.to_dict())
except ApiException as e:
    st.error(f"Market Status API Error: {e}")

# ─────────────────────────────────────
# 📡 Launch live feed via WebSocket
def run_ws():
    asyncio.run(subscribe_feed())

st.subheader("🔄 Live Quote Feed")

if st.button("Start WebSocket Feed"):
    st.success("WebSocket feed activated!")
    threading.Thread(target=run_ws, daemon=True).start()

# 💹 Display live quotes and breakout alerts
if latest_quotes:
    st.subheader("🚀 Latest Price & Breakouts")
    for symbol, info in latest_quotes.items():
        ltp = info.get("ltp", "--")
        ts = info.get("timestamp", "--")
        alert = info.get("alert", None)
        st.metric(label=symbol, value=f"₹{ltp}", delta=alert or "—", help=f"Updated at {ts}")
else:
    st.info("Quotes will populate here once the feed starts...")

# ─────────────────────────────────────
# 📎 Footer
st.markdown("---")
st.caption("Built with ❤️ by Rahul • Powered by Streamlit & Upstox SDK")
