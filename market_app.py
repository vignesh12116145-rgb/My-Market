"""
Master Financial Advisor Telegram Bot
Comprehensive financial news and market monitoring system
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import re

# Telegram Bot
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# News and Data Sources
import feedparser
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd

# Environment variables
from dotenv import load_dotenv

# Configuration
load_dotenv()

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')  # Your Telegram chat ID for alerts

# News source URLs
NEWS_SOURCES = {
    'moneycontrol': {
        'rss': 'https://www.moneycontrol.com/rss/latestnews.xml',
        'market': 'https://www.moneycontrol.com/rss/marketreports.xml',
        'url': 'https://www.moneycontrol.com'
    },
    'bloomberg': {
        'rss': 'https://feeds.bloomberg.com/markets/news.rss',
        'india': 'https://feeds.bloomberg.com/india/news.rss',
        'url': 'https://www.bloomberg.com'
    },
    'economic_times': {
        'rss': 'https://economictimes.indiatimes.com/rssfeedstopstories.cms',
        'market': 'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms',
        'url': 'https://economictimes.indiatimes.com'
    },
    'reuters': {
        'business': 'https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best',
        'url': 'https://www.reuters.com'
    },
    'livemint': {
        'rss': 'https://www.livemint.com/rss/markets',
        'url': 'https://www.livemint.com'
    }
}

# Market indices to track
INDIAN_INDICES = {
    '^NSEI': 'NIFTY 50',
    '^NSEBANK': 'NIFTY BANK',
    '^BSESN': 'SENSEX'
}

GLOBAL_INDICES = {
    '^DJI': 'DOW JONES',
    '^GSPC': 'S&P 500',
    '^IXIC': 'NASDAQ',
    '^FTSE': 'FTSE 100',
    '^N225': 'NIKKEI 225',
    '^HSI': 'HANG SENG'
}

CURRENCIES = {
    'USDINR=X': 'USD/INR',
    'EURUSD=X': 'EUR/USD',
    'GBPUSD=X': 'GBP/USD'
}

COMMODITIES = {
    'GC=F': 'GOLD',
    'CL=F': 'CRUDE OIL',
    'SI=F': 'SILVER',
    'BZ=F': 'BRENT CRUDE'
}

# Thresholds for alerts
ALERT_THRESHOLDS = {
    'market_change': 2.0,  # Alert if market moves more than 2%
    'stock_change': 5.0,   # Alert if stock moves more than 5%
    'volume_spike': 3.0,   # Alert if volume is 3x average
}


class NewsAggregator:
    """Aggregate news from multiple sources"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
    
    async def fetch_rss_feed(self, url: str, source_name: str) -> List[Dict]:
        """Fetch and parse RSS feed"""
        try:
            feed = feedparser.parse(url)
            articles = []
            
            for entry in feed.entries[:10]:  # Top 10 articles
                article = {
                    'title': entry.get('title', 'No Title'),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', entry.get('description', '')),
                    'source': source_name
                }
                articles.append(article)
            
            return articles
        except Exception as e:
            logger.error(f"Error fetching {source_name}: {e}")
            return []
    
    async def get_moneycontrol_news(self) -> List[Dict]:
        """Get latest news from Moneycontrol"""
        articles = []
        articles.extend(await self.fetch_rss_feed(NEWS_SOURCES['moneycontrol']['rss'], 'MoneyControl'))
        articles.extend(await self.fetch_rss_feed(NEWS_SOURCES['moneycontrol']['market'], 'MoneyControl Markets'))
        return articles
    
    async def get_bloomberg_news(self) -> List[Dict]:
        """Get latest news from Bloomberg"""
        articles = []
        articles.extend(await self.fetch_rss_feed(NEWS_SOURCES['bloomberg']['rss'], 'Bloomberg'))
        articles.extend(await self.fetch_rss_feed(NEWS_SOURCES['bloomberg']['india'], 'Bloomberg India'))
        return articles
    
    async def get_economic_times_news(self) -> List[Dict]:
        """Get latest news from Economic Times"""
        articles = []
        articles.extend(await self.fetch_rss_feed(NEWS_SOURCES['economic_times']['rss'], 'Economic Times'))
        articles.extend(await self.fetch_rss_feed(NEWS_SOURCES['economic_times']['market'], 'ET Markets'))
        return articles
    
    async def get_livemint_news(self) -> List[Dict]:
        """Get latest news from LiveMint"""
        return await self.fetch_rss_feed(NEWS_SOURCES['livemint']['rss'], 'LiveMint')
    
    async def get_all_news(self) -> List[Dict]:
        """Aggregate news from all sources"""
        all_articles = []
        
        # Fetch from all sources concurrently
        results = await asyncio.gather(
            self.get_moneycontrol_news(),
            self.get_bloomberg_news(),
            self.get_economic_times_news(),
            self.get_livemint_news(),
            return_exceptions=True
        )
        
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
        
        # Sort by published date (newest first)
        all_articles.sort(key=lambda x: x.get('published', ''), reverse=True)
        
        return all_articles[:50]  # Top 50 articles
    
    async def search_news(self, keyword: str) -> List[Dict]:
        """Search for specific news"""
        all_news = await self.get_all_news()
        keyword_lower = keyword.lower()
        
        filtered = [
            article for article in all_news
            if keyword_lower in article['title'].lower() or 
               keyword_lower in article.get('summary', '').lower()
        ]
        
        return filtered


class MarketDataFetcher:
    """Fetch and analyze market data"""
    
    async def get_market_overview(self) -> Dict:
        """Get comprehensive market overview"""
        data = {
            'indian_indices': await self.get_indices_data(INDIAN_INDICES),
            'global_indices': await self.get_indices_data(GLOBAL_INDICES),
            'currencies': await self.get_indices_data(CURRENCIES),
            'commodities': await self.get_indices_data(COMMODITIES),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return data
    
    async def get_indices_data(self, indices: Dict) -> Dict:
        """Fetch data for multiple indices"""
        results = {}
        
        for symbol, name in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period='1d')
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    prev_close = info.get('previousClose', info.get('regularMarketPreviousClose', current_price))
                    
                    if prev_close and prev_close > 0:
                        change = current_price - prev_close
                        change_pct = (change / prev_close) * 100
                    else:
                        change = 0
                        change_pct = 0
                    
                    results[name] = {
                        'price': round(current_price, 2),
                        'change': round(change, 2),
                        'change_pct': round(change_pct, 2),
                        'volume': hist['Volume'].iloc[-1] if 'Volume' in hist.columns else 0
                    }
            except Exception as e:
                logger.error(f"Error fetching {name}: {e}")
                results[name] = {'error': str(e)}
        
        return results
    
    async def get_fii_dii_data(self) -> Dict:
        """Get FII/DII data (simplified - would need proper API)"""
        # This is a placeholder - you'd need to integrate with NSE/BSE API
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'fii_cash': 'Data requires NSE API integration',
            'dii_cash': 'Data requires NSE API integration',
            'note': 'Please integrate with official NSE/BSE data sources'
        }
    
    async def analyze_stock(self, symbol: str) -> Dict:
        """Detailed stock analysis"""
        try:
            # Add .NS for NSE stocks if not present
            if not symbol.endswith(('.NS', '.BO', '=X', '=F')):
                symbol = f"{symbol}.NS"
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period='1mo')
            
            if hist.empty:
                return {'error': 'No data available for this symbol'}
            
            current_price = hist['Close'].iloc[-1]
            avg_volume = hist['Volume'].mean()
            current_volume = hist['Volume'].iloc[-1]
            
            # Calculate technical indicators
            sma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            high_52w = hist['High'].max()
            low_52w = hist['Low'].min()
            
            analysis = {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'current_price': round(current_price, 2),
                'previous_close': info.get('previousClose', 0),
                'change_pct': round(((current_price - info.get('previousClose', current_price)) / info.get('previousClose', 1)) * 100, 2),
                'volume': current_volume,
                'avg_volume': avg_volume,
                'volume_ratio': round(current_volume / avg_volume, 2) if avg_volume > 0 else 0,
                'sma_20': round(sma_20, 2) if pd.notna(sma_20) else 0,
                '52w_high': round(high_52w, 2),
                '52w_low': round(low_52w, 2),
                'market_cap': info.get('marketCap', 'N/A'),
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'sector': info.get('sector', 'N/A')
            }
            
            # Check for suspicious movements
            if analysis['volume_ratio'] > ALERT_THRESHOLDS['volume_spike']:
                analysis['alert'] = f"⚠️ Volume spike: {analysis['volume_ratio']}x average"
            
            if abs(analysis['change_pct']) > ALERT_THRESHOLDS['stock_change']:
                analysis['alert'] = f"⚠️ Significant price movement: {analysis['change_pct']}%"
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return {'error': str(e)}
    
    async def detect_suspicious_movements(self) -> List[Dict]:
        """Detect unusual stock movements in Indian market"""
        # This would require real-time data feed
        # Placeholder implementation
        suspicious = []
        
        # Example: Check top Nifty stocks
        nifty_stocks = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS']
        
        for symbol in nifty_stocks:
            analysis = await self.analyze_stock(symbol)
            if 'alert' in analysis:
                suspicious.append(analysis)
        
        return suspicious


class TelegramBot:
    """Main Telegram Bot Handler"""
    
    def __init__(self):
        self.news_aggregator = NewsAggregator()
        self.market_fetcher = MarketDataFetcher()
        self.monitoring_active = {}  # Track monitoring per user
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        keyboard = [
            [InlineKeyboardButton("📰 Latest News", callback_data='news_all')],
            [InlineKeyboardButton("📊 Market Overview", callback_data='market_overview')],
            [InlineKeyboardButton("🇮🇳 Indian Markets", callback_data='indian_markets'),
             InlineKeyboardButton("🌍 Global Markets", callback_data='global_markets')],
            [InlineKeyboardButton("💱 Currencies", callback_data='currencies'),
             InlineKeyboardButton("🛢️ Commodities", callback_data='commodities')],
            [InlineKeyboardButton("💼 FII/DII Data", callback_data='fii_dii')],
            [InlineKeyboardButton("🔍 Search News", callback_data='search_news')],
            [InlineKeyboardButton("📈 Analyze Stock", callback_data='analyze_stock')],
            [InlineKeyboardButton("⚠️ Alerts ON/OFF", callback_data='toggle_alerts')],
            [InlineKeyboardButton("ℹ️ Help", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = """
🤖 *Master Financial Advisor Bot*

Your comprehensive source for:
📰 Real-time financial news (MoneyControl, Bloomberg, ET, LiveMint)
📊 Market data (Indian & Global indices)
💱 Currency & Commodity tracking
📈 Stock analysis & alerts
💼 FII/DII movements
🔔 Instant alerts for major market events

Select an option below to get started!
        """
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'news_all':
            await self.send_latest_news(query)
        elif query.data == 'market_overview':
            await self.send_market_overview(query)
        elif query.data == 'indian_markets':
            await self.send_indian_markets(query)
        elif query.data == 'global_markets':
            await self.send_global_markets(query)
        elif query.data == 'currencies':
            await self.send_currencies(query)
        elif query.data == 'commodities':
            await self.send_commodities(query)
        elif query.data == 'fii_dii':
            await self.send_fii_dii(query)
        elif query.data == 'search_news':
            await query.edit_message_text("Please send me a keyword to search for (e.g., 'inflation', 'RBI', 'Tesla')")
        elif query.data == 'analyze_stock':
            await query.edit_message_text("Please send me a stock symbol to analyze (e.g., 'RELIANCE', 'INFY', 'TCS')")
        elif query.data == 'toggle_alerts':
            await self.toggle_alerts(query, context)
        elif query.data == 'help':
            await self.send_help(query)
    
    async def send_latest_news(self, query):
        """Send latest news from all sources"""
        await query.edit_message_text("🔄 Fetching latest news...")
        
        articles = await self.news_aggregator.get_all_news()
        
        if not articles:
            await query.edit_message_text("❌ No news available at the moment.")
            return
        
        message = "📰 *LATEST FINANCIAL NEWS*\n\n"
        
        for i, article in enumerate(articles[:15], 1):
            title = article['title'][:100]
            source = article['source']
            link = article['link']
            
            # Clean summary
            summary = BeautifulSoup(article.get('summary', ''), 'html.parser').get_text()
            summary = summary[:200] + '...' if len(summary) > 200 else summary
            
            message += f"*{i}. {title}*\n"
            message += f"📍 Source: {source}\n"
            message += f"📝 {summary}\n"
            message += f"🔗 [Read More]({link})\n\n"
            
            # Split message if too long
            if len(message) > 3500:
                await query.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)
                message = ""
        
        if message:
            await query.edit_message_text(message, parse_mode='Markdown', disable_web_page_preview=True)
    
    async def send_market_overview(self, query):
        """Send comprehensive market overview"""
        await query.edit_message_text("📊 Fetching market data...")
        
        data = await self.market_fetcher.get_market_overview()
        
        message = f"📊 *MARKET OVERVIEW*\n"
        message += f"🕐 Updated: {data['timestamp']}\n\n"
        
        # Indian Markets
        message += "🇮🇳 *INDIAN MARKETS*\n"
        for name, info in data['indian_indices'].items():
            if 'error' not in info:
                emoji = "🟢" if info['change_pct'] >= 0 else "🔴"
                message += f"{emoji} *{name}*: {info['price']} ({info['change_pct']:+.2f}%)\n"
        
        message += "\n🌍 *GLOBAL MARKETS*\n"
        for name, info in data['global_indices'].items():
            if 'error' not in info:
                emoji = "🟢" if info['change_pct'] >= 0 else "🔴"
                message += f"{emoji} *{name}*: {info['price']} ({info['change_pct']:+.2f}%)\n"
        
        message += "\n💱 *CURRENCIES*\n"
        for name, info in data['currencies'].items():
            if 'error' not in info:
                emoji = "🟢" if info['change_pct'] >= 0 else "🔴"
                message += f"{emoji} *{name}*: {info['price']} ({info['change_pct']:+.2f}%)\n"
        
        message += "\n🛢️ *COMMODITIES*\n"
        for name, info in data['commodities'].items():
            if 'error' not in info:
                emoji = "🟢" if info['change_pct'] >= 0 else "🔴"
                message += f"{emoji} *{name}*: ${info['price']} ({info['change_pct']:+.2f}%)\n"
        
        await query.edit_message_text(message, parse_mode='Markdown')
    
    async def send_indian_markets(self, query):
        """Send Indian market data"""
        data = await self.market_fetcher.get_indices_data(INDIAN_INDICES)
        
        message = "🇮🇳 *INDIAN MARKETS*\n\n"
        for name, info in data.items():
            if 'error' not in info:
                emoji = "🟢" if info['change_pct'] >= 0 else "🔴"
                message += f"{emoji} *{name}*\n"
                message += f"Price: {info['price']}\n"
                message += f"Change: {info['change']:+.2f} ({info['change_pct']:+.2f}%)\n"
                message += f"Volume: {info['volume']:,.0f}\n\n"
        
        await query.edit_message_text(message, parse_mode='Markdown')
    
    async def send_global_markets(self, query):
        """Send global market data"""
        data = await self.market_fetcher.get_indices_data(GLOBAL_INDICES)
        
        message = "🌍 *GLOBAL MARKETS*\n\n"
        for name, info in data.items():
            if 'error' not in info:
                emoji = "🟢" if info['change_pct'] >= 0 else "🔴"
                message += f"{emoji} *{name}*\n"
                message += f"Price: {info['price']}\n"
                message += f"Change: {info['change']:+.2f} ({info['change_pct']:+.2f}%)\n\n"
        
        await query.edit_message_text(message, parse_mode='Markdown')
    
    async def send_currencies(self, query):
        """Send currency data"""
        data = await self.market_fetcher.get_indices_data(CURRENCIES)
        
        message = "💱 *CURRENCY MARKETS*\n\n"
        for name, info in data.items():
            if 'error' not in info:
                emoji = "🟢" if info['change_pct'] >= 0 else "🔴"
                message += f"{emoji} *{name}*\n"
                message += f"Rate: {info['price']}\n"
                message += f"Change: {info['change']:+.4f} ({info['change_pct']:+.2f}%)\n\n"
        
        await query.edit_message_text(message, parse_mode='Markdown')
    
    async def send_commodities(self, query):
        """Send commodity data"""
        data = await self.market_fetcher.get_indices_data(COMMODITIES)
        
        message = "🛢️ *COMMODITY MARKETS*\n\n"
        for name, info in data.items():
            if 'error' not in info:
                emoji = "🟢" if info['change_pct'] >= 0 else "🔴"
                message += f"{emoji} *{name}*\n"
                message += f"Price: ${info['price']}\n"
                message += f"Change: ${info['change']:+.2f} ({info['change_pct']:+.2f}%)\n\n"
        
        await query.edit_message_text(message, parse_mode='Markdown')
    
    async def send_fii_dii(self, query):
        """Send FII/DII data"""
        data = await self.market_fetcher.get_fii_dii_data()
        
        message = f"💼 *FII/DII DATA*\n\n"
        message += f"Date: {data['date']}\n\n"
        message += f"Note: {data['note']}\n\n"
        message += "To get real-time FII/DII data, please integrate with:\n"
        message += "- NSE Official API\n"
        message += "- BSE Official API\n"
        message += "- Or use premium data providers\n"
        
        await query.edit_message_text(message, parse_mode='Markdown')
    
    async def toggle_alerts(self, query, context):
        """Toggle alert monitoring"""
        user_id = query.from_user.id
        
        if user_id in self.monitoring_active and self.monitoring_active[user_id]:
            self.monitoring_active[user_id] = False
            message = "🔕 *Alerts Disabled*\n\nYou will no longer receive automatic alerts."
        else:
            self.monitoring_active[user_id] = True
            message = "🔔 *Alerts Enabled*\n\nYou will receive alerts for:\n"
            message += f"• Market movements > {ALERT_THRESHOLDS['market_change']}%\n"
            message += f"• Stock movements > {ALERT_THRESHOLDS['stock_change']}%\n"
            message += f"• Volume spikes > {ALERT_THRESHOLDS['volume_spike']}x\n"
            message += "• Breaking financial news\n"
        
        await query.edit_message_text(message, parse_mode='Markdown')
    
    async def send_help(self, query):
        """Send help message"""
        help_text = """
ℹ️ *HOW TO USE*

*Commands:*
/start - Main menu
/news [keyword] - Search news
/stock [symbol] - Analyze stock
/market - Market overview
/alerts - Toggle alerts

*Features:*
📰 Real-time news from multiple sources
📊 Live market data tracking
💱 Currency and commodity prices
📈 Stock analysis and alerts
🔔 Automatic notifications for major events

*Stock Symbols:*
Indian stocks: Use NSE symbols (RELIANCE, INFY, TCS)
Global stocks: Use ticker symbols (AAPL, TSLA, GOOGL)

*Data Sources:*
• MoneyControl
• Bloomberg
• Economic Times
• LiveMint
• Yahoo Finance

For support: Contact @YourUsername
        """
        
        await query.edit_message_text(help_text, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages for search and analysis"""
        text = update.message.text
        
        if text.startswith('/news'):
            keyword = text.replace('/news', '').strip()
            if keyword:
                articles = await self.news_aggregator.search_news(keyword)
                if articles:
                    message = f"🔍 *Search Results for '{keyword}'*\n\n"
                    for i, article in enumerate(articles[:10], 1):
                        message += f"*{i}. {article['title'][:80]}*\n"
                        message += f"📍 {article['source']}\n"
                        message += f"🔗 [Read]({article['link']})\n\n"
                    await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)
                else:
                    await update.message.reply_text(f"No news found for '{keyword}'")
        
        elif text.startswith('/stock'):
            symbol = text.replace('/stock', '').strip().upper()
            if symbol:
                analysis = await self.market_fetcher.analyze_stock(symbol)
                if 'error' not in analysis:
                    message = f"📈 *STOCK ANALYSIS: {analysis['name']}*\n\n"
                    message += f"Symbol: {analysis['symbol']}\n"
                    message += f"Price: ₹{analysis['current_price']}\n"
                    message += f"Change: {analysis['change_pct']:+.2f}%\n"
                    message += f"Volume: {analysis['volume']:,.0f}\n"
                    message += f"Avg Volume: {analysis['avg_volume']:,.0f}\n"
                    message += f"Volume Ratio: {analysis['volume_ratio']}x\n"
                    message += f"SMA(20): {analysis['sma_20']}\n"
                    message += f"52W High: {analysis['52w_high']}\n"
                    message += f"52W Low: {analysis['52w_low']}\n"
                    message += f"Market Cap: {analysis['market_cap']}\n"
                    message += f"P/E Ratio: {analysis['pe_ratio']}\n"
                    message += f"Sector: {analysis['sector']}\n"
                    
                    if 'alert' in analysis:
                        message += f"\n{analysis['alert']}\n"
                    
                    await update.message.reply_text(message, parse_mode='Markdown')
                else:
                    await update.message.reply_text(f"Error: {analysis['error']}")
    
    async def monitor_markets(self, context: ContextTypes.DEFAULT_TYPE):
        """Background task to monitor markets and send alerts"""
        try:
            # Check for suspicious movements
            suspicious = await self.market_fetcher.detect_suspicious_movements()
            
            if suspicious and ADMIN_CHAT_ID:
                message = "⚠️ *MARKET ALERT*\n\n"
                for stock in suspicious:
                    message += f"🔔 {stock['name']}\n"
                    message += f"Price: {stock['current_price']} ({stock['change_pct']:+.2f}%)\n"
                    message += f"{stock.get('alert', '')}\n\n"
                
                # Send to users with alerts enabled
                for user_id, enabled in self.monitoring_active.items():
                    if enabled:
                        try:
                            await context.bot.send_message(
                                chat_id=user_id,
                                text=message,
                                parse_mode='Markdown'
                            )
                        except Exception as e:
                            logger.error(f"Error sending alert to {user_id}: {e}")
        
        except Exception as e:
            logger.error(f"Error in market monitoring: {e}")
    
    async def send_breaking_news(self, context: ContextTypes.DEFAULT_TYPE):
        """Background task to check for breaking news"""
        try:
            articles = await self.news_aggregator.get_all_news()
            
            # Check for important keywords
            breaking_keywords = ['breaking', 'alert', 'crash', 'surge', 'emergency', 
                                'rbi', 'sebi', 'budget', 'policy', 'gdp']
            
            for article in articles[:5]:
                title_lower = article['title'].lower()
                if any(keyword in title_lower for keyword in breaking_keywords):
                    message = f"🚨 *BREAKING NEWS*\n\n"
                    message += f"*{article['title']}*\n\n"
                    message += f"📍 Source: {article['source']}\n"
                    message += f"🔗 [Read More]({article['link']})\n"
                    
                    # Send to users with alerts enabled
                    for user_id, enabled in self.monitoring_active.items():
                        if enabled:
                            try:
                                await context.bot.send_message(
                                    chat_id=user_id,
                                    text=message,
                                    parse_mode='Markdown',
                                    disable_web_page_preview=True
                                )
                            except Exception as e:
                                logger.error(f"Error sending news to {user_id}: {e}")
        
        except Exception as e:
            logger.error(f"Error checking breaking news: {e}")


def main():
    """Main function to run the bot"""
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        return
    
    # Create bot instance
    bot = TelegramBot()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CommandHandler("market", lambda u, c: bot.button_callback(u, c)))
    application.add_handler(CommandHandler("alerts", lambda u, c: bot.toggle_alerts(u.callback_query, c)))
    application.add_handler(CallbackQueryHandler(bot.button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    # Add background jobs
    job_queue = application.job_queue
    job_queue.run_repeating(bot.monitor_markets, interval=300, first=10)  # Every 5 minutes
    job_queue.run_repeating(bot.send_breaking_news, interval=600, first=60)  # Every 10 minutes
    
    # Start bot
    logger.info("Starting Master Financial Advisor Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
