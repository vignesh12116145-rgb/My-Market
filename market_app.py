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

# Current News Sources
NEWS_SOURCES = {
    'mint': [
        'https://www.livemint.com/rss/markets',
        'https://www.livemint.com/rss/companies',
        'https://www.livemint.com/rss/money',
        'https://www.livemint.com/rss/news'
    ],
    'bloomberg': [
        'https://feeds.bloomberg.com/markets/news.rss',
        'https://feeds.bloomberg.com/india/news.rss',
        'https://feeds.bloomberg.com/technology/news.rss'
    ],
    'economic_times': [
        'https://economictimes.indiatimes.com/rssfeedstopstories.cms',
        'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms'
    ],
    'reuters': [
        'https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best'
    ]
}

# Bot command triggers
COMMAND_TRIGGERS = {
    'market': ['market', 'markets', 'stock', 'nifty', 'sensex'],
    'news': ['news', 'headlines', 'update', 'latest'],
    'help': ['help', 'commands', 'start', 'hi', 'hello'],
    'breaking': ['breaking', 'alert', 'urgent']
}

def get_market_data_coinmarketcap():
    """Alternative: Get market sentiment from CoinMarketCap (free, no API key needed)"""
    try:
        # This is a simple web scraping approach
        status = "📊 *MARKET STATUS*\n\n"
        status += "_Note: Live market data from Yahoo Finance is currently unavailable._\n"
        status += "_News updates are still working normally._\n\n"
        
        # Get basic info from news headlines instead
        status += "For real-time market prices:\n"
        status += "• Visit: https://www.google.com/finance\n"
        status += "• NSE India: https://www.nseindia.com\n"
        status += "• BSE: https://www.bseindia.com\n"
        
        return status
    except:
        return "📊 *MARKET STATUS*\n\n_Market data temporarily unavailable. Check news for updates._\n"

def get_market_summary_from_news():
    """Extract market info from news headlines"""
    try:
        summary = "📊 *MARKET SUMMARY FROM NEWS*\n\n"
        
        # Get latest market-related headlines
        market_headlines = []
        
        for source_type, feeds in NEWS_SOURCES.items():
            for feed_url in feeds[:1]:  # Just first feed from each source
                try:
                    feed = feedparser.parse(feed_url)
                    for entry in feed.entries[:5]:
                        title = entry.get('title', '')
                        if any(word in title.lower() for word in ['nifty', 'sensex', 'market', 'stock', 'index']):
                            market_headlines.append(f"• {title}")
                            if len(market_headlines) >= 5:
                                break
                except:
                    continue
                
                if len(market_headlines) >= 5:
                    break
            
            if len(market_headlines) >= 5:
                break
        
        if market_headlines:
            summary += "\n".join(market_headlines[:5])
        else:
            summary += "No recent market updates in headlines.\n"
        
        summary += "\n\n_For live prices, visit Google Finance or NSE India._"
        
        return summary
    except:
        return "📊 *MARKET INFO*\n\n_Check news headlines for market updates._\n"

def fetch_rss_headlines(feed_url, source_name, limit=15):
    """Fetch headlines from RSS feeds"""
    headlines = []
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:limit]:
            title = entry.get('title', 'No Title')
            link = entry.get('link', '')
            published = entry.get('published', '')
            
            if title and link:
                headlines.append({
                    'title': title,
                    'link': link,
                    'source': source_name,
                    'published': published
                })
                    
    except Exception as e:
        print(f"Error fetching {source_name}: {e}")
    
    return headlines

def get_news_headlines(limit=40):
    """Get current headlines"""
    if not os.path.exists(DB_FILE): 
        open(DB_FILE, 'w').close()
    
    with open(DB_FILE, "r") as f: 
        sent_ids = set(f.read().splitlines())

    all_headlines = []
    
    # === RSS FEEDS ===
    print("Fetching current news...")
    for source_type, feeds in NEWS_SOURCES.items():
        for feed_url in feeds:
            headlines = fetch_rss_headlines(feed_url, source_type.upper())
            all_headlines.extend(headlines)
            time.sleep(0.3)
    
    print(f"Got {len(all_headlines)} headlines from RSS")
    
    # === NewsAPI - Last 3 days ===
    if NEWS_KEY:
        try:
            print("Fetching NewsAPI...")
            from_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
            
            queries = [
                "india stock market",
                "nifty sensex",
                "RBI SEBI",
                "tariff trade india",
                "rupee dollar",
                "indian economy"
            ]
            
            for query in queries:
                url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&sortBy=publishedAt&pageSize=5&language=en&apiKey={NEWS_KEY}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    for article in data.get('articles', []):
                        all_headlines.append({
                            'title': article.get('title', ''),
                            'link': article.get('url', ''),
                            'source': article.get('source', {}).get('name', 'NEWS'),
                            'published': article.get('publishedAt', '')
                        })
                
                time.sleep(0.4)
            
            print(f"Total after NewsAPI: {len(all_headlines)}")
        except Exception as e:
            print(f"NewsAPI error: {e}")
    
    # === FORMAT HEADLINES ===
    news_items = []
    count = 1
    
    for headline in all_headlines:
        url = headline['link']
        
        if url in sent_ids:
            continue
        
        if not headline['title'] or len(headline['title']) < 10:
            continue
        
        if len(news_items) >= limit:
            break
        
        source = headline['source'].upper()
        title = headline['title']
        
        formatted = f"{count}. *{source}*: {title}\n🔗 [Read]({url})"
        
        news_items.append(formatted)
        count += 1
        
        with open(DB_FILE, "a") as f: 
            f.write(url + "\n")
    
    print(f"Formatted {len(news_items)} unique headlines")
    return news_items

def check_breaking_news():
    """Improved breaking news detection - catches important news like tariffs"""
    if not os.path.exists(BREAKING_NEWS_FILE):
        open(BREAKING_NEWS_FILE, 'w').close()
    
    with open(BREAKING_NEWS_FILE, "r") as f:
        sent_breaking = set(f.read().splitlines())
    
    # Expanded keywords to catch more important news
    breaking_keywords = [
        'breaking', 'urgent', 'alert', 'emergency',
        'crash', 'surge', 'plunge', 'soar', 'plummet',
        'rbi announcement', 'sebi action', 'emergency meeting',
        'market halt', 'circuit breaker', 'trading suspended',
        'tariff', 'trade war', 'trade deal', 'sanctions',
        'us india', 'trump', 'policy change',
        'ban', 'restriction', 'regulation',
        'default', 'bankruptcy', 'collapse'
    ]
    
    breaking_news = []
    
    # Check RSS feeds for breaking news
    print("Checking RSS for breaking news...")
    for source_type, feeds in NEWS_SOURCES.items():
        for feed_url in feeds[:1]:  # Check first feed from each source
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:10]:
                    title = entry.get('title', '')
                    title_lower = title.lower()
                    link = entry.get('link', '')
                    
                    if any(keyword in title_lower for keyword in breaking_keywords):
                        if link not in sent_breaking:
                            breaking_news.append({
                                'title': title,
                                'description': entry.get('summary', title)[:300],
                                'url': link,
                                'source': source_type.upper()
                            })
                            
                            with open(BREAKING_NEWS_FILE, "a") as f:
                                f.write(link + "\n")
            except:
                continue
    
    # Check NewsAPI
    if NEWS_KEY:
        try:
            from_date = datetime.now().strftime('%Y-%m-%d')
            
            # Search for important keywords
            important_queries = [
                "india tariff",
                "us india trade",
                "RBI emergency",
                "market crash india",
                "breaking news india economy"
            ]
            
            for query in important_queries:
                url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&sortBy=publishedAt&pageSize=5&language=en&apiKey={NEWS_KEY}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    for article in data.get('articles', []):
                        title_lower = article.get('title', '').lower()
                        url = article.get('url', '')
                        
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
                
                time.sleep(0.3)
        except:
            pass
    
    return breaking_news

def send_full_briefing():
    """Send comprehensive briefing"""
    try:
        current_hour = datetime.utcnow().hour
        
        if current_hour <= 6:
            time_label = "Morning"
            greeting = "Good Morning! Here is your update."
        else:
            time_label = "Evening"
            greeting = "Good Evening! Here is your update."
        
        # Header
        header = f"🤵 *{time_label.upper()} UPDATE*\n"
        header += f"📅 {datetime.now().strftime('%d %B %Y, %I:%M %p IST')}\n"
        header += f"\n{greeting}\n"
        header += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Market summary from news
        print("Getting market summary from news...")
        market_summary = get_market_summary_from_news()
        
        bot.send_message(CHAT_ID, header + market_summary, parse_mode="Markdown")
        time.sleep(2)
        
        # News Headlines
        bot.send_message(CHAT_ID, "📰 *Getting latest headlines...*", parse_mode="Markdown")
        time.sleep(1)
        
        print("Fetching news...")
        all_headlines = get_news_headlines(40)
        
        if not all_headlines:
            bot.send_message(CHAT_ID, "✅ No new headlines since last update.", parse_mode="Markdown")
        else:
            print(f"Sending {len(all_headlines)} headlines...")
            
            for i in range(0, len(all_headlines), 10):
                chunk = "\n\n".join(all_headlines[i:i+10])
                chunk_header = f"📰 *NEWS HEADLINES ({i+1}-{min(i+10, len(all_headlines))})*\n\n"
                bot.send_message(CHAT_ID, chunk_header + chunk, parse_mode="Markdown", disable_web_page_preview=True)
                time.sleep(2)
            
            summary = f"\n✅ *Update Complete*\n"
            summary += f"📰 Headlines: {len(all_headlines)} articles\n"
            summary += f"🔔 Next update: {'Evening (6 PM IST)' if time_label == 'Morning' else 'Tomorrow Morning (9 AM IST)'}\n"
            bot.send_message(CHAT_ID, summary, parse_mode="Markdown")
        
        print("✅ Briefing completed!")
        
    except Exception as e:
        print(f"Error: {e}")
        try:
            bot.send_message(CHAT_ID, f"⚠️ Error: {str(e)[:200]}", parse_mode="Markdown")
        except:
            pass

def send_breaking_news_alert():
    """Send breaking news alerts"""
    print("Checking for breaking news...")
    
    breaking = check_breaking_news()
    
    if not breaking:
        print("No breaking news found.")
        return
    
    print(f"Found {len(breaking)} breaking news items!")
    
    for news in breaking:
        try:
            alert = f"🚨 *BREAKING NEWS*\n\n"
            alert += f"📰 *{news['source']}*\n"
            alert += f"*{news['title']}*\n\n"
            
            # Clean description
            desc = BeautifulSoup(news['description'], 'html.parser').get_text()
            alert += f"{desc}\n\n"
            alert += f"🔗 [Read Full Story]({news['url']})"
            
            bot.send_message(CHAT_ID, alert, parse_mode="Markdown", disable_web_page_preview=True)
            print(f"✓ Sent: {news['title'][:50]}...")
            time.sleep(1)
        except Exception as e:
            print(f"Error sending alert: {e}")

def detect_command(text):
    """Detect which command user wants"""
    text_lower = text.lower()
    
    for command, triggers in COMMAND_TRIGGERS.items():
        if any(trigger in text_lower for trigger in triggers):
            return command
    
    return None

@bot.message_handler(func=lambda m: True)
def on_message(message):
    """Handle user messages with command triggers"""
    try:
        text = message.text
        command = detect_command(text)
        
        if command == 'help':
            help_text = """
🤵 *MARKET ADVISOR BOT*

*Available Commands:*

📰 *News Commands:*
• `news` or `headlines` or `update` - Get latest news
• `latest` - Same as news

📊 *Market Commands:*
• `market` or `markets` - Market summary from news
• `nifty` or `sensex` or `stock` - Market info

🆘 *Other:*
• `help` or `hi` or `hello` - Show this help
• `breaking` - Check breaking news

*Examples:*
• Just type: `news`
• Or: `give me latest headlines`
• Or: `what's the market doing`
• Or: `hi`

_Bot sends automatic updates twice daily at 9 AM and 6 PM IST._
            """
            bot.reply_to(message, help_text, parse_mode="Markdown")
        
        elif command == 'market':
            bot.reply_to(message, "📊 Getting market info...", parse_mode="Markdown")
            market_summary = get_market_summary_from_news()
            bot.send_message(message.chat.id, market_summary, parse_mode="Markdown")
        
        elif command == 'news':
            bot.reply_to(message, "📰 Fetching latest headlines...", parse_mode="Markdown")
            headlines = get_news_headlines(20)
            
            if headlines:
                for i in range(0, len(headlines), 10):
                    chunk = "\n\n".join(headlines[i:i+10])
                    chunk_header = f"📰 *LATEST HEADLINES ({i+1}-{min(i+10, len(headlines))})*\n\n"
                    bot.send_message(message.chat.id, chunk_header + chunk, parse_mode="Markdown", disable_web_page_preview=True)
                    time.sleep(1)
            else:
                bot.send_message(message.chat.id, "No new headlines available.")
        
        elif command == 'breaking':
            bot.reply_to(message, "🔍 Checking for breaking news...")
            breaking = check_breaking_news()
            
            if breaking:
                for news in breaking[:5]:
                    alert = f"🚨 *BREAKING*\n\n*{news['source']}*: {news['title']}\n\n🔗 [Read]({news['url']})"
                    bot.send_message(message.chat.id, alert, parse_mode="Markdown", disable_web_page_preview=True)
                    time.sleep(1)
            else:
                bot.send_message(message.chat.id, "No breaking news at the moment.")
        
        else:
            # Default response
            bot.reply_to(message, 
                "👋 Hi! I'm your Market Advisor Bot.\n\n"
                "Type `news` for headlines or `help` for commands.",
                parse_mode="Markdown")
    
    except Exception as e:
        print(f"Error handling message: {e}")
        bot.reply_to(message, "Type `help` for available commands.")

# === MAIN EXECUTION ===
if __name__ == "__main__":
    print("\n" + "="*60)
    print("MARKET ADVISOR BOT WITH COMMAND TRIGGERS")
    print("="*60)
    print(f"Time: {datetime.now()}")
    print(f"Bot Token: {'✓' if TOKEN else '✗ MISSING'}")
    print(f"Chat ID: {'✓' if CHAT_ID else '✗ MISSING'}")
    print(f"News API: {'✓' if NEWS_KEY else '✗ MISSING'}")
    print("\nCommand Triggers:")
    for cmd, triggers in COMMAND_TRIGGERS.items():
        print(f"• {cmd}: {', '.join(triggers)}")
    print("="*60 + "\n")
    
    is_github_actions = os.getenv("GITHUB_ACTIONS") == "true"
    
    try:
        if is_github_actions:
            print("Running scheduled update...")
            send_full_briefing()
            print("\nChecking breaking news...")
            send_breaking_news_alert()
            print("\n✅ ALL TASKS COMPLETED\n")
        else:
            print("Starting bot in polling mode...")
            print("Bot will respond to messages!\n")
            print("Try sending:")
            print("• 'news' - for headlines")
            print("• 'market' - for market info")
            print("• 'help' - for all commands\n")
            bot.infinity_polling()
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        if CHAT_ID:
            try:
                bot.send_message(CHAT_ID, f"⚠️ Bot error: {str(e)[:200]}")
            except:
                pass
