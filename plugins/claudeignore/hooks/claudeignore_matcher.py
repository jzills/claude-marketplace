"""Gitignore-style pattern engine for .claudeignore.

Pure logic: no filesystem access, so it can be unit-tested in isolation and
reasoned about without a repository on disk. Symlink resolution belongs to the
caller (see claudeignore_paths.resolve_variants).

Implements the subset of the gitignore specification documented in
skills/claudeignore/references/pattern-syntax.md:

  * blank lines and ``#`` comments are skipped
  * a leading ``!`` negates; a leading ``\\`` escapes ``#`` or ``!``
  * a trailing ``/`` restricts the rule to directories
  * a ``/`` at the start or middle anchors the rule to the ignore file's
    directory; otherwise the rule matches at any depth
  * ``*`` matches within a segment, ``**`` spans segments, ``?`` matches one
    character, ``[...]`` is a character class
  * the last matching rule wins, so negation can re-open a path

One deliberate divergence from git: a path under an excluded *directory* cannot
be re-included, which matches git's own documented behaviour.
"""

import os
import posixpath
import re
from typing import List, Optional


class Rule:
    """A single compiled .claudeignore line."""

    __slots__ = ("pattern", "negated", "dir_only", "regex")

    def __init__(self, pattern: str, negated: bool, dir_only: bool, regex):
        self.pattern = pattern
        self.negated = negated
        self.dir_only = dir_only
        self.regex = regex


def _translate(glob: str) -> str:
    """Translate a gitignore glob into a regex body matching one relative path."""
    out: List[str] = []
    i, n = 0, len(glob)
    while i < n:
        char = glob[i]
        if char == "*":
            j = i
            while j < n and glob[j] == "*":
                j += 1
            if j - i >= 2:
                if j < n and glob[j] == "/":
                    out.append("(?:.*/)?")
                    i = j + 1
                else:
                    out.append(".*")
                    i = j
            else:
                out.append("[^/]*")
                i += 1
        elif char == "?":
            out.append("[^/]")
            i += 1
        elif char == "[":
            j = i + 1
            if j < n and glob[j] in "!^":
                j += 1
            if j < n and glob[j] == "]":
                j += 1
            while j < n and glob[j] != "]":
                j += 1
            if j >= n:
                out.append(re.escape("["))
                i += 1
            else:
                body = glob[i + 1:j]
                if body.startswith("!"):
                    body = "^" + body[1:]
                out.append("[" + body + "]")
                i = j + 1
        elif char == "\\" and i + 1 < n:
            out.append(re.escape(glob[i + 1]))
            i += 2
        else:
            out.append(re.escape(char))
            i += 1
    return "".join(out)


def _normalize_base(base_dir: str) -> str:
    base = posixpath.normpath(base_dir.replace(os.sep, "/")) if base_dir else "/"
    return "" if base == "/" else base.rstrip("/")


def _relative_to_base(abs_path: str, base: str) -> Optional[str]:
    """Path relative to the base directory, or None when it lies outside."""
    path = posixpath.normpath(abs_path.replace(os.sep, "/"))
    if not base:
        return path.lstrip("/")
    if path == base:
        return ""
    if path.startswith(base + "/"):
        return path[len(base) + 1:]
    return None


def compile_patterns(lines, base_dir: str = "/") -> List[Rule]:
    """Compile .claudeignore lines into rules anchored at ``base_dir``."""
    base = _normalize_base(base_dir)
    rules: List[Rule] = []

    for raw in lines:
        original = raw.rstrip("\n")
        line = original.strip()
        if not line or line.startswith("#"):
            continue

        negated = line.startswith("!")
        if negated:
            line = line[1:]
        elif line.startswith("\\") and line[1:2] in ("#", "!"):
            line = line[1:]

        dir_only = line.endswith("/")
        line = line.rstrip("/")
        if not line:
            continue

        if line == "~" or line.startswith("~/"):
            expanded = posixpath.normpath(os.path.expanduser(line))
            relative = _relative_to_base(expanded, base)
            if relative is None:
                continue  # outside this ignore file's reach
            line, anchored = relative, True
        else:
            anchored = "/" in line.rstrip("/")
            if line.startswith("/"):
                line = line[1:]

        body = _translate(line)
        prefix = "" if anchored else "(?:.*/)?"
        try:
            regex = re.compile(prefix + body)
        except re.error as error:
            raise ValueError(
                "unusable .claudeignore pattern {0!r}: {1}".format(original.strip(), error)
            ) from error
        rules.append(Rule(original.strip(), negated, dir_only, regex))

    return rules


class Matcher:
    """Decides whether a path is off-limits under a set of rules."""

    def __init__(self, rules: List[Rule], base_dir: str = "/"):
        self.rules = rules
        self.base = _normalize_base(base_dir)

    def __bool__(self) -> bool:
        return bool(self.rules)

    def _winner(self, relative: str, allow_dir_only: bool) -> Optional[Rule]:
        """The last rule matching this relative path, or None."""
        found = None
        for rule in self.rules:
            if rule.dir_only and not allow_dir_only:
                continue
            if rule.regex.fullmatch(relative):
                found = rule
        return found

    def matched_pattern(self, abs_path: str, is_dir: bool = False) -> Optional[str]:
        """The pattern that puts this path off-limits, or None if it is allowed."""
        rule = self._decide(abs_path, is_dir)
        return rule.pattern if rule else None

    def is_ignored(self, abs_path: str, is_dir: bool = False) -> bool:
        return self._decide(abs_path, is_dir) is not None

    def _decide(self, abs_path: str, is_dir: bool = False) -> Optional[Rule]:
        relative = _relative_to_base(abs_path, self.base)
        if not relative:
            return None

        # An excluded directory carries everything beneath it, and per gitignore
        # semantics that cannot be undone by a negation further down.
        segments = relative.split("/")
        for depth in range(1, len(segments)):
            rule = self._winner("/".join(segments[:depth]), allow_dir_only=True)
            if rule is not None and not rule.negated:
                return rule

        # Directory-only rules apply to the path itself only when the caller has
        # established that it really is a directory, so a *file* named "secrets"
        # is not caught by a "secrets/" rule.
        rule = self._winner(relative, allow_dir_only=is_dir)
        return rule if rule is not None and not rule.negated else None
