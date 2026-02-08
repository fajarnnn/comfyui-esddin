#!/usr/bin/env bash
set -euo pipefail

# Validasi argumen dulu (biar set -u gak ngamuk)
if [[ $# -lt 5 ]]; then
  echo "Usage: $0 <json_file> <ftp> <subject> <hf_token> <hf_token_app>"
  exit 1
fi

JF="$1"
FTP="$2"
SUBJECT="$3"
HF_TOKEN="$4"
HF_TOKEN_APP="$5"

URL="http://127.0.0.1:8188/prompt"
MAIN_OUT="/workspace/runpod-slim/ComfyUI/output"
DST_PATH="/workspace/runpod-slim/${SUBJECT}"

REPO_ID="jpesddin/raw-ig"
PRF_PATH="raw"
POST_PATH="/img_v"
PATH_FORMAT="${PRF_PATH}/${SUBJECT}${POST_PATH}"

export FTP JF URL SUBJECT MAIN_OUT DST_PATH REPO_ID PATH_FORMAT HF_TOKEN HF_TOKEN_APP

echo "JF=$JF"
echo "URL=$URL"
echo "FTP=$FTP"
echo "SUBJECT=$SUBJECT"
echo "MAIN_OUT=$MAIN_OUT"
echo "DST_PATH=$DST_PATH"
echo "REPO_ID=$REPO_ID"
echo "PATH_FORMAT=$PATH_FORMAT"
echo "HF_TOKEN=${HF_TOKEN:0:6}... (hidden)"
echo "HF_TOKEN_APP=${HF_TOKEN_APP:0:6}... (hidden)"

echo "+++++++++++++++++++++++++++++++++++++++++++++++++++++"
echo "START Downloading Source"
echo "+++++++++++++++++++++++++++++++++++++++++++++++++++++"
python3 downloader.py

echo "+++++++++++++++++++++++++++++++++++++++++++++++++++++"
echo "Replace Subject JSON"
echo "+++++++++++++++++++++++++++++++++++++++++++++++++++++"

# Backup yang gak ketiban
# cp -n ANNVIDEOV1.2.json "ANNVIDEOV1.2.json.bak" || true

# Lebih aman: edit di copy biar file asli gak nempel berubah
cp ANNVIDEOV1.2.json ANNVIDEOV1.2.json.tmp
sh replacer.sh "SBJ" "$SUBJECT" ANNVIDEOV1.2.json.tmp
mv ANNVIDEOV1.2.json.tmp annvidprompt.json

echo "+++++++++++++++++++++++++++++++++++++++++++++++++++++"
echo "START INSTALLING COMFYUI CUSTOM NODES & DEPENDENCY"
echo "+++++++++++++++++++++++++++++++++++++++++++++++++++++"
bash ins.sh
