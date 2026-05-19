#!/usr/bin/env bash
# Runs the project's configured test command after every file edit.
# Silent no-op if no command is configured — never blocks Claude.

set -euo pipefail

CONFIG_FILE="${CLAUDE_PROJECT_DIR:-$PWD}/.claude/auto-rewind.md"

# Extract test_command from YAML frontmatter (between --- delimiters)
extract_command() {
  local file="$1"
  awk '/^---/{found++; next} found==1 && /^test_command:/{sub(/^test_command:[[:space:]]*/,""); print; exit}' "$file"
}

# Resolve test command: config file first, env var fallback
TEST_CMD=""

if [[ -f "$CONFIG_FILE" ]]; then
  TEST_CMD="$(extract_command "$CONFIG_FILE")"
fi

if [[ -z "$TEST_CMD" && -n "${AUTO_REWIND_TEST_CMD:-}" ]]; then
  TEST_CMD="$AUTO_REWIND_TEST_CMD"
fi

# No command configured — silent no-op
if [[ -z "$TEST_CMD" ]]; then
  exit 0
fi

# Run the test command; capture output and exit code
OUTPUT=$(eval "$TEST_CMD" 2>&1) && EXIT_CODE=0 || EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 ]]; then
  exit 0
fi

# Inject failure marker into Claude's context (truncated to 50 lines)
TRUNCATED=$(echo "$OUTPUT" | tail -n 50)
echo "[AUTO-REWIND] Tests failed:"
echo "$TRUNCATED"

# Always exit 0 — never block Claude from continuing
exit 0
