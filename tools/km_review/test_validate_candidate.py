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


if __name__ == "__main__":
    unittest.main()
