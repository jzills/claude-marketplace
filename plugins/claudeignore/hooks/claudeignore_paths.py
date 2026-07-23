"""Pull candidate filesystem paths out of a tool_input payload.

Known tools read from an explicit field allowlist, so a Grep *pattern* is never
mistaken for a path. Everything else, including MCP filesystem servers, falls
back to a recursive scan of string values.

Bash is the imprecise case and is handled deliberately: a bare word only counts
as a path when it is path-shaped or actually exists on disk, so `npm run build`
is not read as touching a file named ``build``.
"""

import os
import posixpath
import re
import shlex
from typing import Dict, Iterable, List

# Fields that name a file the tool will open or write.
FILE_FIELDS: Dict[str, tuple] = {
    "Read": ("file_path",),
    "Write": ("file_path",),
    "Edit": ("file_path",),
    "MultiEdit": ("file_path",),
    "NotebookRead": ("notebook_path", "file_path"),
    "NotebookEdit": ("notebook_path", "file_path"),
    # Search tools: only the root they scan. Results are filtered afterwards by
    # the PostToolUse hook, so a repo-wide search still works.
    "Glob": ("path", "base_dir"),
    "Grep": ("path",),
}

_SEPARATORS = r"\s/'\"=:,()\[\];&|<>"
_TRIM = "()`;&|<>\"'{}"
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _absolute(token: str, cwd: str) -> str:
    expanded = os.path.expanduser(token)
    if not posixpath.isabs(expanded):
        expanded = posixpath.join(cwd, expanded)
    return posixpath.normpath(expanded)


def _dedupe(paths: Iterable[str]) -> List[str]:
    seen, out = set(), []
    for path in paths:
        if path not in seen:
            seen.add(path)
            out.append(path)
    return out


def _looks_like_a_path(token: str, cwd: str) -> bool:
    """Path-shaped, or a bare word that names something already on disk."""
    if "://" in token:
        return False  # a URL, not a path
    if "/" in token or token.startswith((".", "~")):
        return True
    return os.path.exists(_absolute(token, cwd))


def bash_tokens(command: str, cwd: str) -> List[str]:
    """Absolute paths a shell command plausibly refers to."""
    try:
        raw = shlex.split(command, posix=True)
    except ValueError:
        raw = command.split()

    candidates = []
    for token in raw:
        token = token.strip(_TRIM)
        if not token or token.startswith("-") or token in (".", ".."):
            continue
        # FOO=path -> path
        name, sep, value = token.partition("=")
        if sep and _IDENTIFIER.match(name) and value:
            token = value.strip(_TRIM)
        if token and _looks_like_a_path(token, cwd):
            candidates.append(_absolute(token, cwd))

    return _dedupe(candidates)


def literal_hits(command: str, literals: Iterable[str]) -> List[str]:
    """Wildcard-free patterns appearing as a whole path segment in a command.

    A backstop for shapes the tokenizer misses, matched on segment boundaries so
    that `echo environment` does not trip a pattern of ``env``.
    """
    hits = []
    for literal in literals:
        if not literal:
            continue
        pattern = (
            r"(?<![^" + _SEPARATORS + r"])"
            + re.escape(literal)
            + r"(?![^" + _SEPARATORS + r"])"
        )
        if re.search(pattern, command):
            hits.append(literal)
    return hits


def _walk_strings(value, out: List[str]) -> None:
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for nested in value.values():
            _walk_strings(nested, out)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _walk_strings(nested, out)


def extract_paths(tool_name: str, tool_input: dict, cwd: str) -> List[str]:
    """Absolute paths this tool call would touch."""
    if not isinstance(tool_input, dict):
        return []

    if tool_name == "Bash":
        return bash_tokens(tool_input.get("command", "") or "", cwd)

    fields = FILE_FIELDS.get(tool_name)
    if fields is not None:
        return _dedupe(
            _absolute(tool_input[field], cwd)
            for field in fields
            if isinstance(tool_input.get(field), str) and tool_input[field]
        )

    # Unknown tool, including mcp__* servers: scan every string value.
    strings: List[str] = []
    _walk_strings(tool_input, strings)
    return _dedupe(
        _absolute(value, cwd)
        for value in strings
        if value and "://" not in value and "/" in value
    )


def resolve_variants(path: str) -> List[str]:
    """The path plus, when it is a symlink, what it resolves to."""
    try:
        real = os.path.realpath(path)
    except OSError:
        return [path]
    return [path] if real == path else [path, real]
