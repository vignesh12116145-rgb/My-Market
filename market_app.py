import os, requests, telebot, time, json, threading
from datetime import datetime, timedelta
import yfinance as yf
from telebot import types

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWS_KEY = os.getenv("NEWS_API_KEY")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telebot.TeleBot(TOKEN)
DB_FILE = "intelligence_memory.json"

# --- PERSISTENCE LOGIC ---
def load_memory():
    if not os.path.exists(DB_FILE): return set()
    with open(DB_FILE, "r") as f: return set(json.load(f))

def save_memory(url):
    mem = list(load_memory())
    mem.append(url)
    with open(DB_FILE, "w") as f: json.dump(mem[-500:], f) # Store last 500

# --- LIVE CRASH MONITOR (99+ POINTS) ---
def monitor_market_crash():
    """Background thread to detect immediate 99-point drops."""
    while True:
        try:
            nifty = yf.Ticker("^NSEI").history(period="2d")
            open_p = nifty['Open'].iloc[-1]
            curr_p = nifty['Close'].iloc[-1]
            if (open_p - curr_p) > 99:
                bot.send_message(CHAT_ID, f"🚨 *CRASH ALERT: Nifty dropped {open_p-curr_p:.2f} points!*")
        except: pass
        time.sleep(60) # Check every 1 minute

# --- MENU BUILDERS ---
def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Indian Market", callback_data="indian_mkt"),
        types.InlineKeyboardButton("🌍 Global Indices", callback_data="global_mkt"),
        types.InlineKeyboardButton("🤖 AI & FinTech", callback_data="tech_news"),
        types.InlineKeyboardButton("🏥 Health & Pharma", callback_data="health_news"),
        types.InlineKeyboardButton("💱 Currencies", callback_data="fx_news"),
        types.InlineKeyboardButton("🥇 Commodities", callback_data="cmd_news")
    )
    return markup

# --- ELABORATE NEWS ENGINE ---
def get_deep_news(query):
    """Fetches elaborate news details instead of headlines."""
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&apiKey={NEWS_KEY}"
    news_report = ""
    sent_urls = load_memory()
    try:
        articles = requests.get(url, timeout=5).json().get('articles', [])
        count = 0
        for a in articles:
            if a['url'] not in sent_urls and count < 5:
                # Providing description for elaborate detail
                news_report += f"📌 *{a['source']['name']}*: {a['title'].upper()}\n_{a.get('description', '')}_\n\n"
                save_memory(a['url'])
                count += 1
        return news_report if news_report else "✅ No new updates in this sector."
    except: return "⚠️ News terminal temporarily offline."

# --- COMMAND HANDLERS ---
@bot.message_handler(commands=['start', 'menu'])
def show_menu(message):
    bot.reply_to(message, "🤵 *EXECUTIVE ADVISOR CONSOLE*\nSelect an option for live financial intelligence:", 
                 reply_markup=get_main_menu(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_menu_click(call):
    bot.answer_callback_query(call.id)
    cid = call.message.chat.id
    
    if call.data == "indian_mkt":
        # Using yfinance for near-real-time global/indian parity
        nifty = yf.Ticker("^NSEI").history(period="1d")['Close'].iloc[-1]
        bot.send_message(cid, f"📊 *LIVE NIFTY 50*: ₹{nifty:,.2f}\n🔍 Fetching elaborate news...")
        bot.send_message(cid, get_deep_news("Nifty OR Sensex OR 'Indian Economy'"), parse_mode="Markdown")
        
    elif call.data == "tech_news":
        bot.send_message(cid, "🤖 *AI & FINTECH INTELLIGENCE*")
        bot.send_message(cid, get_deep_news("AI OR FinTech OR 'Digital Banking'"), parse_mode="Markdown")

# --- EXECUTION ---
if __name__ == "__main__":
    # Start the 99-point monitor in background
    threading.Thread(target=monitor_market_crash, daemon=True).start()
    print("Advisor Bot LIVE with Interactive Menu and Crash Monitor...")
    bot.infinity_polling()
