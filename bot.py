import telebot
import threading
import time
from datetime import datetime
from growwapi import GrowwAPI

# =========================
# CONFIG
# =========================

TELEGRAM_BOT_TOKEN = "8946149776:AAFPJtToVIjgJI01Lsra8Pyjzg_T2YgNGoQ"

GROWW_ACCESS_TOKEN = "eyJraWQiOiJaTUtjVXciLCJhbGciOiJFUzI1NiJ9.eyJleHAiOjI1Njc4Mzg2NDYsImlhdCI6MTc3OTQzODY0NiwibmJmIjoxNzc5NDM4NjQ2LCJzdWIiOiJ7XCJ0b2tlblJlZklkXCI6XCI4ZmU5NjMwYS1mZTkzLTQ3Y2YtODEzZS04MTZmMGQzZDQ4MmFcIixcInZlbmRvckludGVncmF0aW9uS2V5XCI6XCJlMzFmZjIzYjA4NmI0MDZjODg3NGIyZjZkODQ5NTMxM1wiLFwidXNlckFjY291bnRJZFwiOlwiYjRmOTM2MGUtN2Q0MC00MjAzLWIzMDEtZGQwMjg5ZTFiNWYxXCIsXCJkZXZpY2VJZFwiOlwiYTY0MTI3NGUtN2Q1Yy01ODAwLTliZWYtOTk1YThjZmQ2MTBmXCIsXCJzZXNzaW9uSWRcIjpcIjM3OTY4YzIyLTYyNzItNDBmZC04YjRmLWY2ODU3YjBmYWZjY1wiLFwiYWRkaXRpb25hbERhdGFcIjpcIno1NC9NZzltdjE2WXdmb0gvS0EwYkk5Y2o3LzY2TkhZVjJGL3p0cld3MHhSTkczdTlLa2pWZDNoWjU1ZStNZERhWXBOVi9UOUxIRmtQejFFQisybTdRPT1cIixcInJvbGVcIjpcImF1dGgtdG90cFwiLFwic291cmNlSXBBZGRyZXNzXCI6XCIyMDMuOTIuNjIuMTMwLDE3Mi43MC4yMTguMTM1LDM1LjI0MS4yMy4xMjNcIixcInR3b0ZhRXhwaXJ5VHNcIjoyNTY3ODM4NjQ2NjA3LFwidmVuZG9yTmFtZVwiOlwiZ3Jvd3dBcGlcIn0iLCJpc3MiOiJhcGV4LWF1dGgtcHJvZC1hcHAifQ.4GPZUI41074vOgb6YWYgcIm-6pLavElcSJlFJkUVYKfqtTdGD-ngT7azcPz5alcDFLR6TIkYlaSQAMOfDLBAzw"

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# =========================
# INIT GROWW CLIENT
# =========================

groww = GrowwAPI(GROWW_ACCESS_TOKEN)

# =========================
# SYMBOL MAP (IMPORTANT FIX)
# =========================

INDICES = {
    "NIFTY": {
        "exchange": groww.EXCHANGE_NSE,
        "segment": groww.SEGMENT_CASH,
        "symbol": "NIFTY"
    },
    "BANKNIFTY": {
        "exchange": groww.EXCHANGE_NSE,
        "segment": groww.SEGMENT_CASH,
        "symbol": "NIFTY BANK"
    },
    "SENSEX": {
        "exchange": groww.EXCHANGE_BSE,
        "segment": groww.SEGMENT_CASH,
        "symbol": "SENSEX"
    }
}

current_prices = {}
user_alerts = {}

# =========================
# FETCH PRICE (CORRECT SDK USAGE)
# =========================

def fetch_price(key):
    try:
        cfg = INDICES[key]

        quote = groww.get_quote(
            exchange=cfg["exchange"],
            segment=cfg["segment"],
            trading_symbol=cfg["symbol"]
        )

        price = quote.get("average_price") or quote.get("ltp") or quote.get("last_price")

        if price:
            price = float(price)
            current_prices[key] = price
            check_alerts(key, price)
            return price

    except Exception as e:
        print("Error:", key, e)

    return current_prices.get(key)


def get_price(key):
    return current_prices.get(key) or fetch_price(key)

# =========================
# ALERT SYSTEM
# =========================

def check_alerts(key, price):
    for chat_id, data in user_alerts.items():
        if key not in data:
            continue

        for level in data[key][:]:
            if price >= level:
                bot.send_message(chat_id,
                    f"🚨 {key} ALERT\nTarget: {level}\nPrice: {price}"
                )
                data[key].remove(level)

# =========================
# YOUR STRATEGY ENGINE
# =========================

def analysis(key, price):
    if not price:
        return "No price available"

    mult = 1 if key == "NIFTY" else 2.5

    r1 = price + 35 * mult
    r2 = price + 70 * mult
    s1 = price - 40 * mult
    s2 = price - 100 * mult

    entry = price + 20 * mult
    sl = price + 70 * mult
    t1 = price - 45 * mult
    t2 = price - 95 * mult

    trend = "BULLISH 🚀" if price > r2 else "BEARISH 📉"

    return f"""
📊 {key}

Price: {price:.2f}

ENTRY: {entry:.2f}
SL: {sl:.2f}
T1: {t1:.2f}
T2: {t2:.2f}

R1: {r1:.2f}
R2: {r2:.2f}

Trend: {trend}

⏱ {datetime.now().strftime('%H:%M:%S')}
"""

# =========================
# BACKGROUND UPDATER
# =========================

def updater():
    while True:
        for k in INDICES:
            fetch_price(k)
        time.sleep(2)

# =========================
# TELEGRAM COMMANDS
# =========================

@bot.message_handler(commands=['start', 'help'])
def help_cmd(msg):
    bot.reply_to(msg,
        "/nifty\n/banknifty\n/sensex\n/live\n/alert 25000"
    )


@bot.message_handler(commands=['nifty'])
def nifty(msg):
    bot.reply_to(msg, analysis("NIFTY", get_price("NIFTY")))


@bot.message_handler(commands=['banknifty'])
def bank(msg):
    bot.reply_to(msg, analysis("BANKNIFTY", get_price("BANKNIFTY")))


@bot.message_handler(commands=['sensex'])
def sensex(msg):
    bot.reply_to(msg, analysis("SENSEX", get_price("SENSEX")))


@bot.message_handler(commands=['live'])
def live(msg):
    text = "LIVE PRICES\n\n"
    for k in INDICES:
        text += f"{k}: {get_price(k)}\n"
    bot.reply_to(msg, text)


@bot.message_handler(commands=['alert'])
def alert(msg):
    try:
        level = float(msg.text.split()[1])
        chat_id = msg.chat.id

        user_alerts.setdefault(chat_id, {}).setdefault("NIFTY", []).append(level)

        bot.reply_to(msg, "Alert set!")

    except:
        bot.reply_to(msg, "Usage: /alert 25000")

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    print("Bot starting...")

    threading.Thread(target=updater, daemon=True).start()

    bot.infinity_polling()
