import requests

BASE_URL = "http://127.0.0.1:8188"

try:
    requests.post(
        f"{BASE_URL}/queue",
        json={"clear": True},
        timeout=3
    )
    print("🧹 Pending queue cleared")
except Exception as e:
    print("❌ Clear pending failed:", e)

