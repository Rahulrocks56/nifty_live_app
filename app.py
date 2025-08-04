# app.py

import streamlit as st
from upstox_client import UpstoxClient
from upstox_client.rest import ApiException
from upstox_client.models import GetProfileResponse, GetMarketStatusResponse

# ========== Setup Streamlit UI ==========
st.set_page_config(page_title="Nifty 50 Live Tracker", layout="wide")
st.title("📈 Nifty 50 Live Dashboard")
st.caption("Powered by Upstox SDK & Streamlit")

# ========== Load Secrets ==========
ACCESS_TOKEN = st.secrets["ACCESS_TOKEN"]

# ========== Configure API Client ==========
configuration = UpstoxClient.Configuration()
configuration.access_token = ACCESS_TOKEN
client = UpstoxClient(configuration)

# ========== Fetch & Display User Info ==========
st.subheader("👤 User Info")

try:
    profile: GetProfileResponse = client.get_profile_api().get_profile()
    st.json(profile.to_dict())
except ApiException as e:
    st.error(f"Profile API Exception: {e}")

# ========== Fetch & Display Market Status ==========
st.subheader("📊 Market Status")

try:
    market_status: GetMarketStatusResponse = client.get_market_api().get_market_status()
    st.json(market_status.to_dict())
except ApiException as e:
    st.error(f"Market Status API Exception: {e}")

# ========== Placeholder for Nifty 50 Quotes ==========
st.subheader("🧠 Nifty 50 Live Data (Coming Soon)")
st.info("Real-time quotes and breakout logic coming next...")

# ========== Footer ==========
st.markdown("---")
st.caption("Developed by Rahul • Streamlit + Upstox SDK")
