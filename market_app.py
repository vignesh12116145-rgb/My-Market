import requests
import os
import yfinance as yf

def send_telegram(text):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text})

if __name__ == "__main__":
    try:
        nifty = yf.Ticker("^NSEI").history(period="1d")['Close'].iloc[-1]
        msg = f"📊 Nifty 50: {nifty:.2f}"
    except Exception as e:
        msg = "Market data fetch failed."
    
    send_telegram(msg)
