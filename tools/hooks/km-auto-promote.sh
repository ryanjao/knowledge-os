#!/usr/bin/env bash
# SessionStart hook：
#   (0) Pre-flight 完整性校驗：確認敏感檔仍被 git 忽略（偵測組態漂移）。
#   (1) 開場自動促進（auto km-review）待審候選。
#   (2) 永遠注入「SOP 開場確認標頭」指示（對應 ~/.claude/CLAUDE.md §0.8 可觀測性）。
#
# 安裝建議：全域 ~/.claude/settings.json（與 Stop hook km-session-wrap.sh 並列）。
# vault 路徑可用環境變數 KM_VAULT 覆寫（預設下方絕對路徑）。
set -u
input=$(cat)
VAULT="${KM_VAULT:-/Users/juiyujao/Projects/knowledge-os}"

# (0) Pre-flight 完整性校驗：靜態 .gitignore 可能因改名/誤刪/被追蹤而漂移失效。
#     用 git check-ignore 在執行期主動確認敏感檔仍被忽略（exit 0=忽略）；
#     僅在 git work tree 內檢查，非 git 環境（純 Obsidian vault）靜默略過。
#     偵測到漂移 → 鎖定 Notion 同步（不在隔離破口下外推）+ 注入醒目警告。
#     本地促進仍放行（只寫本地 SoT，不外洩）。
guard_breach=""
if git -C "$VAULT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  for f in "05_Secrets/secrets.env" "notion.config.local.json"; do
    if ! git -C "$VAULT" check-ignore -q "$f"; then
      guard_breach="${guard_breach}${guard_breach:+、}$f"
    fi
  done
fi

# (1) auto-promote 待審候選（有候選才有輸出）
promote_out=""
if [ -d "$VAULT/01_Inbox/_candidates" ]; then
  promote_out=$(python3 "$VAULT/tools/km_review/promote.py" --vault "$VAULT" 2>&1)
fi

# (1b) 有實際併入 → 自動同步到 Notion（--no-autolog 避免與候選流程重複；非致命）
#      組態漂移時鎖定同步（guard_breach 非空即跳過）。
sync_out=""
if [ -z "$guard_breach" ] && printf '%s' "$promote_out" | grep -q '併入 [1-9]'; then
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
# 組態漂移警告置於最前（最高優先級，要求 AI 第一時間提醒使用者）
[ -n "$guard_breach" ] && ctx="🚨【安全警告：組態漂移】下列敏感檔已不被 .gitignore 忽略（可能被 git 追蹤/上傳）：${guard_breach}。Notion 自動同步已鎖定。請第一時間提醒使用者：立即檢查 .gitignore / .claudeignore，並用 \`git rm --cached <檔>\` 解除任何已被追蹤的敏感檔，修復後再恢復同步。

$ctx"

jq -n --arg m "$ctx" '{hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$m}}'
exit 0
