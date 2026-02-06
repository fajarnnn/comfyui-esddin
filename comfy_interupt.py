import requests

BASE_URL = "http://127.0.0.1:8188"

try:
    requests.post(f"{BASE_URL}/interrupt", timeout=3)
    print("⛔ Interrupt sent")
except Exception as e:
    print("❌ Interrupt failed:", e)

