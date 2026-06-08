#!/usr/bin/env python3
"""macOS channel：osascript 通知；container 內 fallback 到 host 的 notify-server。

stdin 讀 JSON (NotifyMessage)。永遠 exit 0。
"""

import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

# 讓 channel 也能 import notify_lib（同 .claude/hooks 目錄底下）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from notify_lib.env import env_int, load_env  # noqa: E402
from notify_lib.truncate import truncate  # noqa: E402

_NOTIFY_SERVER_URL = "http://host.docker.internal:9999/notify"
_NOTIFY_SERVER_TIMEOUT = 5
_OSASCRIPT_TIMEOUT = 2


def _escape_applescript(s: str) -> str:
    """AppleScript 字面值內的 \\ 與 " 要 escape。"""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _send_osascript(title: str, subtitle: str, message: str) -> bool:
    if not shutil.which("osascript"):
        return False
    script = (
        f'display notification "{_escape_applescript(message)}" '
        f'with title "{_escape_applescript(title)}" '
        f'subtitle "{_escape_applescript(subtitle)}"'
    )
    try:
        subprocess.run(
            ["osascript", "-e", script],
            timeout=_OSASCRIPT_TIMEOUT,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.SubprocessError, OSError):
        return False


def _send_notify_server(title: str, subtitle: str, message: str) -> bool:
    payload = json.dumps(
        {"title": title, "message": message, "subtitle": subtitle},
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        _NOTIFY_SERVER_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_NOTIFY_SERVER_TIMEOUT):
            return True
    except (urllib.error.URLError, OSError):
        return False


def main() -> None:
    try:
        msg = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"macos channel: stdin not json: {e}", file=sys.stderr)
        return

    env_file = (
        Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())) / ".claude" / "hooks" / ".env"
    )
    env = load_env(env_file)
    max_len = env_int(env, "CLAUDE_NOTIFY_MACOS_MAX_LEN", 50)

    summary = truncate(msg.get("summary", ""), max_len)
    title = "Claude Code"
    subtitle = f"{msg['project_name']} — {msg['status_text']}"
    body = f"{msg['status_emoji']} {msg['status_text']}"
    if summary:
        body += f"：{summary}"

    if _send_osascript(title, subtitle, body):
        return
    _send_notify_server(title, subtitle, body)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"macos channel: {e}", file=sys.stderr)
    sys.exit(0)
