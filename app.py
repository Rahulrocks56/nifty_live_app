import streamlit as st
import threading
import asyncio
from datetime import datetime
from upstox_client import Configuration, ApiClient
from upstox_client.api.get_profile_api import GetProfileApi
from upstox_client.api.get_market_api import GetMarketApi
from upstox_client.rest import ApiException

# ========== Streamlit Setup ==========
st.set_page_config(page_title="📈 Nifty 50 Dashboard", layout="wide")
st.title("📡 Nifty 50 Breakout Tracker")

# ========== Load Secrets ==========
ACCESS_TOKEN = st.secrets["ACCESS_TOKEN"]

# ========== Upstox Client Setup ==========
config = Configuration()
config.access_token = ACCESS_TOKEN
client = ApiClient(configuration=config)

# ========== Show User Profile ==========
try:
    profile_api = GetProfileApi(client)
    profile = profile_api.get_profile()
    st.subheader("👤 User Info")
    st.json(profile.to_dict())
except ApiException as e:
    st.error(f"Profile API Error: {e}")

# ========== Show Market Status ==========
try:
    market_api = GetMarketApi(client)
    status = market_api.get_market_status()
    st.subheader("📊 Market Status")
    st.json(status.to_dict())
except ApiException as e:
    st.error(f"Market Status API Error: {e}")

# ========== WebSocket Integration ==========
st.subheader("🧠 Live Quote Feed")

from nifty_ws import subscribe_feed, latest_quotes  # Ensure this module exists

def run_ws():
    asyncio.run(subscribe_feed())

if st.button("Start WebSocket Feed"):
    st.success("WebSocket started — listening for quotes...")
    threading.Thread(target=run_ws, daemon=True).start()

# Display live quotes and alerts
if latest_quotes:
    for symbol, info in latest_quotes.items():
        ltp = info.get("ltp")
        ts = info.get("timestamp", datetime.now().strftime('%H:%M:%S'))
        alert = info.get("alert")
        st.metric(label=f"{symbol}", value=f"₹{ltp}", delta=alert or "—", help=f"Last updated: {ts}")
else:
    st.info("Quotes will appear here once feed starts...")

# ========== Footer ==========
st.markdown("---")
st.caption("Built with ❤️ by Rahul • Powered by Streamlit & Upstox SDK")
