#!/usr/bin/env python3
"""敏感掃描：寫入 SoT 前的 fail-fast 防線。

規則的單一真實來源 = 根目錄 data-contract.yaml §6 `sensitive_scan.hard_block`。
本模組用極小的行式提取器讀出 pattern（stdlib-only，配合 knowledge-os 零 pip 依賴），
不引入 PyYAML。

設計鐵則（對應 CLAUDE.md §0.9 不可簡化區「可觀測性：靜默失敗＝禁止」）：
  載入失敗一律 raise SensitiveContractError，**不可**靜默回傳空規則——
  空規則 = 掃描器形同關閉 = false security。

  # ponytail: 只解析 hard_block（單行 scalar 結構固定），不做通用 YAML parser
  # upgrade when: data-contract.yaml 改用多行 scalar / 巢狀 anchor，或需解析 soft_warn
"""
import re

__all__ = ["load_hard_block", "scan", "SensitiveContractError"]


class SensitiveContractError(Exception):
    """data-contract.yaml 的 sensitive_scan 區塊找不到或無法解析。"""


def _unquote(s):
    """還原 YAML scalar，並忽略閉合引號後的行內註解。

    單引號：'' → ' ；雙引號：\\" → " 、\\\\ → \\ ；
    plain scalar：去掉「空白 + #」之後的註解。
    """
    s = s.strip()
    if not s:
        return s
    q = s[0]
    if q == "'":
        out, i, n = [], 1, len(s)
        while i < n:
            c = s[i]
            if c == "'":
                if i + 1 < n and s[i + 1] == "'":  # '' → 字面單引號
                    out.append("'")
                    i += 2
                    continue
                break  # 閉合引號，其後（含註解）一律忽略
            out.append(c)
            i += 1
        return "".join(out)
    if q == '"':
        out, i, n = [], 1, len(s)
        while i < n:
            c = s[i]
            if c == "\\" and i + 1 < n:
                nxt = s[i + 1]
                out.append('"' if nxt == '"' else ("\\" if nxt == "\\" else nxt))
                i += 2
                continue
            if c == '"':
                break
            out.append(c)
            i += 1
        return "".join(out)
    # plain scalar：去掉行內註解（# 前需有空白）
    return re.match(r"^(.*?)(?:\s+#.*)?$", s).group(1).strip()


def _indent(line):
    return len(line) - len(line.lstrip(" "))


def load_hard_block(contract_path):
    """讀 data-contract.yaml，回傳 (whitelist_pattern_or_None, [(id, compiled_regex), ...])。

    找不到檔案 / 缺 sensitive_scan / 缺 hard_block 清單 / 零規則 → raise。
    pattern 編譯失敗（re.error）也會往外丟，皆為大聲失敗。
    """
    try:
        with open(contract_path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except FileNotFoundError as e:
        raise SensitiveContractError(f"找不到資料契約：{contract_path}") from e

    # 1) 定位 sensitive_scan: 區塊（top-level key，0 縮排），界定其行範圍
    sec_start = None
    for i, ln in enumerate(lines):
        if re.match(r"^sensitive_scan:\s*$", ln):
            sec_start = i
            break
    if sec_start is None:
        raise SensitiveContractError("data-contract.yaml 缺 sensitive_scan 區塊")
    sec_end = len(lines)
    for j in range(sec_start + 1, len(lines)):
        ln = lines[j]
        if ln.strip() and not ln.startswith(" ") and not ln.startswith("#"):
            sec_end = j
            break
    block = lines[sec_start + 1:sec_end]

    # 2) token_whitelist（2 縮排）
    whitelist = None
    for ln in block:
        m = re.match(r"^  token_whitelist:\s*(.+)$", ln)
        if m:
            whitelist = _unquote(m.group(1))
            break

    # 3) hard_block: 清單（2 縮排、冒號後無內容；
    #    排除 policy.hard_block —— 它是 `hard_block: "..."` 字串值，冒號後有內容）
    hb_start = None
    for k, ln in enumerate(block):
        if re.match(r"^  hard_block:\s*$", ln):
            hb_start = k
            break
    if hb_start is None:
        raise SensitiveContractError("sensitive_scan 缺 hard_block 清單")

    items = []
    cur_id = None
    for ln in block[hb_start + 1:]:
        if not ln.strip():
            continue
        if _indent(ln) <= 2:   # 回到 sibling key（如 soft_warn:）→ 清單結束
            break
        mid = re.match(r"^\s*-\s*id:\s*(.+)$", ln)
        mpat = re.match(r"^\s*pattern:\s*(.+)$", ln)
        if mid:
            cur_id = _unquote(mid.group(1))
        elif mpat and cur_id:
            items.append((cur_id, _unquote(mpat.group(1))))
            cur_id = None

    if not items:
        raise SensitiveContractError("hard_block 清單為空或無法解析")
    compiled = [(rid, re.compile(pat)) for rid, pat in items]
    return whitelist, compiled


def scan(text, whitelist, compiled):
    """回傳命中的規則 id（去重保序）。先移除 {{SECRET_XXX}} 佔位符避免誤判。

    回傳「規則 id」而非命中內容——對應契約「報告只記檔案與規則 ID，不輸出內容」。
    """
    if whitelist:
        text = re.sub(whitelist, "", text)
    out, seen = [], set()
    for rid, rx in compiled:
        if rid not in seen and rx.search(text):
            seen.add(rid)
            out.append(rid)
    return out
