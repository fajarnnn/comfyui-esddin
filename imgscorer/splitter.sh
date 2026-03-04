SRC_DIR="/workspace/runpod-slim/ComfyUI/input/qwen/${SUBJECT}_qwen"
DUPE_DIR="/workspace/runpod-slim/ComfyUI/input/qwen/${SUBJECT}_qwen/dupe"

echo "Processing Subject: $SUBJECT"
echo "Source: $SRC_DIR"

# Buat folder dupe jika belum ada
mkdir -p "$DUPE_DIR"

# Cek apakah direktori sumber ada
if [ ! -d "$SRC_DIR" ]; then
    echo "Error: Directory $SRC_DIR tidak ditemukan!"
    exit 1
fi

declare -A seen

# Gunakan nullglob agar jika folder kosong tidak memproses string "*"
shopt -s nullglob

for file in "$SRC_DIR"/*; do
    # Lewati jika itu folder (termasuk folder dupe itu sendiri)
    [ -f "$file" ] || continue

    name=$(basename "$file")

    # Ambil nama dasar tanpa ekstensi
    base="${name%.*}"

    # Ambil N field pertama berdasarkan delimiter _
    key=$(echo "$base" | cut -d'_' -f1-"$CUT_FIELDS")

    if [[ -n "${seen[$key]:-}" ]]; then
        mv "$file" "$DUPE_DIR/"
        echo "MOVED  [$key] -> $name"
    else
        seen["$key"]=1
        echo "KEEP   [$key] -> $name"
    fi
done

echo "Done! File duplikat dipindahkan ke: $DUPE_DIR"