import requests
import os
import yfinance as yf

def get_market_data():
    try:
        # Fetching Nifty 50
        nifty = yf.Ticker("^NSEI").history(period="1d")['Close'].iloc[-1]
        return f"📈 Nifty 50: {nifty:.2f}"
    except:
        return "Market data temporarily unavailable."

def send_telegram(text):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text})

if __name__ == "__main__":
    report = get_market_data()
    send_telegram(report)
