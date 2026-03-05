import time
import requests
import subprocess
import os
import re
import sys

# --- Konfigurasi ---
LOG_FILE = "/workspace/runpod-slim/comfyui.log"
TELE_TOKEN = "8667029481:AAH9hNvk9bIKGdEiFljJa6nnKjpu2LtCEMo"
TELE_ID = "1471991896"

def log_debug(msg):
    # Print ke terminal/monitor.log secara instan
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)

def send_tele(message):
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    payload = {"chat_id": TELE_ID, "text": message, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        log_debug(f"Telegram API Response: {r.status_code}")
    except Exception as e:
        log_debug(f"Telegram API Error: {e}")

def monitor():
    log_debug("!!! MONITOR SCRIPT STARTED !!!")
    log_debug(f"Targeting log: {LOG_FILE}")
    
    while True:
        if not os.path.exists(LOG_FILE):
            log_debug("CRITICAL: Log file target tidak ditemukan di path!")
        else:
            try:
                # Ambil snapshot log
                log_debug("Reading 100 lines from log...")
                raw_data = subprocess.check_output(f"tail -n 100 {LOG_FILE}", shell=True).decode('utf-8', errors='ignore')
                
                curr_match = re.findall(r"CURRENT_IDX\s*:\s*(\d+)", raw_data)
                total_match = re.findall(r"TOTAL_IMAGE\s*:\s*(\d+)", raw_data)
                
                log_debug(f"Matches found -> CURR_LIST: {curr_match} | TOTAL_LIST: {total_match}")

                if curr_match and total_match:
                    c = int(curr_match[-1])
                    t = int(total_match[-1])
                    actual = c + 1
                    log_debug(f"SUCCESS: Current Image {actual}/{t}")
                    
                    send_tele(f"⏳ <b>Update Progress</b>\nImage: {actual} / {t}")
                    
                    if actual >= t:
                        send_tele("✅ <b>Selesai!</b>")
                        log_debug("Workflow finished. Exiting...")
                        break
                else:
                    log_debug("WARNING: Pattern CURRENT_IDX/TOTAL_IMAGE tidak ditemukan di teks tail.")
            except Exception as e:
                log_debug(f"ERROR during loop: {e}")
        
        log_debug("Sleeping for 60 seconds...")
        time.sleep(60)

if __name__ == "__main__":
    monitor()