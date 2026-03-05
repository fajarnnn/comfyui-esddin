import time
import requests
import subprocess
import os
import re

# --- Konfigurasi ---
LOG_FILE = "/workspace/runpod-slim/comfyui.log"
TELE_TOKEN = "8667029481:AAH9hNvk9bIKGdEiFljJa6nnKjpu2LtCEMo"
TELE_ID = "1471991896"

def send_tele(message):
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    payload = {"chat_id": TELE_ID, "text": message, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code
    except Exception as e:
        print(f"Telegram Error: {e}")
        return None

def get_latest_val(pattern, text):
    # Regex diperbaiki untuk menangkap angka di baris mana pun
    matches = re.findall(rf"{pattern}\s*:\s*(\d+)", text)
    if matches:
        return int(matches[-1])
    return None

def check_and_report():
    if not os.path.exists(LOG_FILE):
        print("Log file not found...")
        return False

    try:
        # Ambil snapshot 100 baris biar lebih aman
        result = subprocess.check_output(["tail", "-n", "100", LOG_FILE]).decode('utf-8', errors='ignore')
        
        curr_idx = get_latest_val("CURRENT_IDX", result)
        total_img = get_latest_val("TOTAL_IMAGE", result)

        if curr_idx is not None and total_img is not None:
            actual_curr = curr_idx + 1
            msg = f"⏳ <b>Update Progress</b>\nImage: <code>{actual_curr}</code> / <code>{total_img}</code>"
            send_tele(msg)
            
            if actual_curr >= total_img:
                send_tele("✅ <b>Workflow Selesai!</b>")
                return True # Berhenti kalau kelar
        else:
            print(f"Debug: Data belum lengkap (CURR: {curr_idx}, TOTAL: {total_img})")
    except Exception as e:
        print(f"Error: {e}")
    
    return False

def monitor():
    print(f"Monitor started... Reporting every 60s.")
    
    # HIT PERTAMA: Langsung lapor pas script jalan
    check_and_report()
    
    # LOOP SELANJUTNYA
    while True:
        time.sleep(60)
        should_stop = check_and_report()
        if should_stop:
            break

if __name__ == "__main__":
    monitor()