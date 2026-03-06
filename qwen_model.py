import os
import sys
from huggingface_hub import hf_hub_download

# --- Config ---
token = os.getenv("HF_TOKEN_APP")
# Path absolut sesuai permintaanmu
base_path = "/workspace/runpod-slim/ComfyUI/models/checkpoints"
repo_id = "Phr00t/Qwen-Image-Edit-Rapid-AIO"
file_name = "v19/Qwen-Rapid-AIO-NSFW-v19.safetensors"

if not token:
    print("❌ ERROR: HF_TOKEN_APP tidak ditemukan di env!")
    sys.exit(1)

print(f"🚀 Memulai download model ke: {base_path}")

try:
    # Buat folder jika belum ada
    os.makedirs(base_path, exist_ok=True)

    # Download file
    # local_dir_use_symlinks=False wajib agar file fisik yang didownload, bukan pointer
    downloaded_path = hf_hub_download(
        repo_id=repo_id,
        filename=file_name,
        token=token,
        local_dir=base_path,
        local_dir_use_symlinks=False
    )

    # Karena file di HF ada di dalam folder 'v19/', hf_hub_download akan membuat folder 'v19' di lokal.
    # Kita pindahkan ke root /checkpoints/ agar path-nya sesuai keinginanmu.
    expected_path = os.path.join(base_path, "Qwen-Rapid-AIO-NSFW-v19.safetensors")
    current_path = os.path.join(base_path, file_name)

    if os.path.exists(current_path):
        os.rename(current_path, expected_path)
        # Hapus folder v19 yang kosong
        v19_dir = os.path.dirname(current_path)
        if os.path.isdir(v19_dir) and not os.listdir(v19_dir):
            os.rmdir(v19_dir)
        
        print(f"✅ SUCCESS: Model sekarang berada di {expected_path}")
    else:
        print(f"✅ OK: Model sudah ada di {expected_path}")

except Exception as e:
    print(f"❌ FAILED: {str(e)}")