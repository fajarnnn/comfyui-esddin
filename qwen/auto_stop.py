
import time
import requests
import subprocess
import os
import sys

# --- Konfigurasi ---
POD_ID = "4vvw4zx4pguc07"
TELE_TOKEN = "8667029481:AAH9hNvk9bIKGdEiFljJa6nnKjpu2LtCEMo"
TELE_ID = "1471991896"

def send_tele(message):
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    payload = {"chat_id": TELE_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

if __name__ == "__main__":
    # Cek parameter jam, kalo gak ada default ke 2 jam
    try:
        hours = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
    except ValueError:
        print("Format salah! Pake angka, contoh: python3 auto_stop.py 2.5")
        sys.exit(1)

    total_seconds = int(hours * 3600)
    warning_threshold = 300  # 5 Menit
    
    if total_seconds <= warning_threshold:
        print("Durasi terlalu pendek, Bro!")
        sys.exit(1)

    print(f"🚀 Auto-Stop aktif untuk {hours} jam ke depan.")
    
    # Tunggu sampai sisa 5 menit
    time.sleep(total_seconds - warning_threshold)
    
    # Notif Telegram 5 Menit sebelum mati
    send_tele(f"⚠️ <b>WARNING:</b> Server mati 5 menit lagi.\nKetik <code>pkill -f auto_stop.py</code> kalo mau lanjut.")
    
    # Tunggu 5 menit terakhir
    time.sleep(warning_threshold)
    
    # Eksekusi Stop
    send_tele(f"🔌 <b>Auto-Stop:</b> Waktu {hours} jam habis. Mematikan Pod sekarang!")
    subprocess.run(["runpodctl", "stop", "pod", POD_ID])