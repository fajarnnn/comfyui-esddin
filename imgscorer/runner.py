import requests
import os

URL = os.getenv("URL")
JSON_FILE = os.getenv("JF")

if not URL:
    raise RuntimeError("URL kosong (set env URL dulu)")
if not JSON_FILE:
    raise RuntimeError("JF kosong (set env JF dulu)")
if not os.path.isfile(JSON_FILE):
    raise RuntimeError(f"JSON file tidak ditemukan: {JSON_FILE}")

# === ambil COUNT ===
count_env = os.getenv("COUNT")
if count_env:
    COUNT = int(count_env)
else:
    inp = input("Masukkan COUNT (jumlah loop) [default 1]: ").strip()
    COUNT = int(inp) if inp else 1

with open(JSON_FILE, "rb") as f:
    payload = f.read()

print(f"\n ^=^z^` Start submit")
print(f"URL   : {URL}")
print(f"JSON  : {JSON_FILE}")
print(f"COUNT : {COUNT}\n")

for i in range(1, COUNT + 1):
    print(f" ^v  Run {i} / {COUNT}")

    try:
        r = requests.post(
            URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        r.raise_for_status()
        print(" ^|^t Done")
    except Exception as e:
        print(" ^}^l Error:", e)



