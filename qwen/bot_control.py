import telebot
from telebot import types
import subprocess
import os
import requests
import glob
import shutil

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
    if message.from_user.id != ALLOWED_ID: return
    try:
        files = glob.glob(os.path.join(TEMP_PATH, "*.png"))
        if not files:
            bot.reply_to(message, f"❌ Folder kosong:\n<code>{TEMP_PATH}</code>", parse_mode="HTML")
            return

        files.sort(key=os.path.getmtime, reverse=True)
        latest_files = files[:6]
        
        media = []
        for i, f in enumerate(latest_files):
            photo = open(f, 'rb')
            caption = f"<code>{os.path.basename(f)}</code>" if i == 0 else ""
            media.append(types.InputMediaPhoto(photo, caption=caption, parse_mode="HTML"))

        if media:
            bot.send_media_group(message.chat.id, media)
            for m in media: m.media.close()
                
    except Exception as e:
        bot.reply_to(message, f"❌ Error Last: <code>{str(e)}</code>", parse_mode="HTML")

# --- Perintah: /info ---
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
        
        res = (f"🖥️ <b>System Info</b>\n\n"
               f"RAM: <code>{ram}</code>\n"
               f"VRAM: <code>{vram_info}</code>\n"
               f"DISK: <code>{disk}</code>")
        bot.reply_to(message, res, parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"❌ Error Info: <code>{e}</code>", parse_mode="HTML")

# --- Perintah: /clean ---
@bot.message_handler(commands=['clean'])
def clean_temp(message):
    if message.from_user.id != ALLOWED_ID: return
    os.system(f"rm -f {TEMP_PATH}/*")
    bot.reply_to(message, "🧹 Temp Cleaned!")

# --- Perintah: /reboot ---
@bot.message_handler(commands=['reboot'])
def reboot_comfy(message):
    if message.from_user.id != ALLOWED_ID: return
    try:
        requests.get("http://127.0.0.1:8188/manager/reboot", timeout=5)
        bot.reply_to(message, "🔄 Rebooting...")
    except: 
        bot.reply_to(message, "✅ Command Sent.")

# --- Perintah: /run ---
@bot.message_handler(commands=['run'])
def handle_run(message):
    if message.from_user.id != ALLOWED_ID: return
    try:
        parts = message.text.split()
        if len(parts) < 8:
            bot.reply_to(message, "⚠️ Format: <code>/run subj dr ur cnt n ss prf</code>", parse_mode="HTML")
            return
        
        subject = parts[1]
        bot.reply_to(message, f"🚀 Running: <code>{subject}</code>", parse_mode="HTML")
        
        env = os.environ.copy()
        env["COUNT"] = parts[4]
        
        cmd = ["/bin/bash", "main.sh", "-s", subject, "-dr", parts[2], "-m", "image", "-ur", parts[3], "-n", parts[5], "-ss", parts[6], "-p", parts[7]]
        subprocess.Popen(cmd, cwd=WORKDIR, env=env)
    except Exception as e: 
        bot.reply_to(message, f"❌ Error Run: <code>{e}</code>", parse_mode="HTML")

# --- Perintah: /count ---
@bot.message_handler(commands=['count'])
def count_files(message):
    if message.from_user.id != ALLOWED_ID: return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Format: <code>/count subject_name</code>", parse_mode="HTML")
            return
        
        subject = parts[1]
        base_path = f"/workspace/runpod-slim/ComfyUI/input/renamed/{subject}"
        
        if not os.path.exists(base_path):
            bot.reply_to(message, f"❌ Folder tidak ditemukan:\n<code>{base_path}</code>", parse_mode="HTML")
            return

        subfolders = ["full_body", "half_body"]
        modes = ["solo", "group"]
        
        response = f"📊 <b>Count: {subject}</b>\n"
        total_all = 0

        for sub in subfolders:
            response += f"\n📂 <b>{sub.replace('_', ' ').title()}</b>\n"
            for m in modes:
                path = os.path.join(base_path, sub, m, "*")
                files = [f for f in glob.glob(path) if os.path.isfile(f)]
                count = len(files)
                total_all += count
                icon = "✅" if count > 0 else "⚠️"
                response += f"  ├ {m.capitalize()}: <code>{count}</code> {icon}\n"
        
        response += f"\nTotal: <b>{total_all}</b> file."
        bot.reply_to(message, response, parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"❌ Error Count: <code>{str(e)}</code>", parse_mode="HTML")

# --- Perintah: /delete ---
@bot.message_handler(commands=['delete'])
def delete_subject_folder(message):
    if message.from_user.id != ALLOWED_ID: return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Format: <code>/delete subject_name</code>", parse_mode="HTML")
            return
        
        subject = parts[1]
        target_path = f"/workspace/runpod-slim/ComfyUI/input/renamed/{subject}"
        
        if not os.path.exists(target_path):
            bot.reply_to(message, f"❌ Folder tidak ada:\n<code>{target_path}</code>", parse_mode="HTML")
            return

        shutil.rmtree(target_path)
        bot.reply_to(message, f"🗑️ Deleted: <code>{subject}</code>", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"❌ Error Delete: <code>{str(e)}</code>", parse_mode="HTML")

# --- Perintah: /list ---
@bot.message_handler(commands=['list'])
def list_subjects(message):
    if message.from_user.id != ALLOWED_ID: return
    try:
        base_path = "/workspace/runpod-slim/ComfyUI/input/renamed"
        if not os.path.exists(base_path):
            bot.reply_to(message, "❌ Path tidak ditemukan.", parse_mode="HTML")
            return

        subjects = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
        if not subjects:
            bot.reply_to(message, "📂 Folder Kosong.")
            return

        subjects.sort()
        response = "📂 <b>Daftar Subject:</b>\n\n"
        for i, sub in enumerate(subjects, 1):
            # Klik pada nama folder untuk copy otomatis
            response += f"{i}. <code>{sub}</code>\n"
            
        bot.reply_to(message, response, parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"❌ Error List: <code>{str(e)}</code>", parse_mode="HTML")

# --- Perintah: /install ---
@bot.message_handler(commands=['install'])
def handle_install(message):
    if message.from_user.id != ALLOWED_ID: return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Format: <code>/install HF_TOKEN [TELE_TOKEN] [ID]</code>", parse_mode="HTML")
            return
        
        hf_token = parts[1]
        tele_token = parts[2] if len(parts) > 2 else TOKEN
        tele_id = parts[3] if len(parts) > 3 else str(message.from_user.id)
        
        wrapper_path = "/workspace/comfyui-esddin/run_ins.sh"
        log_path = "/workspace/comfyui-esddin/qwen/install_debug.log"
        
        if not os.path.exists(wrapper_path):
            bot.reply_to(message, f"❌ File tidak ada:\n<code>{wrapper_path}</code>", parse_mode="HTML")
            return

        bot.reply_to(message, "⚙️ <b>Installing...</b>\nCek log: <code>/log install_debug.log</code>", parse_mode="HTML")
        cmd = ["bash", wrapper_path, hf_token, tele_token, tele_id]
        with open(log_path, "a") as f_log:
            subprocess.Popen(cmd, cwd=WORKDIR, stdout=f_log, stderr=f_log)
    except Exception as e:
        bot.reply_to(message, f"❌ Error Install: <code>{e}</code>", parse_mode="HTML")

# --- Perintah: /log ---
@bot.message_handler(commands=['log'])
def send_tail_log(message):
    if message.from_user.id != ALLOWED_ID: return
    try:
        parts = message.text.split()
        filename = parts[1] if len(parts) > 1 else "bot.log"
        log_path = os.path.join(WORKDIR, filename)

        if not os.path.exists(log_path):
            bot.reply_to(message, f"❌ Not found: <code>{filename}</code>", parse_mode="HTML")
            return

        tail_output = subprocess.check_output(["tail", "-n", "15", log_path]).decode('utf-8')
        if not tail_output.strip():
            bot.reply_to(message, "⚪ Log kosong.")
            return

        msg = f"📝 <b>Log: {filename}</b>\n<pre>{tail_output}</pre>"
        bot.reply_to(message, msg if len(msg) < 4000 else msg[:4000], parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"❌ Error Log: <code>{str(e)}</code>", parse_mode="HTML")
        
print("--- BOT IS RUNNING ---")
bot.infinity_polling()