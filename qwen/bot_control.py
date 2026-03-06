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

@bot.message_handler(commands=['install'])
def handle_install(message):
    if message.from_user.id != ALLOWED_ID: return
    
    try:
        parts = message.text.split()
        # Kita butuh minimal 2 (cmd + hf_token)
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Format: /install <HF_TOKEN> [TELE_TOKEN] [TELE_ID]")
            return
        
        hf_token = parts[1]
        # Jika param ke-3 (tele_token) tidak ada, pakai TOKEN bot saat ini
        tele_token = parts[2] if len(parts) > 2 else TOKEN
        # Jika param ke-4 (tele_id) tidak ada, pakai ID pengirim saat ini
        tele_id = parts[3] if len(parts) > 3 else str(message.from_user.id)
        
        bot.reply_to(message, f"⚙️ <b>Memulai Instalasi...</b>\n\nHF: <code>{hf_token[:6]}***</code>\nTele: <code>{tele_id}</code>", parse_mode="HTML")

        # Panggil wrapper script
        cmd = ["bash", "run_ins.sh", hf_token, tele_token, tele_id]
        
        # Jalankan di background agar bot tidak freeze
        with open("install_debug.log", "a") as f_log:
            subprocess.Popen(cmd, cwd=WORKDIR, stdout=f_log, stderr=f_log)
            
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

# --- [Command: /log] ---
@bot.message_handler(commands=['log'])
def send_tail_log(message):
    if message.from_user.id != ALLOWED_ID:
        return
    
    try:
        parts = message.text.split()
        # Jika tidak ada nama file, default ke bot.log
        filename = parts[1] if len(parts) > 1 else "bot.log"
        log_path = os.path.join(WORKDIR, filename)

        if not os.path.exists(log_path):
            bot.reply_to(message, f"❌ File log tidak ditemukan:\n<code>{log_path}</code>", parse_mode="HTML")
            return

        # Mengambil 15 baris terakhir menggunakan perintah 'tail'
        tail_output = subprocess.check_output(["tail", "-n", "15", log_path]).decode('utf-8')
        
        if not tail_output.strip():
            bot.reply_to(message, f"⚪ File <code>{filename}</code> masih kosong.", parse_mode="HTML")
            return

        msg = f"📝 <b>Last 15 lines of {filename}:</b>\n\n<pre>{tail_output}</pre>"
        
        # Jika pesan terlalu panjang untuk Telegram (max 4096 char), kita potong
        if len(msg) > 4000:
            msg = msg[:4000] + "...(truncated)"
            
        bot.reply_to(message, msg, parse_mode="HTML")

    except Exception as e:
        bot.reply_to(message, f"❌ Error reading log: {str(e)}")
        
print("--- BOT IS RUNNING ---")
bot.infinity_polling()