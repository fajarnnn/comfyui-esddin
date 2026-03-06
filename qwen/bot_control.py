import telebot
from telebot import types
import subprocess
import os
import requests
import glob

# --- Konfigurasi ---
TOKEN = os.getenv("TELE_TOKEN")
ALLOWED_ID = int(os.getenv("TELE_ID", 1471991896))
WORKDIR = "/workspace/comfyui-esddin/qwen"
TEMP_PATH = "/workspace/runpod-slim/ComfyUI/temp"

if not TOKEN:
    print("❌ ERROR: TELE_TOKEN tidak ditemukan di environment!")
    exit(1)

bot = telebot.TeleBot(TOKEN)

# --- Perintah: /last ---
@bot.message_handler(commands=['last'])
def send_last_images(message):
    if message.from_user.id != ALLOWED_ID:
        return
    try:
        files = glob.glob(os.path.join(TEMP_PATH, "*.png"))
        if not files:
            bot.send_message(message.chat.id, f"❌ Folder kosong di path:\n<code>{TEMP_PATH}</code>", parse_mode="HTML")
            return

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

# --- Perintah: /info ---
@bot.message_handler(commands=['info'])
def info_device(message):
    if message.from_user.id != ALLOWED_ID:
        return
    try:
        ram = subprocess.check_output("free -h | grep Mem | awk '{print $3 \" / \" $2}'", shell=True).decode().strip()
        disk = subprocess.check_output("df -h /workspace | awk 'NR==2 {print $3 \" / \" $2 \" (\" $5 \")\"}'", shell=True).decode().strip()
        try:
            vram = subprocess.check_output("nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits", shell=True).decode().strip()
            v_used, v_total = vram.split(',')
            vram_info = f"{int(v_used)/1024:.1f}GB / {int(v_total)/1024:.1f}GB"
        except:
            vram_info = "GPU Error"
        bot.reply_to(message, f"🖥️ <b>Info:</b>\nRAM: {ram}\nVRAM: {vram_info}\nDISK: {disk}", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"❌ Error Info: {e}")

# --- Perintah: /clean ---
@bot.message_handler(commands=['clean'])
def clean_temp(message):
    if message.from_user.id != ALLOWED_ID:
        return
    os.system(f"rm -f {TEMP_PATH}/*")
    bot.reply_to(message, "🧹 Temp Cleaned!")

# --- Perintah: /reboot ---
@bot.message_handler(commands=['reboot'])
def reboot_comfy(message):
    if message.from_user.id != ALLOWED_ID:
        return
    try:
        requests.get("http://127.0.0.1:8188/manager/reboot", timeout=5)
        bot.reply_to(message, "🔄 Rebooting...")
    except: 
        bot.reply_to(message, "✅ Perintah dikirim (Server mungkin sedang restart).")

# --- Perintah: /run ---
@bot.message_handler(commands=['run'])
def handle_run(message):
    if message.from_user.id != ALLOWED_ID:
        return
    try:
        parts = message.text.split()
        if len(parts) < 8:
            bot.reply_to(message, "⚠️ Format: /run subj dr ur cnt n ss prf")
            return
        
        subject = parts[1]
        bot.reply_to(message, f"🚀 <b>Running {subject}...</b>", parse_mode="HTML")
        
        env = os.environ.copy()
        env["COUNT"] = parts[4]
        
        cmd = ["/bin/bash", "main.sh", "-s", subject, "-dr", parts[2], "-m", "image", "-ur", parts[3], "-n", parts[5], "-ss", parts[6], "-p", parts[7]]
        subprocess.Popen(cmd, cwd=WORKDIR, env=env)
    except Exception as e: 
        bot.reply_to(message, f"❌ Error Run: {e}")

# --- Perintah: /count ---
@bot.message_handler(commands=['count'])
def count_files(message):
    if message.from_user.id != ALLOWED_ID:
        return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Format: <code>/count subject_name</code>", parse_mode="HTML")
            return
        
        subject = parts[1]
        base_path = f"/workspace/runpod-slim/ComfyUI/input/renamed/{subject}"
        
        if not os.path.exists(base_path):
            bot.reply_to(message, f"❌ Folder subject tidak ditemukan:\n<code>{base_path}</code>", parse_mode="HTML")
            return

        subfolders = ["full_body", "half_body"]
        modes = ["solo", "group"]
        
        response = f"📊 <b>File Count for: {subject}</b>\n"
        total_all = 0

        for sub in subfolders:
            response += f"\n📂 <b>{sub.replace('_', ' ').title()}</b>\n"
            for m in modes:
                path = os.path.join(base_path, sub, m, "*")
                files = [f for f in glob.glob(path) if os.path.isfile(f)]
                count = len(files)
                total_all += count
                
                status_icon = "✅" if count > 0 else "⚠️"
                response += f"  ├ {m.capitalize()}: {count} {status_icon}\n"
        
        response += f"\nTotal Semua: <b>{total_all}</b> file."
        bot.reply_to(message, response, parse_mode="HTML")

    except Exception as e:
        bot.reply_to(message, f"❌ Error Count: {str(e)}")

# --- Perintah: /delete (Hapus Folder Subject) ---
@bot.message_handler(commands=['delete'])
def delete_subject_folder(message):
    if message.from_user.id != ALLOWED_ID:
        return
    try:
        parts = message.text.split()
        # Format: /delete <subject>
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Format: <code>/delete subject_name</code>", parse_mode="HTML")
            return
        
        subject = parts[1]
        target_path = f"/workspace/runpod-slim/ComfyUI/input/renamed/{subject}"
        
        if not os.path.exists(target_path):
            bot.reply_to(message, f"❌ Folder tidak ditemukan:\n<code>{target_path}</code>", parse_mode="HTML")
            return

        # Eksekusi penghapusan folder dan isinya (rm -rf)
        import shutil
        shutil.rmtree(target_path)
        
        bot.reply_to(message, f"🗑️ <b>Folder Deleted:</b>\n<code>{subject}</code>", parse_mode="HTML")

    except Exception as e:
        bot.reply_to(message, f"❌ Error Delete: {str(e)}")

# --- Perintah: /list (Daftar Folder Subject) ---
@bot.message_handler(commands=['list'])
def list_subjects(message):
    if message.from_user.id != ALLOWED_ID:
        return
    try:
        base_path = "/workspace/runpod-slim/ComfyUI/input/renamed"
        
        if not os.path.exists(base_path):
            bot.reply_to(message, "❌ Direktori utama tidak ditemukan.", parse_mode="HTML")
            return

        # Ambil daftar folder saja (abaikan file)
        subjects = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
        
        if not subjects:
            bot.reply_to(message, "📂 <b>Direktori Kosong</b>", parse_mode="HTML")
            return

        # Urutkan secara alfabet
        subjects.sort()
        
        response = "📂 <b>Daftar Subject:</b>\n\n"
        for i, sub in enumerate(subjects, 1):
            response += f"{i}. <code>{sub}</code>\n"
            
        bot.reply_to(message, response, parse_mode="HTML")

    except Exception as e:
        bot.reply_to(message, f"❌ Error List: {str(e)}")
print("--- BOT IS RUNNING ---")
bot.infinity_polling()