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
        # Minimal 8 bagian (cmd + 7 args). Argumen ke-9 (sub) bersifat opsional.
        if len(parts) < 8:
            bot.reply_to(message, "⚠️ Format: <code>/run subj dr ur cnt n ss prf [sub]</code>", parse_mode="HTML")
            return
        
        subject = parts[1]
        # Jika parts[8] ada, gunakan itu sebagai sub. Jika tidak, pakai empty string.
        sub_val = parts[8] if len(parts) > 8 else ""
        
        bot.reply_to(message, f"🚀 Running: <code>{subject}</code>\nSub: <code>{sub_val if sub_val else '(empty)'}</code>", parse_mode="HTML")
        
        env = os.environ.copy()
        env["COUNT"] = parts[4]
        # Masukkan juga ke env jika script main.sh membutuhkannya via env var
        env["sub"] = sub_val 
        
        # Tambahkan flag -sub ke dalam command
        cmd = [
            "/bin/bash", "main.sh", 
            "-s", subject, 
            "-dr", parts[2], 
            "-m", "image", 
            "-ur", parts[3], 
            "-n", parts[5], 
            "-ss", parts[6], 
            "-p", parts[7],
            "-sub", sub_val  # Mengirim nilai sub (bisa kosong "")
        ]
        
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

# --- Perintah: /update (Git Pull & Restart Bot) ---
# --- Perintah: /update (Git Pull & Run via runbot.sh) ---
@bot.message_handler(commands=['update'])
def handle_update(message):
    if message.from_user.id != ALLOWED_ID:
        return
    
    try:
        repo_path = "/workspace/comfyui-esddin"
        runbot_path = "/workspace/comfyui-esddin/runbot.sh"

        bot.reply_to(message, "🔄 <b>Updating code from Git...</b>", parse_mode="HTML")

        # 1. Git Pull
        pull_output = subprocess.check_output(["git", "-C", repo_path, "pull"]).decode("utf-8")
        bot.send_message(message.chat.id, f"📥 <b>Git Output:</b>\n<code>{pull_output}</code>", parse_mode="HTML")

        # 2. Eksekusi runbot.sh menggunakan source
        # Kita bungkus dalam bash -c agar environment ter-export dengan benar
        # Gunakan TOKEN yang sedang dipakai bot saat ini sebagai parameter $1
        bot.send_message(message.chat.id, "♻️ <b>Executing runbot.sh & Restarting...</b>", parse_mode="HTML")
        
        restart_cmd = f"source {runbot_path} {TOKEN}"
        
        # start_new_session agar proses runbot tidak mati saat bot ini kena pkill
        subprocess.Popen(["/bin/bash", "-c", restart_cmd], cwd=repo_path, start_new_session=True)

    except Exception as e:
        bot.reply_to(message, f"❌ Error Update: <code>{str(e)}</code>", parse_mode="HTML")
        
# --- Perintah: /printrun (Generate Macro Commands) ---
@bot.message_handler(commands=['printrun'])
def handle_printrun(message):
    if message.from_user.id != ALLOWED_ID: return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Format: <code>/printrun subject_name</code>", parse_mode="HTML")
            return
        
        subject = parts[1]
        base_path = f"/workspace/runpod-slim/ComfyUI/input/renamed/{subject}"
        
        if not os.path.exists(base_path):
            bot.reply_to(message, f"❌ Subject tidak ditemukan:\n<code>{base_path}</code>", parse_mode="HTML")
            return

        # Fungsi helper untuk hitung file
        def get_count(sub, mode):
            p = os.path.join(base_path, sub, mode, "*")
            return len([f for f in glob.glob(p) if os.path.isfile(f)])

        # Ambil data count
        fb_solo = get_count("full_body", "solo")
        fb_group = get_count("full_body", "group")
        hb_solo = get_count("half_body", "solo")
        hb_group = get_count("half_body", "group")

        # Susun response (Semua dibungkus <code> agar sekali tap langsung copy)
        res = f"🚀 <b>Macro Run for: {subject}</b>\n\n"
        
        # 1. Full Body -> Solo
        res += f"<b>Full Body - Solo ({fb_solo})</b>\n"
        res += f"<code>/run {subject} nt nt {fb_solo} true true 100000 full_body</code>\n\n"
        
        # 2. Full Body -> Group
        res += f"<b>Full Body - Group ({fb_group})</b>\n"
        res += f"<code>/run {subject} nt nt {fb_group} true false 200000 full_body</code>\n\n"
        
        # 3. Half Body - Solo
        res += f"<b>Half Body - Solo ({hb_solo})</b>\n"
        res += f"<code>/run {subject} nt nt {hb_solo} false true 300000 half_body</code>\n\n"
        
        # 4. Half Body - Group
        res += f"<b>Half Body - Group ({hb_group})</b>\n"
        res += f"<code>/run {subject} nt nt {hb_group} false false 400000 half_body</code>"

        bot.reply_to(message, res, parse_mode="HTML")

    except Exception as e:
        bot.reply_to(message, f"❌ Error PrintRun: <code>{str(e)}</code>", parse_mode="HTML")
        
# --- Perintah: /inspect (Cek Status ComfyUI - Path Fixed) ---
@bot.message_handler(commands=['inspect'])
def handle_inspect(message):
    if message.from_user.id != ALLOWED_ID: return
    
    try:
        # Path absolut sesuai instruksi terbaru
        inspect_script = "/workspace/comfyui-esddin/comfy_inspect.py"
        venv_python = "/workspace/runpod-slim/ComfyUI/.venv/bin/python"
        
        if not os.path.exists(inspect_script):
            bot.reply_to(message, f"❌ File tidak ditemukan di:\n<code>{inspect_script}</code>", parse_mode="HTML")
            return

        bot.reply_to(message, "🔍 <b>Inspecting ComfyUI Status...</b>", parse_mode="HTML")

        # Jalankan script menggunakan python dari venv
        output = subprocess.check_output([venv_python, inspect_script], stderr=subprocess.STDOUT).decode("utf-8")

        # Tampilkan hasil dengan tag <pre> agar formatting terminal tidak berantakan
        response = f"📋 <b>ComfyUI Inspector Result:</b>\n<pre>{output}</pre>"
        
        # Telegram punya limit 4096 karakter per pesan
        if len(response) > 4000:
            response = response[:4000] + "\n...(truncated)"
            
        bot.reply_to(message, response, parse_mode="HTML")

    except subprocess.CalledProcessError as e:
        error_out = e.output.decode("utf-8")
        bot.reply_to(message, f"❌ <b>Inspect Error:</b>\n<pre>{error_out}</pre>", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"❌ <b>Error:</b> <code>{str(e)}</code>", parse_mode="HTML")
print("--- BOT IS RUNNING ---")
bot.infinity_polling()