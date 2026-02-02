import os, requests, telebot, time
import yfinance as yf
from datetime import datetime
import feedparser
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWS_KEY = os.getenv("NEWS_API_KEY")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = telebot.TeleBot(TOKEN)
DB_FILE = "sent_news.txt"
BREAKING_NEWS_FILE = "breaking_news.txt"

# Enhanced News Sources
NEWS_SOURCES = {
    'moneycontrol': [
        'https://www.moneycontrol.com/rss/latestnews.xml',
        'https://www.moneycontrol.com/rss/marketreports.xml',
        'https://www.moneycontrol.com/rss/business.xml'
    ],
    'mint': [
        'https://www.livemint.com/rss/markets',
        'https://www.livemint.com/rss/companies',
        'https://www.livemint.com/rss/money'
    ],
    'bloomberg': [
        'https://feeds.bloomberg.com/markets/news.rss',
        'https://feeds.bloomberg.com/india/news.rss',
        'https://feeds.bloomberg.com/technology/news.rss'
    ],
    'economic_times': [
        'https://economictimes.indiatimes.com/rssfeedstopstories.cms',
        'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms'
    ]
}

def get_market_status():
    """Complete Market Overview - Indian, Global, Commodities, Currencies, Indices"""
    status = "📊 *COMPLETE MARKET OVERVIEW*\n\n"
    
    try:
        # === INDIAN INDICES ===
        status += "🇮🇳 *INDIAN MARKETS*\n"
        
        indian_indices = {
            '^NSEI': 'NIFTY 50',
            '^BSESN': 'SENSEX',
            '^NSEBANK': 'BANK NIFTY'
        }
        
        for symbol, name in indian_indices.items():
            try:
                idx = yf.Ticker(symbol)
                hist = idx.history(period="5d")
                
                if len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    change = ((current - prev) / prev) * 100
                    
                    emoji = "🟢" if change >= 0 else "🔴"
                    status += f"{emoji} *{name}*: ₹{current:,.2f} ({change:+.2f}%)\n"
                elif len(hist) == 1:
                    current = hist['Close'].iloc[-1]
                    status += f"• *{name}*: ₹{current:,.2f}\n"
            except Exception as e:
                print(f"Error fetching {name}: {e}")
                status += f"• *{name}*: Updating...\n"
        
        status += "\n"
        
        # === GLOBAL INDICES ===
        status += "🌍 *GLOBAL MARKETS*\n"
        
        global_indices = {
            '^DJI': 'DOW JONES',
            '^GSPC': 'S&P 500',
            '^IXIC': 'NASDAQ',
            '^N225': 'NIKKEI 225',
            '000001.SS': 'SSE COMPOSITE',
            '^HSI': 'HANG SENG'
        }
        
        for symbol, name in global_indices.items():
            try:
                idx = yf.Ticker(symbol)
                hist = idx.history(period="5d")
                
                if len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    change = ((current - prev) / prev) * 100
                    
                    emoji = "🟢" if change >= 0 else "🔴"
                    status += f"{emoji} *{name}*: {current:,.2f} ({change:+.2f}%)\n"
                elif len(hist) == 1:
                    current = hist['Close'].iloc[-1]
                    status += f"• *{name}*: {current:,.2f}\n"
            except Exception as e:
                print(f"Error fetching {name}: {e}")
        
        status += "\n"
        
        # === CURRENCIES ===
        status += "💱 *CURRENCIES*\n"
        
        currencies = {
            'INR=X': 'USD/INR',
            'EURINR=X': 'EUR/INR',
            'GBPINR=X': 'GBP/INR'
        }
        
        for symbol, name in currencies.items():
            try:
                curr = yf.Ticker(symbol)
                hist = curr.history(period="5d")
                
                if len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    change = ((current - prev) / prev) * 100
                    
                    emoji = "🟢" if change >= 0 else "🔴"
                    status += f"{emoji} *{name}*: ₹{current:.2f} ({change:+.2f}%)\n"
                elif len(hist) == 1:
                    current = hist['Close'].iloc[-1]
                    status += f"• *{name}*: ₹{current:.2f}\n"
            except Exception as e:
                print(f"Error fetching {name}: {e}")
        
        status += "\n"
        
        # === COMMODITIES ===
        status += "🥇 *COMMODITIES*\n"
        
        commodities = {
            'GC=F': 'GOLD',
            'SI=F': 'SILVER',
            'HG=F': 'COPPER',
            'CL=F': 'CRUDE OIL'
        }
        
        for symbol, name in commodities.items():
            try:
                comm = yf.Ticker(symbol)
                hist = comm.history(period="5d")
                
                if len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    change = ((current - prev) / prev) * 100
                    
                    emoji = "🟢" if change >= 0 else "🔴"
                    status += f"{emoji} *{name}*: ${current:,.2f} ({change:+.2f}%)\n"
                elif len(hist) == 1:
                    current = hist['Close'].iloc[-1]
                    status += f"• *{name}*: ${current:,.2f}\n"
            except Exception as e:
                print(f"Error fetching {name}: {e}")
        
        status += "\n"
        
        # === INDEX PERFORMANCE ===
        status += "📈 *INDEX PERFORMANCE*\n"
        
        try:
            nifty = yf.Ticker("^NSEI")
            hist = nifty.history(period="5d")
            
            if len(hist) >= 5:
                week_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
                high = hist['High'].max()
                low = hist['Low'].min()
                
                status += f"• NIFTY 50 (5-day): {week_change:+.2f}%\n"
                status += f"  Week High: ₹{high:,.2f} | Low: ₹{low:,.2f}\n"
        except Exception as e:
            print(f"Error fetching performance: {e}")
            status += "• Performance data updating...\n"
        
    except Exception as e:
        print(f"Market status error: {e}")
        status += "\n⚠️ Some market data is currently updating. Please check again in a few minutes.\n"
    
    return status

def fetch_rss_headlines(feed_url, source_name):
    """Fetch headlines only from RSS feeds"""
    headlines = []
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:10]:
            title = entry.get('title', 'No Title')
            link = entry.get('link', '')
            
            if title and link:
                headlines.append({
                    'title': title,
                    'link': link,
                    'source': source_name
                })
    except Exception as e:
        print(f"Error fetching {source_name}: {e}")
    
    return headlines

def get_news_headlines():
    """Get 30-40 headlines from all sources"""
    if not os.path.exists(DB_FILE): 
        open(DB_FILE, 'w').close()
    
    with open(DB_FILE, "r") as f: 
        sent_ids = set(f.read().splitlines())

    all_headlines = []
    
    # === RSS FEEDS - MoneyControl, Mint, Bloomberg ===
    for source_type, feeds in NEWS_SOURCES.items():
        for feed_url in feeds:
            headlines = fetch_rss_headlines(feed_url, source_type.upper())
            all_headlines.extend(headlines)
            time.sleep(0.3)
    
    # === NewsAPI - FinTech, Derivatives, Financial News ===
    if NEWS_KEY:
        try:
            queries = [
                "fintech AND india",
                "derivatives OR futures OR options",
                "nifty OR sensex",
                "stock market india",
                "RBI OR SEBI",
                "financial technology",
                "gold silver commodities",
                "foreign exchange forex"
            ]
            
            for query in queries:
                url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&pageSize=5&language=en&apiKey={NEWS_KEY}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    for article in data.get('articles', []):
                        all_headlines.append({
                            'title': article.get('title', ''),
                            'link': article.get('url', ''),
                            'source': article.get('source', {}).get('name', 'NEWS')
                        })
                
                time.sleep(0.4)
        except Exception as e:
            print(f"NewsAPI error: {e}")
    
    # === FORMAT HEADLINES ONLY ===
    news_items = []
    count = 1
    
    for headline in all_headlines:
        url = headline['link']
        
        # Skip if already sent
        if url in sent_ids:
            continue
        
        # Skip if no title
        if not headline['title'] or len(headline['title']) < 10:
            continue
        
        # Stop at 40 headlines
        if len(news_items) >= 40:
            break
        
        source = headline['source'].upper()
        title = headline['title']
        
        # Simple headline format with numbering
        formatted = f"{count}. *{source}*: {title}\n🔗 [Read]({url})"
        
        news_items.append(formatted)
        count += 1
        
        # Mark as sent
        with open(DB_FILE, "a") as f: 
            f.write(url + "\n")
    
    return news_items

def check_breaking_news():
    """Check for breaking news and send immediately"""
    if not os.path.exists(BREAKING_NEWS_FILE):
        open(BREAKING_NEWS_FILE, 'w').close()
    
    with open(BREAKING_NEWS_FILE, "r") as f:
        sent_breaking = set(f.read().splitlines())
    
    breaking_keywords = [
        'breaking', 'urgent', 'alert', 'emergency', 
        'crash', 'surge', 'plunge', 'soar',
        'rbi announcement', 'sebi action', 'emergency meeting',
        'market halt', 'circuit breaker', 'trading suspended'
    ]
    
    breaking_news = []
    
    # Check NewsAPI for breaking news
    if NEWS_KEY:
        try:
            query = "india AND (stock market OR economy OR RBI OR SEBI)"
            url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&pageSize=10&language=en&apiKey={NEWS_KEY}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for article in data.get('articles', [])[:10]:
                    title_lower = article.get('title', '').lower()
                    url = article.get('url', '')
                    
                    # Check if breaking news
                    if any(keyword in title_lower for keyword in breaking_keywords):
                        if url not in sent_breaking:
                            breaking_news.append({
                                'title': article.get('title', ''),
                                'description': article.get('description', '')[:300],
                                'url': url,
                                'source': article.get('source', {}).get('name', 'NEWS')
                            })
                            
                            with open(BREAKING_NEWS_FILE, "a") as f:
                                f.write(url + "\n")
        except:
            pass
    
    return breaking_news

def send_full_briefing():
    """Send comprehensive twice-daily market briefing"""
    try:
        # Determine time of day
        current_hour = datetime.utcnow().hour
        
        if current_hour <= 6:
            time_label = "Morning"
            greeting = "Good Morning! Here is your market update."
        else:
            time_label = "Evening"
            greeting = "Good Evening! Here is your market closing summary."
        
        # 1. Header
        header = f"🤵 *{time_label.upper()} MARKET UPDATE*\n"
        header += f"📅 {datetime.now().strftime('%d %B %Y, %I:%M %p IST')}\n"
        header += f"\n{greeting}\n"
        header += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # 2. Market Status - Send as separate message to ensure it's visible
        print("Fetching market data...")
        market_data = get_market_status()
        full_market_msg = header + market_data
        
        print(f"Sending market message (length: {len(full_market_msg)} chars)")
        bot.send_message(CHAT_ID, full_market_msg, parse_mode="Markdown")
        print("Market message sent successfully!")
        time.sleep(3)
        
        # 3. News Headlines
        bot.send_message(CHAT_ID, "📰 *Getting latest headlines...*", parse_mode="Markdown")
        time.sleep(1)
        
        print("Fetching news headlines...")
        all_headlines = get_news_headlines()
        print(f"Found {len(all_headlines)} headlines")
        
        if not all_headlines:
            bot.send_message(CHAT_ID, "✅ No new headlines since last update.", parse_mode="Markdown")
        else:
            # Send headlines in chunks of 10
            for i in range(0, len(all_headlines), 10):
                chunk = "\n\n".join(all_headlines[i:i+10])
                chunk_header = f"📰 *NEWS HEADLINES ({i+1}-{min(i+10, len(all_headlines))})*\n\n"
                bot.send_message(CHAT_ID, chunk_header + chunk, parse_mode="Markdown", disable_web_page_preview=True)
                time.sleep(2)
            
            # 4. Summary
            summary = f"\n✅ *{time_label} Update Complete*\n"
            summary += f"📊 Markets: Indian, Global, Currencies, Commodities\n"
            summary += f"📰 Headlines: {len(all_headlines)} news articles\n"
            summary += f"🔔 Next update: {'Evening (6 PM IST)' if time_label == 'Morning' else 'Tomorrow Morning (9 AM IST)'}\n"
            summary += f"\n_Breaking news will be sent immediately if detected._"
            bot.send_message(CHAT_ID, summary, parse_mode="Markdown")
        
        print("Briefing completed successfully!")
        
    except Exception as e:
        error_msg = f"⚠️ Error in briefing: {str(e)[:200]}"
        print(error_msg)
        try:
            bot.send_message(CHAT_ID, error_msg, parse_mode="Markdown")
        except:
            pass

def send_breaking_news_alert():
    """Send immediate alert for breaking news"""
    print("Checking for breaking news...")
    breaking = check_breaking_news()
    
    if not breaking:
        print("No breaking news found.")
        return
    
    print(f"Found {len(breaking)} breaking news items")
    
    for news in breaking:
        try:
            alert = f"🚨 *BREAKING NEWS ALERT*\n\n"
            alert += f"📰 *{news['source']}*\n"
            alert += f"*{news['title']}*\n\n"
            alert += f"{news['description']}\n\n"
            alert += f"🔗 [Read Full Story]({news['url']})"
            
            bot.send_message(CHAT_ID, alert, parse_mode="Markdown", disable_web_page_preview=True)
            time.sleep(1)
        except Exception as e:
            print(f"Error sending breaking news: {e}")

@bot.message_handler(func=lambda m: True)
def on_message(message):
    """Handle user messages"""
    try:
        bot.reply_to(message, 
            "⚙️ *Getting your market update...*\n\n"
            "_This includes Indian markets, global indices, currencies, commodities, and 30-40 latest headlines._\n\n"
            "_Please wait 30 seconds..._", 
            parse_mode="Markdown")
        send_full_briefing()
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)[:100]}")

# === MAIN EXECUTION ===
if __name__ == "__main__":
    print(f"[{datetime.now()}] Starting Market Advisor Bot...")
    print(f"Bot Token: {'Present' if TOKEN else 'MISSING'}")
    print(f"Chat ID: {'Present' if CHAT_ID else 'MISSING'}")
    print(f"News API Key: {'Present' if NEWS_KEY else 'MISSING'}")
    
    # Check if running in GitHub Actions
    is_github_actions = os.getenv("GITHUB_ACTIONS") == "true"
    print(f"Running in GitHub Actions: {is_github_actions}")
    
    try:
        if is_github_actions:
            # In GitHub Actions - send scheduled update
            print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("Running scheduled update...")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
            
            send_full_briefing()
            
            print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("Checking for breaking news...")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
            
            send_breaking_news_alert()
            
            print(f"\n[{datetime.now()}] ✅ All tasks completed successfully!")
        else:
            # Running locally - start bot polling
            print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("Starting bot in polling mode...")
            print("Send any message to the bot to get update")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
            bot.infinity_polling()
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if CHAT_ID:
            try:
                bot.send_message(CHAT_ID, f"⚠️ Bot error: {str(e)[:200]}", parse_mode="Markdown")
            except:
                pass
