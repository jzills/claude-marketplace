"""Strip ignored paths out of Grep/Glob results before Claude sees them.

A repo-wide search stays useful: it runs normally and simply returns nothing
from ignored files, plus a notice so the gap is not mistaken for a genuine
absence of matches.

Result lines are matched against every plausible leading path rather than one
fixed shape, because ripgrep output varies by mode:

    /proj/a.ts                  Glob, and Grep files_with_matches
    /proj/a.ts:12:matched       Grep content
    /proj/a.ts-11-context       Grep content with -A/-B/-C
    /proj/a.ts:3                Grep count
"""

import os
import posixpath
import re
from typing import List, Optional, Tuple

NOTICE = "[claudeignore] {n} result(s) hidden by .claudeignore"

_NUMBERED = re.compile(r"[:-]\d+[:-]")
_TRAILING_COUNT = re.compile(r":\d+$")


def _candidates(line: str) -> List[str]:
    """Every prefix of a result line that could be the path it refers to."""
    stripped = line.strip()
    if not stripped or stripped == "--":
        return []

    out = [stripped]
    for match in _NUMBERED.finditer(line):
        out.append(line[: match.start()])
    trailing = _TRAILING_COUNT.search(line)
    if trailing:
        out.append(line[: trailing.start()])
    return out


def _is_hidden(line: str, matcher, cwd: str) -> bool:
    for candidate in _candidates(line):
        path = candidate if posixpath.isabs(candidate) else posixpath.join(cwd, candidate)
        path = posixpath.normpath(path)
        if matcher.is_ignored(path, is_dir=os.path.isdir(path)):
            return True
    return False


def _filter_text(text: str, matcher, cwd: str) -> Tuple[Optional[str], int]:
    lines = text.split("\n")
    kept = [line for line in lines if not _is_hidden(line, matcher, cwd)]
    hidden = len(lines) - len(kept)
    if not hidden:
        return None, 0
    kept.append(NOTICE.format(n=hidden))
    return "\n".join(kept), hidden


def _filter_list(values: list, matcher, cwd: str) -> Tuple[Optional[list], int]:
    kept = [v for v in values
            if not (isinstance(v, str) and _is_hidden(v, matcher, cwd))]
    hidden = len(values) - len(kept)
    return (kept, hidden) if hidden else (None, 0)


def filter_output(response, matcher, cwd: str) -> Tuple[Optional[object], int]:
    """Return (replacement, hidden_count), or (None, 0) when nothing changed."""
    if not matcher:
        return None, 0

    if isinstance(response, str):
        return _filter_text(response, matcher, cwd)

    if isinstance(response, dict):
        updated, total = dict(response), 0
        for key, value in response.items():
            if isinstance(value, str):
                replacement, hidden = _filter_text(value, matcher, cwd)
            elif isinstance(value, list):
                replacement, hidden = _filter_list(value, matcher, cwd)
            else:
                continue
            if hidden:
                updated[key] = replacement
                total += hidden
        return (updated, total) if total else (None, 0)

    return None, 0
