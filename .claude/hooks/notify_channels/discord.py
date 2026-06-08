#!/usr/bin/env python3
"""Discord channel：POST 訊息到 webhook URL。

stdin 讀 JSON (NotifyMessage)。.env 無 CLAUDE_DISCORD_WEBHOOK_URL 則 silent exit 0。
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from notify_lib.env import env_int, load_env  # noqa: E402
from notify_lib.truncate import truncate  # noqa: E402

_TIMEOUT = 5


def main() -> None:
    try:
        msg = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"discord channel: stdin not json: {e}", file=sys.stderr)
        return

    env_file = (
        Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())) / ".claude" / "hooks" / ".env"
    )
    env = load_env(env_file)
    webhook = env.get("CLAUDE_DISCORD_WEBHOOK_URL", "").strip()
    if not webhook:
        return  # 沒設 webhook → silent

    max_len = env_int(env, "CLAUDE_NOTIFY_DISCORD_MAX_LEN", 500)
    summary = truncate(msg.get("summary", ""), max_len)

    line1 = f"{msg['project_name']} {msg['status_emoji']} {msg['status_text']}"
    content = line1 if not summary else f"{line1}\n{summary}"

    payload = json.dumps({"content": content}, ensure_ascii=False).encode("utf-8")
    # 自訂 User-Agent：Discord webhook 會擋預設的 "Python-urllib/x.y" → 403 Forbidden
    req = urllib.request.Request(
        webhook,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "harness-templates-notify/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT):
            pass
    except (urllib.error.URLError, OSError) as e:
        print(f"discord channel POST failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"discord channel: {e}", file=sys.stderr)
    sys.exit(0)
