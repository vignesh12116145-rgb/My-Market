# 🤵 Master Financial Advisor - Telegram Bot

**Your comprehensive AI financial advisor delivering detailed market intelligence directly to Telegram.**

## 🎯 What This Bot Does

This bot acts as your **personal financial advisor**, providing:

✅ **NO HEADLINES ONLY** - Every news article includes full descriptions and summaries (400-500 characters)
✅ **30+ Detailed News Articles** per update from MoneyControl, Bloomberg, Economic Times, LiveMint, Reuters
✅ **Complete Market Coverage**: Indian markets, Global indices, Currencies, Commodities, Derivatives
✅ **FII/DII Activity Monitoring** - Institutional investor sentiment analysis
✅ **Suspicious Movement Detection** - Alerts on unusual stock trading patterns
✅ **Instant Alerts** for major market events and breaking news
✅ **Deep Analysis** - Not just prices, but volume analysis, change percentages, and trend indicators

### 📊 Markets Covered

- **Indian Markets**: NIFTY 50, SENSEX, BANK NIFTY
- **Global Indices**: DOW JONES, S&P 500, NASDAQ, FTSE 100, NIKKEI 225
- **Currencies**: USD/INR, EUR/USD, GBP/USD
- **Commodities**: GOLD, SILVER, CRUDE OIL, BRENT CRUDE
- **Top Indian Stocks**: Real-time monitoring with volume analysis

### 📰 News Sources

- **MoneyControl** - Indian market news & analysis
- **Bloomberg** - Global markets & technology
- **Economic Times** - Business & market reports
- **LiveMint** - Financial news & companies
- **Reuters** - Breaking global news
- **NewsAPI** - Comprehensive coverage of: AI, FinTech, Geopolitics, Health/Pharma, Derivatives, Cryptocurrencies, Policy changes (RBI, SEBI)

### 🔔 Alert Features

The bot automatically alerts you when:
- **Volume Spikes**: Trading volume > 1.5x average (FII/DII activity)
- **Big Market Moves**: Index moves > 2%
- **Stock Alerts**: Individual stocks move > 3% or volume spike > 2x
- **Breaking News**: Major announcements, policy changes, emergency events

## 🚀 Quick Setup (3 Steps)

### Step 1: Create Your Telegram Bot

1. Open Telegram, search for **@BotFather**
2. Send `/newbot` command
3. Choose a name (e.g., "My Financial Advisor")
4. Choose username (must end with 'bot', e.g., "myfinance_bot")
5. **Copy the Bot Token** (looks like: `123456789:ABCdefGHI...`)

### Step 2: Get Your Chat ID

1. Search for **@userinfobot** on Telegram
2. Send `/start`
3. **Copy your Chat ID** (looks like: `123456789`)

### Step 3: Setup on GitHub

1. **Go to your existing repository**: `https://github.com/vignesh12116145-rgb/My-Market`

2. **Replace these files**:
   - Delete old `master_advisor.py` and `run_bot.yml`
   - Upload new files from this download

3. **Add GitHub Secrets**:
   - Go to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Add these three secrets:

   ```
   Name: TELEGRAM_TOKEN
   Value: [your bot token from @BotFather]

   Name: TELEGRAM_CHAT_ID
   Value: [your chat ID from @userinfobot]

   Name: NEWS_API_KEY
   Value: [get free key from https://newsapi.org]
   ```

4. **Commit and Push**:
   ```bash
   git add .
   git commit -m "Update to Master Financial Advisor Bot"
   git push origin main
   ```

5. **Enable GitHub Actions**:
   - Go to Actions tab
   - Enable workflows if prompted
   - Click "Run workflow" to test

## 📱 Using Your Bot

### On Telegram

1. Search for your bot (the username you created)
2. Send `/start` or any message
3. Bot will respond with comprehensive market analysis

### Automatic Updates

The bot runs automatically every 4-5 hours via GitHub Actions:
- **Daily Schedule**: 12am, 5am, 10am, 3pm, 8pm, and 2:30am, 7:30am, 12:30pm, 5:30pm, 10:30pm UTC
- **Manual Trigger**: Click "Run workflow" in GitHub Actions
- **On Code Changes**: Automatically runs when you push to main/master branch

### What You'll Receive

**1. Market Status Update** (Every 4-5 hours):
```
🤵 MASTER FINANCIAL ADVISOR - COMPREHENSIVE UPDATE
📅 01 February 2024, 14:30 IST
━━━━━━━━━━━━━━━━━━━━━━━━━━

🇮🇳 INDIAN MARKETS
• NIFTY 50: ₹21,456.75 (+0.85%)
  Volume: 234,567,890 (1.23x avg)
• SENSEX: ₹70,234.50 (+0.92%)
• BANK NIFTY: ₹45,789.30 (+1.20%)

🌍 GLOBAL MARKETS
• DOW JONES: 38,234.50 (-0.45%)
• S&P 500: 4,876.23 (+0.15%)
...

💱 CURRENCIES
• USD/INR: ₹83.12 (+0.15%)
...

🛢️ COMMODITIES
• GOLD: $2,045.50 (+0.80%)
...

🔍 SUSPICIOUS ACTIVITY MONITOR
⚠️ RELIANCE: +3.45% (Vol: 2.1x)
✅ No unusual activity in other stocks

💼 FII/DII SENTIMENT INDICATOR
📈 Strong Buying Pressure - Likely FII/DII accumulation
```

**2. Detailed News (30+ Articles)**:
```
🌍 DETAILED NEWS INTELLIGENCE - Part 1

📌 MONEYCONTROL: RBI keeps repo rate unchanged at 6.5%

Reserve Bank of India's Monetary Policy Committee decided to 
maintain the repo rate at 6.5% for the fifth consecutive meeting. 
The decision comes amid persistent inflation concerns and stable 
economic growth. MPC focused on ensuring price stability while 
supporting growth momentum. The stance remains 'withdrawal of 
accommodation' signaling cautious approach to rate cuts...

🔗 [Read Full Article]

━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 BLOOMBERG: Tech stocks rally on AI boom

Technology sector witnessed strong buying interest as AI-related 
companies reported better-than-expected earnings. Major indices 
gained with NASDAQ leading. Investors optimistic about generative 
AI adoption across industries. Cloud computing and semiconductor 
stocks particularly strong...

🔗 [Read Full Article]

━━━━━━━━━━━━━━━━━━━━━━━━━━
...
```

## ⚙️ Configuration

### Change Update Frequency

Edit `.github/workflows/run_bot.yml`:

```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours
  - cron: '0 */3 * * *'  # Every 3 hours
```

### Monitor More Stocks

Edit `master_advisor.py`, find this line:

```python
top_stocks = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS']
```

Add more stocks:
```python
top_stocks = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS', 
              'ITC.NS', 'LT.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS']
```

### Adjust Alert Thresholds

In `master_advisor.py`:

```python
if vol_ratio > 1.5:  # Change to 2.0 for less sensitivity
if abs(nifty_change) > 2:  # Change to 3 for bigger moves only
if abs(stock_change) > 3 or stock_vol_ratio > 2:  # Adjust as needed
```

## 🔧 Advanced Setup

### Get NewsAPI Key (Free)

1. Go to https://newsapi.org
2. Sign up for free account
3. Get your API key
4. Add to GitHub Secrets as `NEWS_API_KEY`
5. Free tier: 100 requests/day (sufficient for this bot)

### Local Testing

```bash
# Clone repository
git clone https://github.com/vignesh12116145-rgb/My-Market.git
cd My-Market

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
NEWS_API_KEY=your_newsapi_key
EOF

# Run bot
python master_advisor.py
```

### Deploy 24/7 (Optional)

For continuous monitoring instead of scheduled updates:

**Option 1: Heroku**
```bash
heroku create my-financial-bot
heroku config:set TELEGRAM_TOKEN=your_token
heroku config:set TELEGRAM_CHAT_ID=your_chat_id
heroku config:set NEWS_API_KEY=your_key
git push heroku main
```

**Option 2: Render.com** (Recommended)
1. Go to render.com
2. Connect your GitHub repo
3. Create new "Background Worker"
4. Add environment variables
5. Deploy

**Option 3: AWS/GCP/Azure**
- Deploy as a serverless function or container
- Schedule via CloudWatch/Cloud Scheduler

## 📊 Sample Output

### Market Alert Example
```
🚨 BIG MOVE: Market moved 2.45%!
⚠️ ALERT: Suspicious high volume! FII/DII actively trading.
```

### Breaking News Alert
```
📌 ECONOMIC TIMES: Emergency RBI Meeting Announced

Reserve Bank of India has called for an emergency meeting of the 
Monetary Policy Committee citing extraordinary circumstances in 
global financial markets. Sources indicate discussion on potential 
rate intervention measures. Market participants anticipating 
significant policy announcement...

🔗 [Read Full Article]
```

## 🔒 Security & Privacy

- ✅ Bot token and chat ID stored as GitHub Secrets (encrypted)
- ✅ No data stored on third-party servers
- ✅ All processing happens in GitHub Actions (free tier)
- ✅ `sent_news.txt` tracks delivered news to avoid duplicates
- ✅ Rate limiting implemented to avoid API bans

## 🐛 Troubleshooting

### Bot Not Sending Messages

1. **Check GitHub Actions**:
   - Go to Actions tab
   - Look for failed workflows (red X)
   - Click to see error logs

2. **Verify Secrets**:
   - Settings → Secrets → Actions
   - Make sure all three secrets exist
   - Re-add if needed

3. **Test Bot Token**:
   ```bash
   curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
   ```

### No News Received

- NewsAPI free tier limit reached (100 requests/day)
- RSS feeds temporarily down (bot will retry next run)
- All news already sent (check `sent_news.txt`)
- Delete `sent_news.txt` to reset

### Market Data Not Loading

- Yahoo Finance rate limiting (wait 5-10 minutes)
- Markets closed (outside trading hours)
- Temporary API issue (will resolve automatically)

### GitHub Actions Not Running

1. Enable workflows: Actions → "I understand my workflows"
2. Check cron schedule (might be in different timezone)
3. Manually trigger: Actions → Run workflow

## 📈 Monitoring & Logs

### View Bot Activity

1. Go to GitHub Actions tab
2. Click on latest workflow run
3. Expand "Run Financial Advisor Bot"
4. See detailed logs

### Download Sent News History

1. Go to Actions → Latest run
2. Scroll to "Artifacts"
3. Download `bot-logs`
4. Contains `sent_news.txt`

## 🎓 Understanding the Output

### Volume Ratio
- **1.0x** = Normal volume
- **1.5x** = Increased activity (watch closely)
- **2.0x+** = Suspicious spike (possible FII/DII moves)

### FII/DII Indicators
- **Strong Buying** = Institutions accumulating (bullish)
- **Heavy Selling** = Institutions distributing (bearish)
- **Normal Activity** = Wait for clear trend

### Market Movement Alerts
- **< 1%** = Normal daily fluctuation
- **1-2%** = Moderate move (monitor)
- **> 2%** = Significant move (requires attention)
- **> 3%** = Major event (investigate immediately)

## 🤝 Contributing

Found a bug or want to add features?

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m "Add feature"`
4. Push: `git push origin feature-name`
5. Create Pull Request

## 📄 License

MIT License - Free to use and modify

## ⚠️ Disclaimer

**Important**: This bot provides information for educational purposes only. 

- ❌ **NOT financial advice**
- ❌ **NOT investment recommendations**
- ✅ **Do your own research**
- ✅ **Consult licensed financial advisors**
- ✅ **Understand risks before investing**

Past performance does not guarantee future results. Markets are subject to risks.

## 🙏 Credits

**Data Sources**:
- Yahoo Finance (Market Data)
- MoneyControl
- Bloomberg
- Economic Times
- LiveMint
- Reuters
- NewsAPI

**Built With**:
- Python 3.9
- pyTelegramBotAPI
- yfinance
- feedparser
- BeautifulSoup4
- GitHub Actions

---

## 📞 Support

- **Issues**: Open a GitHub issue
- **Questions**: Check existing issues first
- **Updates**: Watch repository for updates

**Repository**: https://github.com/vignesh12116145-rgb/My-Market

---

**Made with ❤️ for financial market enthusiasts**

*Stay informed. Stay ahead.* 📈
