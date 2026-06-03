#!/usr/bin/env bash
# 零依賴 bash 測試。用法：bash tools/hooks/test/run-tests.sh
set -u
HOOK="$(cd "$(dirname "$0")/.." && pwd)/km-session-wrap.sh"
PASS=0; FAIL=0
assert_eq() { # $1=label $2=expected $3=actual
  if [ "$2" = "$3" ]; then PASS=$((PASS+1)); echo "ok   - $1";
  else FAIL=$((FAIL+1)); echo "FAIL - $1"; echo "       expected: [$2]"; echo "       actual:   [$3]"; fi
}
assert_contains() { # $1=label $2=needle $3=haystack
  case "$3" in *"$2"*) PASS=$((PASS+1)); echo "ok   - $1";;
  *) FAIL=$((FAIL+1)); echo "FAIL - $1"; echo "       expected to contain: [$2]"; echo "       in: [$3]";; esac
}

# 每個測試用獨立 temp cwd 與 temp vault
mktmp() { mktemp -d 2>/dev/null || mktemp -d -t kmtest; }

# --- Test 1: stop_hook_active=true → 不 block（空輸出、exit 0）---
t1cwd=$(mktmp); echo "demo" > "$t1cwd/.km-project"
out=$(echo '{"stop_hook_active":true,"cwd":"'"$t1cwd"'","session_id":"abc"}' | KM_VAULT=$(mktmp) bash "$HOOK")
code=$?
assert_eq "stop_hook_active=true 不 block（輸出為空）" "" "$out"
assert_eq "stop_hook_active=true exit 0" "0" "$code"

# --- Test 2: 無 .km-project → no-op（空輸出、exit 0）---
t2cwd=$(mktmp)  # 不放 .km-project
out=$(echo '{"stop_hook_active":false,"cwd":"'"$t2cwd"'","session_id":"abc"}' | KM_VAULT=$(mktmp) bash "$HOOK")
code=$?
assert_eq "無 .km-project 不 block（輸出為空）" "" "$out"
assert_eq "無 .km-project exit 0" "0" "$code"

# --- Test 3: 有 .km-project 且 stop_hook_active=false → block ---
t3cwd=$(mktmp); echo "investment-research-os" > "$t3cwd/.km-project"
t3vault=$(mktmp)
out=$(echo '{"stop_hook_active":false,"cwd":"'"$t3cwd"'","session_id":"ABCDEFGH1234"}' | KM_VAULT="$t3vault" bash "$HOOK")
code3=$?
decision=$(printf '%s' "$out" | jq -r '.decision')
reason=$(printf '%s' "$out" | jq -r '.reason')
assert_eq "block decision" "block" "$decision"
assert_contains "reason 帶專案 slug" "investment-research-os" "$reason"
assert_contains "reason 帶候選路徑" "01_Inbox/_candidates/" "$reason"
assert_contains "reason 帶 session 前綴" "ABCDEFGH" "$reason"
assert_contains "reason 要求只寫候選不動 SoT" "不要" "$reason"
assert_eq "block exit 0" "0" "$code3"

# --- Test 4: 候選已存在 → 不重複 block ---
date_today=$(date +%F)
mkdir -p "$t3vault/01_Inbox/_candidates"
touch "$t3vault/01_Inbox/_candidates/${date_today}--investment-research-os--ABCDEFGH.md"
out2=$(echo '{"stop_hook_active":false,"cwd":"'"$t3cwd"'","session_id":"ABCDEFGH1234"}' | KM_VAULT="$t3vault" bash "$HOOK")
code4=$?
assert_eq "候選已存在則不 block（空輸出）" "" "$out2"
assert_eq "候選已存在 exit 0" "0" "$code4"

# --- Test: reason 內含待審候選計數提醒 ---
tRcwd=$(mktmp); echo "demo" > "$tRcwd/.km-project"
tRvault=$(mktmp); mkdir -p "$tRvault/01_Inbox/_candidates"
# 預先放 2 個待審候選（不同於本 session 將建立的那個）
printf 'x' > "$tRvault/01_Inbox/_candidates/2026-06-01--demo--aaaaaaaa.md"
printf 'x' > "$tRvault/01_Inbox/_candidates/2026-06-02--demo--bbbbbbbb.md"
out=$(echo '{"stop_hook_active":false,"cwd":"'"$tRcwd"'","session_id":"zzzzzzzz"}' | KM_VAULT="$tRvault" bash "$HOOK")
assert_contains "reason 含待審候選提醒" "待審" "$out"
assert_contains "reason 含 /km-review" "/km-review" "$out"

echo "---"; echo "PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ]
