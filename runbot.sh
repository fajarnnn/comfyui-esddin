# 1. Install library (hanya perlu sekali, tapi aman dijalankan ulang)
pip install --no-cache-dir pyTelegramBotAPI requests

# 2. Ambil token dari parameter script
TOKEN_VALUE="$1"

# 3. Fungsi untuk update/tambah ke .bashrc agar tidak duplikat
function add_to_bashrc() {
    local var_name=$1
    local var_value=$2
    if ! grep -q "export $var_name=" ~/.bashrc; then
        echo "export $var_name=\"$var_value\"" >> ~/.bashrc
    else
        # Jika sudah ada, kita update nilainya pakai sed
        sed -i "s|export $var_name=.*|export $var_name=\"$var_value\"|g" ~/.bashrc
    fi
}

# Simpan TOKEN ke bashrc secara permanen
add_to_bashrc "TELE_TOKEN" "$TOKEN_VALUE"

# 4. Jalankan bot di background (Versi bersih tanpa duplikasi nohup)
# Kita pakai $TOKEN_VALUE langsung agar session sekarang langsung jalan
export TELE_TOKEN="$TOKEN_VALUE"

log "Starting bot_control.py in background..."
nohup python3 /workspace/comfyui-esddin/qwen/bot_control.py > /workspace/comfyui-esddin/qwen/bot.log 2>&1 &

log "Bot started and TELE_TOKEN has been saved to .bashrc ✅"