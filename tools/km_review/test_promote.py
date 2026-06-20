import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from promote import promote_candidate, _append_block  # noqa: E402
from sensitive import load_hard_block  # noqa: E402

REAL_CONTRACT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data-contract.yaml")
)
RULES = load_hard_block(REAL_CONTRACT)
CFN = "2026-06-20--knowledge-os--abc12345.md"


def make_vault(d):
    for sub in ("01_Inbox/_candidates", "02_Notes", "04_MOCs",
                "03_Projects/knowledge-os"):
        os.makedirs(os.path.join(d, *sub.split("/")), exist_ok=True)
    with open(os.path.join(d, "03_Projects", "knowledge-os", "goal.md"), "w") as f:
        f.write("---\nuid: 01KKMOSSELFGOAL0001\nkind: dev_goal\n"
                "project: knowledge-os\n---\n# Goal\n## Stage Log\n")
    with open(os.path.join(d, "02_Notes", "lessons.md"), "w") as f:
        f.write("# Lessons\n")
    with open(os.path.join(d, "04_MOCs", "playbook.md"), "w") as f:
        f.write("# Playbook\n")


def candidate(body_did):
    return (
        "---\nuid: 2026-06-20--knowledge-os--abc12345\ndate: 2026-06-20\n"
        "project: knowledge-os\nkind: dev_log\nstatus: draft\n---\n\n"
        "> [!progress] stage=Build date=2026-06-20 "
        "goal=01KKMOSSELFGOAL0001 seq=01\n"
        f"> did: {body_did}\n> result: y\n> next: z\n"
    )


class ScanQuarantineTest(unittest.TestCase):
    def test_secret_candidate_quarantined_before_sot(self):
        with tempfile.TemporaryDirectory() as d:
            make_vault(d)
            cpath = os.path.join(d, "01_Inbox", "_candidates", CFN)
            with open(cpath, "w") as f:
                f.write(candidate("設定 AKIAIOSFODNN7EXAMPLE 完成"))
            status, detail = promote_candidate(d, cpath, scan_rules=RULES)
            self.assertEqual(status, "quarantined")
            self.assertIn("敏感掃描", detail)
            self.assertIn("aws_access_key", detail)
            # SoT 未被污染
            with open(os.path.join(d, "02_Notes", "lessons.md")) as f:
                self.assertNotIn("AKIA", f.read())
            # 候選被移到 _quarantine
            self.assertFalse(os.path.exists(cpath))
            qpath = os.path.join(d, "01_Inbox", "_candidates", "_quarantine", CFN)
            self.assertTrue(os.path.exists(qpath))

    def test_clean_candidate_promotes(self):
        with tempfile.TemporaryDirectory() as d:
            make_vault(d)
            cpath = os.path.join(d, "01_Inbox", "_candidates", CFN)
            with open(cpath, "w") as f:
                f.write(candidate("完成安全審核決策"))
            status, _ = promote_candidate(d, cpath, dry_run=True, scan_rules=RULES)
            self.assertEqual(status, "promoted")


class LedgerAppendTest(unittest.TestCase):
    def test_append_to_missing_file_creates_it(self):
        # 修復 FileNotFoundError：ledger 不存在時應自動建立
        with tempfile.TemporaryDirectory() as d:
            ledger = os.path.join(d, "_auto-promote-log.md")
            _append_block(ledger, "- first line", blank_before=False)
            with open(ledger) as f:
                self.assertEqual(f.read().strip(), "- first line")


if __name__ == "__main__":
    unittest.main()
