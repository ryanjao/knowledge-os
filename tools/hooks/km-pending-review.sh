#!/usr/bin/env bash
# SessionStart hook：開場時提醒尚有幾筆候選待審。
# 輸出 additionalContext（SessionStart 慣例），無待審則靜默。
set -u
input=$(cat)
VAULT="${KM_VAULT:-$(printf '%s' "$input" | jq -r '.cwd // "."')}"
candir="$VAULT/01_Inbox/_candidates"
[ -d "$candir" ] || exit 0
pending=$(ls -1 "$candir"/*.md 2>/dev/null | grep -v '/\.gitkeep$' | wc -l | tr -d ' ')
[ "${pending:-0}" -gt 0 ] || exit 0
msg="📋 knowledge-os：目前有 ${pending} 筆候選待審，跑 /km-review 可清掉。"
jq -n --arg m "$msg" '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$m}}'
exit 0
