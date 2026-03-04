import os
import time
import shutil
from pathlib import Path
from typing import List, Tuple
from huggingface_hub import HfApi

# ================= CONFIG =================
SUBJECT = os.getenv("SUBJECT")

SRC = Path(os.getenv("MAIN_OUT", ""))
DST_ROOT = Path(os.getenv("DST_PATH", ""))
INBOX = DST_ROOT / "inbox"   # tempat file yang siap diupload

REPO_ID = os.getenv("REPO_ID")
PATH_IN_REPO = os.getenv("PATH_FORMAT")  # contoh: "qwen/{subject}_qwen" (sudah di-resolve dari env kamu)

INTERVAL = 120  # detik
VERIFY_ON_ERROR = True       # kalau upload_folder error (timeout), verifikasi ke repo dulu
VERIFY_RETRIES = 3           # berapa kali retry verifikasi
VERIFY_SLEEP = 10            # jeda antar verifikasi (detik)
BATCH_SIZE = 0               # 0 = upload semua; >0 = upload per N file untuk mengurangi timeout
# =========================================

HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN kosong (set env HF_TOKEN dulu, jangan hardcode)")

if not SUBJECT:
    raise RuntimeError("SUBJECT kosong (set env SUBJECT)")
if not REPO_ID:
    raise RuntimeError("REPO_ID kosong (set env REPO_ID)")
if not PATH_IN_REPO:
    raise RuntimeError("PATH_FORMAT/PATH_IN_REPO kosong (set env PATH_FORMAT)")
if not SRC.exists():
    raise RuntimeError(f"MAIN_OUT tidak valid / tidak ada: {SRC}")
if not DST_ROOT:
    raise RuntimeError("DST_PATH kosong (set env DST_PATH)")

api = HfApi(token=HF_TOKEN)
INBOX.mkdir(parents=True, exist_ok=True)


def unique_dest_path(dst_dir: Path, filename: str) -> Path:
    """Kalau filename sudah ada di dst_dir, bikin nama baru: name.ext -> name__dup2.ext -> ..."""
    base = Path(filename).stem
    ext = Path(filename).suffix
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


def list_remote_files_set(repo_id: str, repo_type: str = "dataset") -> set:
    """Ambil semua path file di repo sebagai set (bisa agak berat kalau repo super gede)."""
    return set(api.list_repo_files(repo_id=repo_id, repo_type=repo_type))


def remote_has_all_local(
    repo_id: str,
    repo_type: str,
    path_in_repo: str,
    local_files: List[Path],
) -> Tuple[bool, List[str]]:
    """
    Cek apakah semua file local sudah ada di repo pada folder path_in_repo.
    Return: (ok, missing_paths_in_repo)
    """
    remote = list_remote_files_set(repo_id, repo_type=repo_type)
    prefix = path_in_repo.rstrip("/")
    expected = [f"{prefix}/{p.name}" for p in local_files]
    missing = [p for p in expected if p not in remote]
    return (len(missing) == 0), missing


def delete_files(files: List[Path]) -> int:
    deleted = 0
    for p in files:
        try:
            p.unlink(missing_ok=True)
            deleted += 1
        except Exception as e:
            print(f"⚠️ Gagal delete {p.name}: {e}")
    return deleted


def chunk_list(items: List[Path], n: int) -> List[List[Path]]:
    if n <= 0:
        return [items]
    return [items[i:i+n] for i in range(0, len(items), n)]


print("🚀 Auto-upload started")
print(f"SUBJECT    : {SUBJECT}")
print(f"INTERVAL   : {INTERVAL} detik")
print(f"REPO       : {REPO_ID}")
print(f"HF PATH    : {PATH_IN_REPO}")
print(f"BATCH_SIZE : {BATCH_SIZE if BATCH_SIZE > 0 else 'ALL'}")
print("=================================\n")

while True:
    try:
        # 1) MOVE file dari SRC yang prefix-nya SUBJECT -> INBOX
        moved = []
        for p in SRC.glob(f"{SUBJECT}*"):
            if p.is_file():
                moved.append(move_with_rename(p, INBOX))

        if moved:
            print(f"📦 Moved {len(moved)} file to inbox")

        # 2) Snapshot file inbox SAAT INI
        inbox_files_all = sorted([p for p in INBOX.iterdir() if p.is_file()])
        if not inbox_files_all:
            print("⏳ Tidak ada file baru, skip upload")
        else:
            batches = chunk_list(inbox_files_all, BATCH_SIZE)
            print(f"📤 Uploading {len(inbox_files_all)} file in {len(batches)} batch(es)...")

            for bi, inbox_files in enumerate(batches, start=1):
                print(f"➡️ Batch {bi}/{len(batches)}: {len(inbox_files)} file")

                upload_ok = False
                commit_info = None

                # Upload (selalu upload seluruh folder INBOX, tapi delete hanya batch yg kita proses)
                # Catatan: upload_folder upload isi folder; kalau BATCH_SIZE dipakai,
                # kita tetap aman karena kita delete per-batch, dan file yg belum dihapus akan ikut ke-commit berikutnya.
                try:
                    commit_info = api.upload_folder(
                        repo_id=REPO_ID,
                        repo_type="dataset",
                        folder_path=str(INBOX),
                        path_in_repo=PATH_IN_REPO,
                        commit_message=f"auto upload {SUBJECT} (batch {bi}/{len(batches)})"
                    )
                    print("✅ upload_folder returned:", commit_info)
                    upload_ok = True

                except Exception as e:
                    print("⚠️ upload_folder error:", e)

                    if VERIFY_ON_ERROR:
                        # Verifikasi beberapa kali (kadang butuh delay sampai listing repo update)
                        for vi in range(1, VERIFY_RETRIES + 1):
                            try:
                                ok, missing = remote_has_all_local(
                                    repo_id=REPO_ID,
                                    repo_type="dataset",
                                    path_in_repo=PATH_IN_REPO,
                                    local_files=inbox_files
                                )
                                if ok:
                                    print("✅ Verifikasi: file batch sudah ada di repo walau client timeout. Anggap sukses.")
                                    upload_ok = True
                                    break
                                else:
                                    print(f"🔎 Verifikasi {vi}/{VERIFY_RETRIES}: masih missing {len(missing)} file (contoh: {missing[:3]})")
                            except Exception as ve:
                                print(f"⚠️ Verifikasi {vi}/{VERIFY_RETRIES} error:", ve)

                            if vi < VERIFY_RETRIES:
                                time.sleep(VERIFY_SLEEP)

                # Delete hanya kalau yakin sukses
                if upload_ok:
                    deleted = delete_files(inbox_files)
                    print(f"🧹 Deleted {deleted}/{len(inbox_files)} file (batch {bi})")
                else:
                    print("❌ Batch belum terverifikasi sukses. File TIDAK dihapus, akan diretry loop berikutnya.")

            print("✅ Cycle done.")

    except Exception as e:
        print("⚠️ Error (aman, lanjut loop):", e)

    print(f"😴 Sleep {INTERVAL}s...\n")
    time.sleep(INTERVAL)
