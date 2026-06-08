"""簡易 .env parser，避免引入第三方 dotenv 套件。"""

from pathlib import Path


def load_env(path: Path | str) -> dict[str, str]:
    """讀 .env 檔成 dict。

    支援：`KEY=VALUE` 一行一個、`#` 開頭註解、空行、值兩側可選單/雙引號。
    檔案不存在則回傳空 dict。
    """
    p = Path(path)
    if not p.is_file():
        return {}

    result: dict[str, str] = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        result[key] = value
    return result


def env_int(env: dict[str, str], key: str, default: int) -> int:
    """從 env dict 取整數值，缺 / 空 / 非整數則用 default。"""
    raw = env.get(key, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default
