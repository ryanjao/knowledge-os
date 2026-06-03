import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_candidate import validate, Finding  # noqa: E402
from validate_candidate import render_report, RULE_MESSAGES  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
