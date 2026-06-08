# Git 操作同意規範

AI agent **嚴禁**在未獲得使用者明確同意下，自行執行會改變 git 歷史或遠端狀態的操作。

## 適用操作

以下操作**必須**先取得使用者明確同意：

- `git commit`（含 `--amend`）
- `git push`（含 `--force`、`--force-with-lease`）
- `git merge`、`git rebase`
- `git reset --hard`、`git reset --soft`
- `git cherry-pick`、`git revert`
- `git tag`（建立或刪除）
- `git branch -D`（強制刪除分支）
- 透過 GitLab/GitHub MCP 進行的等價操作

## 何謂「明確同意」

- 使用者**當次對話**要求執行（例如：「commit 一下」、「push 到 remote」）
- 僅「請幫我實作 X 功能」**不構成**對 commit/push 的同意
- 過去對話或其他任務中的同意**不延續**到新任務
- 模糊指令（如「處理一下」、「搞定它」）**不構成**同意

## 不需同意的 git 操作

以下唯讀或本地非破壞性操作**不需**使用者同意：

- `git status`、`git diff`、`git log`、`git show`、`git blame`
- `git branch`（列出）、`git checkout <branch>`、`git switch <branch>`
- `git stash`、`git stash pop`
- `git fetch`（不改變本地 ref）
- `git add`（僅暫存，尚未 commit）

## Sandbox Agent Git Identity

若 target project 根目錄有 `.gitconfig.agent`，sandbox 內 Claude commit 時
請改用 `-c` 直接帶 name / email：

```bash
git -c user.name="agent-name" -c user.email="agent@example.com" commit
```

實際做法：先 `cat .gitconfig.agent` 讀出 `user.name` / `user.email`，再套到
`-c` flag。

> ⚠️ **不能用** `git -c include.path=<相對路徑> commit`。現代 git 為了
> 安全，拒絕從 command-line `-c` 載入相對路徑的 include，會報
> `error: relative config includes must come from files`。
> 若硬要用 include.path，必須是絕對路徑（例：`-c include.path="$PWD/.gitconfig.agent"`），
> 但這比直接帶 `user.name` / `user.email` 麻煩，不推薦。

`.gitconfig.agent` 已在 `.gitignore` 中，不進版控。
複製 `.gitconfig.agent.example` → `.gitconfig.agent` 並填入 agent identity 即可。

## 建立 Branch 的預設行為

使用者說「開一個 branch」、「建一個 branch」時：

- **預設**：使用 `git checkout -b` 或 `git switch -c` 建立實際 branch，在當前 working tree 操作
- **Worktree**：僅在使用者明確說「用 worktree」、「開 worktree」時才改用 `git worktree add`

不得自行將 branch 操作升級為 worktree。

## 原則

寧可多問一次，也不要擅自動手。
