#!/usr/bin/env bash
set -Eeuo pipefail

# =======================
# Config
# =======================
COMFY_DIR="${COMFY_DIR:-/workspace/runpod-slim/ComfyUI}"
CUSTOM_NODES_DIR="$COMFY_DIR/custom_nodes"

# cari venv umum ComfyUI
VENV_DIR=""
for v in "$COMFY_DIR/venv" "$COMFY_DIR/.venv"; do
  if [[ -f "$v/bin/activate" ]]; then
    VENV_DIR="$v"
    break
  fi
done

CONTINUE_ON_ERROR="${CONTINUE_ON_ERROR:-1}"

CUSTOM_NODES=(
  "https://github.com/pythongosssss/ComfyUI-Custom-Scripts"
  "https://github.com/yolain/ComfyUI-Easy-Use"
  "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite"
  "https://github.com/strimmlarn/ComfyUI-Strimmlarns-Aesthetic-Score"
  "https://github.com/hgabha/WWAA-CustomNodes"
  "https://github.com/crystian/ComfyUI-Crystools"
  "https://github.com/jags111/efficiency-nodes-comfyui"
  "https://github.com/icekiub-ai/ComfyUI-IcyHider"
  "https://github.com/cubiq/ComfyUI_essentials"
  "https://github.com/Curt-Park/human-parser-comfyui-node-in-pure-python"
)

# =======================
# Helpers
# =======================
log()  { echo -e "[INFO] $*"; }
warn() { echo -e "[WARN] $*" >&2; }
die()  { echo -e "[ERR ] $*" >&2; exit 1; }

run_or_continue() {
  local msg="$1"
  shift
  if "$@"; then
    return 0
  else
    warn "$msg"
    [[ "$CONTINUE_ON_ERROR" == "1" ]] || exit 1
  fi
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Command not found: $1"
}

pip_install_req_if_exists() {
  local repo_dir="$1"
  local req="$repo_dir/requirements.txt"
  if [[ -f "$req" ]]; then
    log "pip install -r $(basename "$repo_dir")/requirements.txt (venv)"
    /workspace/runpod-slim/ComfyUI/.venv/bin/python -m pip install --no-cache-dir -r "$req"
  else
    log "No requirements.txt in $(basename "$repo_dir")"
  fi
}

# =======================
# Preflight
# =======================
need_cmd git

[[ -d "$COMFY_DIR" ]] || die "COMFY_DIR not found: $COMFY_DIR"
[[ -n "$VENV_DIR" ]]   || die "ComfyUI venv not found (expected venv/ or .venv/)"

mkdir -p "$CUSTOM_NODES_DIR"

log "ComfyUI dir      : $COMFY_DIR"
log "custom_nodes dir : $CUSTOM_NODES_DIR"
log "venv             : $VENV_DIR"

# =======================
# Activate venv
# =======================
log "Activating venv..."
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

log "python : $(python --version)"
log "pip    : $(pip --version)"

log "Upgrading pip/setuptools/wheel in venv..."
pip install --no-cache-dir -U pip setuptools wheel

# =======================
# Main
# =======================
for url in "${CUSTOM_NODES[@]}"; do
  name="$(basename "$url")"
  name="${name%.git}"
  dest="$CUSTOM_NODES_DIR/$name"

  log "========================================"
  log "Node: $name"

  if [[ -d "$dest/.git" ]]; then
    log "Updating repo"
    run_or_continue "git fetch failed: $name" git -C "$dest" fetch --all --prune
    run_or_continue "git pull failed: $name"  git -C "$dest" pull --rebase --autostash
  else
    log "Cloning repo"
    run_or_continue "git clone failed: $name" git clone --depth 1 "$url" "$dest"
  fi

  if [[ -f "$dest/.gitmodules" ]]; then
    log "Updating submodules"
    run_or_continue "submodule failed: $name" git -C "$dest" submodule update --init --recursive
  fi

  run_or_continue "pip install failed: $name" pip_install_req_if_exists "$dest"

  log "Done: $name"
done
python3 /workspace/comfyui-esddin/extra.py
mkdir -p /workspace/runpod-slim/ComfyUI/models/schp
wget -O /workspace/runpod-slim/ComfyUI/models/schp/exp-schp-201908270938-pascal-person-part.pth "https://huggingface.co/alexgenovese/controlnet/resolve/dde0b026ee9fbcb7cb8c262bfffa94dc00c87c69/exp-schp-201908270938-pascal-person-part.pth"
rm -rf /workspace/runpod-slim/ComfyUI/custom_nodes/nodes
git clone https://Esddin:$HF_TOKEN_APP@huggingface.co/datasets/Esddin/nodes --branch master /workspace/runpod-slim/ComfyUI/custom_nodes/nodes
pip install aesthetic-predictor-v2-5
pip install --no-build-isolation "clip @ git+https://github.com/openai/CLIP.git@dcba3cb2e2827b402d2701e7e1c7d9fed8a20ef1"
pip install pytorch_lightning
curl -s -X GET http://127.0.0.1:8188/manager/reboot
log "========================================"
log "All custom nodes installed into venv ✅"
log "Restart ComfyUI supaya node ke-load."
