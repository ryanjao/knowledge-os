#!/usr/bin/env bash
# SessionStart hook：
#   (1) 開場自動促進（auto km-review）待審候選。
#   (2) 永遠注入「SOP 開場確認標頭」指示（對應 ~/.claude/CLAUDE.md §0.8 可觀測性）。
#
# 安裝建議：全域 ~/.claude/settings.json（與 Stop hook km-session-wrap.sh 並列）。
# vault 路徑可用環境變數 KM_VAULT 覆寫（預設下方絕對路徑）。
set -u
input=$(cat)
VAULT="${KM_VAULT:-/Users/juiyujao/Projects/knowledge-os}"

# (1) auto-promote 待審候選（有候選才有輸出）
promote_out=""
if [ -d "$VAULT/01_Inbox/_candidates" ]; then
  promote_out=$(python3 "$VAULT/tools/km_review/promote.py" --vault "$VAULT" 2>&1)
fi

# (1b) 有實際併入 → 自動同步到 Notion（--no-autolog 避免與候選流程重複；非致命）
sync_out=""
if printf '%s' "$promote_out" | grep -q '併入 [1-9]'; then
  KM_SYNC="${KM_SYNC_BIN:-$(command -v km-sync 2>/dev/null)}"
  if [ -n "$KM_SYNC" ] && [ -x "$KM_SYNC" ]; then
    raw=$("$KM_SYNC" sync --vault "$VAULT" --no-autolog 2>&1); code=$?
    last=$(printf '%s' "$raw" | tail -n 1)
    if [ "$code" -eq 0 ]; then sync_out="🔄 Notion sync：$last"
    else sync_out="⚠️ Notion sync 未完成（code $code）：$last"; fi
  fi
fi

# (2) 永遠注入開場確認指示（讓使用者看得到 SOP 已生效）
ctx="【SOP 指示】本 session 第一個回應的最上方，必須先輸出一行骨幹 SOP 確認標頭（格式見 ~/.claude/CLAUDE.md §0.8「Session 開場確認」），讓使用者確認 SOP 已載入並知道目前所在 Phase。"
[ -n "$promote_out" ] && ctx="$ctx

$promote_out"
[ -n "$sync_out" ] && ctx="$ctx
$sync_out"

jq -n --arg m "$ctx" '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$m}}'
exit 0
