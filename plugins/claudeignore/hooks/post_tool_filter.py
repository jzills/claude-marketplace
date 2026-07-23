#!/usr/bin/env python3
"""PostToolUse hook — strip ignored paths out of Grep and Glob results.

A repo-wide search still runs; it just comes back without anything from an
ignored file, plus a notice so the gap is not read as a genuine absence of
matches. Rewrites the result via updatedToolOutput, which Claude Code applies
before the model sees it.
"""

import json
import os
import sys

from claudeignore_config import global_ignore_path, load_config, write_audit_log
from claudeignore_discovery import load_ruleset
from claudeignore_filter import filter_output


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    config = load_config()
    if not config.get("filter_search_results", True):
        sys.exit(0)

    cwd = data.get("cwd") or os.getcwd()

    try:
        ruleset = load_ruleset(cwd, global_ignore_path(config))
        if not ruleset:
            sys.exit(0)
        replacement, hidden = filter_output(data.get("tool_response"), ruleset, cwd)
    except Exception:  # noqa: BLE001 - never break a tool result
        sys.exit(0)

    if not hidden:
        sys.exit(0)

    write_audit_log(config, {
        "decision": "filter",
        "tool": data.get("tool_name", ""),
        "hidden": hidden,
        "session_id": data.get("session_id", ""),
    })

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "updatedToolOutput": replacement,
        }
    }), flush=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
