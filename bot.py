import telebot
import requests
import threading
import time
import os
from datetime import datetime

# ========================
# CONFIG
# ========================


import sys

TELEGRAM_BOT_TOKEN = "8946149776:AAFPJtToVIjgJI01Lsra8Pyjzg_T2YgNGoQ"
GROWW_ACCESS_TOKEN = "eyJraWQiOiJaTUtjVXciLCJhbGciOiJFUzI1NiJ9.eyJleHAiOjI1Njc4MzYyODksImlhdCI6MTc3OTQzNjI4OSwibmJmIjoxNzc5NDM2Mjg5LCJzdWIiOiJ7XCJ0b2tlblJlZklkXCI6XCI1OTExMTJiYS0xZWFjLTQ1MWQtODczYy03NDRmZGFlZWY1ZDdcIixcInZlbmRvckludGVncmF0aW9uS2V5XCI6XCJlMzFmZjIzYjA4NmI0MDZjODg3NGIyZjZkODQ5NTMxM1wiLFwidXNlckFjY291bnRJZFwiOlwiYjRmOTM2MGUtN2Q0MC00MjAzLWIzMDEtZGQwMjg5ZTFiNWYxXCIsXCJkZXZpY2VJZFwiOlwiYTY0MTI3NGUtN2Q1Yy01ODAwLTliZWYtOTk1YThjZmQ2MTBmXCIsXCJzZXNzaW9uSWRcIjpcIjAzYzhkNTVkLTkxZGQtNDhlZi1hMzVlLWViN2VjZTUzMzE5NFwiLFwiYWRkaXRpb25hbERhdGFcIjpcIno1NC9NZzltdjE2WXdmb0gvS0EwYkk5Y2o3LzY2TkhZVjJGL3p0cld3MHhSTkczdTlLa2pWZDNoWjU1ZStNZERhWXBOVi9UOUxIRmtQejFFQisybTdRPT1cIixcInJvbGVcIjpcImF1dGgtdG90cFwiLFwic291cmNlSXBBZGRyZXNzXCI6XCIyMDMuOTIuNjIuMTMwLDE3Mi43MC4yMTguODgsMzUuMjQxLjIzLjEyM1wiLFwidHdvRmFFeHBpcnlUc1wiOjI1Njc4MzYyODk4NzcsXCJ2ZW5kb3JOYW1lXCI6XCJncm93d0FwaVwifSIsImlzcyI6ImFwZXgtYXV0aC1wcm9kLWFwcCJ9.6T3-xb36ZcD9rc0ik-yD97g6WueoYorqqrLF_LBCJJYT_qtjHJu8i36cY3wYsz2lBTR5cuVLkY-w7N9wAX52Pw"

if not TELEGRAM_BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN missing")
    sys.exit()

if not GROWW_ACCESS_TOKEN:
    print("❌ GROWW_ACCESS_TOKEN missing")
    sys.exit()

TELEGRAM_BOT_TOKEN = "8946149776:AAFPJtToVIjgJI01Lsra8Pyjzg_T2YgNGoQ"
GROWW_ACCESS_TOKEN = "1gUnYn&(_Ce*7C@-(5M!%m$OZSBKbpS8"

# ========================
# TELEGRAM BOT
# ========================

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# ========================
# GROWW API
# ========================

BASE_URL = "https://api.groww.in/v1/live-data/ltp"

HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {GROWW_ACCESS_TOKEN}",
    "X-API-VERSION": "1.0"
}

# ========================
# INDICES
# ========================

INDICES = {
    "NIFTY": {
        "symbol": "NSE_NIFTY",
        "name": "🇮🇳 NIFTY 50",
        "mult": 1
    },
    "BANKNIFTY": {
        "symbol": "NSE_BANKNIFTY",
        "name": "🏦 BANK NIFTY",
        "mult": 2.5
    },
    "SENSEX": {
        "symbol": "BSE_SENSEX",
        "name": "📈 SENSEX",
        "mult": 0.7
    }
}

# ========================
# STORAGE
# ========================

current_prices = {
    "NIFTY": None,
    "BANKNIFTY": None,
    "SENSEX": None
}

user_alerts = {}

# ========================
# FETCH PRICE
# ========================

def fetch_price(index_key):

    try:

        symbol = INDICES[index_key]["symbol"]

        params = {
            "segment": "CASH",
            "exchange_symbols": symbol
        }

        response = requests.get(
            BASE_URL,
            headers=HEADERS,
            params=params,
            timeout=10
        )

        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return current_prices.get(index_key)

        data = response.json()

        print(f"📡 {index_key}:", data)

        if data.get("status") != "SUCCESS":
            print(f"❌ API Error: {data}")
            return current_prices.get(index_key)

        payload = data.get("payload", {})

        # safer parsing
        price = None

        if isinstance(payload, dict):

            if symbol in payload:
                price = payload[symbol]

            elif "last_price" in payload:
                price = payload["last_price"]

        if price:

            price = float(price)

            current_prices[index_key] = price

            check_alerts(index_key, price)

            return price

        return current_prices.get(index_key)

    except Exception as e:
        print(f"❌ Error fetching {index_key}: {e}")
        return current_prices.get(index_key)

# ========================
# BACKGROUND UPDATER
# ========================

def price_updater():

    print("📡 Live updater started...")

    while True:

        try:

            for key in INDICES:
                fetch_price(key)

            time.sleep(2)

        except Exception as e:
            print("❌ Updater crash:", e)
            time.sleep(5)

# ========================
# GET PRICE
# ========================

def get_price(index_key):

    price = current_prices.get(index_key)

    if price:
        return price

    return fetch_price(index_key)

# ========================
# TEST CONNECTION
# ========================

def test_connection():

    try:

        params = {
            "segment": "CASH",
            "exchange_symbols": "NSE_NIFTY"
        }

        response = requests.get(
            BASE_URL,
            headers=HEADERS,
            params=params,
            timeout=10
        )

        print("📡 Raw Response:", response.text)

        if response.status_code == 200:
            print("✅ Groww API connected!")
            return True

        print("❌ API connection failed")
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
                        f"""
🚨 ALERT TRIGGERED

📊 {index_key}
🎯 Target: ₹{alert_price}
💰 Current: ₹{price:.2f}
"""
                    )

                    alerts[index_key].remove(alert_price)

                except Exception as e:
                    print("❌ Alert error:", e)

# ========================
# ANALYSIS ENGINE
# ========================

def generate_analysis(index_key, price):

    if not price:
        return "❌ Price unavailable"

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

💰 Price: ₹{price:.2f}
🕒 {datetime.now().strftime('%H:%M:%S')}

━━━━━━━━━━━━━━

🎯 TRADE SETUP

SELL ENTRY: {entry}
STOP LOSS: {sl}

TARGET 1: {target1}
TARGET 2: {target2}

━━━━━━━━━━━━━━

📈 RESISTANCE
R1: {resistance1}
R2: {resistance2}

📉 SUPPORT
S1: {support1}
S2: {support2}

━━━━━━━━━━━━━━

📊 TREND: {trend}

⚡ Source: Groww API
"""

# ========================
# COMMANDS
# ========================

@bot.message_handler(commands=['start', 'help'])
def help_cmd(message):

    bot.reply_to(
        message,
        """
🤖 Groww Trading Bot

Commands:

/nifty
/banknifty
/sensex
/live
/alert 25000
"""
    )

# ========================
# LIVE
# ========================

@bot.message_handler(commands=['live'])
def live_cmd(message):

    text = "📊 LIVE MARKET\n\n"

    for key in INDICES:

        price = get_price(key)

        if price:
            text += f"{INDICES[key]['name']}: ₹{price:.2f}\n"
        else:
            text += f"{INDICES[key]['name']}: ❌ unavailable\n"

    text += f"\n🕒 {datetime.now().strftime('%H:%M:%S')}"

    bot.reply_to(message, text)

# ========================
# INDEX COMMANDS
# ========================

@bot.message_handler(commands=['nifty'])
def nifty_cmd(message):
    bot.reply_to(
        message,
        generate_analysis("NIFTY", get_price("NIFTY"))
    )

@bot.message_handler(commands=['banknifty'])
def banknifty_cmd(message):
    bot.reply_to(
        message,
        generate_analysis("BANKNIFTY", get_price("BANKNIFTY"))
    )

@bot.message_handler(commands=['sensex'])
def sensex_cmd(message):
    bot.reply_to(
        message,
        generate_analysis("SENSEX", get_price("SENSEX"))
    )

# ========================
# ALERT COMMAND
# ========================

@bot.message_handler(commands=['alert'])
def alert_cmd(message):

    try:

        price_level = float(message.text.split()[1])

        chat_id = message.chat.id

        if chat_id not in user_alerts:
            user_alerts[chat_id] = {}

        if "NIFTY" not in user_alerts[chat_id]:
            user_alerts[chat_id]["NIFTY"] = []

        user_alerts[chat_id]["NIFTY"].append(price_level)

        bot.reply_to(
            message,
            f"✅ Alert added at ₹{price_level}"
        )

    except:
        bot.reply_to(message, "Usage: /alert 25000")

# ========================
# MAIN
# ========================

if __name__ == "__main__":

    print("🤖 Starting Groww Trading Bot...")

    if test_connection():

        threading.Thread(
            target=price_updater,
            daemon=True
        ).start()

        print("🚀 Bot running...")

        bot.infinity_polling()

    else:
        print("❌ Could not connect to Groww API")
