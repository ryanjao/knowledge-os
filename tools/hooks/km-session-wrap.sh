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

# sentinel：每個 session 只 block 一次（Stop 在每一輪回應後都觸發，不只 session 結束）
sentinel="/tmp/km-wrap-asked-${sid8}"
[ -f "$sentinel" ] && exit 0
touch "$sentinel"

# 候選已存在 → 不重複 block
[ -f "$candidate" ] && exit 0

reason="本次開發 session 結束。請執行 Session 收尾捕捉：

0. **先判斷本 session 是否有實質產出**（程式／設計／設定／文件的實際變更、解掉的錯誤、或明確決策）。
   若**沒有**（純問候、純問答、查詢、無任何檔案變更或決策）→ **不要建立任何候選草稿**，直接正常結束。
1. 若有實質產出，建立候選草稿檔（只新增此檔，**不要**修改 03_Projects 目標卡或任何 SoT 檔）：
   路徑：$candidate
2. 內容用以下格式（依本次 session 實情填寫，可多筆 [!progress] 與 [!lesson]）：
   - 先讀 $VAULT/03_Projects/$project/ 找 kind: dev_goal 目標卡，取其 frontmatter uid 當 goal=；找不到就 goal=${project}。
   - [!progress] stage=<目前階段> date=$today goal=<uid或${project}> seq=01 source=<來源> ，body：did/result/next。
   - 每個本次踩到並解掉的錯誤寫一筆 [!lesson] skill=<相關skill> stage=<階段> error=<錯誤類型短標籤> source=<來源>，body：what/fix/rule。
   - source= 標知識來源（見 _docs/conventions.md §6）：human=你的判斷／決策；ai=Claude 推論未經人工驗證；experiment=本次實測／跑過驗證過；external=外部來源（可再加 source_ref=URL）。本次多為當下實作與解錯 → 通常 source=experiment。
3. 寫完該檔後即可正常結束（停止）。"

pending=$(ls -1 "$candir"/*.md 2>/dev/null | grep -v '/\.gitkeep$' | wc -l | tr -d ' ')
if [ "${pending:-0}" -gt 0 ]; then
  reason="$reason

📋 目前 _candidates/ 有 ${pending} 筆候選待審，記得跑 /km-review 清掉。"
fi

jq -n --arg r "$reason" '{decision:"block", reason:$r}'
exit 0
