#!/usr/bin/env bash
set -euo pipefail

# Validasi argumen (Sekarang minimal 8 karena ada PRF_PATH di $7 dan TELE_TOKEN di $8)
if [[ $# -lt 8 ]]; then
  echo "Usage: $0 <json_file> <ftp> <subject> <hf_gm> <hf_nt> <hf_jp> <prf_path> <tele_token>"
  exit 1
fi

# Assignment variabel
JF="$1"
FTP="$2"
SUBJECT="$3"
HF_TOKEN_GM="$4"
HF_TOKEN_NT="$5"
HF_TOKEN_JP="$6"
PRF_PATH="$7"
TELE_TOKEN="$8" # Parameter baru

# Konfigurasi Standar
URL="http://127.0.0.1:8188/prompt"
MAIN_OUT="/workspace/runpod-slim/ComfyUI/output"
DST_PATH="/workspace/runpod-slim/${SUBJECT}"
REPO_ID_GM="gmesddin/raw-asia"
REPO_ID_NT="nutakuesddin/raw-ign"
REPO_ID_JP="jpesddin/raw-ig"
PATH_FORMAT="${PRF_PATH}/${SUBJECT}"

# ---------------------------------------------------------
# FUNGSI AUTO-EXPORT PERMANEN
# ---------------------------------------------------------
function add_to_bashrc() {
    local var_name=$1
    local var_value=$2
    
    if ! grep -q "export $var_name=" ~/.bashrc; then
        echo "export $var_name=\"$var_value\"" >> ~/.bashrc
        echo "✅ $var_name added to .bashrc"
    else
        sed -i "s|export $var_name=.*|export $var_name=\"$var_value\"|g" ~/.bashrc
        echo "🔄 $var_name updated in .bashrc"
    fi
}

echo "Updating .bashrc with all environment variables..."

# Export variabel path & config
add_to_bashrc "JF" "$JF"
add_to_bashrc "FTP" "$FTP"
add_to_bashrc "SUBJECT" "$SUBJECT"
add_to_bashrc "MAIN_OUT" "$MAIN_OUT"
add_to_bashrc "DST_PATH" "$DST_PATH"
add_to_bashrc "URL" "$URL"
add_to_bashrc "PATH_FORMAT" "$PATH_FORMAT"
add_to_bashrc "PRF_PATH" "$PRF_PATH"

# Export token & repo ID
add_to_bashrc "HF_TOKEN_GM" "$HF_TOKEN_GM"
add_to_bashrc "HF_TOKEN_NT" "$HF_TOKEN_NT"
add_to_bashrc "HF_TOKEN_JP" "$HF_TOKEN_JP"
add_to_bashrc "REPO_ID_GM" "$REPO_ID_GM"
add_to_bashrc "REPO_ID_NT" "$REPO_ID_NT"
add_to_bashrc "REPO_ID_JP" "$REPO_ID_JP"

# Export TELE_TOKEN ke .bashrc
add_to_bashrc "TELE_TOKEN" "$TELE_TOKEN"

# ---------------------------------------------------------
# SUNTIK LANGSUNG KE SESSION SEKARANG
# ---------------------------------------------------------
export JF="$JF"
export FTP="$FTP"
export SUBJECT="$SUBJECT"
export MAIN_OUT="$MAIN_OUT"
export DST_PATH="$DST_PATH"
export URL="$URL"
export PATH_FORMAT="$PATH_FORMAT"
export PRF_PATH="$PRF_PATH"
export HF_TOKEN_GM="$HF_TOKEN_GM"
export HF_TOKEN_NT="$HF_TOKEN_NT"
export HF_TOKEN_JP="$HF_TOKEN_JP"
export REPO_ID_GM="$REPO_ID_GM"
export REPO_ID_NT="$REPO_ID_NT"
export REPO_ID_JP="$REPO_ID_JP"
export TELE_TOKEN="$TELE_TOKEN" # Suntik ke session agar bot bisa langsung baca

echo "---------------------------------------------------------"
echo "Variables summarized:"
echo "Subject    : $SUBJECT"
echo "Tele Token : ${TELE_TOKEN:0:5}*** (Hidden)"
echo "---------------------------------------------------------"

# Eksekusi script selanjutnya
# python3 downloader.py dll...