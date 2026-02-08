#!/usr/bin/env bash
set -euo pipefail

SUBJECT="$3"
HF_TOKEN="$4"
HF_TOKE_APP="$5"
MAIN_OUT="/workspace/runpod-slim/ComfyUI/output"
DST_PATH="/workspace/runpod-slim/${SUBJECT}"

REPO_ID="jpesddin/raw-ig"
PRF_PATH="raw"
POST_PATH="/img_v"
PATH_FORMAT="${PRF_PATH}/${SUBJECT}${POST_PATH}"
if [[ -z "${1:-}" ]]; then
  echo "Usage: source runnerenv.sh <json_file>"
  return 1 2>/dev/null || exit 1
fi

JF="$1"
URL="http://127.0.0.1:8188/prompt"
FTP="$2"
export FTP
export JF
export URL

echo "JF=$JF"
echo "URL=$URL"
echo "FTP=$FTP"
export SUBJECT
export MAIN_OUT
export DST_PATH
export REPO_ID
export PATH_FORMAT
export HF_TOKEN
export HF_TOKEN_APP

echo "SUBJECT=$SUBJECT"
echo "MAIN_OUT=$MAIN_OUT"
echo "DST_PATH=$DST_PATH"
echo "REPO_ID=$REPO_ID"
echo "PATH_FORMAT=$PATH_FORMAT"
echo "HF_TOKEN=${HF_TOKEN:0:6}... (hidden)"
echo "HF_TOKEN_APP=${HF_TOKEN:0:6}... (hidden)"