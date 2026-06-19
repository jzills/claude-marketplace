---
name: create-release
description: Use when you need to create a software release. Triggers on: "create a release", "cut a release", "prepare a release", "release the software", "ship the release", "release version X", "start the release process".
version: 1.0.0
---

# Create Release

## Overview

Orchestrates the full developer-side release workflow: determine the next version, cut
a release branch, push it, wait for CI to pass, and open a PR into `main`. Tagging is
intentionally out of scope — it belongs to the CI/CD pipeline as a post-merge step.

## Prerequisites

Verify `gh` is installed and authenticated before doing anything else:

```bash
gh auth status
```

If not authenticated, tell the user: "You need to authenticate first — run `gh auth login` in your terminal." Stop there.

## Workflow

### Step 1 — Determine release version

**REQUIRED SUB-SKILL:** Invoke `semantic-versioning` (no args needed).

The reported version (e.g. `v1.2.0`) is now available in conversation for the remaining
steps. Use it everywhere `vX.Y.Z` appears below.

### Step 2 — Detect branching strategy and create the release branch

Detect the branching strategy:

```bash
git ls-remote --heads origin develop
```

- Non-empty output → **REQUIRED SUB-SKILL:** Invoke `branching-strategy:gitflow`
- Empty output → **REQUIRED SUB-SKILL:** Invoke `branching-strategy:trunk`

The strategy skill determines the correct base branch. Use the base branch it provides:

```bash
git checkout <base-branch> && git pull origin <base-branch>
git checkout -b release/vX.Y.Z
git push -u origin release/vX.Y.Z
```

Report the branch name and detected strategy to the user before continuing.

**Edge cases:**
- Already on a branch named `release/*`: confirm with the user before creating a new one.
- Release branch already exists remotely: ask whether to reuse it or create a new version.

### Step 3 — Wait for CI to pass

**REQUIRED SUB-SKILL:** Invoke `monitor-pipeline` with args:
`"watch branch release/vX.Y.Z"`

- If `monitor-pipeline` reports **success**: proceed to step 4.
- If `monitor-pipeline` reports **failure**: tell the user which step failed, suggest
  pushing fixes to `release/vX.Y.Z` and re-running this skill from step 3, and stop.

### Step 4 — Open the release PR

Resolve the default branch (production target for release PRs in both GitFlow and trunk-based strategies):

```bash
gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'
```

**REQUIRED SUB-SKILL:** Invoke `github-pr` with args:
`"open a release PR from release/vX.Y.Z into <default-branch>. Title: 'release: vX.Y.Z'. The PR merges the release branch into <default-branch> for the vX.Y.Z release."`

### Step 5 — Report completion

Tell the user:
- The PR URL
- That the `vX.Y.Z` tag will be applied by the CI/CD pipeline after the PR is merged
- Next action: review and merge the PR

## Using This Skill From Other Skills

When a skill needs to trigger a full release as part of a larger workflow, add this to
the calling skill's SKILL.md:

```
**REQUIRED SUB-SKILL:** Invoke `create-release` to cut the release branch, wait for CI,
and open the release PR. The PR URL and version will be available in conversation.
```
