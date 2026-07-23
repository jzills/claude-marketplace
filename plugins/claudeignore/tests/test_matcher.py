"""Tests for the gitignore pattern engine."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks"))

from claudeignore_matcher import Matcher, compile_patterns  # noqa: E402


def matcher(*lines, base="/proj"):
    return Matcher(compile_patterns(list(lines), base), base)


class TestBasicMatching(unittest.TestCase):
    def test_exact_filename_matches_at_root(self):
        m = matcher(".env")
        self.assertTrue(m.is_ignored("/proj/.env"))

    def test_exact_filename_matches_at_any_depth(self):
        m = matcher(".env")
        self.assertTrue(m.is_ignored("/proj/services/api/.env"))

    def test_unrelated_file_is_not_ignored(self):
        m = matcher(".env")
        self.assertFalse(m.is_ignored("/proj/README.md"))

    def test_substring_of_filename_does_not_match(self):
        m = matcher(".env")
        self.assertFalse(m.is_ignored("/proj/.environment"))

    def test_path_outside_base_dir_is_never_ignored(self):
        m = matcher(".env")
        self.assertFalse(m.is_ignored("/other/.env"))

    def test_blank_lines_and_comments_are_skipped(self):
        m = matcher("", "# a comment", "   ", ".env")
        self.assertTrue(m.is_ignored("/proj/.env"))
        self.assertFalse(m.is_ignored("/proj/# a comment"))

    def test_escaped_hash_is_a_literal_filename(self):
        m = matcher(r"\#notes")
        self.assertTrue(m.is_ignored("/proj/#notes"))


class TestWildcards(unittest.TestCase):
    def test_star_matches_within_a_segment(self):
        m = matcher("*.pem")
        self.assertTrue(m.is_ignored("/proj/server.pem"))
        self.assertTrue(m.is_ignored("/proj/certs/nested/server.pem"))

    def test_star_does_not_cross_a_separator(self):
        m = matcher("secrets/*.key")
        self.assertTrue(m.is_ignored("/proj/secrets/api.key"))
        self.assertFalse(m.is_ignored("/proj/secrets/deep/api.key"))

    def test_doublestar_crosses_separators(self):
        m = matcher("secrets/**/*.key")
        self.assertTrue(m.is_ignored("/proj/secrets/deep/nested/api.key"))

    def test_trailing_doublestar_matches_everything_below(self):
        m = matcher("secrets/**")
        self.assertTrue(m.is_ignored("/proj/secrets/api.key"))
        self.assertTrue(m.is_ignored("/proj/secrets/deep/api.key"))

    def test_question_mark_matches_one_character(self):
        m = matcher("key?.pem")
        self.assertTrue(m.is_ignored("/proj/key1.pem"))
        self.assertFalse(m.is_ignored("/proj/key12.pem"))

    def test_character_class(self):
        m = matcher("key[0-9].pem")
        self.assertTrue(m.is_ignored("/proj/key7.pem"))
        self.assertFalse(m.is_ignored("/proj/keyX.pem"))


class TestAnchoring(unittest.TestCase):
    def test_leading_slash_anchors_to_base_dir(self):
        m = matcher("/build")
        self.assertTrue(m.is_ignored("/proj/build"))
        self.assertFalse(m.is_ignored("/proj/app/build"))

    def test_interior_slash_anchors_to_base_dir(self):
        m = matcher("src/generated")
        self.assertTrue(m.is_ignored("/proj/src/generated"))
        self.assertFalse(m.is_ignored("/proj/app/src/generated"))

    def test_no_slash_matches_at_any_depth(self):
        m = matcher("build")
        self.assertTrue(m.is_ignored("/proj/build"))
        self.assertTrue(m.is_ignored("/proj/app/build"))


class TestDirectoryPatterns(unittest.TestCase):
    def test_trailing_slash_matches_files_under_the_directory(self):
        m = matcher("secrets/")
        self.assertTrue(m.is_ignored("/proj/secrets/api.key"))
        self.assertTrue(m.is_ignored("/proj/deep/secrets/api.key"))

    def test_directory_pattern_does_not_match_a_like_named_file(self):
        m = matcher("secrets/")
        self.assertFalse(m.is_ignored("/proj/secrets"))

    def test_directory_pattern_matches_the_directory_itself(self):
        """A Grep or Glob rooted at an ignored directory must be caught."""
        m = matcher("secrets/")
        self.assertTrue(m.is_ignored("/proj/secrets", is_dir=True))

    def test_matched_pattern_honours_the_directory_hint(self):
        m = matcher("secrets/")
        self.assertEqual(m.matched_pattern("/proj/secrets", is_dir=True), "secrets/")
        self.assertIsNone(m.matched_pattern("/proj/secrets"))

    def test_plain_directory_name_covers_its_contents(self):
        m = matcher("secrets")
        self.assertTrue(m.is_ignored("/proj/secrets/api.key"))
        self.assertTrue(m.is_ignored("/proj/secrets"))


class TestNegation(unittest.TestCase):
    def test_negation_reopens_a_previously_ignored_path(self):
        m = matcher("*.pem", "!public.pem")
        self.assertTrue(m.is_ignored("/proj/server.pem"))
        self.assertFalse(m.is_ignored("/proj/public.pem"))

    def test_last_matching_rule_wins(self):
        m = matcher("*.pem", "!public.pem", "public.pem")
        self.assertTrue(m.is_ignored("/proj/public.pem"))

    def test_escaped_bang_is_a_literal_filename(self):
        m = matcher(r"\!important")
        self.assertTrue(m.is_ignored("/proj/!important"))


class TestMatchedPattern(unittest.TestCase):
    def test_reports_the_pattern_responsible_for_the_match(self):
        m = matcher("*.log", "secrets/**")
        self.assertEqual(m.matched_pattern("/proj/secrets/api.key"), "secrets/**")

    def test_reports_none_when_not_ignored(self):
        m = matcher("*.log")
        self.assertIsNone(m.matched_pattern("/proj/README.md"))


class TestBadPatterns(unittest.TestCase):
    def test_an_uncompilable_pattern_names_itself_in_the_error(self):
        with self.assertRaises(ValueError) as caught:
            compile_patterns(["*.pem", "[z-a]"], "/proj")
        self.assertIn("[z-a]", str(caught.exception))

    def test_an_unclosed_bracket_is_treated_as_a_literal(self):
        m = matcher("key[.pem")
        self.assertTrue(m.is_ignored("/proj/key[.pem"))


class TestAbsoluteBase(unittest.TestCase):
    """Global ignore files match against the whole filesystem."""

    def test_bare_pattern_matches_anywhere(self):
        m = matcher("*.pem", base="/")
        self.assertTrue(m.is_ignored("/home/alice/certs/server.pem"))

    def test_absolute_pattern_anchors_at_root(self):
        m = matcher("/etc/shadow", base="/")
        self.assertTrue(m.is_ignored("/etc/shadow"))
        self.assertFalse(m.is_ignored("/proj/etc/shadow"))


if __name__ == "__main__":
    unittest.main()
