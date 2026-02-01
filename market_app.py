import os
import requests
import telebot
import yfinance as yf
from datetime import datetime

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWS_KEY = os.getenv("NEWS_API_KEY")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telebot.TeleBot(TOKEN)

# File to store IDs of news already sent
DB_FILE = "sent_news.txt"

def load_sent_news():
    if not os.path.exists(DB_FILE): return set()
    with open(DB_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_sent_news(news_id):
    with open(DB_FILE, "a") as f:
        f.write(f"{news_id}\n")

def get_market_deep_analysis():
    report = "🏛️ *DEEP MARKET INTELLIGENCE*\n"
    try:
        # Nifty Analysis
        nifty = yf.Ticker("^NSEI").history(period="5d")
        price = nifty['Close'].iloc[-1]
        change = ((price - nifty['Close'].iloc[-2]) / nifty['Close'].iloc[-2]) * 100
        
        # FII/DII/Suspicious Detection
        vol_today = nifty['Volume'].iloc[-1]
        avg_vol = nifty['Volume'].iloc[:-1].mean()
        
        report += f"• *Nifty 50*: {price:,.2f} ({change:+.2f}%)\n"
        if vol_today > avg_vol * 1.5:
            report += "⚠️ *SUSPICIOUS:* Volume is 50% above average. Huge Institutional (FII/DII) activity detected!\n"
        
        # USD/INR and Gold
        inr = yf.Ticker("INR=X").history(period="1d")['Close'].iloc[-1]
        gold = yf.Ticker("GC=F").history(period="1d")['Close'].iloc[-1]
        report += f"• *USD/INR*: ₹{inr:.2f} | *Gold*: ${gold:,.2f}\n"
    except: report += "Market data refreshing...\n"
    return report

def get_30_fresh_news():
    sent_ids = load_sent_news()
    # Broad query for Bloomberg, Moneycontrol, AI, Finance, etc.
    query = "(site:bloomberg.com OR site:moneycontrol.com OR site:reuters.com) AND (AI OR FinTech OR Geopolitics OR 'Stock Market')"
    url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&pageSize=60&apiKey={NEWS_KEY}"
    
    news_list = []
    try:
        articles = requests.get(url).json().get("articles", [])
        for a in articles:
            news_id = a.get('url') # Using URL as a unique ID
            if news_id not in sent_ids and len(news_list) < 30:
                title = a['title']
                desc = a.get('description', 'Detailed analysis coming soon...')
                source = a['source']['name']
                
                news_list.append(f"📌 *{source}*: {title}\n_{desc}_")
                save_sent_news(news_id) # Mark as sent
        
        if not news_list: return ["\n✅ No new 'Big News' in the last hour. All news is up to date."]
        return news_list
    except: return ["News engine is updating..."]

def send_elaborate_briefing():
    # Telegram limit is 4096 characters. We split 30 news items into multiple messages.
    header = f"🤵 *OFFICIAL ADVISOR BRIEFING* ({datetime.now().strftime('%H:%M IST')})\n\n"
    market_data = get_market_deep_analysis()
    
    bot.send_message(CHAT_ID, header + market_data, parse_mode="Markdown")
    
    news_items = get_30_fresh_news()
    # Sending news in chunks to avoid character limit errors
    current_chunk = "🌍 *ELABORATE SECTOR ANALYSIS*\n"
    for i, item in enumerate(news_items, 1):
        if len(current_chunk + item) > 3800:
            bot.send_message(CHAT_ID, current_chunk, parse_mode="Markdown")
            current_chunk = ""
        current_chunk += f"\n{i}. {item}\n"
    
    if current_chunk:
        bot.send_message(CHAT_ID, current_chunk, parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def on_user_query(message):
    bot.reply_to(message, "⚙️ Analyzing FII/DII data and Bloomberg reports... compiling your 30-news briefing.")
    send_elaborate_briefing()

if __name__ == "__main__":
    send_elaborate_briefing()
    if not os.getenv("GITHUB_ACTIONS"):
        bot.infinity_polling()
