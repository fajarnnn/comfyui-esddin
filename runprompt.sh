#!/usr/bin/env bash

COUNT=$1

if [[ -z "$COUNT" ]]; then
  echo "Usage: $0 <jumlah_loop>"
  exit 1
fi

for ((i=1; i<=COUNT; i++)); do
  echo "▶ Run $i / $COUNT"

  curl -s -X POST http://127.0.0.1:8188/prompt \
    -H "Content-Type: application/json" \
    -d @prompt2.json

  echo "✔ Done $i"
done

