#!/usr/bin/env bash
set -euo pipefail

# Validasi argumen
if [[ $# -lt 6 ]]; then
  echo "Usage: $0 <json_file> <ftp> <subject> <hf_gm> <hf_nt> <hf_jp>"
  exit 1
fi

# Assignment variabel
JF="$1"
FTP="$2"
SUBJECT="$3"
HF_TOKEN_GM="$4"
HF_TOKEN_NT="$5"
HF_TOKEN_JP="$6"

# Konfigurasi Standar
URL="http://127.0.0.1:8188/prompt"
MAIN_OUT="/workspace/runpod-slim/ComfyUI/output"
DST_PATH="/workspace/runpod-slim/${SUBJECT}"
REPO_ID_GM="gmesddin/raw-asia"
REPO_ID_NT="nutakuesddin/raw-ign"
REPO_ID_JP="jpesddin/raw-ig"
PRF_PATH="$7"
PATH_FORMAT="${PRF_PATH}/${SUBJECT}"

# ---------------------------------------------------------
# FUNGSI AUTO-EXPORT PERMANEN
# ---------------------------------------------------------
function add_to_bashrc() {
    local var_name=$1
    local var_value=$2
    
    # Cek apakah variabel sudah ada di .bashrc
    if ! grep -q "export $var_name=" ~/.bashrc; then
        # Kalau belum ada, tambahkan di baris baru
        echo "export $var_name=\"$var_value\"" >> ~/.bashrc
        echo "✅ $var_name added to .bashrc"
    else
        # Kalau sudah ada, update nilainya pakai sed (delimiter | biar aman dari path /)
        sed -i "s|export $var_name=.*|export $var_name=\"$var_value\"|g" ~/.bashrc
        echo "🔄 $var_name updated in .bashrc"
    fi
}

echo "Updating .bashrc with all environment variables..."

# Export semua variabel yang lo butuhin
add_to_bashrc "SUBJECT" "$SUBJECT"
add_to_bashrc "MAIN_OUT" "$MAIN_OUT"
add_to_bashrc "DST_PATH" "$DST_PATH"
add_to_bashrc "URL" "$URL"
add_to_bashrc "PATH_FORMAT" "$PATH_FORMAT"

# Export semua token & repo ID
add_to_bashrc "HF_TOKEN_GM" "$HF_TOKEN_GM"
add_to_bashrc "HF_TOKEN_NT" "$HF_TOKEN_NT"
add_to_bashrc "HF_TOKEN_JP" "$HF_TOKEN_JP"
add_to_bashrc "REPO_ID_GM" "$REPO_ID_GM"
add_to_bashrc "REPO_ID_NT" "$REPO_ID_NT"
add_to_bashrc "REPO_ID_JP" "$REPO_ID_JP"

# Load ke session saat ini biar langsung bisa dipake script python dibawahnya
export SUBJECT MAIN_OUT DST_PATH URL PATH_FORMAT HF_TOKEN_GM HF_TOKEN_NT HF_TOKEN_JP REPO_ID_GM REPO_ID_NT REPO_ID_JP
# ---------------------------------------------------------

echo "+++++++++++++++++++++++++++++++++++++++++++++++++++++"
echo "ENV PERMANENTLY SAVED"
echo "+++++++++++++++++++++++++++++++++++++++++++++++++++++"

echo "START Downloading Source..."
python3 downloader.py

echo "Generating Workflow JSON..."
python3 imagescorejson.py --n 2 --subject "$SUBJECT" --filejson "$JF"

echo "DONE!"