---
name: auto-claude-md
description: Keeps CLAUDE.md in sync with the codebase by diffing recent commits and patching stale or missing documentation. Triggers automatically after git commits via `[AUTO-CLAUDE-MD]` hook injection. Also invoke manually when the user asks to update, sync, refresh, or audit CLAUDE.md, or asks whether their project docs are up to date. Use this skill whenever there's a question about whether CLAUDE.md reflects the current state of the repo.
---

# Auto CLAUDE.md

Keep CLAUDE.md accurate by reviewing recent commits and making targeted edits — never wholesale rewrites. The goal is a CLAUDE.md that reflects the actual current state of the repo without inflating it with noise.

## Triggers

**Hook-triggered**: Context contains `[AUTO-CLAUDE-MD] Commit detected:` — the hook has already identified the commit hash, message, and file stat. Use that context directly; don't re-run git commands to gather what's already there.

**Manual**: User asks to update or sync CLAUDE.md, or invokes the skill directly. Default scope: last 5 commits, or whatever range the user specifies.

## What Warrants an Update

Update CLAUDE.md when commits introduce:
- New or renamed CLI commands, scripts, or entrypoints
- New or removed dependencies, tools, or runtimes
- Architecture changes: new modules, renamed layers, new patterns
- Changed build, test, lint, run, or migration commands
- New configuration files that affect the dev workflow
- New environment variables or setup requirements

**Do not update for:**
- Bug fixes that don't change the interface
- Pure refactors that preserve external behavior
- Test-only changes
- Content changes (adding data, updating strings, editing copy)

When in doubt, skip. A CLAUDE.md that says too little is better than one that says the wrong thing.

## Process

### Step 1 — Gather context

**If hook-triggered**, the commit hash and stat are already in context. Read the full diff for files that look relevant:
```
git diff <hash>~1 <hash> -- <path/to/relevant/file>
```

Focus on files that affect how someone works in the repo: dependency manifests (`pyproject.toml`, `package.json`, `Cargo.toml`, etc.), `Makefile`, entrypoint scripts, CI workflow files, and changes to the top-level source structure.

**If manual**, check recent history first:
```
git log --oneline -10
```
Default to the last 5 commits unless the user specifies a range. Then get the diff stat for that range:
```
git diff HEAD~5 HEAD --stat
```

### Step 2 — Read CLAUDE.md

Read the full CLAUDE.md. Note its sections and writing style — you'll preserve both.

If CLAUDE.md doesn't exist, ask the user whether to create one. Don't create it silently; they may prefer to run `/init` for a full scaffold.

### Step 3 — Cross-reference

For each meaningful change in the diff, ask:
- Is this already documented accurately? → skip
- Is a section now wrong or outdated? → update that section
- Is this genuinely worth adding and not covered anywhere? → add it in the right place

Be conservative. Missing information is usually fine; wrong information causes real problems.

### Step 4 — Edit surgically

Make targeted edits:
- Fix a specific command or path that changed
- Add one entry to an existing list
- Add a new section only when it clearly doesn't fit anywhere existing

Preserve the user's writing style. Don't reformulate their prose, add structure they didn't have, or clean up things that weren't broken.

### Step 5 — Report

Tell the user concisely what changed in CLAUDE.md, or that no update was needed:

- "Updated the lint command in **Stack** (`flake8` → `ruff check src/`)"
- "Added `DATABASE_URL` to the **Environment** section"
- "No updates needed — the commit only refactored internal request handling"

Never update silently. Always say what changed and why the commit warranted it.
