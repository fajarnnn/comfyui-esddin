import telebot
import subprocess
import os
import requests
import glob

# Konfigurasi
TOKEN = "8667029481:AAH9hNvk9bIKGdEiFljJa6nnKjpu2LtCEMo"
ALLOWED_ID = 1471991896
WORKDIR = "/workspace/comfyui-esddin/qwen"
TEMP_DIR = "/workspace/runpod-slim/ComfyUI/temp/*"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    msg = (
        "👋 <b>Halo Bro!</b>\n\n"
        "Perintah yang tersedia:\n"
        "1. <code>/run [subj] [dr] [ur] [cnt] [n] [ss] [prf]</code>\n"
        "2. <code>/reboot</code> - Restart ComfyUI\n"
        "3. <code>/clean</code> - Hapus isi folder Temp\n"
        "4. <code>/ping</code> - Cek bot aktif"
    )
    bot.reply_to(message, msg, parse_mode="HTML")

@bot.message_handler(commands=['ping'])
def ping_bot(message):
    bot.reply_to(message, "✅ Bot Standby, Bro!")

@bot.message_handler(commands=['clean'])
def clean_temp(message):
    if message.from_user.id != ALLOWED_ID:
        return
    
    bot.reply_to(message, "🧹 <b>Sedang membersihkan folder temp...</b>", parse_mode="HTML")
    try:
        # Menjalankan perintah rm lewat shell
        os.system(f"rm -f {TEMP_DIR}")
        bot.reply_to(message, "✨ Folder temp berhasil dibersihkan!")
    except Exception as e:
        bot.reply_to(message, f"❌ Gagal membersihkan temp: {str(e)}")

@bot.message_handler(commands=['reboot'])
def reboot_comfy(message):
    if message.from_user.id != ALLOWED_ID:
        return
    
    bot.reply_to(message, "🔄 <b>Mengirim perintah Reboot ke ComfyUI...</b>", parse_mode="HTML")
    try:
        r = requests.get("http://127.0.0.1:8188/manager/reboot", timeout=10)
        if r.status_code == 200:
            bot.reply_to(message, "✅ ComfyUI sedang restart, tunggu sekitar 10-20 detik.")
        else:
            bot.reply_to(message, f"⚠️ Server merespon dengan status: {r.status_code}")
    except Exception as e:
        bot.reply_to(message, f"❌ Gagal konek ke ComfyUI: {str(e)}")

@bot.message_handler(commands=['run'])
def handle_run(message):
    if message.from_user.id != ALLOWED_ID:
        return

    try:
        parts = message.text.split()
        if len(parts) < 8:
            msg = "⚠️ <b>Format Salah!</b>\nContoh: <code>/run 23.11_ nt nt 150 true false 200000</code>"
            bot.reply_to(message, msg, parse_mode="HTML")
            return

        subject, dr, ur, count, n_val, ss_val, prf = parts[1:8]

        bot.reply_to(message, f"🚀 <b>Workflow Dimulai!</b>\nSubject: <code>{subject}</code>\nCount: <code>{count}</code>", parse_mode="HTML")

        env = os.environ.copy()
        env["COUNT"] = count
        cmd = ["/bin/bash", "main.sh", "-s", subject, "-dr", dr, "-ur", ur, "-n", n_val, "-ss", ss_val, "-p", prf]
        
        subprocess.Popen(cmd, cwd=WORKDIR, env=env)

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

print("Bot standby, Bro...")
bot.infinity_polling()