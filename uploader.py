import os
import time
import shutil
from pathlib import Path
from huggingface_hub import HfApi

# ================= CONFIG =================
SUBJECT = os.getenv("SUBJECT")

SRC = Path(os.getenv("MAIN_OUT"))
DST_ROOT = Path(os.getenv("DST_PATH"))
INBOX = DST_ROOT / "inbox"   # tempat file yang siap diupload

REPO_ID = os.getenv("REPO_ID")
PATH_IN_REPO = os.getenv("PATH_FORMAT")

INTERVAL = 60  # detik
# =========================================

HF_TOKEN = os.getenv("HF_TOKEN");
if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN kosong (set env HF_TOKEN dulu, jangan hardcode)")

api = HfApi(token=HF_TOKEN)

INBOX.mkdir(parents=True, exist_ok=True)

def unique_dest_path(dst_dir: Path, filename: str) -> Path:
    """
    Kalau filename sudah ada di dst_dir, bikin nama baru:
    name.ext -> name__dup2.ext -> name__dup3.ext -> ...
    """
    base = Path(filename).stem
    ext  = Path(filename).suffix
    candidate = dst_dir / f"{base}{ext}"
    if not candidate.exists():
        return candidate

    i = 2
    while True:
        candidate = dst_dir / f"{base}__dup{i}{ext}"
        if not candidate.exists():
            return candidate
        i += 1

def move_with_rename(src_path: Path, dst_dir: Path) -> Path:
    dst_path = unique_dest_path(dst_dir, src_path.name)
    shutil.move(str(src_path), str(dst_path))
    return dst_path

print("🚀 Auto-upload started")
print(f"SUBJECT  : {SUBJECT}")
print(f"INTERVAL : {INTERVAL} detik")
print(f"HF PATH  : {PATH_IN_REPO}")
print("=================================\n")

while True:
    try:
        # 1) MOVE file dari SRC yang prefix-nya SUBJECT -> INBOX
        moved = []
        for p in SRC.glob(f"{SUBJECT}*"):
            if p.is_file():
                newp = move_with_rename(p, INBOX)
                moved.append(newp)

        if moved:
            print(f"📦 Moved {len(moved)} file to inbox")

        # 2) Ambil snapshot file inbox SAAT INI (biar aman)
        inbox_files = [p for p in INBOX.iterdir() if p.is_file()]
        if not inbox_files:
            print("⏳ Tidak ada file baru, skip upload")
        else:
            print(f"📤 Uploading {len(inbox_files)} file...")

            # Upload folder inbox
            api.upload_folder(
                repo_id=REPO_ID,
                repo_type="dataset",
                folder_path=str(INBOX),
                path_in_repo=PATH_IN_REPO,
                commit_message=f"auto upload {SUBJECT}"
            )

            # 3) Kalau sukses, HAPUS file yang barusan diupload
            deleted = 0
            for p in inbox_files:
                try:
                    p.unlink(missing_ok=True)  # py>=3.8
                    deleted += 1
                except Exception as e:
                    print(f"⚠️ Gagal delete {p.name}: {e}")

            print(f"✅ Upload sukses (deleted {deleted}/{len(inbox_files)} file dari inbox)")

    except Exception as e:
        print("⚠️ Error (aman, lanjut loop):", e)

    print(f"😴 Sleep {INTERVAL}s...\n")
    time.sleep(INTERVAL)
