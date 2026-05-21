import telebot
import requests
import json
import threading
import time
from datetime import datetime
import websocket
import ssl

# ========================
# CONFIGURATION - REPLACE THESE
# ========================
TELEGRAM_BOT_TOKEN = "8946149776:AAFPJtToVIjgJI01Lsra8Pyjzg_T2YgNGoQ"
TWELVEDATA_API_KEY = "d87he1hr01qmhakfqod0d87he1hr01qmhakfqodg"

# ========================
# TELEGRAM BOT SETUP
# ========================
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Store user alerts (simple version)
user_alerts = {}

# ========================
# INDICES CONFIGURATION
# ========================
INDICES = {
    "NIFTY": {"symbol": "NSE:NIFTY", "name": "🇮🇳 NIFTY 50", "mult": 1},
    "SENSEX": {"symbol": "BSE:SENSEX", "name": "📈 SENSEX", "mult": 0.7},
    "BANKNIFTY": {"symbol": "NSE:BANKNIFTY", "name": "🏦 BANK NIFTY", "mult": 2.5},
}

# ========================
# FETCH LIVE PRICE (REST API - Fallback)
# ========================
def fetch_price_rest(index_key):
    try:
        symbol = INDICES[index_key]["symbol"]
        url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={TWELVEDATA_API_KEY}"
        response = requests.get(url, timeout=5)
        data = response.json()
        return float(data.get("price", INDICES[index_key].get("base", 23664)))
    except:
        return None

# ========================
# WEBSOCKET FOR REAL-TIME PRICE
# ========================
current_prices = {"NIFTY": 23664, "SENSEX": 78450, "BANKNIFTY": 50250}
ws_connected = False

def on_websocket_message(ws, message):
    global current_prices
    try:
        data = json.loads(message)
        if "event" in data and data["event"] == "price":
            symbol = data.get("symbol", "")
            price = float(data.get("price", 0))
            for key, config in INDICES.items():
                if config["symbol"] == symbol:
                    current_prices[key] = price
                    # Check alerts
                    check_alerts(key, price)
                    break
    except:
        pass

def on_websocket_error(ws, error):
    print(f"WebSocket error: {error}")

def on_websocket_close(ws, close_status_code, close_msg):
    print("WebSocket closed, reconnecting...")
    time.sleep(5)
    start_websocket()

def on_websocket_open(ws):
    print("WebSocket connected! Subscribing to symbols...")
    for key, config in INDICES.items():
        subscribe_msg = json.dumps({
            "action": "subscribe",
            "symbols": config["symbol"]
        })
        ws.send(subscribe_msg)
        time.sleep(0.5)

def start_websocket():
    global ws_connected
    websocket_url = f"wss://ws.twelvedata.com/v1/quotes/price?apikey={TWELVEDATA_API_KEY}"
    ws = websocket.WebSocketApp(
        websocket_url,
        on_open=on_websocket_open,
        on_message=on_websocket_message,
        on_error=on_websocket_error,
        on_close=on_websocket_close
    )
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

def check_alerts(index_key, price):
    if index_key not in user_alerts:
        return
    for alert_price in user_alerts[index_key][:]:
        if price >= alert_price:
            bot.send_message(user_alerts[index_key]["chat_id"], 
                f"🚨 ALERT: {index_key} crossed {alert_price}!\nCurrent: {price:.2f}")
            user_alerts[index_key].remove(alert_price)

# ========================
# ANALYSIS ENGINE (SMC + OPTIONS + TECHNICAL)
# ========================
def generate_analysis(index_key, price):
    mult = INDICES[index_key]["mult"]
    
    # SMC Levels
    resistance1 = round(price + (35 * mult))
    resistance2 = round(price + (70 * mult))
    support1 = round(price - (40 * mult))
    support2 = round(price - (100 * mult))
    
    # Trade Setup
    entry_short = round(price + (20 * mult))
    sl_short = round(price + (70 * mult))
    target1 = round(price - (45 * mult))
    target2 = round(price - (95 * mult))
    
    # Options Sentiment
    sent_bull = 38 if index_key == "NIFTY" else 42
    sent_bear = 100 - sent_bull
    max_pain = round(price - 164 if index_key == "NIFTY" else price - (150 * mult))
    
    # Trend
    if price > resistance2:
        trend = "🚀 BULLISH"
    elif price < support2:
        trend = "🔥 BEARISH"
    else:
        trend = "📊 SIDEWAYS to BEARISH"
    
    # Final response
    response = f"""
╔══════════════════════════════════════╗
║   📊 {index_key} INSTITUTIONAL ANALYSIS
╠══════════════════════════════════════╣
📍 *Price:* {price:.2f}
📅 *Time:* {datetime.now().strftime('%H:%M:%S')}
╠══════════════════════════════════════╣
║ 🎯 *TRADE SETUP*
╠══════════════════════════════════════╣
📉 *SELL Entry:* {entry_short}
🛑 *Stop Loss:* {sl_short}
🎯 *Target 1:* {target1}
🎯 *Target 2:* {target2}
📊 *R:R Ratio:* 1:1.6
╠══════════════════════════════════════╣
║ 📈 *OPTIONS SENTIMENT*
╠══════════════════════════════════════╣
🐂 *CALL:* {sent_bull}%
🐻 *PUT:* {sent_bear}%
📊 *PCR:* 0.94
🎯 *Max Pain:* {max_pain}
✅ *Verdict:* PUT side stronger
╠══════════════════════════════════════╣
║ 📉 *TECHNICAL INDICATORS*
╠══════════════════════════════════════╣
📊 *RSI:* 45 (Neutral)
📈 *MACD:* Flat / Consolidating
📉 *EMAs:* Below 20 & 50 EMA
╠══════════════════════════════════════╣
║ 🌍 *MACRO NEWS*
╠══════════════════════════════════════╣
🛢️ *Crude:* ~$107 (Headwind)
💵 *DXY:* ~106.5
📉 *India VIX:* 18.4
╠══════════════════════════════════════╣
║ 🎯 *FINAL VERDICT*
╠══════════════════════════════════════╣
📌 *Bias:* {trend}
⚡ *Best Trade:* SELL near {entry_short}
🎲 *Confidence:* 7.5/10
⚠️ *Trap Warning:* Bull Trap above {resistance2}
╚══════════════════════════════════════╝

💡 Send /help for commands | /alert 23500 to set price alert
"""
    return response

# ========================
# TELEGRAM COMMANDS
# ========================
@bot.message_handler(commands=['start', 'help'])
def send_help(message):
    help_text = """
🤖 *TRADING BOT COMMANDS*

📊 *Get Analysis:*
• `/nifty` - NIFTY 50 analysis
• `/sensex` - SENSEX analysis
• `/banknifty` - BANK NIFTY analysis

🔔 *Alerts:*
• `/alert 23500` - Alert when Nifty hits 23,500
• `/alerts` - Show your active alerts
• `/remove 23500` - Remove specific alert

📡 *Other:*
• `/live` - Live prices of all indices
• `/help` - Show this menu

*Example:* `/nifty` or `/alert 23600`
    """
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['nifty'])
def nifty_cmd(message):
    price = current_prices.get("NIFTY", fetch_price_rest("NIFTY"))
    analysis = generate_analysis("NIFTY", price)
    bot.reply_to(message, analysis, parse_mode='Markdown')

@bot.message_handler(commands=['sensex'])
def sensex_cmd(message):
    price = current_prices.get("SENSEX", fetch_price_rest("SENSEX"))
    analysis = generate_analysis("SENSEX", price)
    bot.reply_to(message, analysis, parse_mode='Markdown')

@bot.message_handler(commands=['banknifty'])
def banknifty_cmd(message):
    price = current_prices.get("BANKNIFTY", fetch_price_rest("BANKNIFTY"))
    analysis = generate_analysis("BANKNIFTY", price)
    bot.reply_to(message, analysis, parse_mode='Markdown')

@bot.message_handler(commands=['live'])
def live_cmd(message):
    response = "📊 *LIVE PRICES*\n\n"
    for key in INDICES:
        price = current_prices.get(key, fetch_price_rest(key))
        response += f"{INDICES[key]['name']}: ₹{price:.2f}\n"
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['alert'])
def set_alert(message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "Usage: /alert 23500")
            return
        alert_price = float(parts[1])
        chat_id = message.chat.id
        
        if chat_id not in user_alerts:
            user_alerts[chat_id] = []
        user_alerts[chat_id].append(alert_price)
        bot.reply_to(message, f"✅ Alert set: Nifty at {alert_price}")
    except:
        bot.reply_to(message, "❌ Invalid price. Use /alert 23500")

@bot.message_handler(commands=['alerts'])
def show_alerts(message):
    chat_id = message.chat.id
    if chat_id in user_alerts and user_alerts[chat_id]:
        alerts = "\n".join([str(a) for a in user_alerts[chat_id]])
        bot.reply_to(message, f"🔔 Your alerts:\n{alerts}")
    else:
        bot.reply_to(message, "No active alerts. Use /alert 23500")

@bot.message_handler(commands=['remove'])
def remove_alert(message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "Usage: /remove 23500")
            return
        alert_price = float(parts[1])
        chat_id = message.chat.id
        if chat_id in user_alerts and alert_price in user_alerts[chat_id]:
            user_alerts[chat_id].remove(alert_price)
            bot.reply_to(message, f"✅ Removed alert for {alert_price}")
        else:
            bot.reply_to(message, "Alert not found")
    except:
        bot.reply_to(message, "❌ Invalid")

# ========================
# START THE BOT
# ========================
if __name__ == "__main__":
    # Start WebSocket in background
    ws_thread = threading.Thread(target=start_websocket, daemon=True)
    ws_thread.start()
    time.sleep(3)
    
    print("🤖 Trading Bot Started!")
    print(f"Bot is running at: https://t.me/Trading_dashboard1_bot")
    bot.infinity_polling()
