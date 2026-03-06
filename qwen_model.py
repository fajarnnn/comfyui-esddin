import os
import sys
from huggingface_hub import hf_hub_download

# --- Config ---
token = os.getenv("HF_TOKEN_APP")
base_path = "/workspace/runpod-slim/ComfyUI/models/checkpoints"
repo_id = "Phr00t/Qwen-Image-Edit-Rapid-AIO"
file_name = "v19/Qwen-Rapid-AIO-NSFW-v19.safetensors"
final_filename = "Qwen-Rapid-AIO-NSFW-v19.safetensors"

if not token:
    print("❌ ERROR: HF_TOKEN_APP tidak ditemukan!")
    sys.exit(1)

try:
    os.makedirs(base_path, exist_ok=True)
    target_path = os.path.join(base_path, final_filename)

    if os.path.exists(target_path):
        print(f"✅ Model sudah ada, skip download.")
        sys.exit(0)

    print(f"📥 Downloading (Direct to Folder, No Cache)...")
    
    # local_dir_use_symlinks=False -> Jangan pakai link, tulis file asli.
    # Ditambah manual pindah folder agar tidak menumpuk di ~/.cache
    downloaded_path = hf_hub_download(
        repo_id=repo_id,
        filename=file_name,
        token=token,
        local_dir=base_path,
        local_dir_use_symlinks=False,
        # Ini triknya: paksa cache ke folder temp di dalam workspace 
        # supaya tidak makan quota root partition /dev/mapper
        cache_dir=os.path.join(base_path, ".cache_tmp") 
    )

    # Pindahkan file ke lokasi final
    current_loc = os.path.join(base_path, file_name)
    if os.path.exists(current_loc):
        os.rename(current_loc, target_path)
        
        # Bersihkan folder v19 dan .cache_tmp segera
        import shutil
        shutil.rmtree(os.path.join(base_path, "v19"), ignore_errors=True)
        shutil.rmtree(os.path.join(base_path, ".cache_tmp"), ignore_errors=True)
        
        print(f"✨ DONE: Model disimpan di {target_path}")

except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)