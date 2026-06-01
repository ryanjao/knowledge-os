# Session Wrap Capture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 每次 Claude Code 開發 session 結束時，自動以 Stop hook 讓 Claude 寫一塊候選草稿（進度 + 用過的 skill + 錯誤→教訓）到 vault 暫存區，人工 `/km-review` 核准後才併入 SoT。

**Architecture:** 全域 Stop hook（bash + jq）在 cwd 有 `.km-project` 時回傳 `{"decision":"block","reason":...}`，指示仍在執行的 Claude 用自身 context 寫候選；`stop_hook_active` 旗標防迴圈。候選進 `01_Inbox/_candidates/`（gitignore，非 SoT）。`/km-review` 指令做 promotion：`[!progress]`→目標卡 Stage Log、`[!lesson]`→`02_Notes/lessons.md` 並追加一行到 `04_MOCs/playbook.md` 索引。

**Tech Stack:** bash, jq（環境已有，現有全域 hook 即用 jq）；Claude Code Stop hook 協定；Obsidian Markdown / callout；Claude Code project slash command。

**設計來源：** `docs/superpowers/specs/2026-06-01-session-wrap-capture-design.md`（已核准）。

**Repo 慣例：** 本 vault 慣例直接提交 `main`（非 worktree）。每完成一個 Task 即 commit。只 stage 該 Task 檔案，勿動既有未提交變更（`.obsidian/graph.json`、兩個 `goal.md`、`design-spec.md`）。

**路徑常數：** vault 根 = `/Users/juiyujao/Projects/knowledge-os`（下稱 `$VAULT`）。

---

## Task 1: Stop hook 腳本 — `stop_hook_active` 防迴圈與無標記 no-op

**Files:**
- Create: `tools/hooks/km-session-wrap.sh`
- Create: `tools/hooks/test/run-tests.sh`

- [ ] **Step 1: 寫測試骨架 + 前兩個失敗測試**

Create `tools/hooks/test/run-tests.sh`:

```bash
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
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `bash tools/hooks/test/run-tests.sh`
Expected: FAIL（`km-session-wrap.sh` 不存在，hook 執行報錯，輸出非空 / exit 非 0）

- [ ] **Step 3: 寫最小實作（只處理防迴圈與 no-op）**

Create `tools/hooks/km-session-wrap.sh`:

```bash
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
```

- [ ] **Step 4: 跑測試確認通過**

Run: `bash tools/hooks/test/run-tests.sh`
Expected: PASS（`PASS=4 FAIL=0`）

- [ ] **Step 5: Commit**

```bash
git add tools/hooks/km-session-wrap.sh tools/hooks/test/run-tests.sh
git commit -m "feat(hook): km-session-wrap 防迴圈與無標記 no-op + 測試骨架"
```

---

## Task 2: Stop hook 腳本 — 有標記時 block 並產生指示

**Files:**
- Modify: `tools/hooks/km-session-wrap.sh`
- Modify: `tools/hooks/test/run-tests.sh`

- [ ] **Step 1: 加失敗測試（有 .km-project → block + reason 內容）**

在 `run-tests.sh` 的 `echo "---"` 之前插入：

```bash
# --- Test 3: 有 .km-project 且 stop_hook_active=false → block ---
t3cwd=$(mktmp); echo "investment-research-os" > "$t3cwd/.km-project"
t3vault=$(mktmp)
out=$(echo '{"stop_hook_active":false,"cwd":"'"$t3cwd"'","session_id":"ABCDEFGH1234"}' | KM_VAULT="$t3vault" bash "$HOOK")
decision=$(printf '%s' "$out" | jq -r '.decision')
reason=$(printf '%s' "$out" | jq -r '.reason')
assert_eq "block decision" "block" "$decision"
assert_contains "reason 帶專案 slug" "investment-research-os" "$reason"
assert_contains "reason 帶候選路徑" "01_Inbox/_candidates/" "$reason"
assert_contains "reason 帶 session 前綴" "ABCDEFGH" "$reason"
assert_contains "reason 要求只寫候選不動 SoT" "不要" "$reason"

# --- Test 4: 候選已存在 → 不重複 block ---
date_today=$(date +%F)
mkdir -p "$t3vault/01_Inbox/_candidates"
touch "$t3vault/01_Inbox/_candidates/${date_today}--investment-research-os--ABCDEFGH.md"
out2=$(echo '{"stop_hook_active":false,"cwd":"'"$t3cwd"'","session_id":"ABCDEFGH1234"}' | KM_VAULT="$t3vault" bash "$HOOK")
assert_eq "候選已存在則不 block（空輸出）" "" "$out2"
```

- [ ] **Step 2: 跑測試確認新測試失敗**

Run: `bash tools/hooks/test/run-tests.sh`
Expected: FAIL（Test 3/4 失敗：目前 marker 找到後直接 `exit 0`，無 block 輸出）

- [ ] **Step 3: 實作 block 邏輯（取代 Task 1 的佔位 `exit 0`）**

把 `tools/hooks/km-session-wrap.sh` 末行 `exit 0  # 後續 Task 2 補 block 邏輯` 換成：

```bash
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
   - 先讀 $VAULT/03_Projects/$project/ 找 kind: dev_goal 目標卡，取其 frontmatter uid 當 goal=；找不到就 goal=$project。
   - [!progress] stage=<目前階段> date=$today goal=<uid或$project> seq=01 ，body：did/result/next。
   - 每個本次踩到並解掉的錯誤寫一筆 [!lesson] skill=<相關skill> stage=<階段> error=<錯誤類型短標籤>，body：what/fix/rule。
3. 寫完該檔後即可正常結束（停止）。"

jq -n --arg r "$reason" '{decision:"block", reason:$r}'
exit 0
```

- [ ] **Step 4: 跑測試確認全數通過**

Run: `bash tools/hooks/test/run-tests.sh`
Expected: PASS（`PASS=10 FAIL=0`）

- [ ] **Step 5: Commit**

```bash
git add tools/hooks/km-session-wrap.sh tools/hooks/test/run-tests.sh
git commit -m "feat(hook): 有 .km-project 時 block 並產生收尾指示"
```

---

## Task 3: 候選暫存目錄與 gitignore

**Files:**
- Create: `01_Inbox/_candidates/.gitkeep`
- Modify: `.gitignore`

- [ ] **Step 1: 建目錄佔位檔**

```bash
mkdir -p "01_Inbox/_candidates"
printf '' > 01_Inbox/_candidates/.gitkeep
```

- [ ] **Step 2: 在 `.gitignore` 末尾追加**（讓候選草稿不進版控，保留目錄）

```gitignore

# Session Wrap 候選草稿（暫存、可丟、核准後刪除；不進版控）
01_Inbox/_candidates/*
!01_Inbox/_candidates/.gitkeep
```

- [ ] **Step 3: 驗證 gitignore 生效**

Run: `printf 'x' > 01_Inbox/_candidates/probe.md && git status --short 01_Inbox/_candidates/`
Expected: 只見 `.gitkeep`（已 tracked 則無輸出），**不**見 `probe.md`
Cleanup: `rm 01_Inbox/_candidates/probe.md`

- [ ] **Step 4: Commit**

```bash
git add 01_Inbox/_candidates/.gitkeep .gitignore
git commit -m "chore: 候選草稿暫存目錄 + gitignore"
```

---

## Task 4: `.km-project` 標記（vault dogfood）+ 慣例文件

**Files:**
- Create: `.km-project`
- Create: `tools/hooks/README.md`

- [ ] **Step 1: 在 vault 根建立標記（讓 knowledge-os 自己的 session 也被收尾）**

```bash
printf 'knowledge-os\n' > .km-project
```

- [ ] **Step 2: 寫 hook 安裝與慣例說明**

Create `tools/hooks/README.md`:

```markdown
# Session Wrap Capture — Hook

## 它做什麼
每次 Claude Code session 結束（Stop 事件），若當前 repo 根目錄有 `.km-project`，
hook 會讓 Claude 用自身 context 寫一塊候選草稿到
`<vault>/01_Inbox/_candidates/`，之後用 `/km-review` 核准併入 SoT。

## `.km-project` 慣例
在「要追蹤開發進度的 code repo」根目錄放一個 `.km-project`，
內容為對應的 vault 專案 slug（單行），例如：

    investment-research-os

沒有此檔的 repo，hook 一律 no-op，不打擾。

## 安裝（全域 settings.json）
在 `~/.claude/settings.json` 的 `hooks` 加入（與既有 hook 並存）：

    "Stop": [
      {
        "hooks": [
          { "type": "command",
            "command": "bash /Users/juiyujao/Projects/knowledge-os/tools/hooks/km-session-wrap.sh" }
        ]
      }
    ]

vault 路徑可用環境變數 `KM_VAULT` 覆寫（預設 /Users/juiyujao/Projects/knowledge-os）。

## 測試
    bash tools/hooks/test/run-tests.sh
```

- [ ] **Step 3: Commit**

```bash
git add .km-project tools/hooks/README.md
git commit -m "feat: vault .km-project 標記 + hook 安裝/慣例說明"
```

---

## Task 5: 安裝 Stop hook 到全域 settings.json（手動 + 驗證）

**Files:**
- Modify: `~/.claude/settings.json`（repo 外，需手動）

- [ ] **Step 1: 備份**

Run: `cp ~/.claude/settings.json ~/.claude/settings.json.bak`
Expected: 無輸出（成功）

- [ ] **Step 2: 用 jq 加入 Stop hook（與既有 UserPromptSubmit 並存）**

Run:
```bash
tmp=$(mktemp)
jq '.hooks.Stop = [{"hooks":[{"type":"command","command":"bash /Users/juiyujao/Projects/knowledge-os/tools/hooks/km-session-wrap.sh"}]}]' \
  ~/.claude/settings.json > "$tmp" && mv "$tmp" ~/.claude/settings.json
```
Expected: 無錯誤

- [ ] **Step 3: 驗證 JSON 合法且含 Stop hook**

Run: `jq '.hooks | keys' ~/.claude/settings.json`
Expected: 包含 `"Stop"` 與 `"UserPromptSubmit"`

- [ ] **Step 4: 整合測試（模擬一次真實 hook 呼叫）**

Run:
```bash
echo '{"stop_hook_active":false,"cwd":"'"$PWD"'","session_id":"TESTSESSION01"}' \
  | bash tools/hooks/km-session-wrap.sh | jq -r '.decision'
```
Expected: `block`（因 vault 根有 `.km-project`）
> 註：此步只驗證腳本，**不會**真的寫檔（block 只是回傳指示）。

- [ ] **Step 5: 無檔案變更，不需 commit**

說明：settings.json 在 repo 外。若日後想版控，另存範本；本步不 commit。

---

## Task 6: `[!lesson]` 慣例文件（callouts.md）

**Files:**
- Modify: `_docs/callouts.md`

- [ ] **Step 1: 在 `_docs/callouts.md` 的 `[!progress]` 區段之後追加**

````markdown

## `[!lesson]`：錯誤→教訓（session 收尾捕捉，會被同步工具抽取）

由 Session Wrap 收尾自動產生、`/km-review` 核准後存入 `02_Notes/lessons.md`：

```markdown
> [!lesson] skill=test-driven-development stage=Build error=flaky-test
> what: 測試偶發失敗，誤判是程式 bug
> fix: 改用固定 seed，隔離時間依賴
> rule: Build 階段寫測試先釘死隨機源
```

- header 屬性：`skill`（相關 skill）/ `stage`（Idea|Build|Validate|Ship|Maintain）/ `error`（錯誤類型短標籤）。
- body 鍵：`what`（發生什麼）/ `fix`（怎麼解）/ `rule`（萃取出的可復用規則）。
- 累積的教訓索引見 `04_MOCs/playbook.md`（append-only）。
````

- [ ] **Step 2: 驗證渲染（人工檢視）**

Run: `sed -n '/\[!lesson\]/,/playbook/p' _docs/callouts.md`
Expected: 看到完整 `[!lesson]` 區段

- [ ] **Step 3: Commit**

```bash
git add _docs/callouts.md
git commit -m "docs: callouts 字典新增 [!lesson] 慣例"
```

---

## Task 7: 教訓集與 playbook 索引（種子檔）

**Files:**
- Create: `02_Notes/lessons.md`
- Create: `04_MOCs/playbook.md`

- [ ] **Step 1: 建 append-only 教訓集**

Create `02_Notes/lessons.md`:

```markdown
---
uid: 01KSESSIONWRAPLESSONS0001
status: verified
kind: note
title: "教訓集 Lessons（append-only）"
mirror: false
---

# 教訓集 Lessons

> Session Wrap 收尾捕捉、`/km-review` 核准後追加於此（append-only，不重排、不搬家）。
> 每筆對應一個 `[!lesson]`。彙整索引見 [[playbook]]。

<!-- /km-review 由此行下方往下 append [!lesson] callouts -->
```

- [ ] **Step 2: 建 append-only playbook 索引**

Create `04_MOCs/playbook.md`:

```markdown
---
uid: 01KSESSIONWRAPPLAYBOOK001
status: verified
kind: note
title: "做法 Playbook（階段 × skill × 錯誤，append-only 索引）"
mirror: false
---

# 做法 Playbook

> 由下而上長出來：每次 `/km-review` 核准一筆教訓，就追加一行索引（append-only）。
> 用 Obsidian 搜尋 `stage=Build` 或 `skill=` 即可拉出某階段/某 skill 的歷史教訓。
> （備註：採 append-only 索引而非 Dataview，因 Dataview 無法解析 callout 標頭屬性。）

格式：`- {date} — stage={stage} skill={skill} error={error} — {rule}`

## 索引
<!-- /km-review 由此行下方往下 append 一行索引 -->
```

- [ ] **Step 3: Commit**

```bash
git add 02_Notes/lessons.md 04_MOCs/playbook.md
git commit -m "feat: 教訓集 lessons.md + playbook 索引種子檔"
```

---

## Task 8: `/km-review` 指令

**Files:**
- Create: `.claude/commands/km-review.md`

- [ ] **Step 1: 寫指令（Claude Code project slash command）**

Create `.claude/commands/km-review.md`:

```markdown
---
description: 審核 Session Wrap 候選草稿，核准後併入 SoT
---

你是 knowledge-os 的 promotion 守門員。執行候選審核流程，嚴守「提議→預覽→核准→寫入」。

## 步驟
1. 列出 `01_Inbox/_candidates/` 內所有 `.md` 候選檔（忽略 `.gitkeep`）。若無 → 回報「無待審候選」並結束。
2. 逐一處理每個候選檔：
   a. 完整顯示其內容（[!progress] 與 [!lesson] 區塊）。
   b. 問使用者：approve / edit / reject。
   c. **approve：**
      - 對每個 `[!progress]`：找出其 `goal=` 對應的目標卡
        （`03_Projects/<slug>/` 內 frontmatter `uid` 等於該 goal 值的 dev_goal 檔；
        若 goal 非 uid 而是專案 slug 或找不到，回報並詢問要併入哪張目標卡）。
        把該 `[!progress]` callout 追加到目標卡的 `## Stage Log` 區段末尾。
      - 對每個 `[!lesson]`：
        - 把該 callout 追加到 `02_Notes/lessons.md` 末尾（append-only）。
        - 從其 header 取 `stage`/`skill`/`error`、body 取 `rule`，
          追加一行到 `04_MOCs/playbook.md` 的「## 索引」下方：
          `- <date> — stage=<stage> skill=<skill> error=<error> — <rule>`
          （date 取自同候選的 progress date，或今日）。
      - 全部併入成功後，刪除該候選檔。
   d. **edit：** 讓使用者口述修改，改完再回到 b。
   e. **reject：** 刪除候選檔，不寫入任何 SoT。
3. 結束時摘要：併入幾筆 progress、幾筆 lesson、刪幾個候選。

## 硬規定
- 候選檔（`01_Inbox/_candidates/`）是唯一允許「被刪」的對象；其餘只 append，不重排、不改舊內容。
- 未經使用者明確 approve，不得寫入 `03_Projects/`、`02_Notes/lessons.md`、`04_MOCs/playbook.md`。
```

- [ ] **Step 2: 驗證指令被辨識（人工）**

說明：在 Claude Code 輸入 `/km-review` 應出現此指令。若候選目錄為空，應回報「無待審候選」。
（此為 prompt 型指令，無單元測試；以實際執行驗證。）

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/km-review.md
git commit -m "feat: /km-review 候選審核 promotion 指令"
```

---

## Task 9: 端到端 dogfood（產一個真候選 → /km-review）

**Files:** 無新檔（操作驗證）

- [ ] **Step 1: 手動產生一個候選草稿**（模擬 hook 指示的產物）

```bash
mkdir -p 01_Inbox/_candidates
cat > "01_Inbox/_candidates/$(date +%F)--knowledge-os--DOGFOOD1.md" <<'EOF'
> [!progress] stage=Build date=2026-06-01 goal=knowledge-os seq=01
> did: 實作 Session Wrap Capture（hook + /km-review + 慣例）
> result: hook 測試全綠
> next: 端到端 dogfood

> [!lesson] skill=test-driven-development stage=Build error=hook-loop
> what: Stop hook 直接 block 會無限迴圈
> fix: 用 stop_hook_active 旗標，第二次 stop 即放行
> rule: 會 block 的 Stop hook 一律先檢查 stop_hook_active
EOF
```

- [ ] **Step 2: 驗證候選未進版控（gitignore 生效）**

Run: `git status --short 01_Inbox/_candidates/`
Expected: 無此候選檔（只可能見 `.gitkeep`）

- [ ] **Step 3: 跑 `/km-review` 並 approve**

說明：在 Claude Code 執行 `/km-review`，approve 該候選。
Expected 結果：
- `03_Projects/` 無 `knowledge-os` 目標卡 → 指令應回報並詢問併入目標；
  此 dogfood 可選 reject progress 或指定一張現有目標卡測試 append。
- `[!lesson]` 應 append 進 `02_Notes/lessons.md`，且 `04_MOCs/playbook.md` 索引多一行。
- 候選檔被刪除。

- [ ] **Step 4: 驗證 promotion 結果**

Run: `tail -n 5 02_Notes/lessons.md && echo '---' && tail -n 3 04_MOCs/playbook.md`
Expected: lessons.md 末尾有該 `[!lesson]`；playbook.md 索引多一行 `... stage=Build skill=test-driven-development error=hook-loop ...`

- [ ] **Step 5: Commit（promotion 產生的 SoT 變更）**

```bash
git add 02_Notes/lessons.md 04_MOCs/playbook.md 03_Projects/
git commit -m "test: Session Wrap 端到端 dogfood（promotion 驗證）"
```
> 若 dogfood 選擇 reject，無 SoT 變更則跳過 commit。

---

## Task 10: 同步設計文件 — spec / data-contract / Notion Mirror

**Files:**
- Modify: `_docs/spec.md`
- Modify: `data-contract.yaml`
- Modify: Notion「規格書」頁（via MCP）

- [ ] **Step 1: `_docs/spec.md` §3.1 callout 表加一列**

在 `_docs/spec.md` §3.1 的 callout 表格 `[!progress]` 列之後加：

```markdown
| `[!lesson]` | **錯誤→教訓**：Session 收尾捕捉，`/km-review` 核准後存入 `02_Notes/lessons.md`（見 6.6） |
```

- [ ] **Step 2: `_docs/spec.md` 新增 §6.6 與更新 §5 playbook 說明**

在 §6.5 之後插入：

```markdown
### 6.6 Session 收尾自動捕捉（Session Wrap Capture）
- 全域 Claude Code Stop hook：cwd 有 `.km-project`（內容＝專案 slug）時，讓 Claude 用自身 context 寫候選草稿到 `01_Inbox/_candidates/`（非 SoT，gitignore）。`stop_hook_active` 防迴圈。
- 候選含 `[!progress]`（did/result/next，需求 3）與 `[!lesson]`（skill/stage/error → what/fix/rule，需求 1）。
- `/km-review` 做 promotion：`[!progress]`→目標卡 Stage Log、`[!lesson]`→`02_Notes/lessons.md`，並追加一行到 `04_MOCs/playbook.md` 索引。守 §8.1 人工核准閘。
- 設計與計畫：`docs/superpowers/specs/2026-06-01-session-wrap-capture-design.md`、`docs/superpowers/plans/2026-06-01-session-wrap-capture.md`。
```

並把 §7.1 之外的「playbook = Dataview」相關敘述（若有）統一為：**playbook 採 append-only 索引（`04_MOCs/playbook.md`），非 Dataview**（因 Dataview 無法解析 callout 標頭屬性）。

- [ ] **Step 3: `data-contract.yaml` 登記 `[!lesson]` 抽取（為未來 Notion 投影預留）**

在 `extraction:` 區段 `stage_log:` 之後加（縮排對齊）：

```yaml
  lesson:
    callout:
      type: "lesson"
      header_match: "[!lesson]"   # 不分大小寫
      attributes_allowed: [skill, stage, error]
      body_fields:
        preferred_keys: [what, fix, rule]
        fallback: "raw_block"
    output:
      entity: "dev_lesson"
      note: "Phase 2b+ 才投影到 Notion；目前僅本地存於 02_Notes/lessons.md"
```

- [ ] **Step 4: 驗證 YAML 合法**

Run: `python3 -c "import yaml,sys; yaml.safe_load(open('data-contract.yaml')); print('ok')"`
Expected: `ok`

- [ ] **Step 5: Commit 本地文件**

```bash
git add _docs/spec.md data-contract.yaml
git commit -m "docs: spec/契約 登記 [!lesson] 與 Session Wrap 流程（§6.6）"
```

- [ ] **Step 6: 同步 Notion Mirror（MCP）**

用 `mcp__claude_ai_Notion__notion-update-page` 的 `update_content`，對 page_id `36f97daade5080269a7ff81502e9937c`：
- 在 §3.1 callout 表加 `[!lesson]` 列（Notion `<table>` 多一 `<tr>`）。
- 在 §6.5 之後加 §6.6（內容同 Step 2）。
先 `notion-fetch` 取得對應 `old_str` 片段再替換。
Expected: 回傳該 page_id，無錯誤。

> 註：Notion 是 Mirror，本步失敗不影響 SoT（符合 FM-2）。

---

## Self-Review（規劃者自查結果）

**Spec coverage：** spec §2.1 in-scope 全覆蓋 → Stop hook(Task 1–2,5)、`.km-project`(Task 4)、候選產生(Task 2 指示 + Task 9)、`[!lesson]`(Task 6)、playbook(Task 7)、`/km-review`(Task 8)、spec/契約/callouts/Mirror 更新(Task 6,10)。需求 1=Task 6/7/8；需求 3=Task 2/8。

**設計微調（已記錄）：** spec §5「Dataview playbook」→ append-only 索引（Task 7 + Task 10 Step 2 同步 spec）。理由：Dataview 無法解析 callout 標頭屬性。

**Placeholder scan：** 無 TBD/TODO；每個 code step 附完整內容。

**Type/名稱一致：** 候選路徑格式 `${date}--${project}--${sid8}.md` 在 Task 2 腳本、Task 2 測試、Task 8 指令、Task 9 dogfood 一致；callout 屬性 `skill/stage/error` + body `what/fix/rule` 在 Task 2/6/7/8/10 一致；`stop_hook_active` 防迴圈在 Task 1 測試與 Task 2 腳本一致。

**已知限制／需執行者注意：**
- `.km-project` 只在 vault 根（dogfood）；外部 code repo 由使用者依 Task 4 README 自行放置。
- Task 5、Task 8 Step 2、Task 9 Step 3、Task 10 Step 6 為人工/MCP 驗證（非單元測試），因 hook 安裝、slash command、Notion 屬本質上的整合行為。
```
