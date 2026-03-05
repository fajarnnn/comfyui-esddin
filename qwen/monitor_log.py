import time
import requests
import re
import os

# --- Konfigurasi ---
LOG_FILE = "/workspace/runpod-slim/comfyui.log"
TELE_TOKEN = "8667029481:AAH9hNvk9bIKGdEiFljJa6nnKjpu2LtCEMo"
TELE_ID = "1471991896"

def send_tele(message):
    url = f"https://api.telegram.org/bot{TELE_TOKEN}/sendMessage"
    payload = {"chat_id": TELE_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Gagal kirim Telegram: {e}")

def monitor_log():
    print(f"Memulai pemantauan log: {LOG_FILE}")
    
    # Variabel untuk tracking progres
    last_sent_percent = 0
    
    # Pastikan file ada sebelum mulai
    while not os.path.exists(LOG_FILE):
        time.sleep(1)

    with open(LOG_FILE, "r") as f:
        # Pindah ke baris paling akhir
        f.seek(0, 2)
        
        while True:
            line = f.readline()
            if not line:
                time.sleep(1)
                continue
            
            # Cari baris CURRENT_IDX dan TOTAL_IMAGE
            if "CURRENT_IDX:" in line:
                try:
                    curr_idx = int(line.split(":")[1].strip())
                    # Kita butuh baris TOTAL_IMAGE juga, biasanya muncul berurutan
                    # Baca baris berikutnya untuk ambil TOTAL_IMAGE
                    next_line = f.readline()
                    if "TOTAL_IMAGE:" in next_line:
                        total_img = int(next_line.split(":")[1].strip())
                        
                        actual_curr = curr_idx + 1
                        progress = (actual_curr / total_img) * 100
                        
                        # Cek kelipatan 25% (25, 50, 75)
                        # Kita pakai interval agar tidak spam jika log menulis berulang
                        for p in [25, 50, 75]:
                            if progress >= p > last_sent_percent:
                                send_tele(f"📊 <b>Progres Workflow</b>\nProses: {p}%\nDetail: {actual_curr}/{total_img} Image")
                                last_sent_percent = p
                        
                        # Cek jika sudah selesai
                        if actual_curr >= total_img:
                            send_tele(f"✅ <b>Workflow Selesai!</b>\nTotal: {total_img}/{total_img} Image berhasil diproses.")
                            print("Selesai. Mematikan monitor...")
                            break
                except Exception as e:
                    print(f"Error parsing log: {e}")

if __name__ == "__main__":
    monitor_log()