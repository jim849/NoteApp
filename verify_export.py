"""Verify a NotesApp CSV export using the server's EXPORT_HMAC_KEY."""

import argparse
import hashlib
import hmac
import os
from pathlib import Path


def verify_export(data: bytes, key: bytes) -> bool:
    """Preserve CSV bytes exactly; only the final HMAC line is excluded."""
    lines = data.splitlines(keepends=True)
    prefix = b"# HMAC: "
    if not lines or not lines[-1].startswith(prefix):
        return False
    content = b"".join(lines[:-1])
    stored = lines[-1][len(prefix):].strip()
    expected = hmac.new(key, content, hashlib.sha256).hexdigest().encode("ascii")
    return hmac.compare_digest(expected, stored)


def main() -> int:
    parser = argparse.ArgumentParser(description="验证 NotesApp 成绩 CSV 的 HMAC")
    parser.add_argument("file", type=Path, help="待验证的 CSV 文件路径")
    args = parser.parse_args()
    key = os.environ.get("EXPORT_HMAC_KEY")
    if not key:
        print("无法验证：缺少 EXPORT_HMAC_KEY，请在 NotesApp 服务器容器内运行。")
        return 2
    try:
        data = args.file.read_bytes()
    except OSError as exc:
        print(f"无法读取文件：{exc}")
        return 2
    if verify_export(data, key.encode("utf-8")):
        print("CHECK PASSED：文件校验通过")
        return 0
    print("CHECK FAILED：内容或 HMAC 被修改、HMAC 缺失，或密钥不一致")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
