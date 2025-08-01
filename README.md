📈 Nifty 50 Real-Time Tracker – Streamlit App



Track real-time Nifty 50 data using Upstox WebSocket, powered by Streamlit and advanced technical indicators. This dashboard detects trends, generates breakout alerts, and visualizes key market metrics.



🔧 Features



\- ✅ Live Nifty 50 price stream via Upstox WebSocket  

\- 📊 Technical Indicators:

&nbsp; - EMA (20 \& 50)

&nbsp; - RSI (14)

&nbsp; - MACD + Histogram

&nbsp; - ADX

&nbsp; - Aroon Up \& Down

&nbsp; - Bollinger Bands



\- 🚨 Alerts:

&nbsp; - Trend crossover detection

&nbsp; - Bollinger Band breach signaling breakout/breakdown



\- 📉 Dashboard Highlights:

&nbsp; - Real-time candlestick chart

&nbsp; - Auto-refresh every 10 seconds

&nbsp; - Price metrics \& trend status



⚙️ Installation



Clone the repository and install dependencies:



```bash

git clone https://github.com/your-username/nifty-tracker

cd nifty-tracker

pip install -r requirements.txt

streamlit run app.py



🔑 Configuration



1\. Upstox API

Edit app.py and alert\_bot.py:



API\_KEY = "YOUR\_UPSTOX\_API\_KEY"

ACCESS\_TOKEN = "YOUR\_UPSTOX\_ACCESS\_TOKEN"



2\. Telegram Bot (Optional for Alerts)



TELEGRAM\_BOT\_TOKEN = "your\_telegram\_bot\_token"

TELEGRAM\_CHAT\_ID = "your\_chat\_id"



3\. Alert Sound



Place a file named alert.mp3 in the project folder for breakout alerts.



🚀 24/7 Telegram Alert Bot

To run background alerts without the Streamlit UI:



python alert\_bot.py



Optional (Linux/macOS) for 24/7 operation:



nohup python alert\_bot.py \&

tail -f nohup.out



📂 Project Structure



nifty\_live\_app/

│

├── app.py             # Streamlit dashboard with alerts

├── alert\_bot.py       # 24/7 Telegram alert bot

├── alert.mp3          # Beep sound for breakout alerts

├── requirements.txt   # Python dependencies

└── README.md          # Project documentation







