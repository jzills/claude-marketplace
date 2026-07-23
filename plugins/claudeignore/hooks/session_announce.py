#!/usr/bin/env python3
"""SessionStart hook — tell Claude up front which paths are off-limits.

The patterns themselves are not secret: .claudeignore is a checked-in file.
Surfacing them at session start saves Claude from discovering the wall one denied
tool call at a time.
"""

import json
import os
import sys

from claudeignore_config import global_ignore_path, load_config
from claudeignore_discovery import load_ruleset

CONTEXT = """A .claudeignore file is active in this workspace. These patterns are \
off-limits for every kind of access, including reading a file just to look at it:

{patterns}

Source: {sources}

Tool calls touching these paths are denied by a hook, and Grep/Glob results from \
them are stripped before you see them. Do not attempt to work around this — treat \
the paths as if they do not exist. If the user needs one of them, say it is \
covered by .claudeignore and ask them to amend the pattern."""


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    config = load_config()
    if not config.get("announce_on_session_start", True):
        sys.exit(0)

    try:
        ruleset = load_ruleset(data.get("cwd") or os.getcwd(), global_ignore_path(config))
        if not ruleset:
            sys.exit(0)
        patterns = "\n".join("  " + pattern for pattern in ruleset.patterns())
        sources = ", ".join(ruleset.sources())
    except Exception:  # noqa: BLE001 - never block a session from starting
        sys.exit(0)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": CONTEXT.format(patterns=patterns, sources=sources),
        }
    }), flush=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
