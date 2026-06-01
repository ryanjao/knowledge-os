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

exit 0  # 後續 Task 2 補 block 邏輯
