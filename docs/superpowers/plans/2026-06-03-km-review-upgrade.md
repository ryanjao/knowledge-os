# km-review 升級 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在候選 promote 進 SoT 前加一道死板的結構驗證鐵閘（機器把關），把語法錯誤翻成白話「入庫審查單」（人類秒懂），並補上 knowledge-os 自我目標卡與雙保險待審提醒。

**Architecture:** Python stdlib 寫的純函式驗證器（`validate(path, vault_root)->list[Finding]`）吐結構化 `rule_id`；白話文案放一張「規則→白話」對照表，由 `/km-review`（agent）渲染成審查單。提醒用 bash：Stop hook 尾段 + 新 SessionStart hook 各數一次待審候選。

**Tech Stack:** Python 3.10 stdlib（`unittest`，零 pip 依賴，比照 repo 既有「零依賴」bash 測試慣例）、bash hooks、Obsidian Markdown。

**設計來源：** `docs/superpowers/specs/2026-06-03-km-review-upgrade-design.md`

---

## 檔案結構

| 檔案 | 責任 |
|---|---|
| `tools/km_review/validate_candidate.py` | 純驗證邏輯 + 規則對照表 + CLI 薄包裝 |
| `tools/km_review/test_validate_candidate.py` | TDD 測試（stdlib unittest） |
| `03_Projects/knowledge-os/goal.md` | knowledge-os 自我 dev_goal 目標卡 |
| `.claude/commands/km-review.md` | 接驗證器 + 白話審查單 + slug 自動解析（修改） |
| `tools/hooks/km-session-wrap.sh` | 尾段加待審計數提醒（修改） |
| `tools/hooks/km-pending-review.sh` | 新增：SessionStart 待審提醒腳本 |
| `tools/hooks/test/run-tests.sh` | 加 pending-review + reason 計數測試（修改） |
| `.claude/settings.json` | 新增：版控 SessionStart hook 接線 |

**測試怎麼跑：** `python3 tools/km_review/test_validate_candidate.py`（檔尾 `unittest.main()`，零設定）。

**驗證器資料型別（全 task 共用，先固定）：**
```python
from collections import namedtuple
Finding = namedtuple("Finding", ["rule_id", "level", "location", "raw"])
# level: "block"（攔截）/ "warn"（放行但提示）。本期全部 block。
# location: 人看的定位（如 "[!progress] #1" 或 "檔名"）
# raw: 機器事實（如缺的欄位名 "seq"），渲染端拿來填白話模板
```

---

## Task 1: 驗證器骨架 + 檔名規則

**Files:**
- Create: `tools/km_review/validate_candidate.py`
- Test: `tools/km_review/test_validate_candidate.py`

- [ ] **Step 1: 寫失敗測試**

```python
# tools/km_review/test_validate_candidate.py
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_candidate import validate, Finding  # noqa: E402


def write_candidate(dirpath, filename, body):
    """在指定目錄寫一個候選檔，回傳完整路徑。"""
    path = os.path.join(dirpath, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    return path


GOOD_PROGRESS = (
    "> [!progress] stage=Build date=2026-06-03 goal=knowledge-os seq=01\n"
    "> did: 做了一件事\n"
    "> result: 成功\n"
    "> next: 下一步\n"
)


class FilenameRuleTest(unittest.TestCase):
    def test_bad_filename_triggers_err_filename(self):
        with tempfile.TemporaryDirectory() as d:
            path = write_candidate(d, "bad-name.md", GOOD_PROGRESS)
            rule_ids = [f.rule_id for f in validate(path, vault_root=d)]
            self.assertIn("ERR_FILENAME", rule_ids)

    def test_good_filename_no_err_filename(self):
        with tempfile.TemporaryDirectory() as d:
            path = write_candidate(
                d, "2026-06-03--knowledge-os--abc12345.md", GOOD_PROGRESS
            )
            rule_ids = [f.rule_id for f in validate(path, vault_root=d)]
            self.assertNotIn("ERR_FILENAME", rule_ids)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python3 tools/km_review/test_validate_candidate.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'validate_candidate'`

- [ ] **Step 3: 最小實作（骨架 + 檔名規則）**

```python
# tools/km_review/validate_candidate.py
"""knowledge-os 候選草稿結構驗證器。

只驗「結構」（欄位齊不齊、格式對不對），不碰語意（內容看不看得懂留給人）。
吐 rule_id；白話文案見本檔 RULE_MESSAGES，由 /km-review 渲染成審查單。
"""
import os
import re
from collections import namedtuple

Finding = namedtuple("Finding", ["rule_id", "level", "location", "raw"])

FILENAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}--[a-z0-9-]+--[0-9a-f]{6,}\.md$")


def _check_filename(path):
    name = os.path.basename(path)
    if not FILENAME_RE.match(name):
        return [Finding("ERR_FILENAME", "block", "檔名", name)]
    return []


def validate(path, vault_root=None):
    """驗證一個候選檔，回傳 Finding 清單（空＝通過）。"""
    findings = []
    findings += _check_filename(path)
    return findings
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python3 tools/km_review/test_validate_candidate.py`
Expected: PASS（2 tests）

- [ ] **Step 5: Commit**

```bash
git add tools/km_review/validate_candidate.py tools/km_review/test_validate_candidate.py
git commit -m "feat(km-review): 候選驗證器骨架 + 檔名規則"
```

---

## Task 2: `[!progress]` 結構規則

**Files:**
- Modify: `tools/km_review/validate_candidate.py`
- Test: `tools/km_review/test_validate_candidate.py`

- [ ] **Step 1: 寫失敗測試**（append 到測試檔，`if __name__` 之前）

```python
PROGRESS_FNAME = "2026-06-03--knowledge-os--abc12345.md"


class ProgressRuleTest(unittest.TestCase):
    def test_missing_seq_in_header(self):
        body = (
            "> [!progress] stage=Build date=2026-06-03 goal=knowledge-os\n"
            "> did: x\n> result: y\n> next: z\n"
        )
        with tempfile.TemporaryDirectory() as d:
            path = write_candidate(d, PROGRESS_FNAME, body)
            findings = validate(path, vault_root=d)
            hdr = [f for f in findings if f.rule_id == "ERR_PROGRESS_HEADER"]
            self.assertTrue(hdr)
            self.assertIn("seq", hdr[0].raw)

    def test_missing_next_in_body(self):
        body = (
            "> [!progress] stage=Build date=2026-06-03 goal=knowledge-os seq=01\n"
            "> did: x\n> result: y\n"
        )
        with tempfile.TemporaryDirectory() as d:
            path = write_candidate(d, PROGRESS_FNAME, body)
            findings = validate(path, vault_root=d)
            bod = [f for f in findings if f.rule_id == "ERR_PROGRESS_BODY"]
            self.assertTrue(bod)
            self.assertIn("next", bod[0].raw)

    def test_good_progress_no_progress_errors(self):
        with tempfile.TemporaryDirectory() as d:
            path = write_candidate(d, PROGRESS_FNAME, GOOD_PROGRESS)
            findings = validate(path, vault_root=d)
            ids = [f.rule_id for f in findings]
            self.assertNotIn("ERR_PROGRESS_HEADER", ids)
            self.assertNotIn("ERR_PROGRESS_BODY", ids)
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python3 tools/km_review/test_validate_candidate.py`
Expected: FAIL — `ERR_PROGRESS_HEADER` / `ERR_PROGRESS_BODY` 不存在

- [ ] **Step 3: 實作 callout 解析 + progress 規則**

在 `validate_candidate.py` 加入 callout 切塊與欄位解析，並在 `validate()` 串接：

```python
CALLOUT_START_RE = re.compile(r"^>\s*\[!(progress|lesson)\]\s*(.*)$")
HEADER_KV_RE = re.compile(r"(\w+)=")
BODY_KEY_RE = re.compile(r"^>\s*(\w+)\s*:")

REQUIRED = {
    "progress": {"header": ["stage", "date", "goal", "seq"],
                 "body": ["did", "result", "next"]},
    "lesson": {"header": ["skill", "stage", "error"],
               "body": ["what", "fix", "rule"]},
}


def _parse_callouts(text):
    """切出 callout 區塊，回傳 [(kind, header_line, [body_lines], start_lineno)]。"""
    blocks = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = CALLOUT_START_RE.match(lines[i])
        if m:
            kind = m.group(1)
            header = m.group(2)
            body = []
            start = i + 1
            j = i + 1
            while j < len(lines) and lines[j].lstrip().startswith(">"):
                body.append(lines[j])
                j += 1
            blocks.append((kind, header, body, start))
            i = j
        else:
            i += 1
    return blocks


def _check_callout_fields(kind, header, body, idx):
    findings = []
    loc = f"[!{kind}] #{idx}"
    header_keys = set(HEADER_KV_RE.findall(header))
    missing_h = [k for k in REQUIRED[kind]["header"] if k not in header_keys]
    if missing_h:
        findings.append(Finding(
            f"ERR_{kind.upper()}_HEADER", "block", loc, ",".join(missing_h)))
    body_keys = set()
    for line in body:
        bm = BODY_KEY_RE.match(line)
        if bm:
            body_keys.add(bm.group(1))
    missing_b = [k for k in REQUIRED[kind]["body"] if k not in body_keys]
    if missing_b:
        findings.append(Finding(
            f"ERR_{kind.upper()}_BODY", "block", loc, ",".join(missing_b)))
    return findings
```

並改 `validate()`：

```python
def validate(path, vault_root=None):
    findings = []
    findings += _check_filename(path)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    blocks = _parse_callouts(text)
    counters = {"progress": 0, "lesson": 0}
    for kind, header, body, _start in blocks:
        counters[kind] += 1
        findings += _check_callout_fields(kind, header, body, counters[kind])
    return findings
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python3 tools/km_review/test_validate_candidate.py`
Expected: PASS（全部，含 Task 1 的）

- [ ] **Step 5: Commit**

```bash
git add tools/km_review/validate_candidate.py tools/km_review/test_validate_candidate.py
git commit -m "feat(km-review): [!progress] 結構規則 + callout 解析"
```

---

## Task 3: `[!lesson]` 結構規則

**Files:**
- Modify: `tools/km_review/test_validate_candidate.py`（邏輯已由 Task 2 的泛用 `_check_callout_fields` 覆蓋，本 task 只補測試鎖行為）

- [ ] **Step 1: 寫測試**

```python
class LessonRuleTest(unittest.TestCase):
    def test_missing_error_in_header(self):
        body = (
            "> [!lesson] skill=tdd stage=Build\n"
            "> what: x\n> fix: y\n> rule: z\n"
        )
        with tempfile.TemporaryDirectory() as d:
            path = write_candidate(d, PROGRESS_FNAME, body)
            findings = validate(path, vault_root=d)
            hdr = [f for f in findings if f.rule_id == "ERR_LESSON_HEADER"]
            self.assertTrue(hdr)
            self.assertIn("error", hdr[0].raw)

    def test_missing_fix_in_body(self):
        body = (
            "> [!lesson] skill=tdd stage=Build error=oops\n"
            "> what: x\n> rule: z\n"
        )
        with tempfile.TemporaryDirectory() as d:
            path = write_candidate(d, PROGRESS_FNAME, body)
            findings = validate(path, vault_root=d)
            bod = [f for f in findings if f.rule_id == "ERR_LESSON_BODY"]
            self.assertTrue(bod)
            self.assertIn("fix", bod[0].raw)
```

- [ ] **Step 2: 跑測試確認通過（行為已存在）**

Run: `python3 tools/km_review/test_validate_candidate.py`
Expected: PASS — 泛用規則已覆蓋 lesson；測試把行為鎖死防回歸

- [ ] **Step 3: Commit**

```bash
git add tools/km_review/test_validate_candidate.py
git commit -m "test(km-review): 鎖 [!lesson] 結構規則"
```

---

## Task 4: callout 破框規則

**Files:**
- Modify: `tools/km_review/validate_candidate.py`, `tools/km_review/test_validate_candidate.py`

破框定義：候選檔有 `[!progress]`/`[!lesson]` 起始行，但**整份檔案沒有任何 callout 被解析出來**（例如起始行沒以 `>` 開頭、或框被切斷）。另含「整份檔完全沒有任何 progress/lesson 區塊」。

- [ ] **Step 1: 寫失敗測試**

```python
class CalloutIntegrityTest(unittest.TestCase):
    def test_no_callout_at_all(self):
        with tempfile.TemporaryDirectory() as d:
            path = write_candidate(d, PROGRESS_FNAME, "純文字沒有任何 callout\n")
            ids = [f.rule_id for f in validate(path, vault_root=d)]
            self.assertIn("ERR_NO_CALLOUT", ids)

    def test_broken_callout_marker_without_gt(self):
        # 起始行缺 '>'，無法被解析成 callout
        body = "[!progress] stage=Build date=2026-06-03 goal=knowledge-os seq=01\n"
        with tempfile.TemporaryDirectory() as d:
            path = write_candidate(d, PROGRESS_FNAME, body)
            ids = [f.rule_id for f in validate(path, vault_root=d)]
            self.assertIn("ERR_CALLOUT_BROKEN", ids)
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python3 tools/km_review/test_validate_candidate.py`
Expected: FAIL — 兩個 rule_id 都還沒產出

- [ ] **Step 3: 實作**

在 `validate_candidate.py` 加偵測，並在 `validate()` blocks 解析後插入：

```python
BROKEN_MARKER_RE = re.compile(r"^\s*\[!(progress|lesson)\]")
```

`validate()` 內，`blocks = _parse_callouts(text)` 之後、迴圈之前加入：

```python
    if not blocks:
        # 有 marker 文字卻沒解析出 callout → 破框；完全沒 marker → 沒內容
        if any(BROKEN_MARKER_RE.match(ln) for ln in text.splitlines()):
            findings.append(Finding("ERR_CALLOUT_BROKEN", "block", "callout", ""))
        else:
            findings.append(Finding("ERR_NO_CALLOUT", "block", "整份檔", ""))
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python3 tools/km_review/test_validate_candidate.py`
Expected: PASS（全部）

- [ ] **Step 5: Commit**

```bash
git add tools/km_review/validate_candidate.py tools/km_review/test_validate_candidate.py
git commit -m "feat(km-review): callout 破框 / 無內容規則"
```

---

## Task 5: `goal=` 解析規則

**Files:**
- Modify: `tools/km_review/validate_candidate.py`, `tools/km_review/test_validate_candidate.py`

規則：每個 `[!progress]` 的 `goal=` 值，必須能對應到某 `dev_goal` 目標卡的 `uid`，**或**等於某 `03_Projects/<slug>/` 內含 `dev_goal` 卡的專案 slug；都對不到 → `ERR_GOAL_UNRESOLVED`。

- [ ] **Step 1: 寫失敗測試**

```python
def make_goal_card(vault, slug, uid):
    """在 temp vault 建一張 dev_goal 目標卡。"""
    pdir = os.path.join(vault, "03_Projects", slug)
    os.makedirs(pdir, exist_ok=True)
    with open(os.path.join(pdir, "goal.md"), "w", encoding="utf-8") as f:
        f.write(f"---\nuid: {uid}\nkind: dev_goal\nproject: {slug}\n---\n# Goal\n")


class GoalResolutionTest(unittest.TestCase):
    def test_goal_slug_resolves(self):
        with tempfile.TemporaryDirectory() as d:
            make_goal_card(d, "knowledge-os", "01KKMOSSELFGOAL0001")
            path = write_candidate(d, PROGRESS_FNAME, GOOD_PROGRESS)  # goal=knowledge-os
            ids = [f.rule_id for f in validate(path, vault_root=d)]
            self.assertNotIn("ERR_GOAL_UNRESOLVED", ids)

    def test_goal_uid_resolves(self):
        body = GOOD_PROGRESS.replace("goal=knowledge-os", "goal=01KKMOSSELFGOAL0001")
        with tempfile.TemporaryDirectory() as d:
            make_goal_card(d, "knowledge-os", "01KKMOSSELFGOAL0001")
            path = write_candidate(d, PROGRESS_FNAME, body)
            ids = [f.rule_id for f in validate(path, vault_root=d)]
            self.assertNotIn("ERR_GOAL_UNRESOLVED", ids)

    def test_unknown_goal_blocks(self):
        body = GOOD_PROGRESS.replace("goal=knowledge-os", "goal=does-not-exist")
        with tempfile.TemporaryDirectory() as d:
            make_goal_card(d, "knowledge-os", "01KKMOSSELFGOAL0001")
            path = write_candidate(d, PROGRESS_FNAME, body)
            ids = [f.rule_id for f in validate(path, vault_root=d)]
            self.assertIn("ERR_GOAL_UNRESOLVED", ids)
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python3 tools/km_review/test_validate_candidate.py`
Expected: FAIL — `ERR_GOAL_UNRESOLVED` 邏輯尚未存在

- [ ] **Step 3: 實作 goal 索引 + 規則**

```python
UID_RE = re.compile(r"^uid:\s*(\S+)", re.M)
KIND_DEVGOAL_RE = re.compile(r"^kind:\s*dev_goal\s*$", re.M)
HEADER_GOAL_RE = re.compile(r"goal=(\S+)")


def _collect_goal_ids(vault_root):
    """掃 03_Projects/*/ 的 dev_goal 卡，回傳可接受的 goal 值集合（uid + slug）。"""
    ids = set()
    if not vault_root:
        return ids
    proj = os.path.join(vault_root, "03_Projects")
    if not os.path.isdir(proj):
        return ids
    for slug in os.listdir(proj):
        sdir = os.path.join(proj, slug)
        if not os.path.isdir(sdir):
            continue
        for fn in os.listdir(sdir):
            if not fn.endswith(".md"):
                continue
            with open(os.path.join(sdir, fn), encoding="utf-8") as f:
                head = f.read(2000)
            if KIND_DEVGOAL_RE.search(head):
                ids.add(slug)
                m = UID_RE.search(head)
                if m:
                    ids.add(m.group(1))
    return ids
```

在 `validate()` 的 callout 迴圈裡，對 `progress` 區塊檢查 goal（先在迴圈前算 `goal_ids = _collect_goal_ids(vault_root)`）：

```python
    goal_ids = _collect_goal_ids(vault_root)
    for kind, header, body, _start in blocks:
        counters[kind] += 1
        findings += _check_callout_fields(kind, header, body, counters[kind])
        if kind == "progress":
            gm = HEADER_GOAL_RE.search(header)
            if gm and goal_ids and gm.group(1) not in goal_ids:
                findings.append(Finding(
                    "ERR_GOAL_UNRESOLVED", "block",
                    f"[!progress] #{counters['progress']}", gm.group(1)))
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python3 tools/km_review/test_validate_candidate.py`
Expected: PASS（全部）

- [ ] **Step 5: Commit**

```bash
git add tools/km_review/validate_candidate.py tools/km_review/test_validate_candidate.py
git commit -m "feat(km-review): goal= 解析規則（uid 或專案 slug）"
```

---

## Task 6: 規則→白話對照表 + 渲染 + CLI

**Files:**
- Modify: `tools/km_review/validate_candidate.py`, `tools/km_review/test_validate_candidate.py`

- [ ] **Step 1: 寫失敗測試**

```python
from validate_candidate import render_report, RULE_MESSAGES  # noqa: E402


class RenderTest(unittest.TestCase):
    def test_every_rule_id_has_message(self):
        used = {"ERR_FILENAME", "ERR_PROGRESS_HEADER", "ERR_PROGRESS_BODY",
                "ERR_LESSON_HEADER", "ERR_LESSON_BODY", "ERR_CALLOUT_BROKEN",
                "ERR_NO_CALLOUT", "ERR_GOAL_UNRESOLVED"}
        self.assertTrue(used.issubset(set(RULE_MESSAGES.keys())))

    def test_report_is_plain_language_not_raw_ruleid(self):
        f = Finding("ERR_PROGRESS_HEADER", "block", "[!progress] #1", "seq")
        report = render_report([f], "x.md")
        self.assertIn("症狀", report)
        self.assertIn("規定", report)
        self.assertIn("建議", report)
        self.assertNotIn("ERR_PROGRESS_HEADER", report)  # 火星文不外露

    def test_clean_report_says_pass(self):
        report = render_report([], "x.md")
        self.assertIn("通過", report)
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python3 tools/km_review/test_validate_candidate.py`
Expected: FAIL — `render_report` / `RULE_MESSAGES` 未定義

- [ ] **Step 3: 實作對照表 + 渲染 + CLI**

```python
# 規則→白話對照表（UI 與規則解耦：改措辭不動驗證邏輯）
RULE_MESSAGES = {
    "ERR_FILENAME": {
        "症狀": "候選檔名格式不對。",
        "規定": "須為 YYYY-MM-DD--<slug>--<hash>.md。",
        "建議": "依規則重新命名候選檔。"},
    "ERR_PROGRESS_HEADER": {
        "症狀": "進度區塊標頭缺欄位（{raw}）。",
        "規定": "[!progress] 標頭須含 stage / date / goal / seq。",
        "建議": "補上缺少的欄位。"},
    "ERR_PROGRESS_BODY": {
        "症狀": "進度區塊內文缺欄位（{raw}）。",
        "規定": "[!progress] 內文須含 did / result / next 三行。",
        "建議": "補上缺少的行。"},
    "ERR_LESSON_HEADER": {
        "症狀": "教訓區塊標頭缺欄位（{raw}）。",
        "規定": "[!lesson] 標頭須含 skill / stage / error。",
        "建議": "補上缺少的欄位。"},
    "ERR_LESSON_BODY": {
        "症狀": "教訓區塊內文缺欄位（{raw}）。",
        "規定": "[!lesson] 內文須含 what / fix / rule 三行。",
        "建議": "補上缺少的行。"},
    "ERR_CALLOUT_BROKEN": {
        "症狀": "callout 框破掉，標頭沒被正確解析。",
        "規定": "每行須以 '>' 起頭，如 > [!progress] ...。",
        "建議": "幫每行補上 '>' 前綴。"},
    "ERR_NO_CALLOUT": {
        "症狀": "整份候選沒有任何 [!progress] 或 [!lesson]。",
        "規定": "候選至少要有一個 progress 或 lesson 區塊。",
        "建議": "退回重寫，補上實際內容。"},
    "ERR_GOAL_UNRESOLVED": {
        "症狀": "goal={raw} 對不到任何目標卡。",
        "規定": "goal= 須為某 dev_goal 卡的 uid，或某 03_Projects/<slug> 專案。",
        "建議": "改成正確的 uid/slug，或先替該專案建目標卡。"},
}


def render_report(findings, candidate_path):
    """把 findings 渲染成白話「入庫審查單」（不外露 rule_id）。"""
    name = os.path.basename(candidate_path)
    if not findings:
        return f"📋 入庫審查單：{name}\n檢查結果：✅ 結構通過，可進入人工核准。"
    lines = [f"📋 入庫審查單：{name}",
             f"檢查結果：❌ 結構不符（{len(findings)} 項），已攔截。", ""]
    for i, f in enumerate(findings, 1):
        msg = RULE_MESSAGES.get(f.rule_id, {
            "症狀": "未知問題", "規定": "-", "建議": "-"})
        lines.append(f"項目 {i}（{f.location}）")
        lines.append("• 症狀：" + msg["症狀"].format(raw=f.raw))
        lines.append("• 規定：" + msg["規定"].format(raw=f.raw))
        lines.append("• 建議：" + msg["建議"].format(raw=f.raw))
        lines.append("")
    return "\n".join(lines).rstrip()


def _default_vault(path):
    """候選在 <vault>/01_Inbox/_candidates/x.md → 回推 vault root。"""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(path))))


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="驗證 knowledge-os 候選草稿結構")
    p.add_argument("candidate")
    p.add_argument("--vault", default=None)
    args = p.parse_args(argv)
    vault = args.vault or _default_vault(args.candidate)
    findings = validate(args.candidate, vault_root=vault)
    print(render_report(findings, args.candidate))
    return 1 if any(f.level == "block" for f in findings) else 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
```

> 注意：檔尾若已有 `if __name__ == "__main__":` 由 CLI 取代；本檔不再被 import 時自動執行 `unittest`（測試在獨立檔）。

- [ ] **Step 4: 跑測試確認通過**

Run: `python3 tools/km_review/test_validate_candidate.py`
Expected: PASS（全部）

- [ ] **Step 5: 手動煙霧測試 CLI**

Run: `python3 tools/km_review/validate_candidate.py 01_Inbox/_candidates/2026-06-03--knowledge-os--1090b430.md --vault .`
Expected: 印出白話審查單；因 `03_Projects/knowledge-os/` 目標卡尚未建立（Task 7 才建），會出現「goal=knowledge-os 對不到目標卡」一項——這是預期的，Task 7 後會消失。

- [ ] **Step 6: Commit**

```bash
git add tools/km_review/validate_candidate.py tools/km_review/test_validate_candidate.py
git commit -m "feat(km-review): 規則→白話對照表 + 審查單渲染 + CLI"
```

---

## Task 7: knowledge-os 自我目標卡 + km-review slug 自動解析

**Files:**
- Create: `03_Projects/knowledge-os/goal.md`
- Modify: `.claude/commands/km-review.md`

- [ ] **Step 1: 建自我目標卡**

```markdown
---
uid: 01KKMOSSELFGOAL0001
status: verified
kind: dev_goal
project: knowledge-os
stage: Build
method: [TDD, Python, Bash]
phase_done: 0
phase_total: 1
mirror: true
source_date: 2026-06-03
---
# Goal：knowledge-os 系統本身的開發

## 方法 Method
- spec → plan → TDD 實作 → dogfood
- 守 §8.1 人工核准閘；SoT append-only

## DoD
- Session Wrap + /km-review promotion 閉環可用
- 候選 promote 前有結構驗證鐵閘 + 白話審查單

## Stage Log
<!-- /km-review 由此 append [!progress] -->
```

- [ ] **Step 2: 驗證目標卡讓 CLI 不再報 goal 未解析**

Run: `python3 tools/km_review/validate_candidate.py 01_Inbox/_candidates/2026-06-03--knowledge-os--1090b430.md --vault .`
Expected: 審查單**不再**出現「goal=knowledge-os 對不到」；結構通過（✅）。

- [ ] **Step 3: 改 km-review.md 步驟 2c 的 slug 解析**

把 `.claude/commands/km-review.md` 步驟 2c 中目標卡定位這段：

原文：
```
        （`03_Projects/<slug>/` 內 frontmatter `uid` 等於該 goal 值的 dev_goal 檔；
        若 goal 非 uid 而是專案 slug 或找不到，回報並詢問要併入哪張目標卡）。
```
改為：
```
        （依序解析 goal 值：
         1. 等於某 `03_Projects/<slug>/` 內 dev_goal 檔的 frontmatter `uid` → 用該卡；
         2. 否則等於某 `03_Projects/<slug>/` 且該目錄含 dev_goal 卡 → 自動用該卡，不再追問；
         3. 都對不到 → 回報並詢問要併入哪張目標卡）。
```

- [ ] **Step 4: Commit**

```bash
git add 03_Projects/knowledge-os/goal.md .claude/commands/km-review.md
git commit -m "feat(km-review): knowledge-os 自我目標卡 + slug 自動解析"
```

---

## Task 8: km-review 接驗證器 + 白話審查單

**Files:**
- Modify: `.claude/commands/km-review.md`

- [ ] **Step 1: 改步驟 2，插入驗證關**

把 `.claude/commands/km-review.md` 步驟 2 的子步驟 a/b 之間插入驗證，整段改為：

```
2. 逐一處理每個候選檔：
   a. **結構驗證（鐵閘）**：執行
      `python3 tools/km_review/validate_candidate.py <候選檔> --vault .`
      把輸出的白話「入庫審查單」原樣顯示給使用者。
   b. 完整顯示候選內容（[!progress] 與 [!lesson] 區塊）。
   c. 若審查單有 ❌ 攔截項 → 預設引導 `edit`（你提自動修法），但仍由使用者決定；
      無攔截 → 問使用者：approve / edit / reject。
   d. **approve：** （以下併入流程同原 2c）…
   e. **edit：** 讓使用者口述修改，改完回到 a（重新驗證）。
   f. **reject：** 刪除候選檔，不寫入任何 SoT。
```
（原 2c→2d、2d→2e、2e→2f 順位後移；併入細節與「## 硬規定」不變。）

- [ ] **Step 2: 人工抽驗（讀一遍指令是否自洽）**

Run: `sed -n '1,60p' .claude/commands/km-review.md`
Expected: 步驟順序自洽、驗證在核准前、人工 Y 閘仍在。

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/km-review.md
git commit -m "feat(km-review): 核准前先跑結構驗證 + 顯示白話審查單"
```

---

## Task 9: 收尾端待審提醒（Stop hook 尾段）

**Files:**
- Modify: `tools/hooks/km-session-wrap.sh`, `tools/hooks/test/run-tests.sh`

- [ ] **Step 1: 寫失敗測試**（append 到 `tools/hooks/test/run-tests.sh` 既有測試之後、結尾統計之前）

```bash
# --- Test: reason 內含待審候選計數提醒 ---
tRcwd=$(mktmp); echo "demo" > "$tRcwd/.km-project"
tRvault=$(mktmp); mkdir -p "$tRvault/01_Inbox/_candidates"
# 預先放 2 個待審候選（不同於本 session 將建立的那個）
printf 'x' > "$tRvault/01_Inbox/_candidates/2026-06-01--demo--aaaaaaaa.md"
printf 'x' > "$tRvault/01_Inbox/_candidates/2026-06-02--demo--bbbbbbbb.md"
out=$(echo '{"stop_hook_active":false,"cwd":"'"$tRcwd"'","session_id":"zzzzzzzz"}' | KM_VAULT="$tRvault" bash "$HOOK")
assert_contains "reason 含待審候選提醒" "待審" "$out"
assert_contains "reason 含 /km-review" "/km-review" "$out"
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `bash tools/hooks/test/run-tests.sh`
Expected: 兩條新 assert FAIL（reason 尚無待審字樣）

- [ ] **Step 3: 實作——在 reason 尾段加待審計數**

在 `tools/hooks/km-session-wrap.sh` 組好 `reason`（`jq -n` 之前）插入：

```bash
pending=$(ls -1 "$candir"/*.md 2>/dev/null | grep -v '/\.gitkeep$' | wc -l | tr -d ' ')
if [ "${pending:-0}" -gt 0 ]; then
  reason="$reason

📋 目前 _candidates/ 有 $pending 筆候選待審，記得跑 /km-review 清掉。"
fi
```
（放在 `candidate` 計算之後、`jq -n --arg r "$reason"` 之前。注意 `$pending` 用 `${pending}` 界定，避免變數緊接中文觸發 bash 3.2 問題——既有教訓。）

- [ ] **Step 4: 跑測試確認通過**

Run: `bash tools/hooks/test/run-tests.sh`
Expected: 全綠（含既有 + 2 新）

- [ ] **Step 5: Commit**

```bash
git add tools/hooks/km-session-wrap.sh tools/hooks/test/run-tests.sh
git commit -m "feat(km-review): 收尾 hook 加待審候選計數提醒"
```

---

## Task 10: 開場端待審提醒（SessionStart hook）

**Files:**
- Create: `tools/hooks/km-pending-review.sh`
- Create: `.claude/settings.json`
- Modify: `tools/hooks/test/run-tests.sh`

- [ ] **Step 1: 寫失敗測試**（append 到 `run-tests.sh`）

```bash
PENDING_HOOK="$(cd "$(dirname "$0")/.." && pwd)/km-pending-review.sh"
# --- Test: 有待審候選 → 輸出提醒 ---
tPvault=$(mktmp); mkdir -p "$tPvault/01_Inbox/_candidates"
printf 'x' > "$tPvault/01_Inbox/_candidates/2026-06-01--demo--aaaaaaaa.md"
out=$(echo '{"cwd":"'"$tPvault"'"}' | KM_VAULT="$tPvault" bash "$PENDING_HOOK")
assert_contains "開場提醒含待審" "待審" "$out"
# --- Test: 無待審候選 → 不吵（空輸出）---
tP0vault=$(mktmp); mkdir -p "$tP0vault/01_Inbox/_candidates"
out=$(echo '{"cwd":"'"$tP0vault"'"}' | KM_VAULT="$tP0vault" bash "$PENDING_HOOK")
assert_eq "無待審不輸出" "" "$out"
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `bash tools/hooks/test/run-tests.sh`
Expected: FAIL — `km-pending-review.sh` 不存在

- [ ] **Step 3: 實作 SessionStart 腳本**

```bash
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
```

- [ ] **Step 4: 跑測試確認通過**

Run: `bash tools/hooks/test/run-tests.sh`
Expected: 全綠

- [ ] **Step 5: 版控接線 SessionStart hook**

建 `.claude/settings.json`：

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$CLAUDE_PROJECT_DIR/tools/hooks/km-pending-review.sh\""
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 6: Commit**

```bash
chmod +x tools/hooks/km-pending-review.sh
git add tools/hooks/km-pending-review.sh tools/hooks/test/run-tests.sh .claude/settings.json
git commit -m "feat(km-review): 開場 SessionStart 待審提醒 hook + 版控接線"
```

---

## Task 11: Dogfood — 用驗證器清真實 backlog

**Files:** 無新增；驗證整條鏈在真實候選上動作。

- [ ] **Step 1: 對三個真實候選跑驗證器**

Run:
```bash
for c in 01_Inbox/_candidates/2026-06-0*.md; do
  echo "=== $c ==="; python3 tools/km_review/validate_candidate.py "$c" --vault .
done
```
Expected: 6/01、6/02、6/03 三個候選**結構皆通過（✅）**（goal=knowledge-os 已可解析）。若有 ❌，依審查單修候選後重跑。

- [ ] **Step 2: 跑全套測試做最終把關**

Run:
```bash
python3 tools/km_review/test_validate_candidate.py && bash tools/hooks/test/run-tests.sh
```
Expected: 兩套都全綠。

- [ ] **Step 3:（人工，非自動）實際跑 `/km-review` 清 backlog**

在 Claude Code 對話打 `/km-review`，逐一審 6/01、6/02、6/03：確認每個都先顯示白話審查單、再要你按 Y、promote 進 `03_Projects/knowledge-os/goal.md` 的 Stage Log 與 `02_Notes/lessons.md`。此步驟產出由人工核准，不在自動化測試內。

---

## Self-Review（已執行）

- **Spec 覆蓋**：A 驗證器→Task 1–6；B 接線→Task 8；C 目標卡+slug→Task 7；D 雙保險→Task 9（收尾）+Task 10（開場）；範圍切割（結構 only）→各規則皆結構性，無語意判斷。✅
- **Placeholder 掃描**：無 TBD/TODO；每個 code step 附完整程式碼。✅
- **型別一致**：`Finding(rule_id, level, location, raw)` 全程一致；`validate(path, vault_root)`、`render_report(findings, path)`、`RULE_MESSAGES` 鍵與 Task 6 測試斷言一致；rule_id 命名（`ERR_PROGRESS_HEADER` 等）跨 Task 一致。✅
- **已知次序依賴**：Task 6 Step 5 煙霧測試會報 goal 未解析，Task 7 建目標卡後消除——已在 Task 6/7 標注，非缺陷。✅
```
