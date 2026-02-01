import requests
import os
import yfinance as yf

def get_market_report():
    try:
        # Fetch Nifty 50 and Sensex
        nifty = yf.Ticker("^NSEI").history(period="1d")['Close'].iloc[-1]
        sensex = yf.Ticker("^BSESN").history(period="1d")['Close'].iloc[-1]
        return f"📊 *MARKET UPDATE*\n\n🔹 Nifty 50: {nifty:,.2f}\n🔹 Sensex: {sensex:,.2f}\n"
    except Exception:
        return "📊 *MARKET UPDATE*\n(Market data unavailable)\n"

def get_news_report():
    api_key = os.getenv("NEWS_API_KEY")
    url = f"https://newsapi.org/v2/top-headlines?country=in&category=business&pageSize=3&apiKey={api_key}"
    
    try:
        response = requests.get(url).json()
        articles = response.get("articles", [])
        news_text = "\n📰 *TOP BUSINESS NEWS*\n"
        
        for i, article in enumerate(articles, 1):
            title = article['title'].split(' - ')[0] # Clean title
            news_text += f"{i}. {title}\n"
        
        return news_text
    except Exception:
        return "\n📰 *TOP BUSINESS NEWS*\n(News unavailable)"

def send_to_telegram(message):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # Using Markdown for bold text and icons
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

if __name__ == "__main__":
    market_data = get_market_report()
    news_data = get_news_report()
    
    final_message = f"{market_data}{news_data}"
    send_to_telegram(final_message)
