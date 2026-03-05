import telebot
import subprocess
import os

# Konfigurasi
TOKEN = "8667029481:AAH9hNvk9bIKGdEiFljJa6nnKjpu2LtCEMo"
ALLOWED_ID = 1471991896
WORKDIR = "/workspace/comfyui-esddin/qwen"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['run'])
def handle_run(message):
    if message.from_user.id != ALLOWED_ID:
        bot.reply_to(message, "❌ Akses ditolak.")
        return

    try:
        # Format: /run <subject> <dr> <ur> <count> <isTrue> <isSolo> <prf>
        # Contoh: /run 23.11_ nt nt 150 true false 200000
        parts = message.text.split()
        
        if len(parts) < 8:
            msg = (
                "⚠️ *Format Salah!*\n\n"
                "Gunakan:\n"
                "`/run <subject> <dr> <ur> <count> <n> <ss> <prf>`\n\n"
                "Contoh:\n"
                "`/run 23.11_ nt nt 150 true false 200000`"
            )
            bot.reply_to(message, msg, parse_mode="Markdown")
            return

        # Mapping argumen
        subject = parts[1]
        dr      = parts[2]
        ur      = parts[3]
        count   = parts[4]
        n_val   = parts[5]
        ss_val  = parts[6]
        prf     = parts[7]

        bot.reply_to(message, f"🚀 *Workflow Dimulai!*\n"
                              f"Subject: `{subject}`\n"
                              f"Count: `{count}`\n"
                              f"PRF: `{prf}`", parse_mode="Markdown")

        # Menjalankan command dengan variabel environment COUNT
        # Kita set environment variable COUNT di sini
        env = os.environ.copy()
        env["COUNT"] = count

        cmd = [
            "/bin/bash", "main.sh",
            "-s", subject,
            "-dr", dr,
            "-ur", ur,
            "-n", n_val,
            "-ss", ss_val,
            "-p", prf
        ]

        # Jalankan di background
        subprocess.Popen(cmd, cwd=WORKDIR, env=env)

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

print("Bot standby, Jar...")
bot.infinity_polling()