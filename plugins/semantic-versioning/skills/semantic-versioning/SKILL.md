---
name: semantic-versioning
description: Use when you need to determine the next semantic version number for a release. Invoke as a sub-skill before creating a release branch, publishing a package, generating a changelog, or tagging a release. Also triggers on: "what version should I release?", "determine the version", "figure out the semver", "what's the next version?", "bump the version", "version bump", "release version".
version: 1.0.0
---

# Semantic Versioning

## Overview

Determines the next semantic version number by inspecting git history and project conventions. Reports the computed version in conversation so calling skills can use it in branch names, tags, and release artifacts.

## Workflow

### Step 1 — Detect current version

Follow the priority order in `references/version-detection.md`:

1. Parse `git tag` for the highest SemVer-shaped tag (`vX.Y.Z` or `X.Y.Z`)
2. If no tags, inspect remote branches matching `release/*` patterns
3. If neither, assume `0.0.0`

### Step 2 — Gather evidence for bump type

- **Primary:** scan `git log <current-version>..HEAD` for conventional commit types
- **Fallback:** if no conventional commits found, read `CHANGELOG.md` Unreleased section

### Step 3 — Classify bump type

Apply the rules from `references/bump-inference.md`:

| Evidence | Bump |
|---|---|
| `BREAKING CHANGE:` footer or `!` suffix (e.g. `feat!:`) | major |
| Any `feat:` commit | minor |
| Only `fix:`, `perf:`, `refactor:`, `docs:`, `chore:`, `style:`, `test:` | patch |
| No conventional commits → CHANGELOG `### Removed` | major |
| No conventional commits → CHANGELOG `### Added` or `### Changed` | minor |
| No conventional commits → CHANGELOG only `### Fixed` | patch |

Always use the **highest** bump found across all evidence. If both sources are inconclusive, ask: "I couldn't determine the bump type automatically. Is this a major, minor, or patch release?"

### Step 4 — Compute next version

Apply the bump to the current version per SemVer 2.0.0 rules:

- `major`: increment X, reset Y and Z to 0 → `2.3.1` becomes `3.0.0`
- `minor`: increment Y, reset Z to 0 → `2.3.1` becomes `2.4.0`
- `patch`: increment Z only → `2.3.1` becomes `2.3.2`

### Step 5 — Report

Announce the result with reasoning:

> "The next version is **v2.1.0** (minor bump — 3 `feat:` commits detected since v2.0.1)"

The reported version is then available in the conversation for the calling skill to use.

## Using This Skill From Other Skills

When a skill needs the next version number before proceeding (e.g., naming a release branch or generating a tag), add this to the calling skill's SKILL.md:

```
**REQUIRED SUB-SKILL:** Invoke `semantic-versioning` to determine the release version.
The reported version (e.g. "v2.1.0") will be available in the conversation for use
in branch names, tags, and release artifacts.
```
