"""knowledge-os 候選草稿結構驗證器。

只驗「結構」（欄位齊不齊、格式對不對），不碰語意（內容看不看得懂留給人）。
吐 rule_id；白話文案見本檔 RULE_MESSAGES，由 /km-review 渲染成審查單。
"""
import os
import re
from collections import namedtuple

Finding = namedtuple("Finding", ["rule_id", "level", "location", "raw"])

FILENAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}--[a-z0-9-]+--[0-9a-f]{6,}\.md$")

UID_RE = re.compile(r"^uid:\s*(\S+)", re.M)
KIND_DEVGOAL_RE = re.compile(r"^kind:\s*dev_goal\s*$", re.M)
HEADER_GOAL_RE = re.compile(r"goal=(\S+)")

CALLOUT_START_RE = re.compile(r"^>\s*\[!(progress|lesson)\]\s*(.*)$")
HEADER_KV_RE = re.compile(r"(\w+)=")
BODY_KEY_RE = re.compile(r"^>\s*(\w+)\s*:")
BROKEN_MARKER_RE = re.compile(r"^\s*\[!(progress|lesson)\]")

REQUIRED = {
    "progress": {"header": ["stage", "date", "goal", "seq"],
                 "body": ["did", "result", "next"]},
    "lesson": {"header": ["skill", "stage", "error"],
               "body": ["what", "fix", "rule"]},
}


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


def _check_filename(path):
    name = os.path.basename(path)
    if not FILENAME_RE.match(name):
        return [Finding("ERR_FILENAME", "block", "檔名", name)]
    return []


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


def validate(path, vault_root=None):
    """驗證一個候選檔，回傳 Finding 清單（空＝通過）。"""
    findings = []
    findings += _check_filename(path)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    blocks = _parse_callouts(text)
    if not blocks:
        # 有 marker 文字卻沒解析出 callout → 破框；完全沒 marker → 沒內容
        if any(BROKEN_MARKER_RE.match(ln) for ln in text.splitlines()):
            findings.append(Finding("ERR_CALLOUT_BROKEN", "block", "callout", ""))
        else:
            findings.append(Finding("ERR_NO_CALLOUT", "block", "整份檔", ""))
    goal_ids = _collect_goal_ids(vault_root)
    counters = {"progress": 0, "lesson": 0}
    for kind, header, body, _start in blocks:
        counters[kind] += 1
        findings += _check_callout_fields(kind, header, body, counters[kind])
        if kind == "progress":
            gm = HEADER_GOAL_RE.search(header)
            if gm and goal_ids and gm.group(1) not in goal_ids:
                findings.append(Finding(
                    "ERR_GOAL_UNRESOLVED", "block",
                    f"[!progress] #{counters['progress']}", gm.group(1)))
    return findings
