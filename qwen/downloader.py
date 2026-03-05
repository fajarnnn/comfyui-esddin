import os
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from huggingface_hub import hf_hub_download, HfApi
from huggingface_hub.hf_api import RepoFile

# ================= ARGS SETUP =================
parser = argparse.ArgumentParser(description="HF Downloader")
# Pakai --repo untuk milih gm/nt/jp
parser.add_argument("--repo", type=str, choices=["gm", "nt", "jp"], required=True)
# Pakai --prefix untuk milih folder (qwen/final/raw)
parser.add_argument("--prefix", type=str, default="qwen")
args = parser.parse_args()

# ================= CONFIG & MAPPING =================
REPO_CONFIG = {
    "gm": {"repo": "gmesddin/raw-asia", "token": "HF_TOKEN_GM"},
    "nt": {"repo": "nutakuesddin/raw-ign", "token": "HF_TOKEN_NT"},
    "jp": {"repo": "jpesddin/raw-ig", "token": "HF_TOKEN_JP"}
}

LOCAL_DIR = "/workspace/runpod-slim/ComfyUI/input/"
SBJ = os.getenv("SUBJECT")
# FTP tetep ambil dari ENV (isinya: image / video)
FTP_MODE = (os.getenv("FTP") or "image").lower().strip()

# Penentuan Repo & Token dari Args
REPO_ID = REPO_CONFIG[args.repo]["repo"]
token_env_name = REPO_CONFIG[args.repo]["token"]
HTOK = os.getenv(token_env_name)

# Prefix dinamis dari Args + Env Subject
PREFIX = f"{args.prefix}/{SBJ}"
MAX_WORKERS = 8

# Mapping ekstensi berdasarkan FTP mode
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
ALLOW_EXT = IMAGE_EXT if FTP_MODE == "image" else VIDEO_EXT

# ================= VALIDASI =================
if not SBJ:
    raise RuntimeError("SUBJECT env kosong!")
if not HTOK:
    raise RuntimeError(f"Token {token_env_name} tidak ditemukan!")

print(f"🚀 Starting Download")
print(f"Target Repo : {REPO_ID}")
print(f"Prefix Path : {PREFIX}")
print(f"FTP Mode    : {FTP_MODE}") # image atau video

os.makedirs(LOCAL_DIR, exist_ok=True)
api = HfApi(token=HTOK)

# --- Proses List & Filter ---
try:
    items = list(api.list_repo_tree(
        repo_id=REPO_ID,
        repo_type="dataset",
        path_in_repo=PREFIX,
        recursive=True
    ))
except Exception as e:
    print(f"❌ Error listing repo (cek path prefix): {e}")
    items = []

files = [
    it.path for it in items 
    if isinstance(it, RepoFile) and os.path.splitext(it.path)[1].lower() in ALLOW_EXT
]

print(f"Total files to download: {len(files)}")

# --- Proses Download ---
def dl(path_in_repo: str):
    return hf_hub_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        filename=path_in_repo,
        local_dir=LOCAL_DIR,
        local_dir_use_symlinks=False,
        resume_download=True,
        token=HTOK
    )

ok, fail = 0, 0
if files:
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(dl, f): f for f in files}
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                fut.result()
                ok += 1
            except Exception as e:
                fail += 1
                print(f"FAIL: {futs[fut]} -> {e}")
            
            if i % 50 == 0 or i == len(files):
                print(f"Progress: {i}/{len(files)} (ok={ok}, fail={fail})")

print(f"🏁 DONE: {{'ok': {ok}, 'fail': {fail}}}")