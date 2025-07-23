from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime
import os

# অ্যাডমিন টেলিগ্রাম ID (আপনারটা দিন)
ADMIN_ID = 6796353433  # <-- আপনার টেলিগ্রাম আইডি

# ইউজার ডেটা
user_data = {}
today_code = ""  # আজকের ভিডিও কোড
DAILY_TAP_LIMIT = 5000
COINS_PER_TAP = 5
WATCH_REWARD = 5000

def today_str():
    return datetime.utcnow().strftime("%Y-%m-%d")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("স্বাগতম SA Tap বটে! আয় করতে /tap অথবা /watch <code> ব্যবহার করুন।")

async def tap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today = today_str()
    user = user_data.setdefault(user_id, {"tap": {}, "coins": 0, "watched": {}})
    taps = user["tap"].get(today, 0)

    if taps * COINS_PER_TAP >= DAILY_TAP_LIMIT:
        await update.message.reply_text("❌ আজকের ট্যাপ লিমিট শেষ। কাল আবার আসুন।")
        return

    user["tap"][today] = taps + 1
    user["coins"] += COINS_PER_TAP
    await update.message.reply_text(f"✅ ট্যাপ সফল! মোট কয়েন: {user['coins']}")

async def watch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global today_code
    user_id = update.effective_user.id
    if len(context.args) != 1:
        await update.message.reply_text("❗ কোড দিন: /watch <code>")
        return
    code = context.args[0]
    user = user_data.setdefault(user_id, {"tap": {}, "coins": 0, "watched": {}})
    today = today_str()

    if user["watched"].get(today):
        await update.message.reply_text("❌ আপনি আজ ইতিমধ্যে ভিডিও দেখেছেন।")
        return

    if code == today_code:
        user["coins"] += WATCH_REWARD
        user["watched"][today] = True
        await update.message.reply_text(f"🎉 সঠিক কোড! আপনি পেলেন {WATCH_REWARD} কয়েন। মোট: {user['coins']}")
    else:
        await update.message.reply_text("❌ ভুল কোড।")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = user_data.get(user_id, {"coins": 0})
    await update.message.reply_text(f"💰 আপনার মোট কয়েন: {user['coins']}")

async def setcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global today_code
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ আপনি এই কমান্ড ব্যবহার করতে পারবেন না।")
        return
    if len(context.args) != 1:
        await update.message.reply_text("❗ নতুন কোড দিন: /setcode <new_code>")
        return
    today_code = context.args[0]
    await update.message.reply_text(f"✅ আজকের কোড সেট করা হয়েছে: {today_code}")

# বট চালু
if __name__ == "__main__":
    TOKEN = "7932269020:AAHgy13mzJRJ3fx-FE9j9IyISVoV6LC0Rk4"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tap", tap))
    app.add_handler(CommandHandler("watch", watch))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("setcode", setcode))  # Admin only

    print("✅ Bot is running...")
    app.run_polling()
