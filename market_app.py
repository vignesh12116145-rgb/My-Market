import os, requests, telebot, time, json, threading
from datetime import datetime, timedelta
import feedparser
from bs4 import BeautifulSoup
from telebot import types

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWS_KEY = os.getenv("NEWS_API_KEY")  # newsapi.org
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Optional Free API Keys (set as environment variables)
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")  # alphavantage.co - 500/day
FINNHUB_KEY = os.getenv("FINNHUB_KEY")  # finnhub.io - 60/min
COINGECKO_KEY = os.getenv("COINGECKO_KEY")  # coingecko.com - completely free
FRED_KEY = os.getenv("FRED_KEY")  # fred.stlouisfed.org - completely free

bot = telebot.TeleBot(TOKEN)
DB_FILE = "advisor_memory.json"
ALERT_SENT = {}

# --- PERSISTENCE ---
def load_mem():
    if not os.path.exists(DB_FILE):
        return {"seen_urls": [], "last_update": None, "user_alerts": {}}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {"seen_urls": [], "last_update": None, "user_alerts": {}}

def save_mem(url=None, user_id=None, alert_data=None):
    mem = load_mem()
    
    if url:
        if "seen_urls" not in mem:
            mem["seen_urls"] = []
        mem["seen_urls"].append(url)
        mem["seen_urls"] = mem["seen_urls"][-1000:]
    
    if user_id and alert_data:
        if "user_alerts" not in mem:
            mem["user_alerts"] = {}
        mem["user_alerts"][str(user_id)] = alert_data
    
    mem["last_update"] = datetime.now().isoformat()
    
    with open(DB_FILE, "w") as f:
        json.dump(mem, f)

# ===========================================
# STOCK MARKET DATA
# ===========================================

def get_nse_data():
    """NSE India - Free, official"""
    try:
        url = "https://www.nseindia.com/api/allIndices"
        headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            indices = {}
            
            for index in data.get('data', []):
                name = index.get('index', '')
                if name in ['NIFTY 50', 'NIFTY BANK', 'NIFTY IT', 'NIFTY PHARMA']:
                    indices[name] = {
                        'last': float(index.get('last', 0)),
                        'change': float(index.get('percentChange', 0)),
                        'open': float(index.get('open', 0))
                    }
            return indices
    except:
        pass
    return None

def get_alpha_vantage_stock(symbol):
    """Alpha Vantage - 500 calls/day free"""
    if not ALPHA_VANTAGE_KEY:
        return None
    
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            quote = data.get('Global Quote', {})
            
            return {
                'price': float(quote.get('05. price', 0)),
                'change': float(quote.get('09. change', 0)),
                'change_pct': float(quote.get('10. change percent', '0').replace('%', ''))
            }
    except:
        pass
    return None

def get_finnhub_stock(symbol):
    """Finnhub - 60 calls/min free"""
    if not FINNHUB_KEY:
        return None
    
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_KEY}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            current = data.get('c', 0)
            prev = data.get('pc', 0)
            
            if prev > 0:
                return {
                    'price': current,
                    'change': current - prev,
                    'change_pct': ((current - prev) / prev) * 100
                }
    except:
        pass
    return None

def get_yahoo_finance_data(symbol):
    """Yahoo Finance - Free, no key needed"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()['chart']['result'][0]['meta']
            current = data.get('regularMarketPrice', 0)
            prev = data.get('previousClose', current)
            
            if prev > 0:
                return {
                    'price': current,
                    'change': current - prev,
                    'change_pct': ((current - prev) / prev) * 100
                }
    except:
        pass
    return None

# ===========================================
# CRYPTOCURRENCY
# ===========================================

def get_crypto_prices():
    """CoinGecko - Completely free, no key needed"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,binancecoin,ripple,cardano&vs_currencies=usd,inr&include_24hr_change=true"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            crypto_data = {}
            for coin, values in data.items():
                crypto_data[coin] = {
                    'usd': values.get('usd', 0),
                    'inr': values.get('inr', 0),
                    'change_24h': values.get('usd_24h_change', 0)
                }
            
            return crypto_data
    except:
        pass
    return None

# ===========================================
# FOREX / CURRENCIES
# ===========================================

def get_currency_rates():
    """ExchangeRate-API - 1500 calls/month free"""
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            rates = response.json().get('rates', {})
            return {
                'USD/INR': rates.get('INR', 0),
                'EUR/INR': rates.get('INR', 0) / rates.get('EUR', 1) if rates.get('EUR') else 0,
                'GBP/INR': rates.get('INR', 0) / rates.get('GBP', 1) if rates.get('GBP') else 0,
                'JPY/INR': rates.get('INR', 0) / rates.get('JPY', 1) if rates.get('JPY') else 0
            }
    except:
        pass
    return None

def get_frankfurter_rates():
    """Frankfurter - Completely free, no key needed"""
    try:
        url = "https://api.frankfurter.app/latest?from=USD&to=INR,EUR,GBP"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('rates', {})
    except:
        pass
    return None

# ===========================================
# COMMODITIES
# ===========================================

def get_commodity_prices():
    """Multiple free sources"""
    commodities = {}
    
    # Yahoo Finance for commodities
    symbols = {'GC=F': 'GOLD', 'SI=F': 'SILVER', 'CL=F': 'CRUDE_OIL', 'HG=F': 'COPPER', 'NG=F': 'NATURAL_GAS'}
    
    for symbol, name in symbols.items():
        data = get_yahoo_finance_data(symbol)
        if data:
            commodities[name] = data
    
    return commodities if commodities else None

# ===========================================
# ECONOMIC DATA
# ===========================================

def get_fred_data(series_id):
    """FRED API - Completely free, unlimited"""
    if not FRED_KEY:
        return None
    
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_KEY}&file_type=json&limit=1&sort_order=desc"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            observations = data.get('observations', [])
            if observations:
                return {
                    'value': observations[0].get('value'),
                    'date': observations[0].get('date')
                }
    except:
        pass
    return None

def get_economic_indicators():
    """Get key economic indicators from FRED"""
    indicators = {}
    
    if FRED_KEY:
        # US indicators
        indicators['US_GDP'] = get_fred_data('GDP')
        indicators['US_UNEMPLOYMENT'] = get_fred_data('UNRATE')
        indicators['US_INFLATION'] = get_fred_data('CPIAUCSL')
        indicators['US_INTEREST_RATE'] = get_fred_data('FEDFUNDS')
    
    return indicators if indicators else None

# ===========================================
# NEWS
# ===========================================

def get_news(category="general", query=None):
    """NewsAPI - 100 requests/day free"""
    if not NEWS_KEY:
        return []
    
    seen = load_mem().get("seen_urls", [])
    news_items = []
    
    try:
        from_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        
        if query:
            url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&language=en&sortBy=publishedAt&pageSize=10&apiKey={NEWS_KEY}"
        else:
            url = f"https://newsapi.org/v2/top-headlines?category={category}&language=en&pageSize=10&apiKey={NEWS_KEY}"
        
        response = requests.get(url, timeout=8)
        
        if response.status_code == 200:
            articles = response.json().get('articles', [])
            
            for article in articles[:5]:
                article_url = article.get('url', '')
                
                if article_url in seen:
                    continue
                
                source = article.get('source', {}).get('name', 'NEWS')
                title = article.get('title', '')
                description = article.get('description', '')
                
                if not title or len(title) < 10:
                    continue
                
                if description:
                    desc_clean = BeautifulSoup(description, 'html.parser').get_text()[:300]
                else:
                    desc_clean = "Read full article for details."
                
                news_items.append({
                    'source': source,
                    'title': title,
                    'description': desc_clean,
                    'url': article_url
                })
                
                save_mem(url=article_url)
    except Exception as e:
        print(f"News API error: {e}")
    
    return news_items

def get_finnhub_news(category="general"):
    """Finnhub News - 60 calls/min free"""
    if not FINNHUB_KEY:
        return []
    
    try:
        url = f"https://finnhub.io/api/v1/news?category={category}&token={FINNHUB_KEY}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            return response.json()[:5]
    except:
        pass
    return []

# ===========================================
# COMPLETE MARKET OVERVIEW
# ===========================================

def get_complete_overview():
    """Get EVERYTHING - all markets, currencies, commodities, crypto"""
    overview = "📊 *COMPLETE FINANCIAL OVERVIEW*\n\n"
    
    bot.send_chat_action(CHAT_ID, "typing")
    
    # Indian Markets
    nse_data = get_nse_data()
    if nse_data:
        overview += "🇮🇳 *INDIAN MARKETS*\n"
        for name, data in nse_data.items():
            emoji = "🟢" if data['change'] >= 0 else "🔴"
            overview += f"{emoji} *{name}*: ₹{data['last']:,.2f} ({data['change']:+.2f}%)\n"
        overview += "\n"
    
    # Global Markets
    overview += "🌍 *GLOBAL MARKETS*\n"
    global_symbols = {'^DJI': 'DOW JONES', '^GSPC': 'S&P 500', '^IXIC': 'NASDAQ', '^N225': 'NIKKEI'}
    
    for symbol, name in global_symbols.items():
        data = get_yahoo_finance_data(symbol)
        if data:
            emoji = "🟢" if data['change_pct'] >= 0 else "🔴"
            overview += f"{emoji} *{name}*: {data['price']:,.2f} ({data['change_pct']:+.2f}%)\n"
    overview += "\n"
    
    # Cryptocurrencies
    crypto_data = get_crypto_prices()
    if crypto_data:
        overview += "₿ *CRYPTOCURRENCIES*\n"
        crypto_names = {'bitcoin': 'BTC', 'ethereum': 'ETH', 'binancecoin': 'BNB', 'ripple': 'XRP', 'cardano': 'ADA'}
        
        for coin, name in crypto_names.items():
            if coin in crypto_data:
                data = crypto_data[coin]
                emoji = "🟢" if data['change_24h'] >= 0 else "🔴"
                overview += f"{emoji} *{name}*: ${data['usd']:,.2f} (₹{data['inr']:,.0f}) {data['change_24h']:+.2f}%\n"
        overview += "\n"
    
    # Currencies
    currencies = get_currency_rates()
    if currencies:
        overview += "💱 *FOREX RATES*\n"
        for pair, rate in currencies.items():
            if rate > 0:
                overview += f"• *{pair}*: ₹{rate:.2f}\n"
        overview += "\n"
    
    # Commodities
    commodities = get_commodity_prices()
    if commodities:
        overview += "🥇 *COMMODITIES*\n"
        for name, data in commodities.items():
            emoji = "🟢" if data['change_pct'] >= 0 else "🔴"
            overview += f"{emoji} *{name}*: ${data['price']:,.2f} ({data['change_pct']:+.2f}%)\n"
        overview += "\n"
    
    # Economic Indicators
    if FRED_KEY:
        indicators = get_economic_indicators()
        if indicators:
            overview += "📈 *ECONOMIC INDICATORS*\n"
            if indicators.get('US_GDP'):
                overview += f"• US GDP: {indicators['US_GDP']['value']} ({indicators['US_GDP']['date']})\n"
            if indicators.get('US_UNEMPLOYMENT'):
                overview += f"• US Unemployment: {indicators['US_UNEMPLOYMENT']['value']}%\n"
            if indicators.get('US_INFLATION'):
                overview += f"• US Inflation (CPI): {indicators['US_INFLATION']['value']}\n"
            overview += "\n"
    
    overview += f"🕐 *Updated*: {datetime.now().strftime('%I:%M %p IST')}"
    
    return overview

# ===========================================
# ENHANCED INTERACTIVE MENU
# ===========================================

def get_main_menu():
    """Enhanced menu with ALL features"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Complete Overview", callback_data="overview"),
        types.InlineKeyboardButton("🇮🇳 Indian Markets", callback_data="indian"),
        types.InlineKeyboardButton("🌍 Global Markets", callback_data="global"),
        types.InlineKeyboardButton("₿ Cryptocurrencies", callback_data="crypto"),
        types.InlineKeyboardButton("💱 Forex Rates", callback_data="forex"),
        types.InlineKeyboardButton("🥇 Commodities", callback_data="commodities"),
        types.InlineKeyboardButton("📈 Economic Data", callback_data="economic"),
        types.InlineKeyboardButton("📰 Financial News", callback_data="news"),
        types.InlineKeyboardButton("🔍 Search Stock", callback_data="search"),
        types.InlineKeyboardButton("⚙️ Settings", callback_data="settings")
    )
    return markup

def get_reply_keyboard():
    """Persistent keyboard at bottom"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📊 Overview", "📰 News")
    markup.add("🇮🇳 Indian", "🌍 Global")
    markup.add("₿ Crypto", "💱 Forex")
    markup.add("🥇 Commodities", "📈 Economic")
    markup.add("🔄 Refresh", "❌ Hide")
    return markup

# ===========================================
# MARKET MONITOR (Background Thread)
# ===========================================

def monitor_markets():
    """Smart market monitoring with alerts"""
    global ALERT_SENT
    last_check = {}
    
    print("🔍 Market Monitor: ACTIVE")
    
    while True:
        try:
            now = datetime.now()
            hour = now.hour
            
            # Only during market hours (9-16 IST)
            if not (9 <= hour <= 16):
                time.sleep(300)
                continue
            
            bot.send_chat_action(CHAT_ID, "typing")
            
            indices = get_nse_data()
            
            if not indices:
                time.sleep(120)
                continue
            
            for name, data in indices.items():
                current = data['last']
                change_pct = data['change']
                point_change = current - data['open']
                
                alert_msg = None
                
                # Big moves
                if abs(change_pct) > 1.5:
                    if change_pct < -1.5:
                        alert_msg = f"🚨 *CRASH ALERT*\n\n*{name}* down *{abs(change_pct):.2f}%*!\n\nCurrent: ₹{current:,.2f}\nDrop: {point_change:,.0f} points"
                    else:
                        alert_msg = f"🚀 *SURGE ALERT*\n\n*{name}* up *{change_pct:.2f}%*!\n\nCurrent: ₹{current:,.2f}\nGain: +{point_change:,.0f} points"
                
                # Rapid change detection
                if name in last_check:
                    last_price = last_check[name]
                    quick_change = ((current - last_price) / last_price) * 100
                    
                    if abs(quick_change) > 0.5:
                        alert_msg = f"⚡ *RAPID MOVE*\n\n*{name}* moved *{quick_change:+.2f}%* in 2 minutes!\n\nCurrent: ₹{current:,.2f}"
                
                # Send alert with cooldown
                alert_key = f"{name}_{datetime.now().strftime('%Y%m%d%H%M')[:-1]}"
                
                if alert_msg and alert_key not in ALERT_SENT:
                    try:
                        bot.send_message(CHAT_ID, alert_msg, parse_mode="Markdown")
                        ALERT_SENT[alert_key] = True
                    except:
                        pass
                
                last_check[name] = current
            
            if len(ALERT_SENT) > 50:
                ALERT_SENT.clear()
        
        except Exception as e:
            print(f"Monitor error: {e}")
        
        time.sleep(120)

# ===========================================
# SCHEDULED BRIEFINGS
# ===========================================

def scheduled_updates():
    """Morning and evening briefings"""
    while True:
        try:
            now = datetime.now()
            hour = now.hour
            minute = now.minute
            
            # Morning: 9 AM
            if hour == 9 and minute == 0:
                bot.send_chat_action(CHAT_ID, "typing")
                header = "🤵 *MORNING BRIEFING*\n"
                header += f"📅 {now.strftime('%d %B %Y, %I:%M %p')}\n\n"
                
                overview = get_complete_overview()
                bot.send_message(CHAT_ID, header + overview, parse_mode="Markdown")
                
                time.sleep(60)
                
                news = get_news(query="india stock market OR economy")
                send_news_items(news, "Morning Top News")
            
            # Evening: 6 PM
            elif hour == 18 and minute == 0:
                bot.send_chat_action(CHAT_ID, "typing")
                header = "🤵 *EVENING BRIEFING*\n"
                header += f"📅 {now.strftime('%d %B %Y, %I:%M %p')}\n\n"
                
                overview = get_complete_overview()
                bot.send_message(CHAT_ID, header + overview, parse_mode="Markdown")
                
                time.sleep(60)
                
                news = get_news(query="finance OR business")
                send_news_items(news, "Evening Top News")
        
        except:
            pass
        
        time.sleep(60)

# ===========================================
# HELPER FUNCTIONS
# ===========================================

def send_news_items(news_items, title="News"):
    """Send formatted news"""
    if not news_items:
        bot.send_message(CHAT_ID, "No new news available")
        return
    
    bot.send_chat_action(CHAT_ID, "typing")
    
    msg = f"📰 *{title.upper()}*\n\n"
    
    for item in news_items:
        msg += f"📌 *{item['source'].upper()}*\n"
        msg += f"*{item['title']}*\n\n"
        msg += f"_{item['description']}_\n\n"
        msg += f"🔗 [Read]({item['url']})\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    try:
        bot.send_message(CHAT_ID, msg, parse_mode="Markdown", disable_web_page_preview=True)
    except:
        # Message too long, split
        for item in news_items:
            small_msg = f"📰 *{item['source']}*: {item['title']}\n🔗 [Read]({item['url']})"
            bot.send_message(CHAT_ID, small_msg, parse_mode="Markdown", disable_web_page_preview=True)
            time.sleep(0.5)

# ===========================================
# HANDLERS
# ===========================================

@bot.message_handler(commands=['start', 'menu', 'help'])
def start(message):
    """Welcome with full menu"""
    welcome = (
        "🤵 *ULTIMATE FINANCIAL ADVISOR BOT*\n\n"
        "✅ Indian & Global Markets\n"
        "✅ Cryptocurrencies\n"
        "✅ Forex & Commodities\n"
        "✅ Economic Indicators\n"
        "✅ Real-time News\n"
        "✅ Smart Alerts\n\n"
        "_Choose an option:_"
    )
    
    bot.send_message(
        message.chat.id,
        welcome,
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )
    
    # Also send reply keyboard
    bot.send_message(
        message.chat.id,
        "Quick access buttons below ⬇️",
        reply_markup=get_reply_keyboard()
    )

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    """Handle text and reply keyboard"""
    text = message.text.lower()
    
    bot.send_chat_action(message.chat.id, "typing")
    
    if any(word in text for word in ['overview', 'market', 'complete']):
        msg = bot.send_message(message.chat.id, "⏳ Loading complete overview...")
        overview = get_complete_overview()
        bot.edit_message_text(overview, message.chat.id, msg.message_id, parse_mode="Markdown")
    
    elif 'indian' in text or 'nifty' in text or 'sensex' in text:
        nse_data = get_nse_data()
        if nse_data:
            msg = "🇮🇳 *INDIAN MARKETS*\n\n"
            for name, data in nse_data.items():
                emoji = "🟢" if data['change'] >= 0 else "🔴"
                msg += f"{emoji} *{name}*: ₹{data['last']:,.2f} ({data['change']:+.2f}%)\n"
            bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    
    elif 'crypto' in text or 'bitcoin' in text:
        crypto = get_crypto_prices()
        if crypto:
            msg = "₿ *CRYPTOCURRENCIES*\n\n"
            for coin, data in crypto.items():
                emoji = "🟢" if data['change_24h'] >= 0 else "🔴"
                msg += f"{emoji} *{coin.upper()}*: ${data['usd']:,.2f} ({data['change_24h']:+.2f}%)\n"
            bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    
    elif 'news' in text or 'headlines' in text:
        news = get_news(query="finance OR business OR economy")
        send_news_items(news, "Latest Financial News")
    
    elif 'forex' in text or 'currency' in text:
        currencies = get_currency_rates()
        if currencies:
            msg = "💱 *FOREX RATES*\n\n"
            for pair, rate in currencies.items():
                msg += f"• *{pair}*: ₹{rate:.2f}\n"
            bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    
    elif 'commodit' in text or 'gold' in text or 'oil' in text:
        commodities = get_commodity_prices()
        if commodities:
            msg = "🥇 *COMMODITIES*\n\n"
            for name, data in commodities.items():
                emoji = "🟢" if data['change_pct'] >= 0 else "🔴"
                msg += f"{emoji} *{name}*: ${data['price']:,.2f} ({data['change_pct']:+.2f}%)\n"
            bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    
    elif 'refresh' in text or 'update' in text:
        bot.send_message(message.chat.id, "🔄 Refreshing...", reply_markup=get_main_menu())
    
    elif 'hide' in text:
        bot.send_message(message.chat.id, "✅ Keyboard hidden", reply_markup=types.ReplyKeyboardRemove())
    
    else:
        bot.send_message(message.chat.id, "👋 Use buttons or type: overview, news, crypto, forex", reply_markup=get_main_menu())

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    """Handle inline button clicks"""
    bot.answer_callback_query(call.id, "Processing...")
    bot.send_chat_action(call.message.chat.id, "typing")
    
    cid = call.message.chat.id
    
    try:
        if call.data == "overview":
            msg = bot.send_message(cid, "⏳ Loading...")
            overview = get_complete_overview()
            bot.edit_message_text(overview, cid, msg.message_id, parse_mode="Markdown")
        
        elif call.data == "indian":
            nse_data = get_nse_data()
            if nse_data:
                msg = "🇮🇳 *INDIAN MARKETS*\n\n"
                for name, data in nse_data.items():
                    emoji = "🟢" if data['change'] >= 0 else "🔴"
                    msg += f"{emoji} *{name}*: ₹{data['last']:,.2f} ({data['change']:+.2f}%)\n"
                bot.send_message(cid, msg, parse_mode="Markdown")
        
        elif call.data == "crypto":
            crypto = get_crypto_prices()
            if crypto:
                msg = "₿ *CRYPTOCURRENCIES*\n\n"
                crypto_names = {'bitcoin': 'BTC', 'ethereum': 'ETH', 'binancecoin': 'BNB'}
                for coin, name in crypto_names.items():
                    if coin in crypto:
                        data = crypto[coin]
                        emoji = "🟢" if data['change_24h'] >= 0 else "🔴"
                        msg += f"{emoji} *{name}*: ${data['usd']:,.2f} (₹{data['inr']:,.0f}) {data['change_24h']:+.2f}%\n"
                bot.send_message(cid, msg, parse_mode="Markdown")
        
        elif call.data == "news":
            news = get_news(query="finance OR business")
            send_news_items(news, "Latest Financial News")
        
        elif call.data == "forex":
            currencies = get_currency_rates()
            if currencies:
                msg = "💱 *FOREX RATES*\n\n"
                for pair, rate in currencies.items():
                    if rate > 0:
                        msg += f"• *{pair}*: ₹{rate:.2f}\n"
                bot.send_message(cid, msg, parse_mode="Markdown")
        
        elif call.data == "commodities":
            commodities = get_commodity_prices()
            if commodities:
                msg = "🥇 *COMMODITIES*\n\n"
                for name, data in commodities.items():
                    emoji = "🟢" if data['change_pct'] >= 0 else "🔴"
                    msg += f"{emoji} *{name}*: ${data['price']:,.2f} ({data['change_pct']:+.2f}%)\n"
                bot.send_message(cid, msg, parse_mode="Markdown")
    
    except Exception as e:
        bot.send_message(cid, f"⚠️ Error: {str(e)[:100]}")

# ===========================================
# MAIN
# ===========================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("ULTIMATE FINANCIAL ADVISOR BOT")
    print("="*70)
    print(f"Time: {datetime.now()}")
    print(f"Bot Token: {'✓' if TOKEN else '✗'}")
    print(f"News API: {'✓' if NEWS_KEY else '✗'}")
    print(f"Alpha Vantage: {'✓' if ALPHA_VANTAGE_KEY else '○ Optional'}")
    print(f"Finnhub: {'✓' if FINNHUB_KEY else '○ Optional'}")
    print(f"FRED: {'✓' if FRED_KEY else '○ Optional'}")
    print("="*70 + "\n")
    
    # Set bot commands
    commands = [
        types.BotCommand("start", "Start bot and show main menu"),
        types.BotCommand("menu", "Show interactive menu"),
        types.BotCommand("help", "Get help and commands")
    ]
    bot.set_my_commands(commands)
    
    is_github = os.getenv("GITHUB_ACTIONS") == "true"
    
    if is_github:
        print("Running scheduled briefing...")
        try:
            overview = get_complete_overview()
            bot.send_message(CHAT_ID, f"📊 *SCHEDULED UPDATE*\n\n{overview}", parse_mode="Markdown")
            
            news = get_news(query="finance OR business")
            send_news_items(news, "Latest News")
            
            print("✅ Done!")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("🚀 Starting background threads...")
        threading.Thread(target=monitor_markets, daemon=True).start()
        threading.Thread(target=scheduled_updates, daemon=True).start()
        
        print("\n✅ Bot ONLINE! All systems running.\n")
        bot.infinity_polling()
