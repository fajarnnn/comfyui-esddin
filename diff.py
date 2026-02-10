import os
from huggingface_hub import HfApi, HfFileSystem

REPO_ID   = "gmesddin/raw-asia"                 # contoh: gmesddin/raw-asia
REPO_TYPE = os.getenv("REPO_TYPE", "dataset")    # dataset/model/space
HF_TOKEN  = ""               # hf_...

FOLDER_QWEN  = os.getenv("FOLDER_QWEN", "qwen").strip().strip("/")
FOLDER_FINAL = os.getenv("FOLDER_FINAL", "final").strip().strip("/")

if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN kosong")
if not REPO_ID:
    raise RuntimeError("REPO_ID kosong")

def _prefix(repo_type: str) -> str:
    return {"dataset":"datasets", "model":"models", "space":"spaces"}.get(repo_type, "datasets")

def list_level1_dirs_fast(hffs: HfFileSystem, base: str) -> set[str]:
    """
    Cara cepat: coba list subfolder level-1 dengan HfFileSystem.ls(detail=True).
    Kalau HF ngasih directory entries, ini super cepat.
    """
    root = f"{_prefix(REPO_TYPE)}/{REPO_ID}/{base}".rstrip("/")
    out = set()
    entries = hffs.ls(root, detail=True)

    for e in entries:
        # e biasanya dict: {"name": "...", "type": "directory"/"file", ...}
        if isinstance(e, dict):
            name = e.get("name") or e.get("path")
            typ  = e.get("type") or e.get("kind")
        else:
            name = getattr(e, "name", None) or getattr(e, "path", None) or str(e)
            typ  = getattr(e, "type", None) or getattr(e, "kind", None)

        if not name:
            continue

        is_dir = (typ in ("directory", "dir", "folder")) or str(name).endswith("/")
        if is_dir:
            out.add(str(name).rstrip("/").split("/")[-1])

    return out

def list_level1_dirs_fallback(api: HfApi, base: str) -> set[str]:
    """
    Cara pasti: parsing dari daftar file repo (bisa lebih lama kalau repo sangat besar).
    Ambil folder level-1 di bawah base (base/<folder>/...).
    """
    base = base.rstrip("/")
    pref = base + "/"
    out = set()

    for p in api.list_repo_files(repo_id=REPO_ID, repo_type=REPO_TYPE):
        if p.startswith(pref):
            rest = p[len(pref):]
            if "/" in rest:
                out.add(rest.split("/", 1)[0])

    return out

hffs = HfFileSystem(token=HF_TOKEN)
api  = HfApi(token=HF_TOKEN)
def normalize_qwen(name: str) -> str:
    return name[:-5] if name.endswith("_qwen") else name

# 1) Coba fast listing dulu
qwen_dirs  = list_level1_dirs_fast(hffs, FOLDER_QWEN)
final_dirs = list_level1_dirs_fast(hffs, FOLDER_FINAL)

# 2) Kalau fast listing gagal (kosong padahal harusnya ada), fallback yang pasti
if not qwen_dirs:
    qwen_dirs = list_level1_dirs_fallback(api, FOLDER_QWEN)

if not final_dirs:
    final_dirs = list_level1_dirs_fallback(api, FOLDER_FINAL)
qwen_norm = {normalize_qwen(n) for n in qwen_dirs}

only_in_qwen = sorted(qwen_norm - final_dirs)

print(f"Repo: {REPO_ID} ({REPO_TYPE})")
print(f"qwen  subfolders: {len(qwen_dirs)}")
print(f"final subfolders: {len(final_dirs)}")
print(f"Only in qwen (qwen \\ final): {len(only_in_qwen)}")
print("----")
for name in only_in_qwen:
    print(name)
