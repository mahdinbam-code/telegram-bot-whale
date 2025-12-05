import telebot
from telebot import types
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# ================= CONFIG =================
TOKEN = "312461944:AAGiCvMtJpOdjrjQuwdCqp9NqTCoLeuDc6A"  # توکن رباتت
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ================= ضد اسپم =================
last_request_time = {}
def is_allowed(user_id):
    now = datetime.now()
    if user_id in last_request_time:
        delta = now - last_request_time[user_id]
        if delta.total_seconds() < 2:  # فاصله ۲ ثانیه
            return False
    last_request_time[user_id] = now
    return True

# ================= ارز دیجیتال =================
CRYPTO_LIST = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", 
               "SOLUSDT", "DOTUSDT", "LTCUSDT", "LINKUSDT", "MATICUSDT", "TRXUSDT",
               "AVAXUSDT", "SHIBUSDT", "ATOMUSDT"]
user_state = {}

def crypto_data(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        r = requests.get(url, timeout=10).json()
        price = r.get("lastPrice", "نامشخص")
        high = r.get("highPrice", "نامشخص")
        low = r.get("lowPrice", "نامشخص")
        vol = r.get("volume", "نامشخص")
        tv_link = f"https://www.tradingview.com/symbols/{symbol}/"
        msg = f"<b>{symbol}</b>\n" \
              f"💵 آخرین قیمت: {price}\n" \
              f"🔺 بالاترین 24ساعته: {high}\n" \
              f"🔻 پایین‌ترین 24ساعته: {low}\n" \
              f"📊 حجم معاملات 24ساعته: {vol}\n" \
              f"<a href='{tv_link}'>مشاهده چارت در تریدینگ ویو</a>"
        return msg
    except:
        return "❌ خطا در دریافت اطلاعات."

# ================= اخبار فارکس =================
def get_forex_news():
    try:
        r = requests.get("https://nfs.faireconomy.media/ff_calendar_thisweek.xml", timeout=10)
        soup = BeautifulSoup(r.content, "xml")
        msg = "📅 اخبار مهم فارکس این هفته:\n\n"
        for e in soup.find_all('event')[:12]:
            impact = e.impact.text.strip() if e.impact else "Low"
            t = e.find("time").text.strip() if e.find("time") else "تمام روز"
            country = e.country.text.strip() if e.country else ""
            title = e.title.text.strip() if e.title else ""
            url = e.url.text.strip() if e.url else ""
            analysis = f"🔹 اگر مثبت باشد → {country} احتمالاً رشد 📈\n" \
                       f"🔹 اگر منفی باشد → {country} احتمالاً ریزش 📉"
            color = "🟢" if impact=="High" else "🟡" if impact=="Medium" else "⚪"
            msg += f"{color} {impact} | {t} | {country} | {title}\n{analysis}\n<a href='{url}'>لینک خبر</a>\n────────────────\n"
        return msg
    except:
        return "❌ خطا در دریافت اخبار."

# ================= کیبوردها =================
main_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add("💰 ارز دیجیتال", "📊 اخبار فارکس", "بازگشت 🔙")

crypto_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
crypto_kb.add(*[types.KeyboardButton(x) for x in CRYPTO_LIST])
crypto_kb.add("جستجوی ارز دلخواه", "بازگشت 🔙")

# ================= HANDLERS =================
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "ربات فعال شد ✅", reply_markup=main_kb)

@bot.message_handler(func=lambda m: m.text == "💰 ارز دیجیتال")
def crypto_main(message):
    if not is_allowed(message.from_user.id):
        bot.send_message(message.chat.id, "⏳ لطفاً کمی صبر کنید.")
        return
    bot.send_message(message.chat.id, "📊 لطفاً ارز مورد نظر را انتخاب کنید:", reply_markup=crypto_kb)

@bot.message_handler(func=lambda m: m.text in CRYPTO_LIST)
def crypto_select(message):
    user_state[message.from_user.id] = {"symbol": message.text}
    symbol = message.text
    analysis_msg = crypto_data(symbol)
    bot.send_message(message.chat.id, analysis_msg, parse_mode="HTML", disable_web_page_preview=False, reply_markup=crypto_kb)
    user_state.pop(message.from_user.id, None)

@bot.message_handler(func=lambda m: m.text == "جستجوی ارز دلخواه")
def crypto_custom(message):
    bot.send_message(message.chat.id, "لطفاً نماد ارز را به صورت <code>BTCUSDT</code> وارد کنید:")

@bot.message_handler(func=lambda m: len(m.text) >= 3 and "USDT" in m.text.upper())
def crypto_input(message):
    symbol = message.text.upper()
    analysis_msg = crypto_data(symbol)
    bot.send_message(message.chat.id, analysis_msg, parse_mode="HTML", disable_web_page_preview=False, reply_markup=crypto_kb)

@bot.message_handler(func=lambda m: m.text == "📊 اخبار فارکس")
def forex_news(message):
    if not is_allowed(message.from_user.id):
        bot.send_message(message.chat.id, "⏳ لطفاً کمی صبر کنید.")
        return
    news_msg = get_forex_news()
    bot.send_message(message.chat.id, news_msg, parse_mode="HTML", disable_web_page_preview=False)

@bot.message_handler(func=lambda m: m.text == "بازگشت 🔙")
def go_back(message):
    bot.send_message(message.chat.id, "🔙 به منوی اصلی برگشتید.", reply_markup=main_kb)

# ================= RUN =================
print("ربات فعال شد — نسخه نهایی پایدار ✅")
bot.infinity_polling()
