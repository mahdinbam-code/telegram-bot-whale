# ================== نصب پیش‌نیازها ==================
!pip install pyTelegramBotAPI requests beautifulsoup4 pillow websocket-client -q

# ================== ایمپورت ها ==================
import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import threading
import websocket
import json

# ================== کانفیگ ==================
TOKEN = "312461944:AAGiCvMtJpOdjrjQuwdCqp9NqTCoLeuDc6A"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# شناسه سازنده ربات
OWNER_ID = 359735994

# ================== ضد اسپم ==================
last_request_time = {}
def is_allowed(user_id, cooldown=2):
    now = datetime.now()
    if user_id in last_request_time:
        delta = now - last_request_time[user_id]
        if delta.total_seconds() < cooldown:
            return False
    last_request_time[user_id] = now
    return True

# ================== ارز دیجیتال ==================
CRYPTO_LIST = ["BTC", "ETH", "BNB", "XRP", "ADA", "DOGE", "SOL", "DOT", "LTC", "LINK",
               "MATIC", "TRX", "AVAX", "SHIB", "ATOM"]

user_state = {}

def get_crypto_data(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}USDT"
        r = requests.get(url, timeout=5).json()
        price = r.get("lastPrice", "❌")
        high = r.get("highPrice", "❌")
        low = r.get("lowPrice", "❌")
        vol = r.get("volume", "❌")
        tv_link = f"https://www.tradingview.com/chart/?symbol={symbol}USDT"
        msg = f"<b>{symbol}USDT</b>\n" \
              f"💰 قیمت: {price}\n" \
              f"📈 بالاترین ۲۴ ساعت: {high}\n" \
              f"📉 پایین‌ترین ۲۴ ساعت: {low}\n" \
              f"🔄 حجم معامله: {vol}\n" \
              f"<a href='{tv_link}'>مشاهده چارت در TradingView</a>"
        return msg
    except:
        return "❌ خطا در دریافت اطلاعات."

# ================== اخبار فارکس ==================
def get_forex_news():
    try:
        r = requests.get("https://nfs.faireconomy.media/ff_calendar_thisweek.xml", timeout=10)
        soup = BeautifulSoup(r.content, "xml")
        msg = "<b>📊 اخبار مهم فارکس این هفته:</b>\n\n"
        for e in soup.find_all('event')[:12]:
            impact = e.impact.text.strip() if e.impact else "Low"
            t = e.find("time").text.strip() if e.find("time") else "تمام روز"
            country = e.country.text.strip() if e.country else ""
            title = e.title.text.strip() if e.title else ""
            url = e.url.text.strip() if e.url else ""
            # تحلیل احتمالی اثر خبر
            analysis = f"🔹 اگر این خبر مثبت باشد → {country} احتمالاً رشد 📈\n" \
                       f"🔹 اگر منفی باشد → {country} احتمالاً ریزش 📉"
            # رنگبندی impact
            if impact.lower() == "high":
                imp_emoji = "🔴"
            elif impact.lower() == "medium":
                imp_emoji = "🟡"
            else:
                imp_emoji = "🟢"
            msg += f"{imp_emoji} {impact} | {t} | {country} | {title}\n{analysis}\n<a href='{url}'>لینک خبر</a>\n────────────────\n"
        return msg
    except:
        return "❌ خطا در دریافت اخبار."

# ================== وال‌ها (Whale Alerts) ==================
WH_CRYPTOS = ["BTCUSDT", "ETHUSDT", "XAUUSDT", "ADAUSDT", "TONUSDT", 
              "XRPUSDT", "DOGEUSDT", "ARBUSDT", "SOLUSDT", "LTCUSDT",
              "MATICUSDT", "TRXUSDT", "AVAXUSDT", "SHIBUSDT", "ATOMUSDT"]

WH_API_URL = "wss://ws.whale-alert.io/"  # فرضی، نمونه websocket
WH_SOURCE = "Whale Alert / Binance / Other Exchanges"

def on_whale_message(msg):
    data = json.loads(msg)
    try:
        symbol = data.get("symbol")
        amount = data.get("amount")
        direction = data.get("direction")  # buy/sell
        if symbol in WH_CRYPTOS:
            text = f"<b>⚡ هشدار وال‌ها</b>\nمنبع: {WH_SOURCE}\n" \
                   f"ارز: {symbol}\nمقدار: {amount}\nعملیات: {direction}"
            # ارسال به همه کاربران (در دیتابیس واقعی باید کاربران ثبت شوند)
            for uid in user_state.keys():
                bot.send_message(uid, text, parse_mode="HTML")
    except:
        pass

# ================== کیبوردها ==================
main_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add("💰 ارز دیجیتال", "📊 اخبار فارکس", "🐋 وال‌ها")

def crypto_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = [types.KeyboardButton(x) for x in CRYPTO_LIST]
    kb.add(*buttons)
    kb.add("جستجوی ارز دلخواه 🔍")
    kb.add("بازگشت 🔙")
    return kb

# ================== HANDLERS ==================
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "ربات فعال شد ✅", reply_markup=main_kb)

# ارز دیجیتال
@bot.message_handler(func=lambda m: m.text == "💰 ارز دیجیتال")
def crypto_main(message):
    if not is_allowed(message.from_user.id):
        bot.send_message(message.chat.id, "⏳ لطفاً کمی صبر کنید.")
        return
    bot.send_message(message.chat.id, "📊 لطفاً ارز مورد نظر را انتخاب کنید:", reply_markup=crypto_keyboard())

@bot.message_handler(func=lambda m: m.text in CRYPTO_LIST)
def crypto_select(message):
    user_state[message.from_user.id] = {"symbol": message.text}
    symbol = message.text
    msg = get_crypto_data(symbol)
    bot.send_message(message.chat.id, msg, parse_mode="HTML", disable_web_page_preview=False, reply_markup=crypto_keyboard())

@bot.message_handler(func=lambda m: m.text == "جستجوی ارز دلخواه 🔍")
def crypto_custom(message):
    msg = bot.send_message(message.chat.id, "نام ارز مورد نظر (نمونه: BTC) را وارد کنید:")
    bot.register_next_step_handler(msg, crypto_custom_step)

def crypto_custom_step(message):
    symbol = message.text.upper()
    msg = get_crypto_data(symbol)
    bot.send_message(message.chat.id, msg, parse_mode="HTML", disable_web_page_preview=False, reply_markup=crypto_keyboard())

# اخبار فارکس
@bot.message_handler(func=lambda m: m.text == "📊 اخبار فارکس")
def forex_news(message):
    if not is_allowed(message.from_user.id):
        bot.send_message(message.chat.id, "⏳ لطفاً کمی صبر کنید.")
        return
    news_msg = get_forex_news()
    bot.send_message(message.chat.id, news_msg, parse_mode="HTML", disable_web_page_preview=False)

# وال‌ها
@bot.message_handler(func=lambda m: m.text == "🐋 وال‌ها")
def whale_main(message):
    bot.send_message(message.chat.id, f"📡 دریافت هشدار وال‌ها از {WH_SOURCE}\n(این بخش در نسخه نهایی به صورت Real-Time فعال می‌شود)")

# بازگشت
@bot.message_handler(func=lambda m: m.text == "بازگشت 🔙")
def go_back(message):
    bot.send_message(message.chat.id, "🔙 به منوی اصلی برگشتید.", reply_markup=main_kb)

# ================== RUN ==================
print("ربات فعال شد — نسخه نهایی پایدار ✅")
bot.infinity_polling()
