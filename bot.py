import telebot
import requests
import json
import threading
import time
from datetime import datetime

# ========================
# CONFIGURATION
# ========================
TELEGRAM_BOT_TOKEN = "8946149776:AAFPJtToVIjgJI01Lsra8Pyjzg_T2YgNGoQ"
TWELVEDATA_API_KEY = "21dd0d043bc843c7923479ba7663112c"

# ========================
# TELEGRAM BOT SETUP
# ========================
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

user_alerts = {}

# ========================
# INDICES (Twelve Data Symbols)
# ========================
INDICES = {
    "NIFTY": {"symbol": "NIFTY", "name": "🇮🇳 NIFTY 50", "mult": 1},
    "SENSEX": {"symbol": "BSE:SENSEX", "name": "📈 SENSEX", "mult": 0.7},
    "BANKNIFTY": {"symbol": "NIFTY BANK", "name": "🏦 BANK NIFTY", "mult": 2.5},
}

# Live price storage
current_prices = {
    "NIFTY": None,
    "SENSEX": None,
    "BANKNIFTY": None
}

# ========================
# FETCH PRICE (REST API)
# ========================
def fetch_price(index_key):
    try:
        symbol = INDICES[index_key]["symbol"]
        url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={TWELVEDATA_API_KEY}"

        response = requests.get(url, timeout=5)
        data = response.json()

        price = data.get("price")

        if price:
            price = float(price)
            current_prices[index_key] = price
            return price
        else:
            print(f"⚠️ API response issue: {data}")
            return current_prices.get(index_key)

    except Exception as e:
        print(f"❌ Error fetching {index_key}: {e}")
        return current_prices.get(index_key)

# ========================
# BACKGROUND PRICE UPDATER
# ========================
def price_updater():
    print("📡 Starting price updater (Twelve Data)...")
    while True:
        for key in INDICES:
            fetch_price(key)
        time.sleep(2)  # update every 2 seconds

# ========================
# GET PRICE
# ========================
def get_price(index_key):
    price = current_prices.get(index_key)
    if price and price > 0:
        return price
    return fetch_price(index_key)

# ========================
# TEST CONNECTION
# ========================
def test_connection():
    try:
        url = f"https://api.twelvedata.com/price?symbol=NIFTY_50&apikey={TWELVEDATA_API_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()

        if "price" in data:
            print(f"✅ Twelve Data API working! NIFTY: {data['price']}")
            return True
        else:
            print("❌ API error:", data)
            return False

    except Exception as e:
        print("❌ Connection failed:", e)
        return False

# ========================
# ALERT SYSTEM
# ========================
def check_alerts(index_key, price):
    for chat_id, alerts in user_alerts.items():
        if index_key not in alerts:
            continue

        for alert_price in alerts[index_key][:]:
            if price >= alert_price:
                try:
                    bot.send_message(
                        chat_id,
                        f"🚨 ALERT: {index_key} crossed {alert_price}\n📊 Current: ₹{price:.2f}"
                    )
                    alerts[index_key].remove(alert_price)
                except:
                    pass

# ========================
# ANALYSIS ENGINE
# ========================
def generate_analysis(index_key, price):
    if not price:
        return f"❌ No price data for {index_key}"

    mult = INDICES[index_key]["mult"]

    resistance1 = round(price + (35 * mult))
    resistance2 = round(price + (70 * mult))
    support1 = round(price - (40 * mult))
    support2 = round(price - (100 * mult))

    entry = round(price + (20 * mult))
    sl = round(price + (70 * mult))
    target1 = round(price - (45 * mult))
    target2 = round(price - (95 * mult))

    trend = "🚀 BULLISH" if price > resistance2 else "📉 BEARISH"

    return f"""
📊 {index_key} ANALYSIS

📍 Price: ₹{price:.2f}
📅 {datetime.now().strftime('%H:%M:%S')}

🎯 SELL SETUP
Entry: {entry}
SL: {sl}
Target 1: {target1}
Target 2: {target2}

📈 Trend: {trend}
📊 Resistance: {resistance1} | {resistance2}
📉 Support: {support1} | {support2}

⚡ Data: Twelve Data REST API
"""

# ========================
# TELEGRAM COMMANDS
# ========================
@bot.message_handler(commands=['start', 'help'])
def help_cmd(message):
    bot.reply_to(message, """
🤖 Trading Bot (Twelve Data)

Commands:
/nifty
/sensex
/banknifty
/live
/alert 23500
""")

@bot.message_handler(commands=['nifty'])
def nifty(message):
    price = get_price("NIFTY")
    bot.reply_to(message, generate_analysis("NIFTY", price))

@bot.message_handler(commands=['sensex'])
def sensex(message):
    price = get_price("SENSEX")
    bot.reply_to(message, generate_analysis("SENSEX", price))

@bot.message_handler(commands=['banknifty'])
def banknifty(message):
    price = get_price("BANKNIFTY")
    bot.reply_to(message, generate_analysis("BANKNIFTY", price))

@bot.message_handler(commands=['live'])
def live(message):
    text = "📊 LIVE PRICES\n\n"
    for k in INDICES:
        price = get_price(k)
        text += f"{INDICES[k]['name']}: ₹{price}\n"
    bot.reply_to(message, text)

@bot.message_handler(commands=['alert'])
def alert(message):
    try:
        price_level = float(message.text.split()[1])
        chat_id = message.chat.id

        if chat_id not in user_alerts:
            user_alerts[chat_id] = {}

        if "NIFTY" not in user_alerts[chat_id]:
            user_alerts[chat_id]["NIFTY"] = []

        user_alerts[chat_id]["NIFTY"].append(price_level)

        bot.reply_to(message, f"✅ Alert set at {price_level}")

    except:
        bot.reply_to(message, "Usage: /alert 23500")

# ========================
# START BOT
# ========================
if __name__ == "__main__":
    print("🤖 Starting bot...")

    if test_connection():
        print("✅ API OK")

        # Start price updater thread
        threading.Thread(target=price_updater, daemon=True).start()

        print("🚀 Bot running...")
        bot.infinity_polling()

    else:
        print("❌ Fix API key or internet connection")
