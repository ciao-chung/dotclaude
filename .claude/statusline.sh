#!/bin/bash
input=$(cat)

# ANSI 顏色
GREEN=$'\033[32m'
YELLOW=$'\033[33m'
RED=$'\033[31m'
RESET=$'\033[0m'

# ── 讀取資料 ──────────────────────────────────────────
model=$(echo "$input" | jq -r '.model.display_name // empty')
total_tokens=$(echo "$input" | jq -r '(.context_window.total_input_tokens + .context_window.total_output_tokens) // empty')
cwd=$(echo "$input" | jq -r '.workspace.current_dir // empty')

five_hour=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
five_hour_reset=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
seven_day=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
seven_day_reset=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty')

# ── 工具函式 ──────────────────────────────────────────

# 進度條（10格寬），依百分比上色
make_bar() {
  local pct="${1:-0}"
  local pct_int
  pct_int=$(printf '%.0f' "$pct")
  local filled=$(( pct_int * 10 / 100 ))
  local empty=$(( 10 - filled ))
  local bar=""
  local i
  for ((i=0; i<filled; i++)); do bar="${bar}▓"; done
  for ((i=0; i<empty; i++)); do bar="${bar}░"; done

  local color="$GREEN"
  [ "$pct_int" -ge 50 ] && color="$YELLOW"
  [ "$pct_int" -ge 80 ] && color="$RED"

  printf "${color}%s${RESET} %d%%" "$bar" "$pct_int"
}

# Unix timestamp → 剩餘幾小時
# 僅顯示小時（給 5h 用）
remaining_hours() {
  local ts="$1"
  [ -z "$ts" ] && return
  local now diff
  now=$(date +%s)
  diff=$(( ts - now ))
  [ "$diff" -le 0 ] && echo "0h" && return
  echo "$(( diff / 3600 ))h"
}

# 顯示天+小時（給 7d 用）
remaining_days_hours() {
  local ts="$1"
  [ -z "$ts" ] && return
  local now diff
  now=$(date +%s)
  diff=$(( ts - now ))
  [ "$diff" -le 0 ] && echo "0h" && return
  local days=$(( diff / 86400 ))
  local hours=$(( (diff % 86400) / 3600 ))
  if [ "$days" -gt 0 ]; then
    echo "${days}d ${hours}h"
  else
    echo "${hours}h"
  fi
}

# ── Folder & Git ──────────────────────────────────────
folder=""
if [ -n "$cwd" ]; then
  folder="${cwd##*/}"
  if git rev-parse --git-dir &>/dev/null 2>&1; then
    branch=$(git branch --show-current 2>/dev/null)
    modified=$(git diff --numstat 2>/dev/null | wc -l | tr -d ' ')
    staged=$(git diff --cached --numstat 2>/dev/null | wc -l | tr -d ' ')
    untracked=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')
    git_info="$branch"
    [ "$staged" -gt 0 ] && git_info="${git_info} ${GREEN}+${staged}${RESET}"
    [ "$modified" -gt 0 ] && git_info="${git_info} ${YELLOW}~${modified}${RESET}"
    [ "$untracked" -gt 0 ] && git_info="${git_info} ${RED}?${untracked}${RESET}"
    git_info="${git_info}"
    folder="${folder} (${git_info})"
  fi
fi

# ── Docker 偵測 ──────────────────────────────────────
ORANGE=$'\033[38;2;255;165;0m'
in_docker=""
if [ -f /.dockerenv ] || grep -q 'docker\|containerd' /proc/1/cgroup 2>/dev/null; then
  in_docker=1
fi

# ── Model emoji ───────────────────────────────────────
case "$model" in
  *[Oo]pus*)   emoji="🐬" ;;
  *[Ss]onnet*) emoji="🦊" ;;
  *)            emoji="🐝" ;;
esac

# ── 第一行 ────────────────────────────────────────────
line1=""
if [ -n "$in_docker" ]; then
  line1="🐳 ${ORANGE}CLAUDE DOCKER SANDBOX${RESET} | "
fi
line1="${line1}${emoji}${model:+ $model}"
[ -n "$folder" ] && line1="$line1 | $folder"
ctx_used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
if [ -n "$ctx_used" ]; then
  LIGHT_GREEN=$'\033[38;2;144;238;144m'
  ctx_int=$(printf '%.0f' "$ctx_used")
  ctx_color="$LIGHT_GREEN"
  [ "$ctx_int" -gt 30 ] && ctx_color="$GREEN"
  [ "$ctx_int" -gt 50 ] && ctx_color="$ORANGE"
  [ "$ctx_int" -gt 70 ] && ctx_color="$RED"
  line1="$line1 | ctx: ${ctx_color}${ctx_used}%${RESET}"
fi
if [ -n "$total_tokens" ]; then
  if [ "$total_tokens" -ge 1000000 ]; then
    tokens_fmt=$(awk "BEGIN { printf \"%.1fM\", $total_tokens/1000000 }")
  elif [ "$total_tokens" -ge 1000 ]; then
    tokens_fmt=$(awk "BEGIN { printf \"%.1fk\", $total_tokens/1000 }")
  else
    tokens_fmt="${total_tokens}"
  fi
  line1="$line1 | tokens: ${tokens_fmt}"
fi

# ── 訂閱方案 ──────────────────────────────────────────
sub_type=$(/opt/homebrew/bin/claude auth status --json 2>/dev/null | jq -r '.subscriptionType // empty' | tr '[:lower:]' '[:upper:]')
SKY_BLUE=$'\033[38;2;135;206;235m'
if [ -n "$sub_type" ]; then
  if [ "$sub_type" = "TEAM" ]; then
    sub_color="$ORANGE"
    sub_emoji="🔋"
  else
    sub_color="$SKY_BLUE"
    sub_emoji="🚀"
  fi
  line1="$line1 | ${sub_color}${sub_emoji} ${sub_type}${RESET}"
fi

# ── 第二行（Rate limits）─────────────────────────────
line2=""
if [ -n "$five_hour" ]; then
  bar=$(make_bar "$five_hour")
  left=$(remaining_hours "$five_hour_reset")
  part="5h: ${bar}"
  [ -n "$left" ] && part="${part} (${left} left)"
  line2="$part"
fi
if [ -n "$seven_day" ]; then
  bar=$(make_bar "$seven_day")
  left=$(remaining_days_hours "$seven_day_reset")
  part="7d: ${bar}"
  [ -n "$left" ] && part="${part} (${left} left)"
  line2="${line2:+${line2} | }${part}"
fi

# ── 輸出 ──────────────────────────────────────────────
[ -n "$line2" ] && printf '%s\n%s' "$line1" "$line2" || printf '%s' "$line1"
