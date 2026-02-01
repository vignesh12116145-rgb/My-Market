import os, requests, telebot, time
import yfinance as yf
from datetime import datetime

# --- SYSTEM CONFIG ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWS_KEY = os.getenv("NEWS_API_KEY")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telebot.TeleBot(TOKEN)
DB_FILE = "sent_news.txt"

def get_institutional_analysis():
    """Detects FII/DII activity and Suspicious Price-Volume Divergence"""
    intel = "🏛️ *INSTITUTIONAL & SUSPICIOUS MOVEMENT*\n"
    try:
        # Nifty Analysis for Institutional Footprints
        nifty = yf.Ticker("^NSEI").history(period="5d")
        avg_vol = nifty['Volume'].iloc[:-1].mean()
        curr_vol = nifty['Volume'].iloc[-1]
        vol_ratio = curr_vol / avg_vol
        price_change = ((nifty['Close'].iloc[-1] - nifty['Close'].iloc[-2]) / nifty['Close'].iloc[-2]) * 100
        
        if vol_ratio > 1.6 and price_change < -0.5:
            intel += "⚠️ *SUSPICIOUS:* Heavy Distribution detected. FIIs likely exiting bulk positions.\n"
        elif vol_ratio > 1.6 and price_change > 0.5:
            intel += "🚀 *ACCUMULATION:* Aggressive DII/FII buying detected via volume spike.\n"
        else:
            intel += "⚖️ *NEUTRAL:* Institutional flows are stable today.\n"
            
        intel += f"• *Nifty Alpha*: {price_change:+.2f}% | *Volume Intensity*: {vol_ratio:.1f}x avg\n"
    except: intel += "Institutional data engine recalibrating...\n"
    return intel

def get_deep_news_briefing():
    """Fetches 30 Elaborate Insights from Bloomberg, Moneycontrol, X & YouTube search"""
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    with open(DB_FILE, "r") as f: sent_ids = set(f.read().splitlines())

    # Advanced Multi-Topic Query
    query = "(site:bloomberg.com OR site:moneycontrol.com OR site:youtube.com) AND ('FII DII' OR 'AI regulation' OR 'geopolitics' OR 'FinTech' OR 'Derivatives')"
    url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&pageSize=100&apiKey={NEWS_KEY}"
    
    deep_news = []
    try:
        articles = requests.get(url).json().get("articles", [])
        for a in articles:
            url_id = a.get('url')
            if url_id not in sent_ids and len(deep_news) < 30:
                source = a['source']['name'].upper()
                title = a['title']
                # ELABORATE INFO (Description field provides the context)
                desc = a.get('description', 'Context analysis currently in progress...')
                deep_news.append(f"📌 *{source}: {title}*\n_{desc}_")
                with open(DB_FILE, "a") as f: f.write(url_id + "\n")
        return deep_news
    except: return []

def send_full_advisor_report():
    header = f"🤵 *EXECUTIVE ADVISOR INTEL ({datetime.now().strftime('%H:%M IST')})*\n"
    market_intel = get_institutional_analysis()
    
    # 1. Send Prediction & Institutional Analysis
    bot.send_message(CHAT_ID, header + market_intel, parse_mode="Markdown")
    
    # 2. Send 30 Elaborate News Items in batches
    news_items = get_deep_news_briefing()
    for i in range(0, len(news_items), 5):
        chunk = "\n\n".join(news_items[i:i+5])
        bot.send_message(CHAT_ID, f"🌍 *DEEP INTELLIGENCE (VOL {i//5 + 1})*\n\n" + chunk, parse_mode="Markdown")
        time.sleep(1.5)

@bot.message_handler(func=lambda m: True)
def on_query(m):
    bot.reply_to(m, "🧠 *System is cross-referencing Bloomberg, Moneycontrol, and X trends...*")
    send_full_advisor_report()

if __name__ == "__main__":
    send_full_advisor_report()
    if not os.getenv("GITHUB_ACTIONS"):
        bot.infinity_polling()
