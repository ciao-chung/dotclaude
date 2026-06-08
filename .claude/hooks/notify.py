#!/usr/bin/env python3
"""通知 hook dispatcher：解析 event → 派發給 .env 啟用的所有 channel。"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_HOOKS_DIR))

from notify_lib.env import load_env  # noqa: E402
from notify_lib.payload import parse  # noqa: E402

_CHANNEL_TIMEOUT = 5
_VALID_CHANNEL = re.compile(r"^[a-z0-9_-]+$")


def _project_dir() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))


def _project_name(env: dict[str, str]) -> str:
    name = env.get("CLAUDE_PROJECT_NAME", "").strip()
    return name or _project_dir().name


def _enabled_channels(env: dict[str, str]) -> list[str]:
    raw = env.get("CLAUDE_NOTIFY_CHANNELS", "").strip()
    if not raw:
        return []
    return [c.strip() for c in raw.split(",") if c.strip()]


def _dispatch(channel: str, payload: bytes) -> None:
    if not _VALID_CHANNEL.match(channel):
        print(f"dispatcher: invalid channel name '{channel}'", file=sys.stderr)
        return
    script = _HOOKS_DIR / "notify_channels" / f"{channel}.py"
    if not script.is_file():
        print(f"dispatcher: unknown channel '{channel}' (no {channel}.py)", file=sys.stderr)
        return
    try:
        subprocess.run(
            [sys.executable, str(script)],
            input=payload,
            timeout=_CHANNEL_TIMEOUT,
            stdout=subprocess.DEVNULL,
            stderr=sys.stderr,
        )
    except subprocess.TimeoutExpired:
        print(f"dispatcher: channel '{channel}' timed out", file=sys.stderr)
    except OSError as e:
        print(f"dispatcher: channel '{channel}' failed: {e}", file=sys.stderr)


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"dispatcher: stdin not json: {e}", file=sys.stderr)
        return

    env_file = _project_dir() / ".claude" / "hooks" / ".env"
    env = load_env(env_file)

    msg = parse(event, project_name=_project_name(env))
    if msg is None:
        return  # 不支援的事件型別

    channels = _enabled_channels(env)
    if not channels:
        return

    payload = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    for channel in channels:
        _dispatch(channel, payload)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"dispatcher: {e}", file=sys.stderr)
    sys.exit(0)
