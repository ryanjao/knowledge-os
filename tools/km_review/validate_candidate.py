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
                if CALLOUT_START_RE.match(lines[j]):
                    break
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
            # goal_ids 為空（vault 無任何 dev_goal 卡）時刻意跳過 goal 檢查，
            # 避免在未填充的 vault 上誤報；vault 有卡時才把對不到的 goal 當 block。
            if gm and goal_ids and gm.group(1) not in goal_ids:
                findings.append(Finding(
                    "ERR_GOAL_UNRESOLVED", "block",
                    f"[!progress] #{counters['progress']}", gm.group(1)))
    return findings


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
