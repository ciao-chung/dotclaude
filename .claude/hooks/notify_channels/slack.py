#!/usr/bin/env python3
"""Slack channel：POST 訊息到 incoming webhook URL。

stdin 讀 JSON (NotifyMessage)。.env 無 CLAUDE_SLACK_WEBHOOK_URL 則 silent exit 0。
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
        print(f"slack channel: stdin not json: {e}", file=sys.stderr)
        return

    env_file = (
        Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())) / ".claude" / "hooks" / ".env"
    )
    env = load_env(env_file)
    webhook = env.get("CLAUDE_SLACK_WEBHOOK_URL", "").strip()
    if not webhook:
        return  # 沒設 webhook → silent

    max_len = env_int(env, "CLAUDE_NOTIFY_SLACK_MAX_LEN", 500)
    summary = truncate(msg.get("summary", ""), max_len)

    line1 = f"{msg['project_name']} {msg['status_emoji']} {msg['status_text']}"
    text = line1 if not summary else f"{line1}\n{summary}"

    payload = json.dumps({"text": text}, ensure_ascii=False).encode("utf-8")
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
        print(f"slack channel POST failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"slack channel: {e}", file=sys.stderr)
    sys.exit(0)
