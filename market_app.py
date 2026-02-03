import os, requests, telebot, time, json, threading
from datetime import datetime
import yfinance as yf
from telebot import types

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWS_KEY = os.getenv("NEWS_API_KEY")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telebot.TeleBot(TOKEN)
DB_FILE = "advisor_memory.json"

# --- PERSISTENCE ENGINE ---
def load_mem():
    if not os.path.exists(DB_FILE): return []
    with open(DB_FILE, "r") as f: return json.load(f)

def save_mem(url):
    mem = load_mem()
    mem.append(url)
    with open(DB_FILE, "w") as f: json.dump(mem[-500:], f)

# --- LIVE CRASH MONITOR (99+ POINTS) ---
def monitor_market():
    """Background loop: Monitors Nifty 50 every 60 seconds for crashes."""
    while True:
        try:
            # Check during Indian Market Hours (roughly)
            nifty = yf.Ticker("^NSEI").history(period="2d")
            open_p = nifty['Open'].iloc[-1]
            curr_p = nifty['Close'].iloc[-1]
            drop = open_p - curr_p
            
            if drop > 99:
                bot.send_message(CHAT_ID, f"🚨 *ADVISOR ALERT: MARKET CRASH*\n\nNifty has dropped *{drop:.2f} points* from today's open.\nLive Price: ₹{curr_p:,.2f}", parse_mode="Markdown")
        except: pass
        time.sleep(60)

# --- ELABORATE NEWS ENGINE ---
def fetch_deep_intel(category):
    queries = {
        "mkt": "Indian Stock Market OR 'Nifty 50' OR 'Sensex'",
        "tech": "AI OR FinTech OR 'NVIDIA' OR 'Digital India'",
        "geo": "Geopolitics OR 'Oil Prices' OR 'Global Trade'",
        "health": "Pharma OR HealthTech OR 'Apollo Hospitals'"
    }
    query = queries.get(category, "Finance")
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&apiKey={NEWS_KEY}"
    
    seen = load_mem()
    intel_report = ""
    try:
        articles = requests.get(url, timeout=5).json().get('articles', [])
        count = 0
        for a in articles:
            if a['url'] not in seen and count < 5:
                # Provide Elaborate Info (Description) instead of just headlines
                intel_report += f"📌 *{a['source']['name']}*: {a['title'].upper()}\n_{a.get('description', 'Context analysis in progress...')}_\n\n"
                save_mem(a['url'])
                count += 1
        return intel_report if intel_report else "✅ System Checked: No new big news."
    except: return "⚠️ Intel server timed out. Try again in 60s."

# --- INTERACTIVE MENU ---
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Indian Market", callback_data="mkt"),
        types.InlineKeyboardButton("🌍 Global/Geo", callback_data="geo"),
        types.InlineKeyboardButton("🤖 AI & FinTech", callback_data="tech"),
        types.InlineKeyboardButton("🏥 Health/Pharma", callback_data="health"),
        types.InlineKeyboardButton("💱 Currencies", callback_data="fx"),
        types.InlineKeyboardButton("🥇 Commodities", callback_data="cmd")
    )
    return markup

# --- HANDLERS ---
@bot.message_handler(commands=['start', 'menu'])
def welcome(message):
    bot.reply_to(message, "🤵 *EXECUTIVE AI ADVISOR*\nReal-time Market & Sector Intelligence.", 
                 reply_markup=get_main_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_menu(call):
    bot.answer_callback_query(call.id, "Gathering Live Intel...")
    cid = call.message.chat.id
    
    if call.data in ["mkt", "tech", "geo", "health"]:
        report = fetch_deep_intel(call.data)
        bot.send_message(cid, report, parse_mode="Markdown")
    
    elif call.data == "fx":
        # Live Currency
        inr = yf.Ticker("INR=X").history(period="1d")['Close'].iloc[-1]
        bot.send_message(cid, f"💱 *USD/INR Live*: ₹{inr:.2f}", parse_mode="Markdown")

# --- START SYSTEM ---
if __name__ == "__main__":
    # Start Crash Monitor in Background
    threading.Thread(target=monitor_market, daemon=True).start()
    print("AI Advisor System: ONLINE")
    bot.infinity_polling()
