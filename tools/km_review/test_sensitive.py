import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sensitive import (  # noqa: E402
    load_hard_block,
    scan,
    SensitiveContractError,
)

REAL_CONTRACT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data-contract.yaml")
)


def write_contract(dirpath, text):
    path = os.path.join(dirpath, "data-contract.yaml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


MINIMAL = """\
version: "x"
sensitive_scan:
  token_whitelist: '\\{\\{SECRET_[A-Z0-9_]+\\}\\}'
  policy:
    hard_block: "命中即整批失敗"
    soft_warn: "命中則 mirror:false"
  hard_block:
    - id: "aws_access_key"
      pattern: 'AKIA[0-9A-Z]{16}'
    - id: "quoted_pattern"
      pattern: '(?i)\\b(secret)\\b\\s*[:=]\\s*[''"]?[^''"\\s]{6,}[''"]?'
  soft_warn:
    - id: "email"
      pattern: 'x@y'
validation:
  require_uid_unique: true
"""


class LoadRealContractTest(unittest.TestCase):
    def test_real_contract_loads_known_ids(self):
        whitelist, compiled = load_hard_block(REAL_CONTRACT)
        ids = [rid for rid, _ in compiled]
        for expect in ("pem_private_key", "jwt", "aws_access_key",
                       "github_token", "private_ipv4",
                       "plaintext_password_assign"):
            self.assertIn(expect, ids)
        self.assertIsNotNone(whitelist)

    def test_real_contract_excludes_policy_and_softwarn(self):
        # policy.hard_block 是字串值、soft_warn 是另一清單，都不可混入 hard_block 規則
        _, compiled = load_hard_block(REAL_CONTRACT)
        ids = [rid for rid, _ in compiled]
        self.assertNotIn("email", ids)
        self.assertNotIn("tw_phone", ids)


class MinimalParseTest(unittest.TestCase):
    def test_minimal_parses_two_hard_block_rules(self):
        with tempfile.TemporaryDirectory() as d:
            p = write_contract(d, MINIMAL)
            _, compiled = load_hard_block(p)
            ids = [rid for rid, _ in compiled]
            self.assertEqual(ids, ["aws_access_key", "quoted_pattern"])

    def test_single_quote_escape_unwrapped(self):
        # YAML 單引號 '' → ' ；確認 [''"] 被正確還原為 ['"]
        with tempfile.TemporaryDirectory() as d:
            p = write_contract(d, MINIMAL)
            whitelist, compiled = load_hard_block(p)
            hits = scan('secret: "hunter2pass"', whitelist, compiled)
            self.assertIn("quoted_pattern", hits)


class FailLoudTest(unittest.TestCase):
    def test_missing_file_raises(self):
        with self.assertRaises(SensitiveContractError):
            load_hard_block("/nonexistent/data-contract.yaml")

    def test_missing_sensitive_scan_raises(self):
        with tempfile.TemporaryDirectory() as d:
            p = write_contract(d, "version: x\nvalidation:\n  a: b\n")
            with self.assertRaises(SensitiveContractError):
                load_hard_block(p)

    def test_missing_hard_block_list_raises(self):
        body = "sensitive_scan:\n  token_whitelist: 'x'\n  soft_warn:\n    - id: \"e\"\n      pattern: 'y'\n"
        with tempfile.TemporaryDirectory() as d:
            p = write_contract(d, body)
            with self.assertRaises(SensitiveContractError):
                load_hard_block(p)


class ScanTest(unittest.TestCase):
    def setUp(self):
        self.whitelist, self.compiled = load_hard_block(REAL_CONTRACT)

    def test_detects_aws_key(self):
        hits = scan("config AKIAIOSFODNN7EXAMPLE here", self.whitelist, self.compiled)
        self.assertIn("aws_access_key", hits)

    def test_detects_private_ip(self):
        hits = scan("proxy at 192.168.1.50 internal", self.whitelist, self.compiled)
        self.assertIn("private_ipv4", hits)

    def test_detects_github_token(self):
        tok = "ghp_" + "a" * 36
        hits = scan(f"token={tok}", self.whitelist, self.compiled)
        self.assertIn("github_token", hits)

    def test_secret_placeholder_not_flagged(self):
        # {{SECRET_XXX}} 是合法引用，不該觸發
        hits = scan("api key is {{SECRET_NTPC_PROXY_IP}}", self.whitelist, self.compiled)
        self.assertEqual(hits, [])

    def test_clean_text_no_hits(self):
        clean = (
            "> [!progress] stage=Build date=2026-06-20 goal=x seq=01\n"
            "> did: 完成安全審核\n> result: 決策已定\n> next: 實作\n"
        )
        self.assertEqual(scan(clean, self.whitelist, self.compiled), [])

    def test_hits_are_deduped(self):
        text = "AKIAIOSFODNN7EXAMPLE and AKIAIOSFODNN7EXAMPL2"
        hits = scan(text, self.whitelist, self.compiled)
        self.assertEqual(hits.count("aws_access_key"), 1)


if __name__ == "__main__":
    unittest.main()
