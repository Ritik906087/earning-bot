import telebot
import json
import time
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

# ================= CONFIG =================

TOKEN = "8534248097:AAHwqpJMYRcjsBkd-7oODAlHygbXO40tmrs"
CHANNEL_ID = -1003856984651
CHANNEL_LINK = "https://t.me/DalyEarningOfficial"
ADMIN_ID = 8033702577

JOIN_REWARD = 5
REF_REWARD = 2
MIN_WITHDRAW = 10

# ==========================================

bot = telebot.TeleBot(TOKEN)

DB_FILE = "database.json"

waiting_upi = {}

# ================= DATABASE =================

def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ================= MENU =================

def menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("💰 Earn Money","👥 Refer & Earn")
    m.row("📊 Dashboard","💳 Withdraw")
    m.row("📢 Join Channel")
    return m

# ================= START =================

@bot.message_handler(commands=['start'])
def start(message):

    db = load_db()
    uid = str(message.from_user.id)

    args = message.text.split()
    ref = None

    if len(args) > 1:
        ref = args[1]

    if uid not in db:

        db[uid] = {
            "balance": 0,
            "ref": ref,
            "refs": 0,
            "joined": False,
            "upi": "",
            "withdraw_pending": False
        }

        # Referral reward
        if ref and ref in db and ref != uid:

            db[ref]["balance"] += REF_REWARD
            db[ref]["refs"] += 1

            bot.send_message(
                int(ref),
                f"🎉 Referral joined!\n₹{REF_REWARD} added"
            )

    save_db(db)

    bot.send_message(
        message.chat.id,
        "💰 Welcome to Daly Earning Bot",
        reply_markup=menu()
    )

# ================= JOIN CHANNEL =================

@bot.message_handler(func=lambda m: m.text=="📢 Join Channel")
def join_channel(message):

    bot.send_message(
        message.chat.id,
        CHANNEL_LINK
    )

# ================= EARN =================

@bot.message_handler(func=lambda m: m.text=="💰 Earn Money")
def earn(message):

    db = load_db()
    uid = str(message.from_user.id)

    try:

        member = bot.get_chat_member(CHANNEL_ID, message.from_user.id)

        if member.status in ["member","administrator","creator"]:

            if not db[uid]["joined"]:

                db[uid]["balance"] += JOIN_REWARD
                db[uid]["joined"] = True

                save_db(db)

                bot.send_message(
                    message.chat.id,
                    f"✅ ₹{JOIN_REWARD} added to wallet"
                )

            else:

                bot.send_message(
                    message.chat.id,
                    "⚠️ Already claimed (Anti-Fake Protection)"
                )

        else:

            bot.send_message(
                message.chat.id,
                "❌ Join channel first"
            )

    except:

        bot.send_message(
            message.chat.id,
            "❌ Join channel first"
        )

# ================= DASHBOARD =================

@bot.message_handler(func=lambda m: m.text=="📊 Dashboard")
def dashboard(message):

    db = load_db()
    uid = str(message.from_user.id)

    bal = db[uid]["balance"]
    refs = db[uid]["refs"]

    bot.send_message(
        message.chat.id,
        f"""
📊 Dashboard

💰 Balance: ₹{bal}
👥 Total Referrals: {refs}
"""
    )

# ================= REFER =================

@bot.message_handler(func=lambda m: m.text=="👥 Refer & Earn")
def refer(message):

    uid = message.from_user.id

    link = f"https://t.me/{bot.get_me().username}?start={uid}"

    bot.send_message(
        message.chat.id,
        f"""
👥 Referral Link:

{link}

Earn ₹{REF_REWARD} per referral
"""
    )

# ================= WITHDRAW =================

@bot.message_handler(func=lambda m: m.text=="💳 Withdraw")
def withdraw(message):

    db = load_db()
    uid = str(message.from_user.id)

    if db[uid]["balance"] < MIN_WITHDRAW:

        bot.send_message(
            message.chat.id,
            f"❌ Minimum withdraw ₹{MIN_WITHDRAW}"
        )
        return

    waiting_upi[uid] = True

    bot.send_message(
        message.chat.id,
        "Enter your UPI ID:"
    )

# ================= SAVE UPI =================

@bot.message_handler(func=lambda m: str(m.from_user.id) in waiting_upi)
def save_upi(message):

    uid = str(message.from_user.id)
    upi = message.text

    db = load_db()

    db[uid]["upi"] = upi
    db[uid]["withdraw_pending"] = True

    amount = db[uid]["balance"]

    save_db(db)

    bot.send_message(
        message.chat.id,
        "✅ Withdraw request sent to admin"
    )

    # Admin approve buttons
    markup = InlineKeyboardMarkup()

    markup.add(
        InlineKeyboardButton(
            "✅ Approve",
            callback_data=f"approve_{uid}"
        ),
        InlineKeyboardButton(
            "❌ Reject",
            callback_data=f"reject_{uid}"
        )
    )

    bot.send_message(
        ADMIN_ID,
        f"""
💳 Withdrawal Request

User: {uid}
Amount: ₹{amount}
UPI: {upi}
""",
        reply_markup=markup
    )

    del waiting_upi[uid]

# ================= ADMIN APPROVE =================

@bot.callback_query_handler(func=lambda call: True)
def callback(call):

    db = load_db()

    data = call.data

    if "approve_" in data:

        uid = data.split("_")[1]

        amount = db[uid]["balance"]

        db[uid]["balance"] = 0
        db[uid]["withdraw_pending"] = False

        save_db(db)

        bot.send_message(
            uid,
            f"✅ Withdraw approved\nAmount ₹{amount} will be sent"
        )

        bot.edit_message_text(
            "✅ Approved",
            call.message.chat.id,
            call.message.message_id
        )

    elif "reject_" in data:

        uid = data.split("_")[1]

        db[uid]["withdraw_pending"] = False

        save_db(db)

        bot.send_message(
            uid,
            "❌ Withdraw rejected"
        )

        bot.edit_message_text(
            "❌ Rejected",
            call.message.chat.id,
            call.message.message_id
        )

# ================= RUN =================

print("Bot running...")
bot.infinity_polling()
