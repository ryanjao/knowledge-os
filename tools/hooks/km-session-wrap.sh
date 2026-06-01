#!/usr/bin/env bash
# Claude Code Stop hook：session 收尾自動捕捉候選草稿。
# 讀 stdin JSON；cwd 有 .km-project 才作用；用 stop_hook_active 防迴圈。
set -u
VAULT="${KM_VAULT:-/Users/juiyujao/Projects/knowledge-os}"

input=$(cat)
stop_active=$(printf '%s' "$input" | jq -r '.stop_hook_active // false')
[ "$stop_active" = "true" ] && exit 0

cwd=$(printf '%s' "$input" | jq -r '.cwd // empty')
[ -z "$cwd" ] && cwd="$PWD"

# 從 cwd 往上找 .km-project
dir="$cwd"; marker=""
while [ -n "$dir" ] && [ "$dir" != "/" ]; do
  if [ -f "$dir/.km-project" ]; then marker="$dir/.km-project"; break; fi
  dir=$(dirname "$dir")
done
[ -z "$marker" ] && exit 0

project=$(tr -d '[:space:]' < "$marker")
[ -z "$project" ] && exit 0

session=$(printf '%s' "$input" | jq -r '.session_id // "unknown"')
sid8=$(printf '%s' "$session" | cut -c1-8)
today=$(date +%F)
candir="$VAULT/01_Inbox/_candidates"
candidate="$candir/${today}--${project}--${sid8}.md"

# 候選已存在 → 不重複 block
[ -f "$candidate" ] && exit 0

reason="本次開發 session 結束。請執行 Session 收尾捕捉：

1. 建立候選草稿檔（只新增此檔，**不要**修改 03_Projects 目標卡或任何 SoT 檔）：
   路徑：$candidate
2. 內容用以下格式（依本次 session 實情填寫，可多筆 [!progress] 與 [!lesson]）：
   - 先讀 $VAULT/03_Projects/$project/ 找 kind: dev_goal 目標卡，取其 frontmatter uid 當 goal=；找不到就 goal=${project}。
   - [!progress] stage=<目前階段> date=$today goal=<uid或${project}> seq=01 ，body：did/result/next。
   - 每個本次踩到並解掉的錯誤寫一筆 [!lesson] skill=<相關skill> stage=<階段> error=<錯誤類型短標籤>，body：what/fix/rule。
3. 寫完該檔後即可正常結束（停止）。"

jq -n --arg r "$reason" '{decision:"block", reason:$r}'
exit 0
