# dotclaude

我個人 Claude Code 設定的公開分享，包含 statusline、skills、rules 等可重用片段。

## 緣起

[Claude Code](https://claude.com/claude-code) 用久了會累積一堆個人化設定 — 自訂 skill、rule、statusline、slash command 等，這些設定散落在 `~/.claude/` 底下。

仿照社群 `dotfiles` / `dotvim` 慣例，這個 repo 把**我自己日常在用、且可安全公開的設定**整理出來，方便：

- 換電腦時快速還原
- 給其他 Claude Code 使用者參考 / 抄
- 自己未來回頭追蹤調整歷史

> 私人設定（含個人專案路徑、會計資訊、家人姓名等）**不**會放進來。

## 內容

```
.claude/
├── statusline.sh    # 自製 statusline，顯示模型 / context / rate limit / git 狀態
├── hooks/           # Stop / Notification 通知 dispatcher（macOS / Discord / Slack）
└── rules/           # Project-level rules（git 操作同意規範等）
```

更多 skill 與 rule 會視整理進度陸續加入。

## statusline.sh — 自製狀態列

### 顯示什麼

第一行：

```
🐬 Claude Opus 4.7 | dotclaude (main +1 ~2 ?3) | ctx: 42% | tokens: 12.3k | 🚀 PRO
```

- **模型 emoji**：🐬 Opus / 🦊 Sonnet / 🐝 其他
- **目前資料夾 + git 狀態**：branch、staged（+）、modified（~）、untracked（?）
- **context window 使用率**：依 % 變色（綠 → 橘 → 紅）
- **本次對話累計 tokens**
- **訂閱方案**：🚀 PRO / 🔋 TEAM
- 若在 Docker container 內，前綴會加上 `🐳 CLAUDE DOCKER SANDBOX`

第二行（rate limits）：

```
5h: ▓▓▓░░░░░░░ 30% (3h left) | 7d: ▓▓▓▓▓░░░░░ 50% (4d 12h left)
```

- 5 小時額度使用率 + 剩餘時間
- 7 天額度使用率 + 剩餘時間

### 怎麼用

#### 1. 安裝依賴

腳本需要 `jq`：

```bash
brew install jq
```

#### 2. 放到 `~/.claude/` 並給執行權限

```bash
cp .claude/statusline.sh ~/.claude/statusline.sh
chmod +x ~/.claude/statusline.sh
```

#### 3. 編輯 `~/.claude/settings.json` 啟用

加入 `statusLine` 區塊：

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash ~/.claude/statusline.sh"
  }
}
```

存檔後重啟 Claude Code 即可看到效果。

### 平台相容性

腳本內有一段透過 `claude auth status --json` 讀訂閱方案，路徑寫死為 `/opt/homebrew/bin/claude`（macOS Apple Silicon）。

若你是 Intel Mac / Linux，請改成你環境的實際路徑：

```bash
which claude
# 把結果填回 statusline.sh 第 131 行
```

或直接改成 `claude`（依 `$PATH` 查找，多數情況可用）。

## hooks/notify — Stop / Notification 通知

### 它做什麼

Claude Code 對話跑完（`Stop`）或需要使用者注意（`Notification`，例如等待 permission prompt）時自動跳通知。預設打到 macOS 桌面，可同時打到 Discord / Slack。

範例：

- ✅ macOS 桌面通知：標題 `Claude Code`、副標題 `dotclaude — 已完成`，內文是 AI 最後回覆切到 50 字的摘要。
- ⚠️ 需要核准時：副標題 `dotclaude — 需要核准`。
- Discord / Slack：第一行 `dotclaude ✅ 已完成`，第二行摘要（預設 500 字內，超過自動斷句）。

### 架構

`notify.py` 是 dispatcher，依 `.env` 的 `CLAUDE_NOTIFY_CHANNELS` 派發到 `notify_channels/*.py`。每個 channel 是獨立 Python 子程序，5 秒 timeout、失敗 silent、永遠 exit 0，不會卡住 Claude Code。

```
.claude/hooks/
├── notify.py            # entry point（settings.json hook 指向這裡）
├── .env.example         # 設定範本
├── notify_lib/          # 共用工具（payload 規格化 / .env parser / 斷句截斷）
└── notify_channels/
    ├── macos.py
    ├── discord.py
    └── slack.py
```

### 怎麼用

#### 1. 複製到 `~/.claude/hooks/`

```bash
cp -R .claude/hooks ~/.claude/hooks && chmod +x ~/.claude/hooks/notify.py ~/.claude/hooks/notify_channels/*.py
```

#### 2. 編輯 `~/.claude/settings.json` 註冊 hook

```json
{
  "hooks": {
    "Stop": [
      { "matcher": "", "hooks": [{ "type": "command", "command": "python3 ~/.claude/hooks/notify.py" }] }
    ],
    "Notification": [
      { "matcher": "", "hooks": [{ "type": "command", "command": "python3 ~/.claude/hooks/notify.py" }] }
    ]
  }
}
```

> 若是放在某 project 內（如本 repo 的 `.claude/settings.json`），路徑用 `"$CLAUDE_PROJECT_DIR"/.claude/hooks/notify.py`。

#### 3. 啟用想要的 channel

```bash
cp ~/.claude/hooks/.env.example ~/.claude/hooks/.env
```

開啟 `.env`，把 `CLAUDE_NOTIFY_CHANNELS` 改成想啟用的（逗號分隔），需要的話填入 webhook：

```bash
CLAUDE_NOTIFY_CHANNELS=macos,discord
CLAUDE_PROJECT_NAME=dotclaude      # 不設則用目錄名
CLAUDE_DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxx/yyyyy
```

存檔後重啟 Claude Code，下次對話結束就會收到通知。

### Channel 速覽

| Channel | 必填環境變數 | 備註 |
|---------|------------|------|
| `macos` | （無） | 用 `osascript`；Docker container 內 fallback 打到 `host.docker.internal:9999/notify`（host 需自架 notify-server） |
| `discord` | `CLAUDE_DISCORD_WEBHOOK_URL` | 沒填則 silent skip；已自訂 User-Agent 規避 Discord 對 `Python-urllib` 的 403 |
| `slack` | `CLAUDE_SLACK_WEBHOOK_URL` | 沒填則 silent skip |

各 channel 的訊息長度上限可用 `CLAUDE_NOTIFY_<CHANNEL>_MAX_LEN` 覆寫（預設：macOS 50 / Discord 500 / Slack 500），超過會在句末符號 / 換行 / 逗號 / 空白等自然斷點切斷。

### 本機測試

不用實際跑 Claude Code 也能驗證 dispatch：

```bash
echo '{"hook_event_name":"Stop","last_assistant_message":"hello"}' | CLAUDE_PROJECT_DIR="$PWD" python3 .claude/hooks/notify.py
```

### 進階：新增 channel

放一支 `notify_channels/<name>.py`，name 須符合 `^[a-z0-9_-]+$`：

- 開頭 `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` 才能 import `notify_lib`
- 從 stdin 讀 JSON（型別見 `notify_lib/payload.py` 的 `NotifyMessage`）
- 缺設定時 silent return、永遠 `sys.exit(0)`，不可阻塞 Stop hook

然後把 `<name>` 加進 `.env` 的 `CLAUDE_NOTIFY_CHANNELS`。

## License

MIT — 隨意 fork / 改 / 用。
