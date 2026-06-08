"""智能斷點截斷字串。"""

_BOUNDARIES = ["。", "．", ".", "!", "?", "\n", "，", ",", " "]


def truncate(text: str, max_len: int) -> str:
    """把 text 截斷到不超過 max_len 字元（不含補上的 '...'）。

    優先在 [int(max_len * 0.6), max_len] 區間內找自然斷點切；找不到則硬切。
    優先序：句末符號 > 換行 > 逗號 > 空白；找到第一個合格的就用。
    """
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    floor = int(max_len * 0.6)
    for boundary in _BOUNDARIES:
        idx = cut.rfind(boundary)
        if idx >= floor:
            return cut[: idx + 1].rstrip() + "..."
    return cut + "..."
