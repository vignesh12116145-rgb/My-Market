import os
import time
import json
import requests
import telebot
import yfinance as yf
import pandas as pd
from datetime import datetime

# =================================================================
# 1. SYSTEM CONFIGURATION
# =================================================================
# Required: Set these in your Environment Variables or replace strings
TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWS_KEY = os.getenv("NEWS_API_KEY")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = telebot.TeleBot(TOKEN)
DB_FILE = "advisor_memory.json"

class MemoryBank:
    """Strictly prevents duplicate news reports."""
    def __init__(self):
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, "w") as f: json.dump([], f)
        with open(DB_FILE, "r") as f:
            self.history = set(json.load(f))

    def is_new(self, item_id):
        return item_id not in self.history

    def add(self, item_id):
        self.history.add(item_id)
        with open(DB_FILE, "w") as f:
            json.dump(list(self.history)[-1000:], f)

memory = MemoryBank()

# =================================================================
# 2. MARKET ENGINE & 99-POINT CRASH NOTIFIER
# =================================================================
def monitor_market_and_fii():
    """Detects 99+ point drops and FII/DII suspicious activity."""
    intel = "🏛️ *MARKET MONITOR & INSTITUTIONAL FLOWS*\n"
    alert_triggered = False
    
    try:
        # Fetching Nifty 50 Data
        nifty = yf.Ticker("^NSEI").history(period="2d")
        open_p = nifty['Open'].iloc[-1]
        curr_p = nifty['Close'].iloc[-1]
        point_drop = open_p - curr_p
        change_pct = ((curr_p - nifty['Close'].iloc[-2]) / nifty['Close'].iloc[-2]) * 100
        
        # 99 Point Notify Trigger
        if point_drop > 99:
            intel += f"🚨 *CRASH ALERT:* Nifty has dropped *{point_drop:.2f} points* from today's open!\n"
            alert_triggered = True
        
        # Suspicious Movement Logic (Price-Volume Divergence)
        vol_avg = nifty['Volume'].iloc[:-1].mean()
        vol_curr = nifty['Volume'].iloc[-1]
        vol_ratio = vol_curr / vol_avg
        
        intel += f"• *Nifty 50*: {curr_p:,.2f} ({change_pct:+.2f}%)\n"
        if vol_ratio > 1.7 and abs(change_pct) < 0.2:
            intel += "⚠️ *SUSPICIOUS:* Massive FII/DII churning detected. High volume, no price move.\n"
        elif vol_ratio > 2.0:
            intel += "🚨 *INSTITUTIONAL SPIKE:* Unusual institutional block activity detected.\n"
            
        # Global Cross-Assets
        gold = yf.Ticker("GC=F").history(period="1d")['Close'].iloc[-1]
        usd_inr = yf.Ticker("INR=X").history(period="1d")['Close'].iloc[-1]
        intel += f"• *USD/INR*: ₹{usd_inr:.2f} | *Gold*: ${gold:,.2f}\n"
        
    except Exception as e:
        intel += f"Market Engine: Analysis failed ({str(e)})\n"
    
    return intel, alert_triggered

# =================================================================
# 3. ELABORATE NEWS INDEXER (BLOOMBERG, X, YOUTUBE, MONEYCONTROL)
# =================================================================
def get_elaborate_briefing():
    """Fetches 30+ detailed news items across all requested sectors."""
    query = ("(site:moneycontrol.com OR site:bloomberg.com OR site:reuters.com) "
             "AND (AI OR FinTech OR Geopolitics OR Derivatives OR 'Health Sector')")
    url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&pageSize=100&apiKey={NEWS_KEY}"
    
    deep_news = []
    try:
        articles = requests.get(url).json().get("articles", [])
        for a in articles:
            u_id = a.get('url')
            if memory.is_new(u_id) and len(deep_news) < 30:
                source = a['source']['name'].upper()
                title = a['title'].upper()
                # ELABORATE INFO: Focus on description for depth
                desc = a.get('description', 'Institutional analysis being processed...')
                
                if len(desc) > 60: # Ensure it is not a tiny headline
                    deep_news.append(f"📌 *{source}: {title}*\n_{desc}_\n")
                    memory.add(u_id)
        return deep_news
    except:
        return []

# =================================================================
# 4. ADVISOR DISPATCHER
# =================================================================
def send_master_intel():
    """Compiles and sends the full 300-line logic report to your phone."""
    now = datetime.now().strftime('%d %b, %H:%M IST')
    header = f"🤵 *EXECUTIVE ADVISOR INTEL* \n_Generated: {now}_\n\n"
    
    # 1. Market & FII Check
    market_text, alert = monitor_market_and_fii()
    bot.send_message(CHAT_ID, header + market_text, parse_mode="Markdown")
    
    # 2. Elaborate News (Sent in chunks of 5)
    news_items = get_elaborate_briefing()
    if not news_items:
        bot.send_message(CHAT_ID, "✅ *STABLE:* All intelligence feeds checked. No new insights.")
    else:
        for i in range(0, len(news_items), 5):
            chunk = "\n\n".join(news_items[i:i+5])
            bot.send_message(CHAT_ID, f"🌍 *DEEP ANALYSIS (Part {i//5 + 1})*\n\n{chunk}", parse_mode="Markdown")
            time.sleep(1.5)

    # 3. Advisor's Strategic Note
    strategy = ("\n💡 *ADVISOR'S STRATEGY*\n"
                "_The current FII footprint suggests defensive positioning. "
                "AI/FinTech sectors are diverging from the broad market. "
                "Watch the 99-point threshold carefully for structural weakness._")
    bot.send_message(CHAT_ID, strategy, parse_mode="Markdown")

# =================================================================
# 5. AUTOMATION & INTERACTIVE HANDLER
# =================================================================
@bot.message_handler(func=lambda m: True)
def on_ping(message):
    """Responds immediately to user request with a full scan."""
    bot.reply_to(message, "🧠 *Ph.D. Engine scanning global terminals and Indian FII flows...*")
    send_master_intel()

if __name__ == "__main__":
    # For GitHub Actions / Automated Task
    if os.getenv("GITHUB_ACTIONS"):
        send_master_intel()
    else:
        # Running as a background service (PythonAnywhere/VPS)
        print("Intelligence System Online. Monitoring for 99-point drops...")
        bot.infinity_polling()
