from datetime import datetime, timezone
import os

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# 🛂  Admin Telegram user-id
ADMIN_ID = 6796353433          # <-- এখানে আপনার অ্যাডমিন আইডি রাখুন

# 🎮  গ্লোবাল স্টোরেজ (RAM-এ, রিস্টার্ট দিলে মুছে যাবে)
user_data = {}
today_code = ""

# 📊  কনফিগ
DAILY_TAP_LIMIT = 5_000        # এক দিনে ট্যাপ থেকে সর্বোচ্চ কয়েন
COINS_PER_TAP   = 5            # প্রতি ট্যাপে কয়েন
WATCH_REWARD    = 5_000        # সঠিক কোড দিলে কয়েন

# ---------- সহায়ক ফাংশন ----------
def today_str() -> str:
    """UTC তারিখ স্ট্রিং ফিরিয়ে দেয়, রিসেটের জন্য সুবিধা।"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ---------- কমান্ড হ্যান্ডলার ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 স্বাগতম **SA Tap**-এ!\n"
        "ট্যাপ করতে `/tap` \n"
        "ভিডিও দেখে পুরস্কার পেতে `/watch <code>`\n"
        "ব্যালান্স দেখতে `/balance`",
        parse_mode="Markdown",
    )


async def tap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today   = today_str()

    user = user_data.setdefault(user_id, {"tap": {}, "coins": 0, "watched": {}})
    taps = user["tap"].get(today, 0)

    if taps * COINS_PER_TAP >= DAILY_TAP_LIMIT:
        await update.message.reply_text("❌ আজকের ট্যাপ-লিমিট শেষ। কাল আবার চেষ্টা করুন।")
        return

    user["tap"][today] = taps + 1
    user["coins"] += COINS_PER_TAP
    await update.message.reply_text(f"✅ ট্যাপ গৃহীত! মোট কয়েন: {user['coins']}")


async def watch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global today_code

    user_id = update.effective_user.id
    if len(context.args) != 1:
        await update.message.reply_text("❗ সঠিক ফরম্যাট: `/watch <code>`", parse_mode="Markdown")
        return

    code  = context.args[0]
    today = today_str()

    user = user_data.setdefault(user_id, {"tap": {}, "coins": 0, "watched": {}})

    if user["watched"].get(today):
        await update.message.reply_text("❌ আপনি আজ ইতিমধ্যে ভিডিও-রিওয়ার্ড নিয়েছেন।")
        return

    if code == today_code:
        user["coins"] += WATCH_REWARD
        user["watched"][today] = True
        await update.message.reply_text(
            f"🎉 সঠিক কোড! আপনি পেলেন {WATCH_REWARD} কয়েন। মোট: {user['coins']}"
        )
    else:
        await update.message.reply_text("❌ ভুল কোড।")


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    coins   = user_data.get(user_id, {}).get("coins", 0)
    await update.message.reply_text(f"💰 আপনার মোট কয়েন: {coins}")


async def setcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global today_code

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ আপনি এই কমান্ড ব্যবহার করতে পারবেন না।")
        return
    if len(context.args) != 1:
        await update.message.reply_text("ব্যবহার: `/setcode <code>`", parse_mode="Markdown")
        return

    today_code = context.args[0]
    await update.message.reply_text(f"✅ আজকের কোড সেট হয়েছে: `{today_code}`", parse_mode="Markdown")


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """প্রতি রাত ১২টায় (বা অ্যাডমিন চাইলে) দৈনিক লিমিট রিসেট করার কমান্ড।"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ আপনি এই কমান্ড ব্যবহার করতে পারবেন না।")
        return

    today = today_str()
    for u in user_data.values():
        u["tap"][today]      = 0
        u["watched"][today]  = False
    await update.message.reply_text("🔄 দৈনিক ডেটা রিসেট হয়েছে।")


# ---------- বট চালু ----------
if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise RuntimeError("⚠️ পরিবেশ-চেঞ্জে BOT_TOKEN সেট করা নেই।")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("tap",      tap))
    app.add_handler(CommandHandler("watch",    watch))
    app.add_handler(CommandHandler("balance",  balance))
    app.add_handler(CommandHandler("setcode",  setcode))
    app.add_handler(CommandHandler("reset",    reset))

    print("🤖 SA Tap Bot is running…")
    app.run_polling()
