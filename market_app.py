import os, requests, telebot, time
from datetime import datetime, timedelta
import feedparser
from bs4 import BeautifulSoup
import json

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWS_KEY = os.getenv("NEWS_API_KEY")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telebot.TeleBot(TOKEN)
DB_FILE = "sent_news.txt"
BREAKING_NEWS_FILE = "breaking_news.txt"

# News Sources
NEWS_SOURCES = {
    'mint': ['https://www.livemint.com/rss/markets'],
    'bloomberg': ['https://feeds.bloomberg.com/markets/news.rss'],
    'economic_times': ['https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms'],
}

def get_indian_market_data():
    """Get REAL Indian market data from NSE India API"""
    market_text = "📊 *INDIAN MARKETS*\n\n"
    
    try:
        # NSE India API - Free, no authentication needed
        url = "https://www.nseindia.com/api/allIndices"
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # Find NIFTY 50
            for index in data.get('data', []):
                if index.get('index') == 'NIFTY 50':
                    last = float(index.get('last', 0))
                    change = float(index.get('percentChange', 0))
                    emoji = "🟢" if change >= 0 else "🔴"
                    market_text += f"{emoji} *NIFTY 50*: ₹{last:,.2f} ({change:+.2f}%)\n"
                    break
            
            # Find NIFTY BANK
            for index in data.get('data', []):
                if index.get('index') == 'NIFTY BANK':
                    last = float(index.get('last', 0))
                    change = float(index.get('percentChange', 0))
                    emoji = "🟢" if change >= 0 else "🔴"
                    market_text += f"{emoji} *BANK NIFTY*: ₹{last:,.2f} ({change:+.2f}%)\n"
                    break
        
        else:
            market_text += "_NSE data temporarily unavailable_\n"
    
    except Exception as e:
        print(f"NSE API Error: {e}")
        market_text += "_Market data updating..._\n"
    
    # Add BSE SENSEX
    try:
        # BSE API
        bse_url = "https://api.bseindia.com/BseIndiaAPI/api/DefaultData/w"
        response = requests.get(bse_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            for item in data.get('Table', []):
                if 'SENSEX' in item.get('IndxNm', ''):
                    value = float(item.get('CurrRate', 0))
                    change = float(item.get('PerChange', 0))
                    emoji = "🟢" if change >= 0 else "🔴"
                    market_text += f"{emoji} *SENSEX*: ₹{value:,.2f} ({change:+.2f}%)\n"
                    break
    except:
        pass
    
    market_text += "\n"
    return market_text

def get_global_market_data():
    """Get global market data from Yahoo Finance API"""
    global_text = "🌍 *GLOBAL MARKETS*\n\n"
    
    symbols = {
        '^DJI': 'DOW JONES',
        '^GSPC': 'S&P 500',
        '^IXIC': 'NASDAQ',
        '^N225': 'NIKKEI'
    }
    
    for symbol, name in symbols.items():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                result = data['chart']['result'][0]
                meta = result['meta']
                
                current = meta.get('regularMarketPrice', 0)
                prev_close = meta.get('previousClose', current)
                
                if prev_close > 0:
                    change_pct = ((current - prev_close) / prev_close) * 100
                    emoji = "🟢" if change_pct >= 0 else "🔴"
                    global_text += f"{emoji} *{name}*: {current:,.2f} ({change_pct:+.2f}%)\n"
        except:
            continue
    
    global_text += "\n"
    return global_text

def get_currency_data():
    """Get currency rates"""
    currency_text = "💱 *CURRENCIES*\n\n"
    
    try:
        # Free currency API
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            rates = data.get('rates', {})
            
            inr = rates.get('INR', 0)
            if inr > 0:
                currency_text += f"• *USD/INR*: ₹{inr:.2f}\n"
            
            eur = rates.get('EUR', 0)
            if eur > 0:
                eur_inr = inr / eur
                currency_text += f"• *EUR/INR*: ₹{eur_inr:.2f}\n"
    except:
        currency_text += "_Currency data updating..._\n"
    
    currency_text += "\n"
    return currency_text

def get_commodity_data():
    """Get commodity prices"""
    commodity_text = "🥇 *COMMODITIES*\n\n"
    
    commodities = {
        'GC=F': 'GOLD',
        'SI=F': 'SILVER',
        'CL=F': 'CRUDE OIL'
    }
    
    for symbol, name in commodities.items():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                result = data['chart']['result'][0]
                meta = result['meta']
                
                current = meta.get('regularMarketPrice', 0)
                prev_close = meta.get('previousClose', current)
                
                if prev_close > 0:
                    change_pct = ((current - prev_close) / prev_close) * 100
                    emoji = "🟢" if change_pct >= 0 else "🔴"
                    commodity_text += f"{emoji} *{name}*: ${current:,.2f} ({change_pct:+.2f}%)\n"
        except:
            continue
    
    commodity_text += "\n"
    return commodity_text

def get_complete_market_overview():
    """Get complete market overview - FAST"""
    print("Fetching market data...")
    
    overview = "📊 *COMPLETE MARKET OVERVIEW*\n\n"
    
    # Get all data concurrently (fast)
    indian = get_indian_market_data()
    global_data = get_global_market_data()
    currencies = get_currency_data()
    commodities = get_commodity_data()
    
    overview += indian + global_data + currencies + commodities
    
    overview += f"🕐 Updated: {datetime.now().strftime('%I:%M %p IST')}\n"
    
    return overview

def fetch_rss_headlines(feed_url, source_name, limit=10):
    """Fetch headlines - FAST"""
    headlines = []
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:limit]:
            title = entry.get('title', '')
            link = entry.get('link', '')
            
            if title and link and len(title) > 10:
                headlines.append({
                    'title': title,
                    'link': link,
                    'source': source_name
                })
    except Exception as e:
        print(f"RSS Error {source_name}: {e}")
    
    return headlines

def get_news_headlines(limit=30):
    """Get news headlines - FAST"""
    if not os.path.exists(DB_FILE):
        open(DB_FILE, 'w').close()
    
    with open(DB_FILE, "r") as f:
        sent_ids = set(f.read().splitlines())
    
    all_headlines = []
    
    # RSS - Fast
    print("Fetching news...")
    for source, feeds in NEWS_SOURCES.items():
        for feed_url in feeds:
            headlines = fetch_rss_headlines(feed_url, source.upper(), limit=15)
            all_headlines.extend(headlines)
    
    # NewsAPI - Last 2 days only
    if NEWS_KEY:
        try:
            from_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
            queries = ["india stock market", "nifty sensex", "tariff trade", "RBI SEBI"]
            
            for query in queries:
                url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&pageSize=5&language=en&apiKey={NEWS_KEY}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    for article in data.get('articles', []):
                        all_headlines.append({
                            'title': article.get('title', ''),
                            'link': article.get('url', ''),
                            'source': article.get('source', {}).get('name', 'NEWS')
                        })
        except:
            pass
    
    # Format
    news_items = []
    count = 1
    
    for headline in all_headlines:
        url = headline['link']
        
        if url in sent_ids or len(news_items) >= limit:
            continue
        
        if not headline['title']:
            continue
        
        source = headline['source'].upper()
        title = headline['title']
        
        formatted = f"{count}. *{source}*: {title}\n🔗 [Read]({url})"
        news_items.append(formatted)
        count += 1
        
        with open(DB_FILE, "a") as f:
            f.write(url + "\n")
    
    return news_items

def check_breaking_news():
    """Check breaking news - IMPORTANT news like tariffs"""
    if not os.path.exists(BREAKING_NEWS_FILE):
        open(BREAKING_NEWS_FILE, 'w').close()
    
    with open(BREAKING_NEWS_FILE, "r") as f:
        sent_breaking = set(f.read().splitlines())
    
    keywords = [
        'breaking', 'urgent', 'tariff', 'trade war', 'us india',
        'rbi emergency', 'sebi action', 'crash', 'surge', 'ban',
        'sanctions', 'policy change', 'trump', 'default'
    ]
    
    breaking = []
    
    # Check NewsAPI
    if NEWS_KEY:
        try:
            queries = ["india tariff", "us india trade", "breaking india economy"]
            
            for query in queries:
                url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&pageSize=5&language=en&apiKey={NEWS_KEY}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    for article in data.get('articles', []):
                        title_lower = article.get('title', '').lower()
                        article_url = article.get('url', '')
                        
                        if any(kw in title_lower for kw in keywords):
                            if article_url not in sent_breaking:
                                breaking.append({
                                    'title': article.get('title', ''),
                                    'description': article.get('description', '')[:250],
                                    'url': article_url,
                                    'source': article.get('source', {}).get('name', 'NEWS')
                                })
                                
                                with open(BREAKING_NEWS_FILE, "a") as f:
                                    f.write(article_url + "\n")
        except:
            pass
    
    return breaking

def send_full_briefing():
    """Send complete briefing - FAST"""
    try:
        current_hour = datetime.utcnow().hour
        time_label = "MORNING" if current_hour <= 6 else "EVENING"
        
        header = f"🤵 *{time_label} UPDATE*\n"
        header += f"📅 {datetime.now().strftime('%d %B %Y, %I:%M %p')}\n"
        header += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Market data
        print("Getting market overview...")
        market_overview = get_complete_market_overview()
        
        bot.send_message(CHAT_ID, header + market_overview, parse_mode="Markdown")
        time.sleep(2)
        
        # News
        print("Getting news...")
        bot.send_message(CHAT_ID, "📰 *Getting headlines...*", parse_mode="Markdown")
        
        headlines = get_news_headlines(30)
        
        if headlines:
            for i in range(0, len(headlines), 10):
                chunk = "\n\n".join(headlines[i:i+10])
                bot.send_message(CHAT_ID, f"📰 *NEWS ({i+1}-{min(i+10, len(headlines))})*\n\n{chunk}", 
                               parse_mode="Markdown", disable_web_page_preview=True)
                time.sleep(1)
            
            bot.send_message(CHAT_ID, f"✅ *Update Complete*\n📰 {len(headlines)} headlines", parse_mode="Markdown")
        else:
            bot.send_message(CHAT_ID, "✅ No new headlines")
        
        print("✅ Done!")
        
    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(CHAT_ID, f"⚠️ Error: {str(e)[:150]}")

def send_breaking_news_alert():
    """Send breaking news alerts"""
    print("Checking breaking news...")
    breaking = check_breaking_news()
    
    if breaking:
        print(f"Found {len(breaking)} breaking news!")
        for news in breaking:
            try:
                alert = f"🚨 *BREAKING*\n\n*{news['source']}*\n{news['title']}\n\n{news['description']}\n\n🔗 [Read]({news['url']})"
                bot.send_message(CHAT_ID, alert, parse_mode="Markdown", disable_web_page_preview=True)
                time.sleep(1)
            except:
                pass

@bot.message_handler(func=lambda m: True)
def on_message(message):
    """ALWAYS respond to user messages"""
    try:
        text = message.text.lower()
        
        # Immediate response
        if any(word in text for word in ['news', 'headlines', 'update', 'latest']):
            bot.reply_to(message, "📰 Getting headlines...")
            headlines = get_news_headlines(20)
            
            if headlines:
                for i in range(0, len(headlines), 10):
                    chunk = "\n\n".join(headlines[i:i+10])
                    bot.send_message(message.chat.id, f"📰 *NEWS*\n\n{chunk}", 
                                   parse_mode="Markdown", disable_web_page_preview=True)
                    time.sleep(1)
            else:
                bot.send_message(message.chat.id, "No new headlines")
        
        elif any(word in text for word in ['market', 'nifty', 'sensex', 'stock']):
            bot.reply_to(message, "📊 Getting market data...")
            market = get_complete_market_overview()
            bot.send_message(message.chat.id, market, parse_mode="Markdown")
        
        elif any(word in text for word in ['breaking', 'urgent', 'alert']):
            bot.reply_to(message, "🔍 Checking breaking news...")
            breaking = check_breaking_news()
            
            if breaking:
                for news in breaking[:3]:
                    alert = f"🚨 *{news['source']}*: {news['title']}\n🔗 [Read]({news['url']})"
                    bot.send_message(message.chat.id, alert, parse_mode="Markdown", disable_web_page_preview=True)
            else:
                bot.send_message(message.chat.id, "No breaking news")
        
        elif any(word in text for word in ['help', 'hi', 'hello', 'start']):
            help_text = """
🤵 *MARKET ADVISOR BOT*

*Commands:*
• `news` - Latest headlines
• `market` - Market overview
• `breaking` - Breaking news
• `help` - This message

*Auto Updates:*
• 9 AM IST (Morning)
• 6 PM IST (Evening)
            """
            bot.reply_to(message, help_text, parse_mode="Markdown")
        
        else:
            # Default response - ALWAYS respond
            bot.reply_to(message, "👋 Type: `news`, `market`, `breaking`, or `help`", parse_mode="Markdown")
    
    except Exception as e:
        print(f"Message error: {e}")
        # ALWAYS respond even on error
        bot.reply_to(message, "Type `help` for commands")

# === MAIN ===
if __name__ == "__main__":
    print("\n" + "="*50)
    print("MARKET ADVISOR BOT - FINAL VERSION")
    print("="*50)
    print(f"Time: {datetime.now()}")
    print(f"Bot: {'✓' if TOKEN else '✗'}")
    print(f"Chat: {'✓' if CHAT_ID else '✗'}")
    print(f"News API: {'✓' if NEWS_KEY else '✗'}")
    print("="*50 + "\n")
    
    is_github = os.getenv("GITHUB_ACTIONS") == "true"
    
    try:
        if is_github:
            print("Running scheduled update...")
            send_full_briefing()
            print("\nChecking breaking news...")
            send_breaking_news_alert()
            print("\n✅ DONE\n")
        else:
            print("Bot is LIVE! Send any message.\n")
            bot.infinity_polling()
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        if CHAT_ID:
            try:
                bot.send_message(CHAT_ID, f"⚠️ Error: {str(e)[:150]}")
            except:
                pass
