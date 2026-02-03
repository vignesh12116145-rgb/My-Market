import os, requests, telebot, time, json, threading
from datetime import datetime, timedelta
import feedparser
from bs4 import BeautifulSoup
from telebot import types

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWS_KEY = os.getenv("NEWS_API_KEY")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telebot.TeleBot(TOKEN)
DB_FILE = "advisor_memory.json"
ALERT_SENT = {}  # Track sent alerts

# --- PERSISTENCE ENGINE ---
def load_mem():
    """Load seen URLs from memory"""
    if not os.path.exists(DB_FILE): 
        return {"seen_urls": [], "last_update": None}
    try:
        with open(DB_FILE, "r") as f: 
            return json.load(f)
    except:
        return {"seen_urls": [], "last_update": None}

def save_mem(url):
    """Save URL to memory (keep last 500)"""
    mem = load_mem()
    if "seen_urls" not in mem:
        mem["seen_urls"] = []
    mem["seen_urls"].append(url)
    mem["seen_urls"] = mem["seen_urls"][-500:]  # Keep last 500
    mem["last_update"] = datetime.now().isoformat()
    with open(DB_FILE, "w") as f: 
        json.dump(mem, f)

# --- SMART MARKET MONITOR ---
def get_nse_data():
    """Get real Indian market data from NSE"""
    try:
        url = "https://www.nseindia.com/api/allIndices"
        headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            indices = {}
            
            for index in data.get('data', []):
                name = index.get('index', '')
                if name in ['NIFTY 50', 'NIFTY BANK']:
                    indices[name] = {
                        'last': float(index.get('last', 0)),
                        'change': float(index.get('percentChange', 0)),
                        'open': float(index.get('open', 0))
                    }
            
            return indices
    except:
        pass
    
    return None

def monitor_market():
    """Enhanced background monitor: Detects crashes, surges, and unusual moves"""
    global ALERT_SENT
    last_check = {}
    
    print("🔍 Market Monitor: ACTIVE")
    
    while True:
        try:
            # Only monitor during market hours (9:15 AM - 3:30 PM IST)
            now = datetime.now()
            hour = now.hour
            minute = now.minute
            
            # Market hours check (approximate)
            if not (9 <= hour <= 15):
                time.sleep(300)  # Check every 5 min outside market hours
                continue
            
            # Get current market data
            indices = get_nse_data()
            
            if not indices:
                time.sleep(120)
                continue
            
            for name, data in indices.items():
                current = data['last']
                change_pct = data['change']
                open_price = data['open']
                
                # Calculate point drop/rise
                point_change = current - open_price
                
                # Alert conditions
                alert_msg = None
                
                # 1. Big percentage moves (>1.5%)
                if abs(change_pct) > 1.5:
                    if change_pct < -1.5:
                        alert_msg = f"🚨 *MARKET CRASH ALERT*\n\n*{name}* is down *{abs(change_pct):.2f}%* today!\n\nCurrent: ₹{current:,.2f}\nDrop: {point_change:,.0f} points"
                    elif change_pct > 1.5:
                        alert_msg = f"🚀 *MARKET SURGE ALERT*\n\n*{name}* is up *{change_pct:.2f}%* today!\n\nCurrent: ₹{current:,.2f}\nGain: +{point_change:,.0f} points"
                
                # 2. Large point moves (NIFTY >200, BANK NIFTY >400)
                threshold = 200 if name == 'NIFTY 50' else 400
                if abs(point_change) > threshold:
                    direction = "DOWN" if point_change < 0 else "UP"
                    emoji = "🚨" if point_change < 0 else "🚀"
                    alert_msg = f"{emoji} *BIG MOVE ALERT*\n\n*{name}* moved {direction} by *{abs(point_change):,.0f} points*!\n\nCurrent: ₹{current:,.2f}\nChange: {change_pct:+.2f}%"
                
                # 3. Rapid change detection (comparing to last check)
                if name in last_check:
                    last_price = last_check[name]
                    quick_change = ((current - last_price) / last_price) * 100
                    
                    if abs(quick_change) > 0.5:  # 0.5% in 2 minutes
                        alert_msg = f"⚡ *RAPID MOVEMENT*\n\n*{name}* moved *{quick_change:+.2f}%* in last 2 minutes!\n\nCurrent: ₹{current:,.2f}"
                
                # Send alert if not sent recently (cooldown: 10 minutes)
                alert_key = f"{name}_{datetime.now().strftime('%Y%m%d%H%M')[:-1]}"  # Round to 10 min
                
                if alert_msg and alert_key not in ALERT_SENT:
                    try:
                        bot.send_message(CHAT_ID, alert_msg, parse_mode="Markdown")
                        ALERT_SENT[alert_key] = True
                        print(f"✓ Alert sent: {name}")
                    except Exception as e:
                        print(f"Alert send error: {e}")
                
                # Update last check
                last_check[name] = current
            
            # Clean old alerts (keep last 50)
            if len(ALERT_SENT) > 50:
                ALERT_SENT.clear()
        
        except Exception as e:
            print(f"Monitor error: {e}")
        
        time.sleep(120)  # Check every 2 minutes during market hours

# --- ENHANCED NEWS ENGINE ---
def fetch_deep_intel(category):
    """Fetch detailed, current news with NO old articles"""
    queries = {
        "mkt": "india (nifty OR sensex OR stock market)",
        "tech": "(AI OR fintech OR technology) india",
        "geo": "geopolitics (trade OR tariff OR sanctions)",
        "health": "(pharma OR healthcare OR biotech) india",
        "all": "india (economy OR finance OR business)"
    }
    
    query = queries.get(category, queries["all"])
    seen = load_mem().get("seen_urls", [])
    
    intel_report = ""
    article_count = 0
    
    # NewsAPI - Last 2 days only
    if NEWS_KEY:
        try:
            from_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
            url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&language=en&sortBy=publishedAt&pageSize=20&apiKey={NEWS_KEY}"
            
            response = requests.get(url, timeout=8)
            
            if response.status_code == 200:
                articles = response.json().get('articles', [])
                
                for article in articles:
                    article_url = article.get('url', '')
                    
                    if article_url in seen:
                        continue
                    
                    if article_count >= 5:
                        break
                    
                    source = article.get('source', {}).get('name', 'NEWS')
                    title = article.get('title', '')
                    description = article.get('description', '')
                    
                    if not title or len(title) < 10:
                        continue
                    
                    # Clean description
                    if description:
                        desc_clean = BeautifulSoup(description, 'html.parser').get_text()[:300]
                    else:
                        desc_clean = "Read full article for details."
                    
                    intel_report += f"📌 *{source.upper()}*\n"
                    intel_report += f"*{title}*\n\n"
                    intel_report += f"_{desc_clean}_\n"
                    intel_report += f"🔗 [Read Full Article]({article_url})\n\n"
                    intel_report += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    
                    save_mem(article_url)
                    article_count += 1
        
        except Exception as e:
            print(f"NewsAPI error: {e}")
    
    # RSS Feeds as backup
    if article_count < 3:
        rss_feeds = {
            "mkt": ['https://www.livemint.com/rss/markets'],
            "tech": ['https://feeds.bloomberg.com/technology/news.rss'],
            "geo": ['https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best'],
            "health": ['https://www.livemint.com/rss/companies']
        }
        
        feeds = rss_feeds.get(category, rss_feeds["mkt"])
        
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:5]:
                    if article_count >= 5:
                        break
                    
                    title = entry.get('title', '')
                    link = entry.get('link', '')
                    
                    if link in seen or not title:
                        continue
                    
                    summary = entry.get('summary', '')
                    if summary:
                        summary_clean = BeautifulSoup(summary, 'html.parser').get_text()[:300]
                    else:
                        summary_clean = ""
                    
                    intel_report += f"📰 *{title}*\n"
                    if summary_clean:
                        intel_report += f"_{summary_clean}_\n"
                    intel_report += f"🔗 [Read]({link})\n\n"
                    
                    save_mem(link)
                    article_count += 1
            
            except:
                continue
    
    return intel_report if intel_report else "✅ No new significant news in this category."

def get_market_overview():
    """Get complete market overview"""
    overview = "📊 *COMPLETE MARKET OVERVIEW*\n\n"
    
    # Indian Markets
    try:
        indices = get_nse_data()
        if indices:
            overview += "🇮🇳 *INDIAN MARKETS*\n"
            for name, data in indices.items():
                change = data['change']
                emoji = "🟢" if change >= 0 else "🔴"
                overview += f"{emoji} *{name}*: ₹{data['last']:,.2f} ({change:+.2f}%)\n"
            overview += "\n"
    except:
        overview += "🇮🇳 *INDIAN MARKETS*: Updating...\n\n"
    
    # Global Markets
    try:
        overview += "🌍 *GLOBAL MARKETS*\n"
        global_symbols = {'^DJI': 'DOW JONES', '^GSPC': 'S&P 500', '^IXIC': 'NASDAQ'}
        
        for symbol, name in global_symbols.items():
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
                response = requests.get(url, timeout=3)
                
                if response.status_code == 200:
                    data = response.json()['chart']['result'][0]['meta']
                    current = data.get('regularMarketPrice', 0)
                    prev = data.get('previousClose', current)
                    
                    if prev > 0:
                        change_pct = ((current - prev) / prev) * 100
                        emoji = "🟢" if change_pct >= 0 else "🔴"
                        overview += f"{emoji} *{name}*: {current:,.2f} ({change_pct:+.2f}%)\n"
            except:
                continue
        
        overview += "\n"
    except:
        overview += "Global data updating...\n\n"
    
    # Currencies
    try:
        overview += "💱 *CURRENCIES*\n"
        curr_url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(curr_url, timeout=3)
        
        if response.status_code == 200:
            rates = response.json().get('rates', {})
            inr = rates.get('INR', 0)
            if inr > 0:
                overview += f"• *USD/INR*: ₹{inr:.2f}\n"
        
        overview += "\n"
    except:
        overview += "Currency data updating...\n\n"
    
    # Commodities
    try:
        overview += "🥇 *COMMODITIES*\n"
        commodities = {'GC=F': 'GOLD', 'SI=F': 'SILVER', 'CL=F': 'CRUDE OIL'}
        
        for symbol, name in commodities.items():
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
                response = requests.get(url, timeout=3)
                
                if response.status_code == 200:
                    data = response.json()['chart']['result'][0]['meta']
                    current = data.get('regularMarketPrice', 0)
                    prev = data.get('previousClose', current)
                    
                    if prev > 0:
                        change_pct = ((current - prev) / prev) * 100
                        emoji = "🟢" if change_pct >= 0 else "🔴"
                        overview += f"{emoji} *{name}*: ${current:,.2f} ({change_pct:+.2f}%)\n"
            except:
                continue
    except:
        overview += "Commodity data updating...\n"
    
    overview += f"\n🕐 Updated: {datetime.now().strftime('%I:%M %p IST')}"
    
    return overview

# --- ENHANCED INTERACTIVE MENU ---
def get_main_keyboard():
    """Enhanced interactive menu with more options"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Market Overview", callback_data="overview"),
        types.InlineKeyboardButton("🇮🇳 Indian Market News", callback_data="mkt"),
        types.InlineKeyboardButton("🌍 Global/Geopolitics", callback_data="geo"),
        types.InlineKeyboardButton("🤖 AI & FinTech", callback_data="tech"),
        types.InlineKeyboardButton("🏥 Health/Pharma", callback_data="health"),
        types.InlineKeyboardButton("💱 Live Currencies", callback_data="fx"),
        types.InlineKeyboardButton("🥇 Commodities", callback_data="cmd"),
        types.InlineKeyboardButton("📰 All Top News", callback_data="all"),
        types.InlineKeyboardButton("🔄 Refresh Menu", callback_data="refresh")
    )
    return markup

# --- HANDLERS ---
@bot.message_handler(commands=['start', 'menu', 'help'])
def welcome(message):
    """Welcome message with menu"""
    welcome_text = (
        "🤵 *EXECUTIVE AI MARKET ADVISOR*\n\n"
        "✅ Real-time market monitoring\n"
        "✅ Crash & surge alerts\n"
        "✅ Comprehensive news intelligence\n"
        "✅ Live market data\n\n"
        "_Select an option below:_"
    )
    bot.reply_to(message, welcome_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    """Handle text messages with keywords"""
    text = message.text.lower()
    
    if any(word in text for word in ['news', 'headlines', 'update']):
        bot.reply_to(message, "📰 Fetching latest news...")
        news = fetch_deep_intel("all")
        bot.send_message(message.chat.id, news, parse_mode="Markdown", disable_web_page_preview=True)
    
    elif any(word in text for word in ['market', 'nifty', 'sensex', 'stock']):
        bot.reply_to(message, "📊 Getting market data...")
        overview = get_market_overview()
        bot.send_message(message.chat.id, overview, parse_mode="Markdown")
    
    else:
        # Show menu
        bot.reply_to(message, "👋 Welcome! Select an option:", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_menu(call):
    """Enhanced callback handler"""
    bot.answer_callback_query(call.id, "Processing...")
    cid = call.message.chat.id
    
    try:
        if call.data == "overview":
            overview = get_market_overview()
            bot.send_message(cid, overview, parse_mode="Markdown")
        
        elif call.data in ["mkt", "tech", "geo", "health", "all"]:
            category_names = {
                "mkt": "Indian Market",
                "tech": "AI & FinTech",
                "geo": "Global/Geopolitics",
                "health": "Health/Pharma",
                "all": "Top"
            }
            
            bot.send_message(cid, f"📰 *{category_names.get(call.data, 'Latest')} News*\n_Gathering intelligence..._", parse_mode="Markdown")
            
            report = fetch_deep_intel(call.data)
            bot.send_message(cid, report, parse_mode="Markdown", disable_web_page_preview=True)
        
        elif call.data == "fx":
            try:
                curr_url = "https://api.exchangerate-api.com/v4/latest/USD"
                response = requests.get(curr_url, timeout=5)
                
                if response.status_code == 200:
                    rates = response.json().get('rates', {})
                    inr = rates.get('INR', 0)
                    eur = rates.get('EUR', 0)
                    gbp = rates.get('GBP', 0)
                    
                    fx_msg = "💱 *LIVE CURRENCY RATES*\n\n"
                    if inr > 0:
                        fx_msg += f"• *USD/INR*: ₹{inr:.2f}\n"
                        if eur > 0:
                            fx_msg += f"• *EUR/INR*: ₹{(inr/eur):.2f}\n"
                        if gbp > 0:
                            fx_msg += f"• *GBP/INR*: ₹{(inr/gbp):.2f}\n"
                    
                    fx_msg += f"\n🕐 {datetime.now().strftime('%I:%M %p IST')}"
                    
                    bot.send_message(cid, fx_msg, parse_mode="Markdown")
            except:
                bot.send_message(cid, "⚠️ Currency data temporarily unavailable")
        
        elif call.data == "cmd":
            bot.send_message(cid, "🥇 Getting commodity prices...")
            
            cmd_msg = "🥇 *LIVE COMMODITY PRICES*\n\n"
            commodities = {'GC=F': 'GOLD', 'SI=F': 'SILVER', 'CL=F': 'CRUDE OIL', 'HG=F': 'COPPER'}
            
            for symbol, name in commodities.items():
                try:
                    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
                    response = requests.get(url, timeout=3)
                    
                    if response.status_code == 200:
                        data = response.json()['chart']['result'][0]['meta']
                        current = data.get('regularMarketPrice', 0)
                        prev = data.get('previousClose', current)
                        
                        if prev > 0:
                            change_pct = ((current - prev) / prev) * 100
                            emoji = "🟢" if change_pct >= 0 else "🔴"
                            cmd_msg += f"{emoji} *{name}*: ${current:,.2f} ({change_pct:+.2f}%)\n"
                except:
                    continue
            
            cmd_msg += f"\n🕐 {datetime.now().strftime('%I:%M %p IST')}"
            bot.send_message(cid, cmd_msg, parse_mode="Markdown")
        
        elif call.data == "refresh":
            bot.send_message(cid, "🔄 Menu refreshed!", reply_markup=get_main_keyboard())
    
    except Exception as e:
        print(f"Callback error: {e}")
        bot.send_message(cid, "⚠️ Error processing request. Try again.")

# --- SCHEDULED UPDATES ---
def scheduled_briefing():
    """Send scheduled morning/evening briefings"""
    while True:
        try:
            now = datetime.now()
            hour = now.hour
            
            # Morning briefing: 9 AM IST
            if hour == 9 and now.minute == 0:
                header = "🤵 *MORNING MARKET BRIEFING*\n"
                header += f"📅 {now.strftime('%d %B %Y, %I:%M %p')}\n\n"
                
                overview = get_market_overview()
                bot.send_message(CHAT_ID, header + overview, parse_mode="Markdown")
                
                time.sleep(60)  # Wait 1 minute
                
                bot.send_message(CHAT_ID, "📰 *TOP MORNING NEWS*", parse_mode="Markdown")
                news = fetch_deep_intel("all")
                bot.send_message(CHAT_ID, news, parse_mode="Markdown", disable_web_page_preview=True)
            
            # Evening briefing: 6 PM IST
            elif hour == 18 and now.minute == 0:
                header = "🤵 *EVENING MARKET BRIEFING*\n"
                header += f"📅 {now.strftime('%d %B %Y, %I:%M %p')}\n\n"
                
                overview = get_market_overview()
                bot.send_message(CHAT_ID, header + overview, parse_mode="Markdown")
                
                time.sleep(60)
                
                bot.send_message(CHAT_ID, "📰 *TOP EVENING NEWS*", parse_mode="Markdown")
                news = fetch_deep_intel("all")
                bot.send_message(CHAT_ID, news, parse_mode="Markdown", disable_web_page_preview=True)
        
        except Exception as e:
            print(f"Scheduled briefing error: {e}")
        
        time.sleep(60)  # Check every minute

# --- START SYSTEM ---
if __name__ == "__main__":
    print("\n" + "="*60)
    print("EXECUTIVE AI MARKET ADVISOR - ENHANCED VERSION")
    print("="*60)
    print(f"Time: {datetime.now()}")
    print(f"Bot Token: {'✓' if TOKEN else '✗ MISSING'}")
    print(f"Chat ID: {'✓' if CHAT_ID else '✗ MISSING'}")
    print(f"News API: {'✓' if NEWS_KEY else '✗ MISSING'}")
    print("="*60)
    
    # Check if running in GitHub Actions
    is_github = os.getenv("GITHUB_ACTIONS") == "true"
    
    if is_github:
        print("\nRunning scheduled briefing...")
        header = "🤵 *SCHEDULED UPDATE*\n"
        header += f"📅 {datetime.now().strftime('%d %B %Y, %I:%M %p')}\n\n"
        
        try:
            overview = get_market_overview()
            bot.send_message(CHAT_ID, header + overview, parse_mode="Markdown")
            
            time.sleep(2)
            
            bot.send_message(CHAT_ID, "📰 *LATEST NEWS*", parse_mode="Markdown")
            news = fetch_deep_intel("all")
            bot.send_message(CHAT_ID, news, parse_mode="Markdown", disable_web_page_preview=True)
            
            print("✅ Briefing sent!")
        except Exception as e:
            print(f"Error: {e}")
    
    else:
        print("\n🚀 Starting Market Monitor Thread...")
        threading.Thread(target=monitor_market, daemon=True).start()
        
        print("📅 Starting Scheduled Briefing Thread...")
        threading.Thread(target=scheduled_briefing, daemon=True).start()
        
        print("\n✅ AI Advisor System: ONLINE\n")
        print("Bot is now running and monitoring markets...")
        print("Press Ctrl+C to stop\n")
        
        bot.infinity_polling()
