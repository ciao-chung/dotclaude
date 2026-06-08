# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository 性質

這是 `dotclaude` — 個人 Claude Code 設定的「公開可分享」子集（類比 `dotfiles`）。
這個 repo 不是 application，它的「成品」就是 `.claude/` 底下的腳本與設定，最終被使用者複製到自己的 `~/.claude/`，由 Claude Code harness 在 runtime 呼叫。

**所有寫入此 repo 的內容必須能公開**。私人路徑、雇主名稱、會計資訊、家人姓名等都不可進版控；若不確定，先問使用者。`.gitignore` 已排除大量本機產物（`.claude/projects/`、`todos/`、`statsig/`、`shell-snapshots/`、`plans/`、`article-memo/`、`settings.local.json`、`.mcp.json`、所有 `**/.env`、`*.key`、`*.pem` 等），新增檔案前確認是否落入這些 pattern。

## 重要規則

`.claude/rules/git-operation-consent.md` 是 project-level rule，對在這個 repo 工作的 Claude 強制適用：**未取得使用者當次對話的明確同意，禁止執行 `git commit`、`git push`、`git merge`、`git rebase`、`git reset --hard`、`git tag` 等改變歷史/遠端狀態的操作**。「請幫我實作 X」不構成 commit 同意。讀取型 git 指令（`status`、`diff`、`log`、`fetch` 等）不需同意。詳閱該檔。

若根目錄存在 `.gitconfig.agent`（已 gitignore），sandbox 內 Claude 應以 `git -c user.name=... -c user.email=... commit` 形式套用其中 identity，**不要**用 `-c include.path=`（相對路徑會被現代 git 拒絕）。

## 架構：兩個獨立子系統

repo 內只有兩塊核心，彼此獨立、可分別取用：

### 1. `.claude/statusline.sh` — 自製狀態列

從 stdin 讀 Claude Code 傳入的 JSON（含 `model`、`workspace.current_dir`、`context_window`、`rate_limits`），輸出兩行 ANSI 上色的 status 文字。
- 第一行：Docker sandbox 標記（若在 container 內偵測 `/.dockerenv` 或 cgroup）、模型 emoji（🐬 Opus / 🦊 Sonnet / 🐝 其他）、folder + git 狀態、ctx 使用率（顏色隨百分比變）、累計 tokens、訂閱方案（🚀 PRO / 🔋 TEAM）。
- 第二行：5h 與 7d rate limit 進度條 + 剩餘時間。

**已知平台耦合**：第 131 行 hardcode `/opt/homebrew/bin/claude auth status --json` 來讀訂閱方案。改非 Apple Silicon macOS 環境前確認 `which claude` 路徑。

### 2. `.claude/hooks/` — 通知 hook dispatcher（dispatcher + channel 架構）

由 `.claude/settings.json` 註冊 `Stop` 與 `Notification` 兩個 hook，都指向同一個 entry point `notify.py`。

**資料流**：
```
Claude Code event (JSON via stdin)
  → notify.py (dispatcher)
      → notify_lib/payload.py    把 raw event 規格化成 NotifyMessage TypedDict
      → notify_lib/env.py        讀 .claude/hooks/.env（自製 parser，避免 dotenv 相依）
      → 依 CLAUDE_NOTIFY_CHANNELS=macos,discord,slack
      → subprocess.run notify_channels/<channel>.py，餵相同 JSON payload 到 stdin
```

每個 channel script 都是獨立子程序：5 秒 timeout、**永遠 exit 0**（即使失敗也不能阻塞 Claude Code 的 Stop hook）、配置缺失時 silent skip（例如 Discord webhook URL 未設就直接 return）。channel name 必須符合 `^[a-z0-9_-]+$`，dispatcher 才會載入對應的 `notify_channels/<name>.py`。

**現有 channel**：
- `macos.py`：先試 `osascript` 本機通知；失敗則 fallback 到 `http://host.docker.internal:9999/notify`（供 container 場景把通知打到 host）。
- `discord.py`：POST 到 webhook，需自訂 `User-Agent`（Discord 會擋 `Python-urllib/x.y` → 403）。
- `slack.py`：POST 到 incoming webhook。

**新增 channel 的標準步驟**：
1. 在 `notify_channels/<name>.py` 建立 script，開頭加入 `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` 才能 import `notify_lib`。
2. 從 stdin 讀 JSON（型別參考 `notify_lib/payload.py` 的 `NotifyMessage`）。
3. 設定 fail-silent 與 `sys.exit(0)`。
4. 在 `.env.example` 與 README 補上對應環境變數。
5. 使用者再到自己的 `.env` 把 `<name>` 加進 `CLAUDE_NOTIFY_CHANNELS`。

長訊息一律走 `notify_lib/truncate.truncate()`：會在 `[0.6 * max_len, max_len]` 區間找句末符號 / 換行 / 逗號 / 空白等自然斷點切，找不到才硬切。各 channel 的長度上限走 `.env` 的 `CLAUDE_NOTIFY_<CHANNEL>_MAX_LEN`。

## 開發常用指令

這個 repo 沒有 build / lint / test 設定（純粹是被 harness 呼叫的腳本）。手動驗證 notify 流程：

```bash
echo '{"hook_event_name":"Stop","last_assistant_message":"hello"}' | CLAUDE_PROJECT_DIR="$PWD" python3 .claude/hooks/notify.py
```

只測單一 channel（跳過 dispatcher）：

```bash
echo '{"event":"Stop","notification_type":"","status_emoji":"✅","status_text":"已完成","summary":"hello","project_name":"dotclaude"}' | CLAUDE_PROJECT_DIR="$PWD" python3 .claude/hooks/notify_channels/macos.py
```

測 statusline：

```bash
echo '{"model":{"display_name":"Claude Opus 4.7"},"workspace":{"current_dir":"'"$PWD"'"},"context_window":{"used_percentage":42,"total_input_tokens":10000,"total_output_tokens":2000},"rate_limits":{"five_hour":{"used_percentage":30,"resets_at":'"$(($(date +%s)+10800))"'},"seven_day":{"used_percentage":50,"resets_at":'"$(($(date +%s)+388800))"'}}}' | bash .claude/statusline.sh
```
