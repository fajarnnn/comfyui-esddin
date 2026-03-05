import telebot
import subprocess
import os
import requests
import glob

# Konfigurasi
TOKEN = "8667029481:AAH9hNvk9bIKGdEiFljJa6nnKjpu2LtCEMo"
ALLOWED_ID = 1471991896
WORKDIR = "/workspace/comfyui-esddin/qwen"
TEMP_PATH = "/workspace/runpod-slim/ComfyUI/temp"

bot = telebot.TeleBot(TOKEN)

def get_sys_info():
    ram = subprocess.check_output("free -h | grep Mem | awk '{print $3 \" / \" $2}'", shell=True).decode().strip()
    disk = subprocess.check_output("df -h /workspace | awk 'NR==2 {print $3 \" / \" $2 \" (\" $5 \")\"}'", shell=True).decode().strip()
    try:
        vram = subprocess.check_output("nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits", shell=True).decode().strip()
        v_used, v_total = vram.split(',')
        vram_info = f"{int(v_used)/1024:.1f}GB / {int(v_total)/1024:.1f}GB"
    except:
        vram_info = "GPU Not Found"
    return ram, vram_info, disk

@bot.message_handler(commands=['last'])
def send_last_images(message):
    if message.from_user.id != ALLOWED_ID:
        return
    
    # Cari semua file gambar di folder temp
    files = glob.glob(f"{TEMP_PATH}/*.png") + glob.glob(f"{TEMP_PATH}/*.jpg") + glob.glob(f"{TEMP_PATH}/*.jpeg")
    
    if not files:
        bot.reply_to(message, "❌ Gak ada file gambar di folder temp, Bro.")
        return

    # Sort berdasarkan waktu modifikasi (paling baru di atas)
    files.sort(key=os.path.getmtime, reverse=True)
    
    # Ambil 2 teratas
    latest_files = files[:2]
    
    bot.reply_to(message, f"📸 Mengirim {len(latest_files)} gambar terbaru dari temp...")
    
    for f in latest_files:
        try:
            with open(f, 'rb') as img:
                bot.send_photo(message.chat.id, img, caption=f"File: {os.path.basename(f)}")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Gagal kirim {os.path.basename(f)}: {e}")

@bot.message_handler(commands=['info'])
def info_device(message):
    if message.from_user.id != ALLOWED_ID: return
    ram, vram, disk = get_sys_info()
    msg = f"🖥️ <b>Device Info:</b>\n\n🔹 <b>RAM:</b> <code>{ram}</code>\n🔹 <b>VRAM:</b> <code>{vram}</code>\n🔹 <b>DISK:</b> <code>{disk}</code>"
    bot.reply_to(message, msg, parse_mode="HTML")

@bot.message_handler(commands=['clean'])
def clean_temp(message):
    if message.from_user.id != ALLOWED_ID: return
    os.system(f"rm -f {TEMP_PATH}/*")
    bot.reply_to(message, "🧹 <b>Temp Cleaned!</b>", parse_mode="HTML")

@bot.message_handler(commands=['reboot'])
def reboot_comfy(message):
    if message.from_user.id != ALLOWED_ID: return
    try:
        requests.get("http://127.0.0.1:8188/manager/reboot", timeout=10)
        bot.reply_to(message, "🔄 Reboot command sent!")
    except:
        bot.reply_to(message, "❌ ComfyUI Offline.")

@bot.message_handler(commands=['run'])
def handle_run(message):
    if message.from_user.id != ALLOWED_ID: return
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