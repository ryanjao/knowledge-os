"""knowledge-os 候選草稿結構驗證器。

只驗「結構」（欄位齊不齊、格式對不對），不碰語意（內容看不看得懂留給人）。
吐 rule_id；白話文案見本檔 RULE_MESSAGES，由 /km-review 渲染成審查單。
"""
import os
import re
from collections import namedtuple

Finding = namedtuple("Finding", ["rule_id", "level", "location", "raw"])

FILENAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}--[a-z0-9-]+--[0-9a-f]{6,}\.md$")

CALLOUT_START_RE = re.compile(r"^>\s*\[!(progress|lesson)\]\s*(.*)$")
HEADER_KV_RE = re.compile(r"(\w+)=")
BODY_KEY_RE = re.compile(r"^>\s*(\w+)\s*:")

REQUIRED = {
    "progress": {"header": ["stage", "date", "goal", "seq"],
                 "body": ["did", "result", "next"]},
    "lesson": {"header": ["skill", "stage", "error"],
               "body": ["what", "fix", "rule"]},
}


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
    counters = {"progress": 0, "lesson": 0}
    for kind, header, body, _start in blocks:
        counters[kind] += 1
        findings += _check_callout_fields(kind, header, body, counters[kind])
    return findings
