import telebot
import subprocess
import os

# Konfigurasi
TOKEN = "8667029481:AAH9hNvk9bIKGdEiFljJa6nnKjpu2LtCEMo"
ALLOWED_ID = 1471991896 # Biar orang lain gak bisa nge-hit server lo
WORKDIR = "/workspace/comfyui-esddin/qwen"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Siap Jar! Kirim perintah dengan format:\n/run <subject> <dr> <ur>\n\nContoh:\n/run 23.11_ nt nt")

@bot.message_handler(commands=['run'])
def run_script(message):
    # Cek ID biar aman
    if message.from_user.id != ALLOWED_ID:
        bot.reply_to(message, "Lu siapa? Gak kenal.")
        return

    try:
        # Ambil argumen dari pesan: /run subject dr ur
        args = message.text.split()
        if len(args) < 4:
            bot.reply_to(message, "Format salah Jar! Pakai: /run <subject> <dr> <ur>")
            return

        subject = args[1]
        dr = args[2]
        ur = args[3]

        bot.reply_to(message, f"🚀 Memulai workflow untuk <b>{subject}</b>...\nMohon tunggu notif selesai.")

        # Jalankan main.sh di background agar bot tidak timeout
        cmd = f"bash {WORKDIR}/main.sh -s {subject} -dr {dr} -ur {ur}"
        
        # Menggunakan Popen agar bot tetap responsif (async)
        subprocess.Popen(cmd, shell=True, cwd=WORKDIR)

    except Exception as e:
        bot.reply_to(message, f"❌ Gagal jalanin script: {str(e)}")

print("Bot standby Jar...")
bot.infinity_polling()