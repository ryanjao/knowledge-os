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
