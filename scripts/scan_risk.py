#!/usr/bin/env python3
"""
风险扫描 CLI（供 CI 使用）

用法:
    python scan_risk.py <解压后的插件目录>
    
退出码:
    0 = 通过（无警告、无危险）
    1 = 有警告（可通过 --allow-warnings 放行）
    2 = 有危险（必须拒绝）
"""
import os
import re
import sys
import json
import argparse

# ===== 从面板 plugins/manager.py 复制过来 =====
DANGER_SH_PATTERNS = [
    r'rm\s+-rf\s+/(?:\s|$)',
    r'mkfs\.',
    r'dd\s+if=.*of=/dev/sd',
    r'curl\s+[^|]*\|\s*(?:sh|bash)',
    r'wget\s+[^|]*\|\s*(?:sh|bash)',
    r'nc\s+-e\s',
    r'/dev/sd[a-z]',
    r'chmod\s+777\s+/',
]
WARN_PY_PATTERNS = [
    r'\bsubprocess\b',
    r'\bos\.system\b',
    r'\bos\.popen\b',
    r'\beval\s*\(',
    r'\bexec\s*\(',
    r'\b__import__\s*\(',
    r'\bctypes\b',
    r'\bsocket\b',
]


def _looks_like_elf(path):
    try:
        with open(path, "rb") as f:
            return f.read(4) == b"\x7fELF"
    except Exception:
        return False


def _is_shebang_script(path):
    try:
        with open(path, "rb") as f:
            return f.read(2) == b"#!"
    except Exception:
        return False


def _safe_read_text(path, limit=512 * 1024):
    try:
        with open(path, "rb") as f:
            data = f.read(limit)
        return data.decode("utf-8", errors="replace")
    except Exception:
        return None


def scan_risk(root):
    danger, warning, info = [], [], []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".git")]
        for fname in filenames:
            fp = os.path.join(dirpath, fname)
            rel = os.path.relpath(fp, root).replace(os.sep, "/")
            ext = os.path.splitext(fname)[1].lower()

            try:
                if ext in (".so", ".o", ".a") or _looks_like_elf(fp):
                    warning.append(f"包含 ELF/共享库: {rel}")

                if ext in (".sh", ".bash") or _is_shebang_script(fp):
                    text = _safe_read_text(fp)
                    if text:
                        for pat in DANGER_SH_PATTERNS:
                            if re.search(pat, text):
                                danger.append(f"危险脚本: {rel} 命中 {pat}")

                if ext == ".py":
                    text = _safe_read_text(fp)
                    if text:
                        for pat in WARN_PY_PATTERNS:
                            if re.search(pat, text):
                                warning.append(f"Python 使用敏感 API: {rel} 命中 {pat}")
            except Exception as e:
                info.append(f"扫描 {rel} 失败: {e}")

    return {"danger": danger, "warning": warning, "info": info}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="解压后的插件目录")
    ap.add_argument("--allow-warnings", action="store_true",
                    help="有警告时也返回 0（仅用于官方提交）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    result = scan_risk(args.path)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for k in ("danger", "warning", "info"):
            for item in result[k]:
                print(f"[{k.upper()}] {item}")

    if result["danger"]:
        sys.exit(2)
    if result["warning"] and not args.allow_warnings:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()