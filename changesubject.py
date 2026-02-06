#!/usr/bin/env python3
import json
import argparse
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(
        description="Patch ComfyUI workflow (overwrite input by default)"
    )
    ap.add_argument(
        "--in",
        dest="infile",
        default="workflow.json",
        help="Input workflow JSON (default: workflow.json)"
    )
    ap.add_argument(
        "--out",
        default=None,
        help="Output workflow JSON (default: overwrite input file)"
    )

    ap.add_argument("--dir", required=True, help='e.g. "input/raw/ka_young2000"')
    ap.add_argument("--idx", required=True, help='e.g. "ka_young2000_1"')
    ap.add_argument("--subject", required=True, help='e.g. "ka_young2000"')
    ap.add_argument("--idxtext", required=True, help='e.g. "ka_young2000_1idx"')
    ap.add_argument("--prefixnum", required=True, help='e.g. "100000"')
    args = ap.parse_args()

    infile = Path(args.infile)
    outfile = Path(args.out) if args.out else infile  # 🔥 overwrite by default

    with infile.open("r", encoding="utf-8") as f:
        data = json.load(f)

    prompt = data["prompt"]

    # 1) directory_path
    prompt["243"]["inputs"]["directory_path"] = args.dir

    # 2) idx base string
    prompt["489"]["inputs"]["value"] = args.idx

    # 3) subject
    prompt["501"]["inputs"]["value"] = args.subject

    # 4) idx text
#    prompt["483:492"]["inputs"]["text_0"] = args.idxtext
    # 5) PREFIX_NUM
    prompt["546"]["inputs"]["value"] = args.prefixnum
    with outfile.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("✅ workflow patched")
    print(f"- file    : {outfile}")
    print(f"- dir     : {args.dir}")
    print(f"- idx     : {args.idx}")
    print(f"- subject : {args.subject}")
    print(f"- idxtext : {args.idxtext}")
    print(f"- prefixnum : {args.prefixnum}")
if __name__ == "__main__":
    main()
