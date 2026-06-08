"""把 Claude Code hook event 解析成統一的 NotifyMessage。"""

from typing import TypedDict


class NotifyMessage(TypedDict):
    event: str
    notification_type: str
    status_emoji: str
    status_text: str
    summary: str
    project_name: str


_SUMMARY_MAX = 200
_STRIPPED_CHARS = '"`\\'


def _clean_summary(text: str) -> str:
    """壓成單行、過濾會炸 shell / AppleScript / Discord JSON 的字元、截到 200 字。"""
    flat = text.strip().replace("\n", " ").replace("\r", " ")
    cleaned = "".join(c for c in flat if c not in _STRIPPED_CHARS)
    return cleaned[:_SUMMARY_MAX]


def parse(event: dict, project_name: str) -> NotifyMessage | None:
    """解析 hook event；不支援的事件回 None。"""
    name = event.get("hook_event_name", "")

    if name == "Stop":
        return NotifyMessage(
            event="Stop",
            notification_type="",
            status_emoji="✅",
            status_text="已完成",
            summary=_clean_summary(event.get("last_assistant_message", "")),
            project_name=project_name,
        )

    if name == "Notification":
        ntype = event.get("notification_type", "")
        if ntype == "permission_prompt":
            return NotifyMessage(
                event="Notification",
                notification_type=ntype,
                status_emoji="⚠️",
                status_text="需要核准",
                summary="",
                project_name=project_name,
            )
        return NotifyMessage(
            event="Notification",
            notification_type=ntype,
            status_emoji="💬",
            status_text="需要注意",
            summary="",
            project_name=project_name,
        )

    return None
