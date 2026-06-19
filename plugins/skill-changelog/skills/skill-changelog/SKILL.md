---
name: skill-changelog
description: Use this skill whenever a skill is being created, modified, or improved — including when writing or editing a SKILL.md, adding/removing references, updating scripts, or changing a skill description. Also trigger when a user says "add a changelog", "track skill changes", "initialize changelog", "update the changelog for this skill", "switch to auto", or "switch to opt-in". This skill must run as part of any skill editing workflow to ensure CHANGELOG.md stays current.
version: 1.1.0
---

# Skill Changelog

Maintain a `CHANGELOG.md` inside the directory of any skill being worked on. Every meaningful edit to a skill warrants a dated, versioned entry.

---

## Skill Locations

Skills live in one of two places — both are valid targets:

1. **Standalone skills**: `~/.claude/skills/<skill-name>/` or `.claude/skills/<skill-name>/`
2. **Plugin skills**: `~/.claude/plugins/marketplaces/<marketplace>/plugins/<plugin>/skills/<skill-name>/`
   — or in marketplace repos: `plugins/<plugin>/skills/<skill-name>/`

`CHANGELOG.md` location depends on context — see **Location Detection** below.

---

## Location Detection

Before writing `CHANGELOG.md`, determine where it belongs:

1. **Resolve the real path** of the `SKILL.md` being edited — the path may be a symlink
   (e.g. `~/.claude/skills/<name>/SKILL.md` symlinked to a repo location):
   ```bash
   readlink -f <path-to-SKILL.md>
   ```
   Use the resolved canonical path for all directory traversal below.
2. Start from the skill's root directory (the folder containing the resolved `SKILL.md`).
3. Walk up the directory tree (up to 4 levels) looking for `.claude-plugin/plugin.json`.
4. **Plugin found:** the directory containing `.claude-plugin/` is the plugin root —
   place `CHANGELOG.md` there.
5. **Plugin not found:** the skill is standalone — place `CHANGELOG.md` next to `SKILL.md`.

**Example — plugin skill (symlinked):**
- Loaded via: `~/.claude/skills/create-release/SKILL.md` (symlink)
- Resolved to: `[repo]/plugins/release-workflow/skills/create-release/SKILL.md`
- Found: `[repo]/plugins/release-workflow/.claude-plugin/plugin.json`
- CHANGELOG: `[repo]/plugins/release-workflow/CHANGELOG.md`

**Example — standalone skill:**
- Skill dir: `~/.claude/skills/conventional-commits/`
- `readlink -f` returns same path (not a symlink)
- No `.claude-plugin/plugin.json` found walking up
- CHANGELOG: `~/.claude/skills/conventional-commits/CHANGELOG.md`

### Plugin-level entry format

When `CHANGELOG.md` is shared across multiple skills in a plugin, prefix each bullet
with the skill name so it's clear what changed:

```markdown
### Added
- `create-release`: initial skill — orchestrates version detection, release branch, CI monitoring, PR creation
- `monitor-pipeline`: initial skill — watches GitHub Actions run, reports pass/fail
```

---

## Operating Modes

The active mode is stored as plain text (`opt-in` or `auto`) in:

```
~/.claude/skills/.skill-changelog/mode
```

If the file does not exist, default to **`opt-in`**.

| Mode | Behavior |
|---|---|
| `opt-in` | Only write to `CHANGELOG.md` if it already exists at the resolved CHANGELOG location (plugin root for plugin skills, skill dir for standalone), or the user explicitly initializes it via this skill |
| `auto` | Always write — create `CHANGELOG.md` if absent, then append an entry |

### Switching modes

When the user says anything like "switch to auto", "track all skills automatically", "go back to opt-in", or "manual only":

1. Write the new mode value to `~/.claude/skills/.skill-changelog/mode`
2. Confirm the change to the user

---

## Standing Rule

Before finishing **any** skill editing task, silently apply this rule:

1. Identify the skill's root directory (the folder containing the `SKILL.md` being edited) and run **Location Detection** to determine the resolved CHANGELOG location.
2. Read `~/.claude/skills/.skill-changelog/mode` (default: `opt-in`)
3. **`opt-in` mode**: proceed only if `CHANGELOG.md` already exists at the resolved location
4. **`auto` mode**: always proceed — create `CHANGELOG.md` at the resolved location if absent, then append an entry

Do this without prompting the user.

---

## CHANGELOG.md Initialization

When creating a new `CHANGELOG.md`, write this header first:

```markdown
# Changelog

All notable changes to this skill will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

<!-- Next release entries go here -->
```

---

## Entry Format

Append entries in reverse-chronological order (newest at the top, below the header):

```markdown
## [<version>] - <YYYY-MM-DD>T<HH:MM:SS>Z

### <Change Type>
- <concise description of what changed and why>
```

### Change types

Use one or more per entry:

- `Added` — new features, sections, references, or scripts
- `Changed` — modifications to existing content or behavior
- `Fixed` — corrections to errors or wrong behavior
- `Removed` — deleted content or files
- `Deprecated` — features marked for future removal
- `Security` — security-related updates

### Versioning

Auto-infer the version bump — do not ask the user:

| Scope | Bump | Examples |
|---|---|---|
| Typo/wording fix, minor clarification | Patch `x.x.N` | Fixed a typo, rephrased a sentence |
| New section, new reference, behavior addition | Minor `x.N.0` | Added a references/ doc, new workflow step |
| Complete rewrite, breaking intent change | Major `N.0.0` | Rewrote the entire skill from scratch |

Start at `1.0.0` for the initial entry of a newly initialized changelog.

### Timestamp

Use the current UTC time in ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`.

---

## Example Entry

```markdown
## [1.1.0] - 2026-04-25T14:32:00Z

### Changed
- Expanded description to include additional trigger phrases to prevent undertriggering

### Added
- `references/schemas.md` with JSON schema for structured output validation
```

---

## Behavior Reference

| Situation | Mode | Action |
|---|---|---|
| User invokes `/skill-changelog` on skill with no `CHANGELOG.md` | either | Create file with header and first entry |
| Organic skill edit, no `CHANGELOG.md` | `opt-in` | Do nothing |
| Organic skill edit, no `CHANGELOG.md` | `auto` | Create `CHANGELOG.md` and add first entry |
| Any skill edit, `CHANGELOG.md` exists | either | Append new versioned entry silently |
| Multiple skills modified in one session | either | Add an entry to each skill's changelog |
| Skill is part of a plugin (`.claude-plugin/plugin.json` found) | either | Place CHANGELOG.md at plugin root, not skill dir |
| Multiple skills in same plugin modified in one session | either | Add one entry per skill to the shared plugin CHANGELOG, prefixing each bullet with the skill name |
| User requests mode change | — | Update mode file, confirm to user |
