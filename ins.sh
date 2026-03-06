#!/usr/bin/env bash
set -Eeuo pipefail

# =======================
# Config
# =======================
COMFY_DIR="/workspace/runpod-slim/ComfyUI"
CUSTOM_NODES_DIR="$COMFY_DIR/custom_nodes"
VENV_DIR="$COMFY_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"

CONTINUE_ON_ERROR="${CONTINUE_ON_ERROR:-1}"

CUSTOM_NODES=(
  "https://github.com/pythongosssss/ComfyUI-Custom-Scripts"
  "https://github.com/ltdrdata/ComfyUI-Impact-Pack"
  "https://github.com/yolain/ComfyUI-Easy-Use"
  "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite"
  "https://github.com/strimmlarn/ComfyUI-Strimmlarns-Aesthetic-Score"
  "https://github.com/hgabha/WWAA-CustomNodes"
  "https://github.com/crystian/ComfyUI-Crystools"
  "https://github.com/jags111/efficiency-nodes-comfyui"
  "https://github.com/cubiq/ComfyUI_essentials"
  "https://github.com/Curt-Park/human-parser-comfyui-node-in-pure-python"
  "https://github.com/icekiub-ai/ComfyUI-IcyHider"
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

pip_install_req_if_exists() {
  local repo_dir="$1"
  local req="$repo_dir/requirements.txt"
  if [[ -f "$req" ]]; then
    log "Installing requirements for $(basename "$repo_dir")..."
    # Menggunakan python -m pip agar 100% masuk ke venv yang benar
    "$PYTHON_BIN" -m pip install --no-cache-dir -r "$req"
  else
    log "No requirements.txt found in $(basename "$repo_dir"), skipping."
  fi
}

# =======================
# Preflight
# =======================
command -v git >/dev/null 2>&1 || die "Git tidak ditemukan!"

[[ -d "$COMFY_DIR" ]] || die "COMFY_DIR tidak ditemukan di: $COMFY_DIR"
[[ -x "$PYTHON_BIN" ]] || die "Venv Python tidak ditemukan di: $PYTHON_BIN"

mkdir -p "$CUSTOM_NODES_DIR"

log "Using Python from Venv: $PYTHON_BIN"

# =======================
# Upgrade Base Tools
# =======================
log "Upgrading pip, setuptools, and wheel di venv..."
"$PYTHON_BIN" -m pip install --no-cache-dir -U pip setuptools wheel

# =======================
# Main: Custom Nodes
# =======================
for url in "${CUSTOM_NODES[@]}"; do
  name="$(basename "$url")"
  name="${name%.git}"
  dest="$CUSTOM_NODES_DIR/$name"

  log "----------------------------------------"
  log "Processing Node: $name"

  if [[ -d "$dest/.git" ]]; then
    log "Updating existing repo..."
    run_or_continue "Git fetch failed: $name" git -C "$dest" fetch --all --prune
    run_or_continue "Git pull failed: $name"  git -C "$dest" pull --rebase --autostash
  else
    log "Cloning new repo..."
    run_or_continue "Git clone failed: $name" git clone --depth 1 "$url" "$dest"
  fi

  # Handle Submodules (Penting untuk beberapa node)
  if [[ -f "$dest/.gitmodules" ]]; then
    log "Updating submodules..."
    git -C "$dest" submodule update --init --recursive
  fi

  # Install requirements.txt milik node
  pip_install_req_if_exists "$dest"
done

# =======================
# Extra Dependencies & Models
# =======================
log "----------------------------------------"
log "Installing extra global dependencies..."

# Pastikan semua pip install tambahan juga pakai $PYTHON_BIN -m pip
"$PYTHON_BIN" -m pip install --no-cache-dir aesthetic-predictor-v2-5 pytorch_lightning pyTelegramBotAPI requests

# Install CLIP dengan no-build-isolation (sesuai kebutuhanmu)
"$PYTHON_BIN" -m pip install --no-cache-dir --no-build-isolation "clip @ git+https://github.com/openai/CLIP.git@dcba3cb2e2827b402d2701e7e1c7d9fed8a20ef1"

# Jalankan extra script jika ada
if [[ -f "/workspace/comfyui-esddin/extra.py" ]]; then
    "$PYTHON_BIN" /workspace/comfyui-esddin/extra.py
fi

# =======================
# File Management & Model Downloads
# =======================
log "Downloading models..."
mkdir -p "$COMFY_DIR/models/schp"
wget -q --show-progress -O "$COMFY_DIR/models/schp/exp-schp-201908270938-pascal-person-part.pth" \
"https://huggingface.co/alexgenovese/controlnet/resolve/dde0b026ee9fbcb7cb8c262bfffa94dc00c87c69/exp-schp-201908270938-pascal-person-part.pth"

# Custom Nodes via git (HuggingFace)
rm -rf "$CUSTOM_NODES_DIR/nodes"
git clone "https://Esddin:$HF_TOKEN_APP@huggingface.co/datasets/Esddin/nodes" --branch master "$CUSTOM_NODES_DIR/nodes"


# --- Bagian Download Model di ins.sh ---
log "Installing huggingface_hub..."
"$PYTHON_BIN" -m pip install --no-cache-dir huggingface_hub
# Checkpoint Download
if [[ -f "/workspace/comfyui-esddin/extra.py" ]]; then
    "$PYTHON_BIN" /workspace/comfyui-esddin/qwen_model.py
fi


# =======================
# Background Bot & Reboot
# =======================
log "Restarting bot_control.py..."
pkill -f bot_control.py || true
sleep 2
nohup nohup /workspace/runpod-slim/ComfyUI/.venv/bin/python /workspace/comfyui-esddin/qwen/bot_control.py > /workspace/comfyui-esddin/qwen/bot.log 2>&1 & /workspace/comfyui-esddin/qwen/bot_control.py > /workspace/comfyui-esddin/qwen/bot.log 2>&1 &

log "Rebooting ComfyUI Manager..."
curl -s -X GET http://127.0.0.1:8188/manager/reboot || warn "Gagal kirim reboot command (mungkin ComfyUI belum jalan)."

log "========================================"
log "Semua dependensi telah dipasang ke venv: $VENV_DIR ✅"