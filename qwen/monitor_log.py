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
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def get_latest_val(pattern, text):
    # Mencari angka terakhir dari pola (misal CURRENT_IDX: 23)
    matches = re.findall(rf"{pattern}\s*:\s*(\d+)", text)
    return int(matches[-1]) if matches else None

def monitor():
    print(f"Monitoring log {LOG_FILE} tiap 1 menit...")
    
    while True:
        if os.path.exists(LOG_FILE):
            try:
                # Ambil snapshot 50 baris terakhir
                result = subprocess.check_output(["tail", "-n", "50", LOG_FILE]).decode('utf-8')
                
                curr_idx = get_latest_val("CURRENT_IDX", result)
                total_img = get_latest_val("TOTAL_IMAGE", result)

                if curr_idx is not None and total_img is not None:
                    actual_curr = curr_idx + 1
                    
                    # Kirim laporan rutin tiap menit
                    msg = f"⏳ <b>Update Progress</b>\nImage: <code>{actual_curr}</code> / <code>{total_img}</code>"
                    send_tele(msg)
                    
                    # Cek kalau sudah benar-benar selesai
                    if actual_curr >= total_img:
                        send_tele(f"✅ <b>Workflow Selesai!</b>\nTotal {total_img} image telah diproses.")
                        print("Selesai. Mematikan monitor...")
                        break
            except Exception as e:
                print(f"Error: {e}")
        
        # Tunggu 1 menit untuk pengecekan berikutnya
        time.sleep(60)

if __name__ == "__main__":
    monitor()