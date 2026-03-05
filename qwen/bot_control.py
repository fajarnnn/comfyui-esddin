import telebot
import subprocess
import os
import requests
import re

# Konfigurasi
TOKEN = "8667029481:AAH9hNvk9bIKGdEiFljJa6nnKjpu2LtCEMo"
ALLOWED_ID = 1471991896
WORKDIR = "/workspace/comfyui-esddin/qwen"
TEMP_DIR = "/workspace/runpod-slim/ComfyUI/temp/*"

bot = telebot.TeleBot(TOKEN)

def get_sys_info():
    # RAM Info
    ram = subprocess.check_output("free -h | grep Mem | awk '{print $3 \" / \" $2}'", shell=True).decode().strip()
    
    # Disk Info (Root /workspace)
    disk = subprocess.check_output("df -h /workspace | awk 'NR==2 {print $3 \" / \" $2 \" (\" $5 \")\"}'", shell=True).decode().strip()
    
    # VRAM Info (Nvidia GPU)
    try:
        vram = subprocess.check_output("nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits", shell=True).decode().strip()
        v_used, v_total = vram.split(',')
        vram_info = f"{int(v_used)/1024:.1f}GB / {int(v_total)/1024:.1f}GB"
    except:
        vram_info = "GPU Not Found"
        
    return ram, vram_info, disk

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    msg = (
        "👋 <b>Halo Bro!</b>\n\n"
        "Perintah yang tersedia:\n"
        "1. <code>/run [subj] [dr] [ur] [cnt] [n] [ss] [prf]</code>\n"
        "2. <code>/info</code> - Cek RAM, VRAM, DISK\n"
        "3. <code>/reboot</code> - Restart ComfyUI\n"
        "4. <code>/clean</code> - Hapus isi folder Temp\n"
        "5. <code>/ping</code> - Cek bot aktif"
    )
    bot.reply_to(message, msg, parse_mode="HTML")

@bot.message_handler(commands=['info'])
def info_device(message):
    if message.from_user.id != ALLOWED_ID:
        return
    
    ram, vram, disk = get_sys_info()
    msg = (
        "🖥️ <b>Device Info:</b>\n\n"
        f"🔹 <b>RAM:</b> <code>{ram}</code>\n"
        f"🔹 <b>VRAM:</b> <code>{vram}</code>\n"
        f"🔹 <b>DISK:</b> <code>{disk}</code>"
    )
    bot.reply_to(message, msg, parse_mode="HTML")

@bot.message_handler(commands=['ping'])
def ping_bot(message):
    bot.reply_to(message, "✅ Bot Standby, Bro!")

@bot.message_handler(commands=['clean'])
def clean_temp(message):
    if message.from_user.id != ALLOWED_ID:
        return
    os.system(f"rm -f {TEMP_DIR}")
    bot.reply_to(message, "🧹 <b>Temp Cleaned!</b>", parse_mode="HTML")

@bot.message_handler(commands=['reboot'])
def reboot_comfy(message):
    if message.from_user.id != ALLOWED_ID:
        return
    bot.reply_to(message, "🔄 <b>Rebooting ComfyUI...</b>", parse_mode="HTML")
    try:
        requests.get("http://127.0.0.1:8188/manager/reboot", timeout=10)
        bot.reply_to(message, "✅ Reboot command sent!")
    except:
        bot.reply_to(message, "❌ ComfyUI Offline.")

@bot.message_handler(commands=['run'])
def handle_run(message):
    if message.from_user.id != ALLOWED_ID:
        return
    try:
        parts = message.text.split()
        if len(parts) < 8:
            bot.reply_to(message, "⚠️ Format: <code>/run subj dr ur cnt n ss prf</code>", parse_mode="HTML")
            return
        subject, dr, ur, count, n_val, ss_val, prf = parts[1:8]
        bot.reply_to(message, f"🚀 <b>Running {subject}...</b>", parse_mode="HTML")
        env = os.environ.copy()
        env["COUNT"] = count
        cmd = ["/bin/bash", "main.sh", "-s", subject, "-dr", dr, "-ur", ur, "-n", n_val, "-ss", ss_val, "-p", prf]
        subprocess.Popen(cmd, cwd=WORKDIR, env=env)
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

print("Bot standby, Bro...")
bot.infinity_polling()