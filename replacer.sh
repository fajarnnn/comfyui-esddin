#!/usr/bin/env bash
set -e

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <OLD> <NEW> <FILE>"
  exit 1
fi

OLD="$1"
NEW="$2"
FILE="$3"

# pakai delimiter | biar aman kalau ada /
sed -i "s|${OLD}|${NEW}|g" "$FILE"
