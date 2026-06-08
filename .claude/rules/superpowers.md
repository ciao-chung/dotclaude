# Superpowers 規則

使用 Superpowers 技能時，必須遵守以下規則：

## 檔案位置

- 所有規劃文件統一放 `.claude/plans/`（已 gitignore，不進版控）
- **brainstorming** 產出的 spec → `.claude/plans/{序號}-{功能}/spec.md` 或 `spec-{主題}.md`
- **writing-plans** 產出的實作計畫 → `.claude/plans/{序號}-{功能}/implementation.md`
- **不使用** `docs/superpowers/` 目錄

## 目錄命名

- 格式：`{序號}-{功能名稱}/`
- 序號接續現有最大編號
- 子編號用英文字母：`02a-`, `02b-`

## 檔案生命週期

- `spec.md` / `spec-*.md` — 長期保留
- `implementation.md` — 實作完成後刪除

## 流程判斷

- 使用者請求已夠具體、可直接落為 task → 跳過 brainstorming，直接 `writing-plans`
- 仍有待討論的設計決策（例如新增通知 channel、改 statusline 結構）→ 先 `brainstorming` 補 spec，再 `writing-plans`

## 實作完成後的必要步驟

當使用 `executing-plans` 或 `subagent-driven-development` **完成所有實作 task 後**，必須依序執行：

1. **手動驗證**
   - 此 repo 無自動化測試 / lint，依改動類型跑對應的 smoke test：
     - `.claude/hooks/` → 用模擬 stdin payload 跑 dispatcher 與相關 channel（指令見 `README.md` 的「本機測試」段、`CLAUDE.md` 的「開發常用指令」段）
     - `.claude/statusline.sh` → 用模擬 status JSON 跑腳本，確認 stdout 輸出符合預期（指令見 `CLAUDE.md` 的「開發常用指令」段）
     - 純文件改動（`*.md`、`rules/`）→ 自讀一遍確認語意正確、連結未壞

2. **Code Review**
   - 使用 `superpowers:requesting-code-review` 或對應的 code-review skill
   - Review 發現的嚴重 / 警告問題必須修復後才算完成

3. **修復後重跑驗證** — 確認 review 修復沒有破壞功能

**不需要此步驟的 skill**：`brainstorming`、`writing-plans`（不產出程式碼）

## finishing-a-development-branch 使用前提

使用 `finishing-a-development-branch` skill **之前**，必須確認已完成：

1. **手動驗證**：依改動類型跑過對應 smoke test（見上節）且結果符合預期
2. **公開邊界檢查**：新增 / 修改的內容不含個人路徑、雇主名稱、會計資訊、家人姓名、私人 webhook URL 等不可公開資訊 — 此 repo 性質強制（見 `CLAUDE.md` 開頭「Repository 性質」段）

尚未完成以上任一項時，**不得直接進入** `finishing-a-development-branch` 流程，應先補做並修復問題。
