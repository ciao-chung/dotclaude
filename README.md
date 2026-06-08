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
└── statusline.sh    # 自製 statusline，顯示模型 / context / rate limit / git 狀態
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

## License

MIT — 隨意 fork / 改 / 用。
