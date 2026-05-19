# auto-rewind

A Claude Code plugin that detects when something went wrong and guides a `/rewind` to a clean checkpoint — instead of fixing forward.

## What It Does

Monitors for three failure signals:
1. **Test failures** — a `PostToolUse` hook runs your test command after every file edit and injects failures into Claude's context
2. **User rejection** — Claude recognizes "wrong", "undo", "not what I wanted", etc.
3. **Self-detection** — Claude realizes prior edits were based on a wrong assumption

When any signal fires, Claude outputs a structured rewind block with the target checkpoint and step-by-step instructions for using `/rewind`.

## Installation

```bash
# Symlink into plugins directory (recommended — picks up updates automatically)
ln -s /path/to/auto-rewind ~/.claude/plugins/auto-rewind

# Or copy
cp -r /path/to/auto-rewind ~/.claude/plugins/auto-rewind
```

Then enable in `~/.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "auto-rewind": true
  }
}
```

## Per-Project Config

Create `.claude/auto-rewind.md` in any project root to configure the plugin for that project. All keys are optional.

```yaml
---
test_command: dotnet test ./MyProject.Tests
behavior_mode: ask
checkpoint_mode: last-prompt
---
```

| Key | Default | Options |
|---|---|---|
| `test_command` | _(none — hook is silent)_ | Any shell command; non-zero exit = failure |
| `behavior_mode` | `ask` | `ask` — Claude proposes rewind and waits for confirmation<br>`auto` — Claude issues rewind instructions immediately with a revised plan |
| `checkpoint_mode` | `last-prompt` | `last-prompt` — rewind to just before the failing prompt<br>`claude-picks` — Claude selects the earliest clean checkpoint based on error analysis |

## Environment Variable Fallback

If no `.claude/auto-rewind.md` exists, the hook checks `$AUTO_REWIND_TEST_CMD`:

```bash
export AUTO_REWIND_TEST_CMD="npm test"
```

Set globally in your shell profile for a project-agnostic default.

## Hook Behavior

- Runs after every `Write`, `Edit`, or `NotebookEdit` tool call
- Silent no-op if neither config file nor env var provides a test command
- Always exits 0 — never blocks Claude from continuing
- Truncates test output to 50 lines to keep context clean

## Safety Guardrail

If Claude issues rewind instructions three consecutive times on the same prompt without resolution, it stops looping and asks for explicit guidance.
