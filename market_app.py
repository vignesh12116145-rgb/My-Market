import os
import requests
import telebot
import yfinance as yf
from datetime import datetime

# Initialize
TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWS_KEY = os.getenv("NEWS_API_KEY")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telebot.TeleBot(TOKEN)

def get_financial_data():
    """Stock Market, Commodities, Currencies, Derivatives"""
    tickers = {
        "Nifty 50": "^NSEI", "Nasdaq": "^IXIC", "Gold": "GC=F", 
        "Crude Oil": "CL=F", "USD/INR": "INR=X", "Bank Nifty": "^NSEBANK"
    }
    data = "🏛️ *MARKET & COMMODITIES*\n"
    for name, sym in tickers.items():
        try:
            val = yf.Ticker(sym).history(period="1d")['Close'].iloc[-1]
            data += f"• {name}: {val:,.2f}\n"
        except: data += f"• {name}: Fetching...\n"
    return data

def get_curated_news():
    """AI, FinTech, Geopolitical, Bloomberg, Moneycontrol, X/YT Trends"""
    # Searching specific domains + keywords
    queries = [
        "site:bloomberg.com Geopolitical AI Finance",
        "site:moneycontrol.com Indian Stock Market Derivatives",
        "FinTech Health AI Global Economy",
        "YouTube X Trending Stock Market Analysis"
    ]
    news_report = "\n🌍 *ADVISOR INSIGHTS & APP NEWS*"
    
    for q in queries:
        url = f"https://newsapi.org/v2/everything?q={q}&sortBy=publishedAt&pageSize=1&apiKey={NEWS_KEY}"
        try:
            art = requests.get(url).json().get("articles", [])[0]
            news_report += f"\n• {art['title'][:75]}..."
        except: pass
    return news_report

def get_advice():
    return "\n\n💡 *FINANCIAL ADVISOR NOTE*\n_Current volatility in Indian markets suggests a cautious approach to derivatives. Monitor Bloomberg for global geopolitical shifts affecting commodities._"

def send_update():
    current_time = datetime.now().strftime('%H:%M IST')
    header = f"🤵 *FINANCIAL ADVISOR BRIEFING ({current_time})*\n\n"
    full_msg = header + get_financial_data() + get_curated_news() + get_advice()
    bot.send_message(CHAT_ID, full_msg, parse_mode="Markdown")

# --- 24/7 LISTENING LOGIC ---
@bot.message_handler(func=lambda message: True)
def respond_to_user(message):
    bot.reply_to(message, "🔍 Scanning Bloomberg, Moneycontrol & Global Markets... One moment.")
    send_update()

if __name__ == "__main__":
    # If GITHUB_ACTIONS environment variable exists, just send the report once
    if os.getenv("GITHUB_ACTIONS"):
        send_update()
    else:
        # For 24/7 Hosting (PythonAnywhere)
        print("Bot is listening for your messages...")
        bot.infinity_polling()
