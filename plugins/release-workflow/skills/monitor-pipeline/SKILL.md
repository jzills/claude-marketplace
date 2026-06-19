---
name: monitor-pipeline
description: Use when you need to wait for a GitHub Actions CI pipeline to complete on a specific branch. Invoke as a sub-skill from release or deployment workflows. Also triggers on: "wait for CI", "watch the pipeline", "check if CI is passing", "monitor the build", "is the pipeline done?".
version: 1.0.0
---

# Monitor Pipeline

## Overview

Watches a GitHub Actions CI run on a specified branch and reports pass/fail in
conversation. Designed to be invoked as a sub-skill so callers can block on CI
completion before continuing (e.g., before opening a release PR).

Assumes GitHub Actions via the `gh` CLI. If the repo uses a different CI system,
tell the user this skill only supports GitHub Actions and stop.

## Workflow

### Step 1 — Identify the branch to watch

Read the branch name from the caller's args (e.g. `"watch branch release/v1.2.0"`).

If no branch was specified in args, read the current branch:

```bash
git branch --show-current
```

### Step 2 — Wait for a run to appear

Poll until a run is found (up to ~60 s, checking every 10 s):

```bash
gh run list --branch <branch> --limit 1 --json databaseId,status,conclusion,name
```

If no run appears after 60 s, tell the user:
> "No CI run found on `<branch>` after 60 s — CI may not be configured for this
> branch. Do you want to proceed anyway?"

Wait for their answer before continuing or stopping.

### Step 3 — Watch the run to completion

```bash
gh run watch <databaseId>
```

`gh run watch` streams live progress — let it run to completion. Once it exits, read
the final status:

```bash
gh run view <databaseId> --json status,conclusion
```

### Step 4 — Report result in conversation

- **Success** (`conclusion: success`):
  > "CI passed on `<branch>` — pipeline is green."

- **Failure** (`conclusion: failure` or `cancelled`):
  > "CI failed on `<branch>` — check `gh run view <databaseId>` for details."
  Return failure to the calling skill so it can halt and inform the user.

## Using This Skill From Other Skills

```
**REQUIRED SUB-SKILL:** Invoke `monitor-pipeline` with args: `"watch branch <branch-name>"`.
- Reports "CI passed" on success; reports "CI failed" on failure.
- On failure, stop and tell the user to fix the branch before retrying.
```
