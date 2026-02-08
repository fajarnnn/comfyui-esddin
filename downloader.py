import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from huggingface_hub import HfApi, hf_hub_download
from huggingface_hub.hf_api import RepoFile

# ================= CONFIG =================
LOCAL_DIR = "/workspace/runpod-slim/ComfyUI/input/"
REPO_ID   = os.getenv("REPO_ID")        # wajib
SBJ       = os.getenv("SUBJECT")        # wajib
FTP       = (os.getenv("FTP") or "").lower().strip()   # image / video
PREFIX    = f"raw/{SBJ}"
MAX_WORKERS = 8
# =========================================

if not REPO_ID or not SBJ:
    raise RuntimeError("REPO_ID / SUBJECT env belum di-set")

# mapping ekstensi
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm", ".avi"}

if FTP == "image":
    ALLOW_EXT = IMAGE_EXT
elif FTP == "video":
    ALLOW_EXT = VIDEO_EXT
else:
    raise RuntimeError("FTP harus 'image' atau 'video'")

print("FTP mode :", FTP)
print("ALLOW_EXT:", sorted(ALLOW_EXT))
HTOK= os.getenv("HF_TOKEN")
print(HTOK)
os.makedirs(LOCAL_DIR, exist_ok=True)
api = HfApi()

items = list(api.list_repo_tree(
    repo_id=REPO_ID,
    repo_type="dataset",
    revision="main",
    path_in_repo=PREFIX,
    recursive=True,
    token=HTOK
))

# filter file
files = []
for it in items:
    if isinstance(it, RepoFile):
        ext = os.path.splitext(it.path)[1].lower()
        if ext in ALLOW_EXT:
            files.append(it.path)

print("Total files after filter:", len(files))

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

ok = 0
fail = 0

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
    futs = {ex.submit(dl, f): f for f in files}
    for i, fut in enumerate(as_completed(futs), 1):
        f = futs[fut]
        try:
            fut.result()
            ok += 1
        except Exception as e:
            fail += 1
            print("FAIL:", f, "->", repr(e))
        if i % 50 == 0 or i == len(files):
            print(f"Progress: {i}/{len(files)} (ok={ok}, fail={fail}, workers={MAX_WORKERS})")

print("DONE:", {"ok": ok, "fail": fail})
