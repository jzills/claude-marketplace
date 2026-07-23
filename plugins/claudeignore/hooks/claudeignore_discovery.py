"""Locate .claudeignore files and assemble the active ruleset.

Two sources, both optional:

  * the nearest ``.claudeignore`` walking up from the session's cwd, stopping at
    the git root so the search never escapes the repository
  * ``~/.claude/.claudeignore`` for machine-wide rules, matched against absolute
    paths so it protects files outside any project

When neither exists the ruleset is empty and every hook exits immediately.
"""

import os
import posixpath
from typing import List, Optional, Tuple

from claudeignore_matcher import Matcher, compile_patterns

IGNORE_FILENAME = ".claudeignore"


def find_project_ignore(cwd: str) -> Optional[str]:
    """The nearest .claudeignore at or above cwd, not passing the git root."""
    directory = os.path.abspath(cwd)
    while True:
        candidate = os.path.join(directory, IGNORE_FILENAME)
        if os.path.isfile(candidate):
            return candidate
        if os.path.isdir(os.path.join(directory, ".git")):
            return None  # repository boundary
        parent = os.path.dirname(directory)
        if parent == directory:
            return None
        directory = parent


def _read(path: str) -> List[str]:
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read().splitlines()
    except OSError:
        return []


class Ruleset:
    """The merged project and global rules for one session."""

    def __init__(self, layers: List[Tuple[Matcher, str]]):
        self.layers = [layer for layer in layers if layer[0]]

    def __bool__(self) -> bool:
        return bool(self.layers)

    def is_ignored(self, path: str, is_dir: bool = False) -> bool:
        return self.explain(path, is_dir) is not None

    def explain(self, path: str, is_dir: bool = False) -> Optional[Tuple[str, str]]:
        """(pattern, source file) for the rule blocking this path, or None."""
        normalized = posixpath.normpath(path.replace(os.sep, "/"))
        for matcher, source in self.layers:
            pattern = matcher.matched_pattern(normalized, is_dir)
            if pattern is not None:
                return pattern, source
        return None

    def patterns(self) -> List[str]:
        return [rule.pattern for matcher, _ in self.layers for rule in matcher.rules]

    def literals(self) -> List[str]:
        """Wildcard-free, non-negated patterns, for the Bash backstop scan."""
        out = []
        for matcher, _ in self.layers:
            for rule in matcher.rules:
                if rule.negated:
                    continue
                text = rule.pattern.rstrip("/").lstrip("/")
                if text and not any(char in text for char in "*?[]"):
                    out.append(text)
        return out

    def sources(self) -> List[str]:
        return [source for _, source in self.layers]


def load_ruleset(cwd: str, global_path: Optional[str]) -> Ruleset:
    layers: List[Tuple[Matcher, str]] = []

    project_file = find_project_ignore(cwd)
    if project_file:
        base = os.path.dirname(project_file)
        layers.append((Matcher(compile_patterns(_read(project_file), base), base),
                       project_file))

    if global_path and os.path.isfile(global_path):
        layers.append((Matcher(compile_patterns(_read(global_path), "/"), "/"),
                       global_path))

    return Ruleset(layers)
