import telebot
from telebot import types
import subprocess
import os
import requests
import glob

# --- Konfigurasi ---
# Mengambil TOKEN dari env 'TELE_TOKEN' (bukan SUBJECT)
TOKEN = os.getenv("TELE_TOKEN")
# Ambil ID dari env, jika tidak ada pakai ID default kamu
ALLOWED_ID = int(os.getenv("TELE_ID", 1471991896))

WORKDIR = "/workspace/comfyui-esddin/qwen"
TEMP_PATH = "/workspace/runpod-slim/ComfyUI/temp"

if not TOKEN:
    print("❌ ERROR: TELE_TOKEN tidak ditemukan di environment!")
    exit(1)

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['last'])
def send_last_images(message):
    if message.from_user.id != ALLOWED_ID:
        return
    
    try:
        # Cari semua PNG
        files = glob.glob(os.path.join(TEMP_PATH, "*.png"))
        
        if not files:
            bot.send_message(message.chat.id, f"❌ Folder kosong di path:\n<code>{TEMP_PATH}</code>", parse_mode="HTML")
            return

        # Sort berdasarkan waktu modifikasi (terbaru di atas)
        files.sort(key=os.path.getmtime, reverse=True)
        latest_files = files[:6]
        
        bot.send_message(message.chat.id, f"📸 Mengirim {len(latest_files)} file terbaru...")

        media = []
        for i, f in enumerate(latest_files):
            photo = open(f, 'rb')
            caption = os.path.basename(f) if i == 0 else ""
            media.append(types.InputMediaPhoto(photo, caption=caption))

        if media:
            bot.send_media_group(message.chat.id, media)
            for m in media:
                m.media.close()
                
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error detect: {str(e)}")

# --- Perintah Lain ---
@bot.message_handler(commands=['info'])
def info_device(message):
    if message.from_user.id != ALLOWED_ID: return
    try:
        ram = subprocess.check_output("free -h | grep Mem | awk '{print $3 \" / \" $2}'", shell=True).decode().strip()
        disk = subprocess.check_output("df -h /workspace | awk 'NR==2 {print $3 \" / \" $2 \" (\" $5 \")\"}'", shell=True).decode().strip()
        try:
            vram = subprocess.check_output("nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits", shell=True).decode().strip()
            v_used, v_total = vram.split(',')
            vram_info = f"{int(v_used)/1024:.1f}GB / {int(v_total)/1024:.1f}GB"
        except: vram_info = "GPU Error"
        bot.reply_to(message, f"🖥️ <b>Info:</b>\nRAM: {ram}\nVRAM: {vram_info}\nDISK: {disk}", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"❌ Error Info: {e}")

@bot.message_handler(commands=['clean'])
def clean_temp(message):
    if message.from_user.id != ALLOWED_ID: return
    os.system(f"rm -f {TEMP_PATH}/*")
    bot.reply_to(message, "🧹 Temp Cleaned!")

@bot.message_handler(commands=['reboot'])
def reboot_comfy(message):
    if message.from_user.id != ALLOWED_ID: return
    try:
        requests.get("http://127.0.0.1:8188/manager/reboot", timeout=5)
        bot.reply_to(message, "🔄 Rebooting...")
    except: 
        bot.reply_to(message, "✅ Perintah dikirim (Server mungkin sedang restart).")

@bot.message_handler(commands=['run'])
def handle_run(message):
    if message.from_user.id != ALLOWED_ID: return
    try:
        parts = message.text.split()
        if len(parts) < 8:
            bot.reply_to(message, "⚠️ Format: /run subj dr ur cnt n ss prf")
            return
        subject = parts[1]
        bot.reply_to(message, f"🚀 <b>Running {subject}...</b>", parse_mode="HTML")
        
        env = os.environ.copy()
        env["COUNT"] = parts[4]
        
        cmd = ["/bin/bash", "main.sh", "-s", subject, "-dr", parts[2], "-ur", parts[3], "-n", parts[5], "-ss", parts[6], "-p", parts[7]]
        subprocess.Popen(cmd, cwd=WORKDIR, env=env)
    except Exception as e: 
        bot.reply_to(message, f"❌ Error Run: {e}")

print("--- BOT IS RUNNING ---")
bot.infinity_polling()