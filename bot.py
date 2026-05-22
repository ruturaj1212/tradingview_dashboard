import telebot
import requests
import threading
import time
from datetime import datetime

# ========================
# CONFIG
# ========================
TELEGRAM_BOT_TOKEN = "8946149776:AAFPJtToVIjgJI01Lsra8Pyjzg_T2YgNGoQ"

# Groww Bearer Token
GROWW_ACCESS_TOKEN = "eyJraWQiOiJaTUtjVXciLCJhbGciOiJFUzI1NiJ9.eyJleHAiOjI1Njc4Mjk2MzAsImlhdCI6MTc3OTQyOTYzMCwibmJmIjoxNzc5NDI5NjMwLCJzdWIiOiJ7XCJ0b2tlblJlZklkXCI6XCI1NzliYTYxMy0zNDA0LTQwMmUtYjlmNC05NTk0NGFkZTVmZTRcIixcInZlbmRvckludGVncmF0aW9uS2V5XCI6XCJlMzFmZjIzYjA4NmI0MDZjODg3NGIyZjZkODQ5NTMxM1wiLFwidXNlckFjY291bnRJZFwiOlwiYjRmOTM2MGUtN2Q0MC00MjAzLWIzMDEtZGQwMjg5ZTFiNWYxXCIsXCJkZXZpY2VJZFwiOlwiYTY0MTI3NGUtN2Q1Yy01ODAwLTliZWYtOTk1YThjZmQ2MTBmXCIsXCJzZXNzaW9uSWRcIjpcImQ2NDllNDI5LWUxZDItNDlhZi1hZTdjLTA3YTkxMTI5NTNlYlwiLFwiYWRkaXRpb25hbERhdGFcIjpcIno1NC9NZzltdjE2WXdmb0gvS0EwYkk5Y2o3LzY2TkhZVjJGL3p0cld3MHhSTkczdTlLa2pWZDNoWjU1ZStNZERhWXBOVi9UOUxIRmtQejFFQisybTdRPT1cIixcInJvbGVcIjpcImF1dGgtdG90cFwiLFwic291cmNlSXBBZGRyZXNzXCI6XCI0OS4yMDQuOTQuMjIyLDE3Mi42OC4xNDcuMTk1LDM1LjI0MS4yMy4xMjNcIixcInR3b0ZhRXhwaXJ5VHNcIjoyNTY3ODI5NjMwNTA3LFwidmVuZG9yTmFtZVwiOlwiZ3Jvd3dBcGlcIn0iLCJpc3MiOiJhcGV4LWF1dGgtcHJvZC1hcHAifQ.TrPyf8k2gBJVBdlQIw9wL-Wc0CZ9jWD_gO0cfdc0lvZMArC5tq_k2kj63DFiyaboqjkjkIxGcHGaKh0XY0GKSw"

# ========================
# TELEGRAM BOT
# ========================
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# ========================
# GROWW API CONFIG
# ========================
BASE_URL = "https://api.groww.in/v1/live-data/ltp"

HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {GROWW_ACCESS_TOKEN}",
    "X-API-VERSION": "1.0"
}

# ========================
# INSTRUMENTS
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
# LIVE PRICE STORAGE
# ========================
current_prices = {
    "NIFTY": None,
    "BANKNIFTY": None,
    "SENSEX": None
}

# ========================
# ALERT STORAGE
# ========================
user_alerts = {}

# ========================
# FETCH LIVE PRICE
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
            timeout=5
        )

        data = response.json()

        print(f"{index_key} response:", data)

        if data.get("status") == "SUCCESS":

            payload = data.get("payload", {})

            if symbol in payload:
                price = float(payload[symbol])

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
    print("📡 Starting Groww live updates...")

    while True:
        for key in INDICES:
            fetch_price(key)

        time.sleep(2)

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

        data = response.json()

        print("Groww response:", data)

        if data.get("status") == "SUCCESS":
            print("✅ Groww API connected!")
            return True

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
                        f"🚨 ALERT\n\n{index_key} crossed {alert_price}\n\nCurrent Price: ₹{price:.2f}"
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

🕒 Time: {datetime.now().strftime('%H:%M:%S')}

━━━━━━━━━━━━━━

🎯 TRADE SETUP

SELL ENTRY: {entry}
STOP LOSS: {sl}

TARGET 1: {target1}
TARGET 2: {target2}

━━━━━━━━━━━━━━

📈 Resistance:
R1: {resistance1}
R2: {resistance2}

📉 Support:
S1: {support1}
S2: {support2}

━━━━━━━━━━━━━━

📊 Trend: {trend}

⚡ Source: Groww Live API
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
# NIFTY
# ========================
@bot.message_handler(commands=['nifty'])
def nifty_cmd(message):

    price = get_price("NIFTY")

    bot.reply_to(
        message,
        generate_analysis("NIFTY", price)
    )

# ========================
# BANKNIFTY
# ========================
@bot.message_handler(commands=['banknifty'])
def banknifty_cmd(message):

    price = get_price("BANKNIFTY")

    bot.reply_to(
        message,
        generate_analysis("BANKNIFTY", price)
    )

# ========================
# SENSEX
# ========================
@bot.message_handler(commands=['sensex'])
def sensex_cmd(message):

    price = get_price("SENSEX")

    bot.reply_to(
        message,
        generate_analysis("SENSEX", price)
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
# ALERT
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
        bot.reply_to(
            message,
            "Usage:\n/alert 25000"
        )

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
