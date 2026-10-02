#!/usr/bin/env python3
"""
校验一份 submissions/*.json：
1. JSON schema
2. 拉 manifest_url → 校验 manifest
3. 拉 download_url → 解压 → scan_risk
"""
import sys
import os
import json
import tempfile
import zipfile
import urllib.request
import subprocess

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "LushRegistry/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def main():
    if len(sys.argv) < 2:
        print("用法: validate_entry.py submissions/xxx.json")
        sys.exit(1)

    entry_path = sys.argv[1]
    with open(entry_path, "r", encoding="utf-8") as f:
        entry = json.load(f)

    # 1. 必填字段
    required = ["id", "manifest_url", "download_url", "submitter"]
    for k in required:
        if k not in entry:
            print(f"缺少字段: {k}")
            sys.exit(1)

    # 2. 拉 manifest
    print(f"拉取 manifest: {entry['manifest_url']}")
    try:
        raw = fetch(entry["manifest_url"])
        mf = json.loads(raw.decode("utf-8"))
    except Exception as e:
        print(f"manifest 拉取/解析失败: {e}")
        sys.exit(1)

    # 3. 校验 manifest 基本字段
    for k in ["id", "name", "version", "api_version", "entry", "plugin_class"]:
        if k not in mf:
            print(f"manifest 缺少字段: {k}")
            sys.exit(1)

    if mf["id"] != entry["id"]:
        print(f"id 不一致: 提交={entry['id']}, manifest={mf['id']}")
        sys.exit(1)

    # 4. 拉 zip
    print(f"→ 下载 zip: {entry['download_url']}")
    try:
        zip_data = fetch(entry["download_url"])
    except Exception as e:
        print(f"下载失败: {e}")
        sys.exit(1)

    # 5. 解压 + 扫描
    with tempfile.TemporaryDirectory() as td:
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            zf.extractall(td)

        # 找到插件根（可能是 td 或 td/xxx-1.0/）
        extract_root = td
        if not os.path.isfile(os.path.join(td, "manifest.json")):
            subs = [d for d in os.listdir(td)
                    if os.path.isdir(os.path.join(td, d))]
            if len(subs) == 1:
                extract_root = os.path.join(td, subs[0])

        # 6. 风险扫描
        r = subprocess.run(
            ["python", "scripts/scan_risk.py", extract_root, "--json"],
            capture_output=True, text=True
        )
        print(r.stdout)
        if r.returncode == 2:
            print("检测到危险内容，拒绝收录")
            sys.exit(1)
        if r.returncode == 1:
            print("有警告，将记录到索引 scan_warnings")

    print("校验通过")
    sys.exit(0)


if __name__ == "__main__":
    import io
    main()