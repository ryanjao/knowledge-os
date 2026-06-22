#!/usr/bin/env python3
"""knowledge-os 候選自動促進器（auto-promote / 自動 km-review）。

驗證通過的候選草稿 → 自動併入 SoT，無需人工逐筆核准。
促進邏輯確定性化（不再由模型臨場判斷），對應 CLAUDE.md §5 的安全網：

  ① 結構驗證（validate_candidate）為硬閘：不過 → 隔離到 _quarantine/，不併入。
  ② progress 併入 goal card 時標 `verified=no`（goal card 是唯一 mirror:true，
     需 km-sync 配合略過 verified=no，錯誤就不外溢到 Notion）。
     lessons.md / playbook.md 皆 mirror:false，不同步，無需標記。
  ③ 每次促進寫入 ledger（01_Inbox/_auto-promote-log.md）供月檢批次掃。
  ④ --verify-all：月檢時批次清除 verified=no（= 已人工掃過，放行同步）。

用法：
  python3 promote.py --vault <vault>             # 促進所有待審候選
  python3 promote.py --vault <vault> --dry-run   # 只報告不寫入
  python3 promote.py --vault <vault> --verify-all # 月檢：清除 verified=no 標記
"""
import argparse
import datetime
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_candidate import validate, _parse_callouts  # noqa: E402
import sensitive  # noqa: E402

VAULT_DEFAULT = "/Users/juiyujao/Projects/knowledge-os"

HEADER_KV_RE = re.compile(r"(\w+)=(\S+)")
GOAL_RE = re.compile(r"goal=(\S+)")
UID_RE = re.compile(r"^uid:\s*(\S+)", re.M)
KIND_DEVGOAL_RE = re.compile(r"^kind:\s*dev_goal\s*$", re.M)
BODY_KEY_RE = re.compile(r"^>\s*(\w+)\s*:\s*(.*)$")
STAGE_LOG_RE = re.compile(r"^##\s+Stage Log\s*$", re.M)

# 安全網開關：預設「自動放行」（不標 verified=no，促進後即可由 km-sync 同步到 Notion）。
# 設環境變數 KM_HOLD=1 可一鍵切回「人工放行」模式（標 verified=no，需 --verify-all 才放行）。
HOLD = os.environ.get("KM_HOLD", "").strip().lower() not in ("", "0", "false", "no")


def _today():
    return datetime.date.today().isoformat()


def _candidates(vault):
    cdir = os.path.join(vault, "01_Inbox", "_candidates")
    if not os.path.isdir(cdir):
        return cdir, []
    files = sorted(
        os.path.join(cdir, f) for f in os.listdir(cdir)
        if f.endswith(".md") and f != ".gitkeep"
    )
    return cdir, files


def _resolve_goal_card(vault, goal):
    """goal（uid 或 slug）→ dev_goal 卡路徑；對不到回 None。uid 優先。"""
    proj = os.path.join(vault, "03_Projects")
    if not os.path.isdir(proj) or not goal:
        return None
    slug_hit = None
    for slug in sorted(os.listdir(proj)):
        sdir = os.path.join(proj, slug)
        if not os.path.isdir(sdir):
            continue
        for fn in sorted(os.listdir(sdir)):
            if not fn.endswith(".md"):
                continue
            p = os.path.join(sdir, fn)
            with open(p, encoding="utf-8") as fh:
                head = fh.read(2000)
            if not KIND_DEVGOAL_RE.search(head):
                continue
            m = UID_RE.search(head)
            if m and m.group(1) == goal:
                return p
            if slug == goal and slug_hit is None:
                slug_hit = p
    return slug_hit


def _callout_text(kind, header, body_lines):
    return "\n".join([f"> [!{kind}] {header}".rstrip()] + body_lines)


def _append_block(path, block, blank_before):
    """append-only：在檔尾接上 block，控制是否空一行分隔。
    檔案不存在時視為空檔自動建立（避免 ledger 等首次寫入 FileNotFoundError）。"""
    text = ""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            text = f.read()
    if text.strip():
        sep = "\n\n" if blank_before else "\n"
        text = text.rstrip("\n") + sep + block.rstrip("\n") + "\n"
    else:
        text = block.rstrip("\n") + "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _append_progress(card_path, callout):
    """把 progress callout 追加到 goal card 的 ## Stage Log 區段末尾。
    無 Stage Log → 自動建區塊 + marker（對應 lesson goal-card-missing-stagelog）。"""
    with open(card_path, encoding="utf-8") as f:
        text = f.read()
    block = callout.rstrip() + "\n"
    m = STAGE_LOG_RE.search(text)
    if not m:
        text = (text.rstrip("\n")
                + "\n\n## Stage Log\n<!-- auto-promote append -->\n\n" + block)
    else:
        start = m.end()
        nxt = re.search(r"^##\s", text[start:], re.M)
        if nxt:
            at = start + nxt.start()
            text = text[:at].rstrip("\n") + "\n\n" + block + "\n" + text[at:]
        else:
            text = text.rstrip("\n") + "\n\n" + block
    with open(card_path, "w", encoding="utf-8") as f:
        f.write(text)


def _body_dict(body_lines):
    d = {}
    for ln in body_lines:
        bm = BODY_KEY_RE.match(ln)
        if bm:
            d[bm.group(1)] = bm.group(2).strip()
    return d


def _quarantine(vault, path):
    qdir = os.path.join(vault, "01_Inbox", "_candidates", "_quarantine")
    os.makedirs(qdir, exist_ok=True)
    shutil.move(path, os.path.join(qdir, os.path.basename(path)))


def _load_scan_rules(vault):
    """從 vault 根目錄 data-contract.yaml 載入 hard_block 敏感掃描規則。
    載入失敗會 raise sensitive.SensitiveContractError（大聲失敗，由 caller 接）。"""
    return sensitive.load_hard_block(os.path.join(vault, "data-contract.yaml"))


def promote_candidate(vault, path, dry_run=False, scan_rules=None):
    """回傳 (status, detail)。status ∈ {promoted, quarantined, skipped}。
    原子性：任一 progress 對不到目標卡、或命中敏感掃描 → 整份隔離，不做部分寫入。"""
    if not os.path.exists(path):
        return "skipped", "檔案已不存在（可能已被前次 run 處理）"
    findings = validate(path, vault_root=vault)
    if any(f.level == "block" for f in findings):
        if not dry_run:
            _quarantine(vault, path)
        return "quarantined", f"結構驗證攔截（{len(findings)} 項）"

    with open(path, encoding="utf-8") as f:
        raw = f.read()

    # 敏感掃描：寫入 SoT 前的 fail-fast（命中即隔離，只報規則 ID，不輸出內容）。
    if scan_rules is None:
        scan_rules = _load_scan_rules(vault)
    hits = sensitive.scan(raw, *scan_rules)
    if hits:
        if not dry_run:
            _quarantine(vault, path)
        return "quarantined", "敏感掃描攔截：" + ", ".join(hits)

    blocks = _parse_callouts(raw)

    # 先解析 + 預解析所有 progress 目標卡（原子性：先確認全部可落地）
    prog_date = _today()
    progress_jobs, lesson_jobs = [], []
    for kind, header, body, _ in blocks:
        if kind == "progress":
            hd = dict(HEADER_KV_RE.findall(header))
            prog_date = hd.get("date", prog_date)
            card = _resolve_goal_card(vault, hd.get("goal"))
            if not card:
                if not dry_run:
                    _quarantine(vault, path)
                return "quarantined", f"goal 對不到目標卡：{hd.get('goal')}"
            if HOLD and "verified=" not in header:
                hdr = header.rstrip() + " verified=no"
            else:
                hdr = header
            progress_jobs.append((card, _callout_text("progress", hdr, body)))
        elif kind == "lesson":
            lesson_jobs.append((header, body))

    if dry_run:
        return "promoted", f"progress×{len(progress_jobs)} lesson×{len(lesson_jobs)}（dry-run）"

    # 寫入：progress → goal card（verified=no）；lesson → lessons.md + playbook 索引
    for card, callout in progress_jobs:
        _append_progress(card, callout)
    lessons_md = os.path.join(vault, "02_Notes", "lessons.md")
    playbook_md = os.path.join(vault, "04_MOCs", "playbook.md")
    for header, body in lesson_jobs:
        _append_block(lessons_md, _callout_text("lesson", header, body), blank_before=True)
        hd = dict(HEADER_KV_RE.findall(header))
        bd = _body_dict(body)
        idx = (f"- {prog_date} — stage={hd.get('stage', '')} "
               f"skill={hd.get('skill', '')} error={hd.get('error', '')} "
               f"— {bd.get('rule', '')}")
        _append_block(playbook_md, idx, blank_before=False)

    os.remove(path)
    return "promoted", f"progress×{len(progress_jobs)} lesson×{len(lesson_jobs)}"


def verify_all(vault, dry_run=False):
    """月檢：批次清除 goal card 內所有 verified=no 標記（= 已人工掃過，放行 Notion 同步）。"""
    proj = os.path.join(vault, "03_Projects")
    cleared = 0
    if not os.path.isdir(proj):
        return 0
    for slug in sorted(os.listdir(proj)):
        sdir = os.path.join(proj, slug)
        if not os.path.isdir(sdir):
            continue
        for fn in sorted(os.listdir(sdir)):
            if not fn.endswith(".md"):
                continue
            p = os.path.join(sdir, fn)
            with open(p, encoding="utf-8") as f:
                text = f.read()
            hits = text.count(" verified=no")
            if hits:
                cleared += hits
                if not dry_run:
                    with open(p, "w", encoding="utf-8") as f:
                        f.write(text.replace(" verified=no", ""))
    return cleared


def main(argv=None):
    ap = argparse.ArgumentParser(description="knowledge-os 候選自動促進器")
    ap.add_argument("--vault", default=VAULT_DEFAULT)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify-all", action="store_true")
    args = ap.parse_args(argv)

    if args.verify_all:
        n = verify_all(args.vault, args.dry_run)
        print(f"✅ km auto-promote：已清除 {n} 個 verified=no（月檢驗證，放行 Notion 同步）。")
        return 0

    _, files = _candidates(args.vault)
    if not files:
        return 0  # 無候選 → 靜默 no-op（hook 不輸出）

    # 敏感掃描規則：載入一次。失敗即 fail-closed（不促進任何候選），大聲報錯不靜默。
    try:
        scan_rules = _load_scan_rules(args.vault)
    except sensitive.SensitiveContractError as e:
        print(f"⛔ km auto-promote 中止：敏感掃描規則載入失敗，未促進任何候選。原因：{e}")
        return 1

    promoted = quarantined = 0
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    ledger_lines = []
    for path in files:
        status, detail = promote_candidate(args.vault, path, args.dry_run, scan_rules)
        if status == "skipped":
            continue
        promoted += status == "promoted"
        quarantined += status == "quarantined"
        ledger_lines.append(f"- {stamp} {os.path.basename(path)} → {status}（{detail}）")

    if not args.dry_run:
        ledger = os.path.join(args.vault, "01_Inbox", "_auto-promote-log.md")
        _append_block(ledger, "\n".join(ledger_lines), blank_before=False)

    msg = f"🤖 km auto-promote：併入 {promoted} 筆"
    if quarantined:
        msg += f"、隔離 {quarantined} 筆（見 _candidates/_quarantine/）"
    if HOLD:
        msg += "。progress 標 verified=no（暫不同步，--verify-all 後放行）。"
    else:
        msg += "（自動放行，待 km-sync 同步）。"
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
