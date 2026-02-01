import os
import requests
import telebot # pip install pyTelegramBotAPI
import yfinance as yf
from datetime import datetime

# --- SETTINGS ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWS_KEY = os.getenv("NEWS_API_KEY")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telebot.TeleBot(TOKEN)

def get_sector_report():
    # Covers: AI, FinTech, Health, Geopolitics, Commodities, Derivatives
    query = "AI OR FinTech OR Geopolitics OR 'Indian Stock Market' OR 'Health Sector' OR Commodities"
    url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&pageSize=4&apiKey={NEWS_KEY}"
    
    # Specific source searches (Bloomberg & Moneycontrol)
    sources = ["bloomberg.com", "moneycontrol.com"]
    source_msg = "\n📊 *APP UPDATES*"
    for site in sources:
        s_url = f"https://newsapi.org/v2/everything?q=site:{site}&pageSize=1&apiKey={NEWS_KEY}"
        try:
            art = requests.get(s_url).json().get("articles", [])[0]
            source_msg += f"\n• {site.split('.')[0].upper()}: {art['title'][:60]}..."
        except: pass

    try:
        data = requests.get(url).json().get("articles", [])
        news = "\n🌍 *GLOBAL & SECTOR NEWS*\n" + "\n".join([f"• {a['title']}" for a in data])
        return f"{news}\n{source_msg}"
    except: return "News currently unavailable."

def get_market_advisor():
    tickers = {"Nifty 50": "^NSEI", "Gold": "GC=F", "USD/INR": "INR=X"}
    m_data = "🏛️ *MARKET SUMMARY*\n"
    for k, v in tickers.items():
        try:
            p = yf.Ticker(v).history(period="1d")['Close'].iloc[-1]
            m_data += f"• {k}: {p:,.2f}\n"
        except: pass
    
    advice = "\n💡 *ADVISOR NOTE*\n_AI and Energy sectors show strength. Diversify into Commodities if Geopolitical news remains volatile._"
    return m_data + advice

def send_full_briefing():
    report = f"📅 *ADVISOR UPDATE - {datetime.now().strftime('%H:%M IST')}*\n"
    report += get_market_advisor() + get_sector_report()
    bot.send_message(CHAT_ID, report, parse_mode="Markdown")

# --- 24/7 LISTENER ---
@bot.message_handler(func=lambda m: True)
def handle_chat(message):
    bot.reply_to(message, "🔍 Analyzing Bloomberg, Moneycontrol, and Market Movements...")
    send_full_briefing()

if __name__ == "__main__":
    # If run by GitHub Actions (hourly), it sends the report.
    # If run on PythonAnywhere, it listens 24/7.
    if os.getenv("GITHUB_ACTIONS"):
        send_full_briefing()
    else:
        print("Bot is listening 24/7...")
        bot.infinity_polling()
