import requests
import os
import yfinance as yf
from datetime import datetime

def get_market_data():
    tickers = {
        "Nifty 50": "^NSEI",
        "Sensex": "^BSESN",
        "Nasdaq (Tech)": "^IXIC",
        "Gold": "GC=F",
        "USD/INR": "INR=X",
        "Crude Oil": "CL=F"
    }
    report = "🏛️ *MARKET & COMMODITIES*\n"
    for name, symbol in tickers.items():
        try:
            val = yf.Ticker(symbol).history(period="1d")['Close'].iloc[-1]
            report += f"• {name}: {val:,.2f}\n"
        except:
            report += f"• {name}: Data Pending\n"
    return report

def get_sector_news():
    api_key = os.getenv("NEWS_API_KEY")
    # Keywords covering AI, FinTech, Health, and Geopolitics
    query = "AI OR FinTech OR Geopolitics OR 'Indian Economy' OR Health"
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&pageSize=5&apiKey={api_key}"
    
    try:
        response = requests.get(url).json()
        articles = response.get("articles", [])
        news_text = "\n🌍 *GLOBAL INSIGHTS & SECTORS*\n"
        for i, art in enumerate(articles, 1):
            news_text += f"{i}. {art['title'][:75]}...\n"
        return news_text
    except:
        return "\n🌍 News feed currently unavailable."

def get_advice():
    # Simulated Financial Advisor Logic
    hour = datetime.now().hour
    advice = "\n💡 *ADVISOR'S NOTE*\n"
    advice += "_Focus on long-term diversification. High volatility in AI and Energy sectors suggests a 'Watch & Wait' approach for derivatives today._"
    return advice

def send_to_telegram(message):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

if __name__ == "__main__":
    header = f"📅 *FINANCIAL HUB ADVISOR - {datetime.now().strftime('%d %b %Y')}*\n\n"
    market = get_market_data()
    news = get_sector_news()
    advice = get_advice()
    
    full_report = f"{header}{market}{news}{advice}"
    send_to_telegram(full_report)
