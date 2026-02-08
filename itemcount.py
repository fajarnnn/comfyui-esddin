import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from huggingface_hub import HfApi, hf_hub_download
from huggingface_hub.hf_api import RepoFile

# ================= CONFIG =================
LOCAL_DIR = "/workspace/runpod-slim/ComfyUI/input/"
REPO_ID   = os.getenv("REPO_ID")        # wajib
SBJ       = os.getenv("SUBJECTLIST")        # wajib
FTP       = (os.getenv("FTPS") or "").lower().strip()   # image / video
POSTF     = os.getenv("POSTF") or ""
PREFIX    = f"raw/{SBJ}/{POSTF}"
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

print("SUBJECT :", SBJ)
print("FTP mode :", FTP)
print("ALLOW_EXT:", sorted(ALLOW_EXT))
print("PREFIX:", sorted(PREFIX))
print("REPO_ID:", sorted(REPO_ID))
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