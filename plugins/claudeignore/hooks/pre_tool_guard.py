#!/usr/bin/env python3
"""PreToolUse hook — deny any tool call that would touch an ignored path.

Reads the Claude Code hook payload on stdin. Emits a deny decision when the call
resolves to a path covered by .claudeignore, and nothing at all otherwise, so
the normal permission flow is untouched for everything else.

Fails closed: if an ignore file exists but cannot be evaluated, the call is
denied rather than silently allowed. Set "on_error": "allow" to invert that.
"""

import json
import os
import sys

from claudeignore_config import global_ignore_path, load_config, write_audit_log
from claudeignore_discovery import find_project_ignore, load_ruleset
from claudeignore_paths import extract_paths, literal_hits, resolve_variants

REASON = """Blocked by .claudeignore.

  path    : {path}
  pattern : {pattern}
  source  : {source}

This path is off-limits for every kind of access, including reading it just to \
look. Do not try to reach it another way — a different tool, a shell command, or \
a script that opens it indirectly are all covered by the same rule. Tell the user \
the path is covered by .claudeignore and that they need to remove or amend that \
pattern to grant access."""

ERROR_REASON = """Blocked by .claudeignore (failing closed).

The claudeignore hook could not evaluate this call: {error}

An ignore file is present, so access is denied rather than allowed by accident. \
This is not a decision about this particular path — every call is blocked until \
it is resolved. Show the user the error above: usually a malformed pattern in \
.claudeignore that needs correcting. Setting "on_error": "allow" in \
~/.claude/claudeignore.config.json makes the hook fail open instead."""


def _deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }), flush=True)
    sys.exit(0)


def _ignore_file_present(cwd: str, config: dict) -> bool:
    """Is there anything to enforce? Decides whether an error fails closed."""
    try:
        return bool(global_ignore_path(config) or find_project_ignore(cwd))
    except Exception:  # noqa: BLE001 - an unreadable tree means nothing to enforce
        return False


def _evaluate(data: dict, config: dict):
    """(reason, audit_entry) when the call must be denied, else None."""
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    cwd = data.get("cwd") or os.getcwd()

    if tool_name == "Bash" and not config.get("bash_inspection", True):
        return None

    ruleset = load_ruleset(cwd, global_ignore_path(config))
    if not ruleset:
        return None

    for candidate in extract_paths(tool_name, tool_input, cwd):
        for variant in resolve_variants(candidate):
            hit = ruleset.explain(variant, is_dir=os.path.isdir(variant))
            if hit:
                pattern, source = hit
                return (
                    REASON.format(path=candidate, pattern=pattern, source=source),
                    {"tool": tool_name, "path": candidate, "pattern": pattern,
                     "source": source, "rule": "path"},
                )

    # Backstop for shapes the tokenizer misses, e.g. a path built into a larger
    # argument. Only wildcard-free patterns, matched on segment boundaries.
    if tool_name == "Bash":
        command = tool_input.get("command", "") or ""
        hits = literal_hits(command, ruleset.literals())
        if hits:
            return (
                REASON.format(path=hits[0], pattern=hits[0],
                              source=", ".join(ruleset.sources())),
                {"tool": tool_name, "path": hits[0], "pattern": hits[0],
                 "source": ", ".join(ruleset.sources()), "rule": "bash-literal"},
            )

    return None


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    config = load_config()

    try:
        outcome = _evaluate(data, config)
    except Exception as error:  # noqa: BLE001 - fail closed, never crash the session
        cwd = data.get("cwd") or os.getcwd()
        if config.get("on_error", "deny") == "deny" and _ignore_file_present(cwd, config):
            write_audit_log(config, {"decision": "deny", "rule": "hook-error",
                                     "error": repr(error)})
            _deny(ERROR_REASON.format(error=error))
        sys.exit(0)

    if outcome:
        reason, entry = outcome
        entry["decision"] = "deny"
        entry["session_id"] = data.get("session_id", "")
        write_audit_log(config, entry)
        _deny(reason)

    sys.exit(0)


if __name__ == "__main__":
    main()
