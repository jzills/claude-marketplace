"""Tests for locating .claudeignore files and assembling the active ruleset."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks"))

from claudeignore_discovery import find_project_ignore, load_ruleset  # noqa: E402


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as handle:
        handle.write(text)


class TestFindProjectIgnore(unittest.TestCase):
    def test_finds_the_file_in_the_current_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = os.path.realpath(tmp)
            write(os.path.join(tmp, ".claudeignore"), ".env\n")
            self.assertEqual(find_project_ignore(tmp), os.path.join(tmp, ".claudeignore"))

    def test_walks_up_from_a_subdirectory(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = os.path.realpath(tmp)
            write(os.path.join(tmp, ".claudeignore"), ".env\n")
            os.makedirs(os.path.join(tmp, "a", "b"))
            self.assertEqual(
                find_project_ignore(os.path.join(tmp, "a", "b")),
                os.path.join(tmp, ".claudeignore"),
            )

    def test_stops_at_the_git_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = os.path.realpath(tmp)
            write(os.path.join(tmp, ".claudeignore"), ".env\n")
            os.makedirs(os.path.join(tmp, "repo", ".git"))
            self.assertIsNone(find_project_ignore(os.path.join(tmp, "repo")))

    def test_nearest_file_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = os.path.realpath(tmp)
            write(os.path.join(tmp, ".claudeignore"), "outer\n")
            write(os.path.join(tmp, "inner", ".claudeignore"), "inner\n")
            self.assertEqual(
                find_project_ignore(os.path.join(tmp, "inner")),
                os.path.join(tmp, "inner", ".claudeignore"),
            )

    def test_returns_none_when_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(find_project_ignore(os.path.realpath(tmp)))


class TestRuleset(unittest.TestCase):
    def test_empty_when_no_ignore_file_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            rules = load_ruleset(os.path.realpath(tmp), global_path=None)
            self.assertFalse(rules)

    def test_project_patterns_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = os.path.realpath(tmp)
            write(os.path.join(tmp, ".claudeignore"), ".env\nsecrets/**\n")
            rules = load_ruleset(tmp, global_path=None)
            self.assertTrue(rules)
            self.assertTrue(rules.is_ignored(os.path.join(tmp, ".env")))
            self.assertFalse(rules.is_ignored(os.path.join(tmp, "README.md")))

    def test_reports_the_pattern_and_its_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = os.path.realpath(tmp)
            write(os.path.join(tmp, ".claudeignore"), "secrets/**\n")
            rules = load_ruleset(tmp, global_path=None)
            pattern, source = rules.explain(os.path.join(tmp, "secrets/api.key"))
            self.assertEqual(pattern, "secrets/**")
            self.assertEqual(source, os.path.join(tmp, ".claudeignore"))

    def test_a_directory_pattern_blocks_the_directory_itself(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = os.path.realpath(tmp)
            write(os.path.join(tmp, ".claudeignore"), "secrets/\n")
            os.makedirs(os.path.join(tmp, "secrets"))
            rules = load_ruleset(tmp, global_path=None)
            self.assertTrue(rules.is_ignored(os.path.join(tmp, "secrets"), is_dir=True))
            self.assertEqual(
                rules.explain(os.path.join(tmp, "secrets"), is_dir=True)[0], "secrets/"
            )

    def test_global_patterns_apply_outside_the_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = os.path.realpath(tmp)
            global_file = os.path.join(tmp, "global-ignore")
            write(global_file, "*.pem\n")
            rules = load_ruleset(os.path.join(tmp, "proj"), global_path=global_file)
            self.assertTrue(rules.is_ignored("/anywhere/at/all/server.pem"))

    def test_literals_exclude_wildcard_patterns(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = os.path.realpath(tmp)
            write(os.path.join(tmp, ".claudeignore"), ".env\n*.pem\nsecrets/\n!keep\n")
            rules = load_ruleset(tmp, global_path=None)
            literals = rules.literals()
            self.assertIn(".env", literals)
            self.assertIn("secrets", literals)
            self.assertNotIn("*.pem", literals)
            self.assertNotIn("keep", literals)

    def test_patterns_lists_every_active_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = os.path.realpath(tmp)
            write(os.path.join(tmp, ".claudeignore"), "# comment\n\n.env\n*.pem\n")
            rules = load_ruleset(tmp, global_path=None)
            self.assertEqual(rules.patterns(), [".env", "*.pem"])


class TestConfig(unittest.TestCase):
    def test_defaults_fill_in_missing_keys(self):
        from claudeignore_config import DEFAULTS, merge_defaults

        merged = merge_defaults({"bash_inspection": False})
        self.assertFalse(merged["bash_inspection"])
        self.assertEqual(merged["on_error"], DEFAULTS["on_error"])

    def test_unknown_keys_are_preserved(self):
        from claudeignore_config import merge_defaults

        self.assertEqual(merge_defaults({"future": 1})["future"], 1)


if __name__ == "__main__":
    unittest.main()
