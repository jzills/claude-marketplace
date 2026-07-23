"""Tests for pulling candidate paths out of a tool_input payload."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks"))

from claudeignore_paths import (  # noqa: E402
    bash_tokens,
    extract_paths,
    literal_hits,
    resolve_variants,
)


class TestFileTools(unittest.TestCase):
    def test_read_uses_file_path(self):
        self.assertEqual(
            extract_paths("Read", {"file_path": "/proj/.env"}, "/proj"),
            ["/proj/.env"],
        )

    def test_relative_file_path_resolves_against_cwd(self):
        self.assertEqual(
            extract_paths("Read", {"file_path": ".env"}, "/proj"),
            ["/proj/.env"],
        )

    def test_write_and_edit_use_file_path(self):
        for tool in ("Write", "Edit", "MultiEdit"):
            self.assertEqual(
                extract_paths(tool, {"file_path": "/proj/secrets/k"}, "/proj"),
                ["/proj/secrets/k"],
                tool,
            )

    def test_notebook_edit_uses_notebook_path(self):
        self.assertEqual(
            extract_paths("NotebookEdit", {"notebook_path": "/proj/nb.ipynb"}, "/proj"),
            ["/proj/nb.ipynb"],
        )

    def test_glob_and_grep_use_the_search_root(self):
        self.assertEqual(
            extract_paths("Glob", {"pattern": "**/*.ts", "path": "/proj/src"}, "/proj"),
            ["/proj/src"],
        )
        self.assertEqual(
            extract_paths("Grep", {"pattern": "token", "path": "secrets"}, "/proj"),
            ["/proj/secrets"],
        )

    def test_search_pattern_is_not_treated_as_a_path(self):
        paths = extract_paths("Grep", {"pattern": "secrets/api.key"}, "/proj")
        self.assertEqual(paths, [])

    def test_missing_fields_yield_nothing(self):
        self.assertEqual(extract_paths("Read", {}, "/proj"), [])


class TestUnknownAndMcpTools(unittest.TestCase):
    def test_mcp_tool_string_values_are_scanned(self):
        paths = extract_paths(
            "mcp__filesystem__read_file", {"path": "/proj/secrets/api.key"}, "/proj"
        )
        self.assertIn("/proj/secrets/api.key", paths)

    def test_nested_string_values_are_scanned(self):
        paths = extract_paths(
            "mcp__x__y", {"args": {"targets": ["/proj/.env"]}}, "/proj"
        )
        self.assertIn("/proj/.env", paths)

    def test_prose_without_a_separator_is_ignored(self):
        paths = extract_paths("mcp__x__y", {"note": "hello world"}, "/proj")
        self.assertEqual(paths, [])


class TestBashTokens(unittest.TestCase):
    def test_dotfile_argument_is_a_candidate(self):
        self.assertIn("/proj/.env", bash_tokens("cat .env", "/proj"))

    def test_path_with_separator_is_a_candidate(self):
        self.assertIn("/proj/secrets/api.key", bash_tokens("cat secrets/api.key", "/proj"))

    def test_flags_are_not_candidates(self):
        tokens = bash_tokens("grep -rn --color=never pattern .env", "/proj")
        self.assertIn("/proj/.env", tokens)
        self.assertNotIn("/proj/-rn", tokens)

    def test_env_assignment_value_is_a_candidate(self):
        self.assertIn("/proj/.env", bash_tokens("FOO=.env printenv", "/proj"))

    def test_quoted_path_is_a_candidate(self):
        self.assertIn("/proj/my secrets/k", bash_tokens('cat "my secrets/k"', "/proj"))

    def test_tilde_expands_to_home(self):
        expected = os.path.join(os.path.expanduser("~"), ".ssh/id_rsa")
        self.assertIn(expected, bash_tokens("cat ~/.ssh/id_rsa", "/proj"))

    def test_absolute_path_is_kept_absolute(self):
        self.assertIn("/etc/shadow", bash_tokens("cat /etc/shadow", "/proj"))

    def test_unbalanced_quotes_still_yield_tokens(self):
        self.assertIn("/proj/.env", bash_tokens("cat .env 'unclosed", "/proj"))

    def test_bare_word_that_is_not_on_disk_is_not_a_candidate(self):
        """`npm run build` must not be read as touching a file named build."""
        tokens = bash_tokens("npm run build", "/proj-does-not-exist")
        self.assertNotIn("/proj-does-not-exist/build", tokens)

    def test_bare_word_that_exists_on_disk_is_a_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            open(os.path.join(tmp, "id_rsa"), "w").close()
            self.assertIn(os.path.join(tmp, "id_rsa"), bash_tokens("cat id_rsa", tmp))

    def test_chained_commands_are_all_scanned(self):
        tokens = bash_tokens("ls && cat secrets/api.key", "/proj")
        self.assertIn("/proj/secrets/api.key", tokens)

    def test_command_substitution_contents_are_scanned(self):
        tokens = bash_tokens("echo $(cat secrets/api.key)", "/proj")
        self.assertIn("/proj/secrets/api.key", tokens)


class TestLiteralHits(unittest.TestCase):
    def test_literal_pattern_found_as_a_path_segment(self):
        self.assertEqual(literal_hits("cat ./.env", [".env"]), [".env"])

    def test_literal_pattern_not_found(self):
        self.assertEqual(literal_hits("npm run dev", [".env"]), [])

    def test_partial_word_is_not_a_hit(self):
        self.assertEqual(literal_hits("echo environment", ["env"]), [])


class TestSymlinkVariants(unittest.TestCase):
    def test_symlink_target_is_included(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "real.env")
            link = os.path.join(tmp, "link.env")
            open(target, "w").close()
            os.symlink(target, link)
            self.assertIn(target, resolve_variants(link))
            self.assertIn(link, resolve_variants(link))

    def test_plain_path_yields_itself_once(self):
        self.assertEqual(resolve_variants("/proj/README.md"), ["/proj/README.md"])


if __name__ == "__main__":
    unittest.main()
