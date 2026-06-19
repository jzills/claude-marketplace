#!/usr/bin/env python3
"""
Detects git commits in Bash tool calls and injects an AUTO-CLAUDE-MD sync trigger.
Fires after every Bash tool use; exits silently unless the command was a git commit.
"""
import json
import os
import re
import subprocess
import sys


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")

    # Only trigger on actual git commit commands
    if not re.search(r'\bgit\s+commit\b', command):
        sys.exit(0)

    project_dir = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

    try:
        commit_hash = subprocess.check_output(
            ["git", "-C", project_dir, "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()

        commit_msg = subprocess.check_output(
            ["git", "-C", project_dir, "log", "-1", "--pretty=format:%s"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()

        # --stat gives a readable summary without full diff noise
        diff_stat = subprocess.check_output(
            ["git", "-C", project_dir, "diff", "HEAD~1", "HEAD", "--stat"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
    except subprocess.CalledProcessError:
        # First commit or not a git repo — skip
        sys.exit(0)

    if not diff_stat:
        sys.exit(0)

    print(f"[AUTO-CLAUDE-MD] Commit detected: {commit_hash[:8]}")
    print(f"Message: {commit_msg}")
    print(f"Changes:")
    print(diff_stat)
    print()
    print("Invoke the auto-claude-md skill to review CLAUDE.md for stale or missing sections.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
