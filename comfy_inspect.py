#!/usr/bin/env python3
import argparse
import json
import sys
import time
from datetime import datetime

import requests


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def http_get(url, timeout=5.0):
    t0 = time.time()
    try:
        r = requests.get(url, timeout=timeout)
        latency = (time.time() - t0) * 1000
        if r.status_code >= 400:
            return None, r.status_code, latency, f"HTTP {r.status_code}"
        try:
            return r.json(), r.status_code, latency, ""
        except Exception:
            return None, r.status_code, latency, "Non-JSON response"
    except requests.exceptions.RequestException as e:
        latency = (time.time() - t0) * 1000
        return None, 0, latency, str(e)


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def kv(k, v):
    print(f"- {k}: {v}")


def main():
    ap = argparse.ArgumentParser(description="ComfyUI Inspector (ringkas by default)")
    ap.add_argument("--base-url", default="http://127.0.0.1:8188")
    ap.add_argument("--timeout", type=float, default=5.0)
    ap.add_argument("--warn-pending", type=int, default=20)
    ap.add_argument("--warn-running", type=int, default=1)
    ap.add_argument("--exit-nonzero-on-warn", action="store_true")
    ap.add_argument("--long", action="store_true", help="Tampilkan detail JSON (verbose)")
    args = ap.parse_args()

    base = args.base_url.rstrip("/")
    timeout = args.timeout
    warn = False

    print(f"[{now()}] ComfyUI Inspector")
    kv("Base URL", base)

    # ================= QUEUE =================
    section("QUEUE STATUS")
    q, status, latency, err = http_get(f"{base}/queue", timeout)

    kv("HTTP", status if status else "NO RESPONSE")
    kv("Latency", f"{latency:.1f} ms")

    if err:
        kv("Queue", f"NOT AVAILABLE ({err})")
    else:
        running = q.get("queue_running", [])
        pending = q.get("queue_pending", [])

        kv("Running jobs", len(running))
        kv("Pending jobs", len(pending))

        if len(pending) >= args.warn_pending:
            warn = True
            kv("WARN", f"Pending >= {args.warn_pending}")

        if args.long:
            print("\n[DETAIL] queue_running:")
            print(json.dumps(running, indent=2))
            print("\n[DETAIL] queue_pending:")
            print(json.dumps(pending, indent=2))

    # ================= SYSTEM (DEFAULT ON) =================
    section("SYSTEM STATUS")
    s, status, latency, err = http_get(f"{base}/system_stats", timeout)

    kv("HTTP", status if status else "NO RESPONSE")
    kv("Latency", f"{latency:.1f} ms")

    if err:
        kv("System", f"NOT AVAILABLE ({err})")
    else:
        # Ringkas aja
        kv("System endpoint", "AVAILABLE")
        kv("Top-level keys", list(s.keys()))

        # Best-effort info
        if "gpu" in s or "gpus" in s:
            kv("GPU info", "AVAILABLE")
        else:
            kv("GPU info", "UNKNOWN")

        if args.long:
            print("\n[DETAIL] system_stats:")
            print(json.dumps(s, indent=2))

    # ================= SUMMARY =================
    section("SUMMARY")
    if warn:
        kv("Status", "WARN")
        kv("Advice", "Pertimbangkan clear pending / throttle submit")
        if args.exit_nonzero_on_warn:
            sys.exit(2)
    else:
        kv("Status", "OK")

    sys.exit(0)


if __name__ == "__main__":
    main()

