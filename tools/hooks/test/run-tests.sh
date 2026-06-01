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

echo "---"; echo "PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ]
