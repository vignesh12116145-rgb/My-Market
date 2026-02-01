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

# Enhanced News Sources with RSS feeds for deeper coverage
NEWS_SOURCES = {
    'moneycontrol': [
        'https://www.moneycontrol.com/rss/latestnews.xml',
        'https://www.moneycontrol.com/rss/marketreports.xml',
        'https://www.moneycontrol.com/rss/business.xml'
    ],
    'bloomberg': [
        'https://feeds.bloomberg.com/markets/news.rss',
        'https://feeds.bloomberg.com/india/news.rss',
        'https://feeds.bloomberg.com/technology/news.rss'
    ],
    'economic_times': [
        'https://economictimes.indiatimes.com/rssfeedstopstories.cms',
        'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms',
        'https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms'
    ],
    'livemint': [
        'https://www.livemint.com/rss/markets',
        'https://www.livemint.com/rss/companies',
        'https://www.livemint.com/rss/money'
    ],
    'reuters': [
        'https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best'
    ]
}

def get_market_status():
    """Deep Market Analysis: Indian & Global Markets, FII/DII Sentiment & Suspicious Moves"""
    status = "🏛️ *COMPREHENSIVE MARKET & INSTITUTIONAL ANALYSIS*\n\n"
    
    try:
        # === INDIAN MARKETS ===
        status += "🇮🇳 *INDIAN MARKETS*\n"
        
        # NIFTY 50 with Deep Analysis
        nifty = yf.Ticker("^NSEI")
        nifty_hist = nifty.history(period="5d")
        nifty_price = nifty_hist['Close'].iloc[-1]
        nifty_change = ((nifty_price - nifty_hist['Close'].iloc[-2]) / nifty_hist['Close'].iloc[-2]) * 100
        nifty_vol = nifty_hist['Volume'].iloc[-1]
        nifty_avg_vol = nifty_hist['Volume'].iloc[:-1].mean()
        vol_ratio = nifty_vol / nifty_avg_vol if nifty_avg_vol > 0 else 0
        
        status += f"• *NIFTY 50*: ₹{nifty_price:,.2f} ({nifty_change:+.2f}%)\n"
        status += f"  Volume: {nifty_vol:,.0f} ({vol_ratio:.2f}x avg)\n"
        
        if vol_ratio > 1.5:
            status += "  ⚠️ *ALERT:* Suspicious high volume! FII/DII actively trading.\n"
        if abs(nifty_change) > 2:
            status += f"  🚨 *BIG MOVE:* Market moved {abs(nifty_change):.2f}%!\n"
        
        # SENSEX
        sensex = yf.Ticker("^BSESN")
        sensex_hist = sensex.history(period="1d")
        if not sensex_hist.empty:
            sensex_price = sensex_hist['Close'].iloc[-1]
            sensex_change = ((sensex_price - sensex_hist['Open'].iloc[-1]) / sensex_hist['Open'].iloc[-1]) * 100
            status += f"• *SENSEX*: ₹{sensex_price:,.2f} ({sensex_change:+.2f}%)\n"
        
        # BANK NIFTY
        banknifty = yf.Ticker("^NSEBANK")
        bank_hist = banknifty.history(period="1d")
        if not bank_hist.empty:
            bank_price = bank_hist['Close'].iloc[-1]
            bank_change = ((bank_price - bank_hist['Open'].iloc[-1]) / bank_hist['Open'].iloc[-1]) * 100
            status += f"• *BANK NIFTY*: ₹{bank_price:,.2f} ({bank_change:+.2f}%)\n"
        
        status += "\n"
        
        # === GLOBAL MARKETS ===
        status += "🌍 *GLOBAL MARKETS*\n"
        
        global_indices = {
            '^DJI': 'DOW JONES',
            '^GSPC': 'S&P 500',
            '^IXIC': 'NASDAQ',
            '^FTSE': 'FTSE 100',
            '^N225': 'NIKKEI 225'
        }
        
        for symbol, name in global_indices.items():
            try:
                idx = yf.Ticker(symbol)
                hist = idx.history(period="1d")
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    change = ((price - hist['Open'].iloc[-1]) / hist['Open'].iloc[-1]) * 100
                    status += f"• *{name}*: {price:,.2f} ({change:+.2f}%)\n"
            except:
                continue
        
        status += "\n"
        
        # === CURRENCIES ===
        status += "💱 *CURRENCIES*\n"
        
        try:
            usd_inr = yf.Ticker("INR=X").history(period="1d")
            if not usd_inr.empty:
                inr_rate = usd_inr['Close'].iloc[-1]
                inr_change = ((inr_rate - usd_inr['Open'].iloc[-1]) / usd_inr['Open'].iloc[-1]) * 100
                status += f"• *USD/INR*: ₹{inr_rate:.2f} ({inr_change:+.2f}%)\n"
        except:
            pass
        
        try:
            eur_usd = yf.Ticker("EURUSD=X").history(period="1d")
            if not eur_usd.empty:
                eur_rate = eur_usd['Close'].iloc[-1]
                status += f"• *EUR/USD*: ${eur_rate:.4f}\n"
        except:
            pass
        
        status += "\n"
        
        # === COMMODITIES ===
        status += "🛢️ *COMMODITIES*\n"
        
        commodities = {
            'GC=F': 'GOLD',
            'SI=F': 'SILVER',
            'CL=F': 'CRUDE OIL',
            'BZ=F': 'BRENT CRUDE'
        }
        
        for symbol, name in commodities.items():
            try:
                comm = yf.Ticker(symbol)
                hist = comm.history(period="1d")
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    change = ((price - hist['Open'].iloc[-1]) / hist['Open'].iloc[-1]) * 100
                    status += f"• *{name}*: ${price:,.2f} ({change:+.2f}%)\n"
            except:
                continue
        
        status += "\n"
        
        # === SUSPICIOUS MOVEMENTS DETECTION ===
        status += "🔍 *SUSPICIOUS ACTIVITY MONITOR*\n"
        
        # Check top Indian stocks for unusual movements
        top_stocks = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS']
        alerts = []
        
        for stock_symbol in top_stocks:
            try:
                stock = yf.Ticker(stock_symbol)
                stock_hist = stock.history(period="5d")
                if len(stock_hist) > 1:
                    stock_price = stock_hist['Close'].iloc[-1]
                    stock_change = ((stock_price - stock_hist['Close'].iloc[-2]) / stock_hist['Close'].iloc[-2]) * 100
                    stock_vol = stock_hist['Volume'].iloc[-1]
                    stock_avg_vol = stock_hist['Volume'].iloc[:-1].mean()
                    stock_vol_ratio = stock_vol / stock_avg_vol if stock_avg_vol > 0 else 0
                    
                    # Alert on big movements or volume spikes
                    if abs(stock_change) > 3 or stock_vol_ratio > 2:
                        stock_name = stock_symbol.replace('.NS', '')
                        alerts.append(f"⚠️ *{stock_name}*: {stock_change:+.2f}% (Vol: {stock_vol_ratio:.1f}x)")
            except:
                continue
        
        if alerts:
            status += "\n".join(alerts) + "\n"
        else:
            status += "✅ No unusual activity detected in top stocks.\n"
        
        status += "\n"
        
        # === FII/DII INDICATOR ===
        status += "💼 *FII/DII SENTIMENT INDICATOR*\n"
        # Based on market breadth and volume
        if vol_ratio > 1.3:
            if nifty_change > 0:
                status += "📈 *Strong Buying Pressure* - Likely FII/DII accumulation\n"
            else:
                status += "📉 *Heavy Selling* - Possible FII/DII distribution\n"
        else:
            status += "➡️ *Normal Activity* - Wait for clearer signals\n"
        
    except Exception as e:
        status += f"⚠️ Market data updating... ({str(e)[:50]})\n"
    
    return status

def fetch_rss_news(feed_url, source_name):
    """Fetch detailed news from RSS feeds"""
    articles = []
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:5]:  # Top 5 from each feed
            # Get full description/content
            description = entry.get('description', entry.get('summary', ''))
            # Clean HTML tags
            if description:
                soup = BeautifulSoup(description, 'html.parser')
                description = soup.get_text()[:500]  # First 500 chars for elaborate info
            
            title = entry.get('title', 'No Title')
            link = entry.get('link', '')
            
            articles.append({
                'title': title,
                'description': description,
                'link': link,
                'source': source_name,
                'published': entry.get('published', '')
            })
    except Exception as e:
        print(f"Error fetching {source_name}: {e}")
    
    return articles

def get_30_elaborate_news():
    """Fetches 30+ detailed insights from Moneycontrol, Bloomberg, etc. + NewsAPI"""
    if not os.path.exists(DB_FILE): 
        open(DB_FILE, 'w').close()
    
    with open(DB_FILE, "r") as f: 
        sent_ids = set(f.read().splitlines())

    all_news = []
    
    # === METHOD 1: RSS FEEDS (Better for elaborate content) ===
    for source_type, feeds in NEWS_SOURCES.items():
        for feed_url in feeds:
            articles = fetch_rss_news(feed_url, source_type.upper())
            all_news.extend(articles)
            time.sleep(0.5)  # Rate limiting
    
    # === METHOD 2: NewsAPI (For additional coverage) ===
    if NEWS_KEY:
        try:
            # Comprehensive query covering all requested topics
            queries = [
                "(AI OR artificial intelligence) AND (finance OR fintech)",
                "(FII OR DII) AND india",
                "derivatives AND (india OR NSE OR BSE)",
                "geopolitics AND (market OR economy)",
                "(moneycontrol OR bloomberg) AND stocks",
                "health AND (pharma OR healthcare OR biotech)",
                "commodities AND (gold OR oil OR silver)",
                "cryptocurrency AND (bitcoin OR ethereum)",
                "RBI OR SEBI OR monetary policy",
                "IPO OR stock market india"
            ]
            
            for query in queries:
                url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&pageSize=10&language=en&apiKey={NEWS_KEY}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    for article in data.get('articles', []):
                        all_news.append({
                            'title': article.get('title', ''),
                            'description': article.get('description', article.get('content', ''))[:500],
                            'link': article.get('url', ''),
                            'source': article.get('source', {}).get('name', 'NEWS'),
                            'published': article.get('publishedAt', '')
                        })
                
                time.sleep(0.5)  # Rate limiting
        except Exception as e:
            print(f"NewsAPI error: {e}")
    
    # === FILTER & FORMAT ===
    news_items = []
    for article in all_news:
        url = article['link']
        
        # Skip if already sent
        if url in sent_ids:
            continue
        
        # Skip if no description (we want elaborate info)
        if not article['description'] or len(article['description']) < 50:
            continue
        
        if len(news_items) >= 30:
            break
        
        # Format with elaborate details
        source = article['source'].upper()
        title = article['title'][:150]
        desc = article['description'][:400]
        
        formatted = f"📌 *{source}*: *{title}*\n\n"
        formatted += f"_{desc}_\n\n"
        formatted += f"🔗 [Read Full Article]({url})"
        
        news_items.append(formatted)
        
        # Mark as sent
        with open(DB_FILE, "a") as f: 
            f.write(url + "\n")
    
    return news_items

def send_full_briefing():
    """Send comprehensive market briefing"""
    try:
        # 1. Header with timestamp
        header = f"🤵 *MASTER FINANCIAL ADVISOR - COMPREHENSIVE UPDATE*\n"
        header += f"📅 {datetime.now().strftime('%d %B %Y, %H:%M IST')}\n"
        header += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # 2. Market Status (Deep Analysis)
        market_msg = header + get_market_status()
        bot.send_message(CHAT_ID, market_msg, parse_mode="Markdown")
        time.sleep(2)
        
        # 3. Detailed News (30+ articles with elaborate info)
        bot.send_message(CHAT_ID, "📰 *Fetching detailed news from all sources...*", parse_mode="Markdown")
        
        all_news = get_30_elaborate_news()
        
        if not all_news:
            bot.send_message(CHAT_ID, "✅ *No new significant news since last update.*\n\n_All markets monitored. Will alert on breaking news._", parse_mode="Markdown")
            return
        
        # Send news in chunks of 3 (to avoid telegram limits and keep it readable)
        for i in range(0, len(all_news), 3):
            chunk = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n".join(all_news[i:i+3])
            chunk_header = f"🌍 *DETAILED NEWS INTELLIGENCE - Part {i//3 + 1}*\n\n"
            bot.send_message(CHAT_ID, chunk_header + chunk, parse_mode="Markdown", disable_web_page_preview=True)
            time.sleep(2)  # Avoid rate limits
        
        # 4. Summary
        summary = f"\n\n✅ *Update Complete*\n"
        summary += f"📊 Markets Analyzed: Indian, Global, Currencies, Commodities\n"
        summary += f"📰 News Articles: {len(all_news)} detailed reports\n"
        summary += f"🔔 Next update in ~4-5 hours\n"
        bot.send_message(CHAT_ID, summary, parse_mode="Markdown")
        
    except Exception as e:
        error_msg = f"⚠️ *Error in briefing*: {str(e)[:200]}"
        bot.send_message(CHAT_ID, error_msg, parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def on_message(message):
    """Handle incoming messages"""
    try:
        bot.reply_to(message, "⚙️ *Initiating comprehensive analysis...*\n\n_This includes:_\n• Market movements\n• FII/DII activity\n• Suspicious trades\n• Global indices\n• 30+ detailed news articles\n\n_Please wait 30-60 seconds..._", parse_mode="Markdown")
        send_full_briefing()
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)[:100]}")

# === MAIN EXECUTION ===
if __name__ == "__main__":
    print(f"[{datetime.now()}] Starting Master Financial Advisor Bot...")
    
    try:
        # Send briefing immediately
        send_full_briefing()
        print(f"[{datetime.now()}] Briefing sent successfully!")
        
        # If not running in GitHub Actions, start polling for user commands
        if not os.getenv("GITHUB_ACTIONS"):
            print("Starting bot polling for user messages...")
            bot.infinity_polling()
    except Exception as e:
        print(f"Error: {e}")
        if CHAT_ID:
            try:
                bot.send_message(CHAT_ID, f"⚠️ Bot encountered an error: {str(e)[:200]}", parse_mode="Markdown")
            except:
                pass
