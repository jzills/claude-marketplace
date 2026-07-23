"""Tests for stripping ignored paths out of Grep/Glob results."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks"))

from claudeignore_filter import filter_output  # noqa: E402
from claudeignore_matcher import Matcher, compile_patterns  # noqa: E402

MATCHER = Matcher(compile_patterns([".env", "secrets/**"], "/proj"), "/proj")


def run(response):
    return filter_output(response, MATCHER, "/proj")


class TestGlobOutput(unittest.TestCase):
    def test_ignored_paths_are_dropped(self):
        filtered, hidden = run("/proj/src/app.ts\n/proj/secrets/api.key\n/proj/README.md")
        self.assertNotIn("secrets/api.key", filtered)
        self.assertIn("/proj/src/app.ts", filtered)
        self.assertIn("/proj/README.md", filtered)
        self.assertEqual(hidden, 1)

    def test_clean_output_is_left_alone(self):
        filtered, hidden = run("/proj/src/app.ts\n/proj/README.md")
        self.assertIsNone(filtered)
        self.assertEqual(hidden, 0)

    def test_a_notice_reports_what_was_hidden(self):
        filtered, _ = run("/proj/.env\n/proj/README.md")
        self.assertIn("claudeignore", filtered)
        self.assertIn("1", filtered)


class TestGrepContentMode(unittest.TestCase):
    def test_match_lines_for_ignored_files_are_dropped(self):
        filtered, hidden = run(
            "/proj/app.py:5:token = 1\n/proj/.env:2:TOKEN=hunter2\n/proj/b.py:9:token = 2"
        )
        self.assertNotIn("hunter2", filtered)
        self.assertIn("/proj/app.py:5:token = 1", filtered)
        self.assertEqual(hidden, 1)

    def test_context_lines_for_ignored_files_are_dropped(self):
        filtered, _ = run(
            "/proj/.env-1-# header\n/proj/.env:2:TOKEN=hunter2\n/proj/ok.py:3:fine"
        )
        self.assertNotIn("hunter2", filtered)
        self.assertNotIn("# header", filtered)
        self.assertIn("/proj/ok.py:3:fine", filtered)

    def test_a_hyphen_in_a_directory_name_does_not_break_parsing(self):
        filtered, hidden = run("/proj/my-dir/f.txt-11-context line\n/proj/.env:1:x")
        self.assertIn("/proj/my-dir/f.txt-11-context line", filtered)
        self.assertEqual(hidden, 1)

    def test_matched_content_mentioning_an_ignored_name_is_kept(self):
        """The content of an allowed file is not itself a path."""
        filtered, hidden = run("/proj/app.py:5:secrets = load('.env')")
        self.assertIsNone(filtered)
        self.assertEqual(hidden, 0)


class TestGrepCountMode(unittest.TestCase):
    def test_counts_for_ignored_files_are_dropped(self):
        filtered, hidden = run("/proj/app.py:3\n/proj/.env:7")
        self.assertIn("/proj/app.py:3", filtered)
        self.assertNotIn("/proj/.env:7", filtered)
        self.assertEqual(hidden, 1)


class TestRelativePaths(unittest.TestCase):
    def test_relative_result_paths_resolve_against_cwd(self):
        filtered, hidden = run("src/app.ts\nsecrets/api.key")
        self.assertNotIn("secrets/api.key", filtered)
        self.assertEqual(hidden, 1)


class TestStructuredResponses(unittest.TestCase):
    def test_filenames_list_is_filtered(self):
        filtered, hidden = run(
            {"filenames": ["/proj/app.ts", "/proj/secrets/api.key"], "numFiles": 2}
        )
        self.assertEqual(filtered["filenames"], ["/proj/app.ts"])
        self.assertEqual(hidden, 1)

    def test_content_field_is_filtered(self):
        filtered, hidden = run({"content": "/proj/app.ts\n/proj/.env"})
        self.assertNotIn("/proj/.env", filtered["content"])
        self.assertEqual(hidden, 1)

    def test_unrecognized_response_shape_is_left_alone(self):
        filtered, hidden = run(42)
        self.assertIsNone(filtered)
        self.assertEqual(hidden, 0)


class TestNoPatterns(unittest.TestCase):
    def test_an_empty_matcher_never_hides_anything(self):
        empty = Matcher(compile_patterns([], "/proj"), "/proj")
        filtered, hidden = filter_output("/proj/.env\n/proj/a.ts", empty, "/proj")
        self.assertIsNone(filtered)
        self.assertEqual(hidden, 0)


if __name__ == "__main__":
    unittest.main()
