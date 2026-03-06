#!/usr/bin/env bash
set -e

# =========================================================
# WRAPPER FOR ins.sh
# Usage: ./run_ins.sh <HF_TOKEN_APP> [TELE_TOKEN] [TELE_ID]
# =========================================================

# 1. Validasi Argumen Wajib (HF_TOKEN_APP)
if [[ -z "${1:-}" ]]; then
    echo "❌ ERROR: HF_TOKEN_APP wajib diisi sebagai parameter pertama!"
    echo "Usage: $0 <HF_TOKEN_APP> [TELE_TOKEN] [TELE_ID]"
    exit 1
fi

# 2. Assignment ke Environment Variables
export HF_TOKEN_APP="$1"

# 3. Parameter Optional (Jika tidak diisi, pakai value lama atau default)
export TELE_TOKEN="${2:-$TELE_TOKEN}"
export TELE_ID="${3:-${TELE_ID:-1471991896}}"

echo "---------------------------------------------------------"
echo "🚀 Preparing to run ins.sh..."
echo "HF_TOKEN_APP : ${HF_TOKEN_APP:0:6}***"
echo "TELE_TOKEN   : ${TELE_TOKEN:0:6}***"
echo "TELE_ID      : $TELE_ID"
echo "---------------------------------------------------------"

# 4. Memastikan ins.sh punya izin eksekusi
chmod +x ins.sh

# 5. Memanggil ins.sh
# Kita pakai 'bash ins.sh' agar variabel yang di-export di sini terbawa ke dalam
bash ./ins.sh

echo "✅ Proses Wrapper Selesai."