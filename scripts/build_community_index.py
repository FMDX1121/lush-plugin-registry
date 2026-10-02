#!/usr/bin/env python3
"""
扫 submissions/*.json，为每条跑一遍验证 + 风险扫描，
生成 index-community.json。
"""
import os
import json
import subprocess
import tempfile
import zipfile
import io
import urllib.request
from datetime import datetime, timezone

SUBMIT_DIR = "submissions"
OUT_FILE = "index-community.json"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "LushRegistry/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def main():
    plugins = []

    for fname in sorted(os.listdir(SUBMIT_DIR)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(SUBMIT_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            entry = json.load(f)

        print(f"处理 {entry['id']}...")
        try:
            mf_raw = fetch(entry["manifest_url"])
            mf = json.loads(mf_raw.decode("utf-8"))
            zip_data = fetch(entry["download_url"])

            with tempfile.TemporaryDirectory() as td:
                with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                    zf.extractall(td)
                root = td
                if not os.path.isfile(os.path.join(td, "manifest.json")):
                    subs = [d for d in os.listdir(td)
                            if os.path.isdir(os.path.join(td, d))]
                    if len(subs) == 1:
                        root = os.path.join(td, subs[0])

                r = subprocess.run(
                    ["python", "scripts/scan_risk.py", root, "--json"],
                    capture_output=True, text=True
                )
                scan = json.loads(r.stdout)

            if scan["danger"]:
                print(f"  跳过（危险）")
                continue

            plugins.append({
                "id": mf["id"],
                "name": mf.get("name", mf["id"]),
                "version": mf["version"],
                "author": mf.get("author", ""),
                "description": mf.get("description", ""),
                "homepage": entry.get("homepage", ""),
                "manifest_url": entry["manifest_url"],
                "download_url": entry["download_url"],
                "icon_url": entry.get("icon_url") or mf.get("icon_url"),
                "size": len(zip_data),
                "tags": entry.get("tags", []),
                "verified": False,
                "submitted_at": entry.get("submitted_at") or _now(),
                "submitted_by": entry.get("submitter", ""),
                "scan_status": "warning" if scan["warning"] else "passed",
                "scan_warnings": scan["warning"],
                "scan_danger": [],
            })
        except Exception as e:
            print(f"  失败: {e}")
            continue

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "version": 1,
            "kind": "community",
            "updated_at": _now(),
            "count": len(plugins),
            "plugins": plugins,
        }, f, ensure_ascii=False, indent=2)

    print(f"写入 {OUT_FILE}，共 {len(plugins)} 条")


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    main()