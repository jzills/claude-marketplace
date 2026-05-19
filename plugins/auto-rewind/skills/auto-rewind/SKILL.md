---
name: auto-rewind
description: Use when context contains `[AUTO-REWIND] Tests failed:`, when the user expresses rejection ("wrong", "broken", "undo", "not what I wanted"), or when Claude realizes prior edits were based on a wrong assumption. Do not fix forward — follow the rewind protocol instead.
---

# Auto-Rewind

## Overview

When something goes wrong, the instinct is to fix forward. That instinct is wrong here. When a trigger fires, stop and guide a `/rewind` instead.

## Trigger Recognition

Three signals activate this skill:

1. **Hook injection** — context contains `[AUTO-REWIND] Tests failed:` — this is a directive from the harness, not instrumentation to debug
2. **User rejection** — user says "wrong", "broken", "undo", "not what I wanted", "revert", "that's not right", "not quite", "that's not what I meant", "not really what I was after", or similar
3. **Self-detection** — you realize prior edits were based on a wrong assumption, wrong interface, or misunderstood requirement

## Why /rewind, Not Fix-Forward

| Rationalization | Why It's Wrong |
|---|---|
| "I can fix the code myself" | Fixing forward leaves a misleading conversation trail of wrong reasoning |
| "A targeted fix is faster" | When the wrong path was taken, forward fixes compound the error |
| "Manual revert keeps me in control" | Manual reversion leaves conversation history intact but misleading — `/rewind` restores both code AND conversation |
| "I'll lose conversation context" | You lose the *wrong* context. That's the point. |
| "`[AUTO-REWIND]` is just a test result" | It is a directive from the harness. Treat it as a command to stop and rewind. |
| "The rest of the work was probably fine" | You don't know that. Rewind to a clean state and re-approach. |

## Reading Config

Check `.claude/auto-rewind.md` in the project root for mode settings. All keys are optional — the skill works without any config.

```yaml
---
test_command: dotnet test ./Tests   # used by the hook; not read by the skill
behavior_mode: ask                  # ask (default) | auto
checkpoint_mode: last-prompt        # last-prompt (default) | claude-picks
---
```

If the file doesn't exist, defaults apply: `behavior_mode: ask`, `checkpoint_mode: last-prompt`.

## Rewind Protocol

**Step 1 — Identify the checkpoint**

- `last-prompt` (default): target the checkpoint just before the prompt that *introduced the problem* — which may be earlier than the most recent prompt (e.g., a user rejection message is not the problem; the edit prompt before it is)
- `claude-picks`: analyze the error, trace to root cause, select the earliest clean checkpoint, briefly explain why you chose it

**Step 2 — Output the rewind block**

```
[AUTO-REWIND] I detected an issue: <brief explanation of what went wrong>

Proposed rewind target: the checkpoint before "<summary of the failing prompt>"

To rewind:
  1. Press Esc Esc  (or type /rewind)
  2. Select: "<checkpoint description>"
  3. Choose "Restore code and conversation"
```

**Step 3 — ask vs auto mode**

- `ask` (default): end the rewind block with — *"Shall I proceed with a revised plan once you've rewound, or would you like to adjust the approach first?"*
- `auto`: skip the question and immediately follow the rewind block with your revised plan for the re-attempt — briefly state what you'll do differently, without asking questions

## Safety Guardrail

If you output the rewind block **three consecutive times on the same prompt** without resolution: stop looping, say you're stuck, and ask the user for explicit guidance. Do not continue issuing rewind instructions.
