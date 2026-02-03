import telebot
from telebot import types
import os

# --- CONFIGURATION ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

# 1. MAIN MENU BUILDER
def main_menu():
    """Creates the main persistent menu for the user."""
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    
    # Adding buttons for different sectors
    btn1 = types.KeyboardButton("📊 Market Overview")
    btn2 = types.KeyboardButton("🏛️ FII / DII Flows")
    btn3 = types.KeyboardButton("🌍 Global News")
    btn4 = types.KeyboardButton("🤖 AI & FinTech")
    btn5 = types.KeyboardButton("🏥 Health & Pharma")
    btn6 = types.KeyboardButton("📈 Derivatives")
    btn7 = types.KeyboardButton("💱 Currencies")
    btn8 = types.KeyboardButton("🥇 Commodities")
    btn9 = types.KeyboardButton("🚨 Breaking News")
    
    keyboard.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8, btn9)
    return keyboard

# 2. INLINE ACTION MENU (Example for Market Sub-menu)
def market_submenu():
    """Creates a sub-menu using inline buttons for specific market segments."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    item1 = types.InlineKeyboardButton("Nifty 50", callback_data='nifty_50')
    item2 = types.InlineKeyboardButton("Bank Nifty", callback_data='bank_nifty')
    item3 = types.InlineKeyboardButton("Sensex", callback_data='sensex')
    item4 = types.InlineKeyboardButton("Top Gainer/Loser", callback_data='top_movers')
    markup.add(item1, item2, item3, item4)
    return markup

# --- HANDLERS ---

@bot.message_handler(commands=['start', 'menu'])
def welcome(message):
    bot.reply_to(
        message, 
        "👋 *Market Advisor Hub*\nYour all-in-one place for Indian & Global insights.", 
        reply_markup=main_menu(), 
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: True)
def handle_menu_clicks(message):
    """Handles logic for each menu button."""
    chat_id = message.chat.id
    text = message.text
    
    if text == "📊 Market Overview":
        bot.send_message(chat_id, "Select Segment:", reply_markup=market_submenu())
    
    elif text == "🏛️ FII / DII Flows":
        # Placeholder for your scraping function
        bot.send_message(chat_id, "🔍 Fetching latest FII/DII Net Activity...")
        # get_fii_dii_data() would go here
    
    elif text == "🤖 AI & FinTech":
        bot.send_message(chat_id, "📝 *Deep Info (FinTech):*\nGenerating elaborate report...")
        # get_elaborate_news('fintech') would go here
        
    elif text == "🚨 Breaking News":
        bot.send_message(chat_id, "📡 *Scanning Bloomberg & MoneyControl...*")

# 3. CALLBACK HANDLER FOR INLINE BUTTONS
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "nifty_50":
        # Call your existing function for Nifty
        bot.answer_callback_query(call.id, "Loading Nifty Data...")
        bot.send_message(call.message.chat.id, "Nifty 50: ₹24,150 (🟢 +0.45%)")

# --- EXECUTION ---
if __name__ == "__main__":
    print("Advisor Bot Online with Advanced Menu...")
    bot.infinity_polling()
