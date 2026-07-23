# claudeignore

A Claude Code plugin that enforces a `.claudeignore` file. Anything it matches is
denied to every tool before the call runs — no reading, no writing, no grepping,
no shelling out to `cat`.

Claude Code has no native `.claudeignore`. It has `permissions.deny` rules, but
those live in `settings.json`, are not a project convention, and are invisible to
teammates. This plugin gives you the file convention, backed by hooks.

```
# .claudeignore
.env
secrets/**
*.pem
!.env.example
```

That is the entire setup. Drop the file in your project root and every path it
matches becomes unreachable. **With no `.claudeignore` present the plugin is
completely inert** — every hook exits immediately without reading anything else.

The guard runs on file tools, search tools, Bash, and MCP calls, costing roughly
**25 ms per such call** — almost entirely Python interpreter startup, whether or
not an ignore file exists.

---

## Installation

```shell
/plugin install claudeignore@jzills
```

Or copy the directory into `~/.claude/plugins/` and enable it in
`~/.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "claudeignore": true
  }
}
```

The config file bootstraps itself from the plugin default on first run.

---

## How it works

Three hooks over one shared pattern engine.

| Hook | Event | Job |
|------|-------|-----|
| `pre_tool_guard.py` | `PreToolUse` | Denies any tool call that resolves to an ignored path |
| `post_tool_filter.py` | `PostToolUse` | Strips ignored paths out of Grep and Glob results |
| `session_announce.py` | `SessionStart` | Tells Claude the active patterns up front |

A denied call comes back with the path, the pattern that matched, and the file it
came from:

```
Blocked by .claudeignore.

  path    : /proj/secrets/api.key
  pattern : secrets/**
  source  : /proj/.claudeignore

This path is off-limits for every kind of access, including reading it just to
look. Do not try to reach it another way...
```

Grep and Glob are not blocked outright — a repo-wide search still runs, it just
comes back without anything from an ignored file:

```
/proj/src/app.ts:1:const token = 1
[claudeignore] 2 result(s) hidden by .claudeignore
```

The notice matters: without it, a filtered search reads as a genuine absence of
matches.

---

## What is actually guaranteed

Overstating this would be the point of failure, so:

| Surface | Coverage |
|---------|----------|
| `Read`, `Write`, `Edit`, `MultiEdit`, `NotebookRead`, `NotebookEdit` | **Complete.** Denied before the tool runs. |
| `Glob`, `Grep` | **Complete.** Denied when the search root is ignored; results stripped otherwise. |
| MCP servers and unrecognized tools | **Complete for path-shaped arguments.** Every string value in the payload is checked. |
| Symlinks | **Complete.** Both the link and its target are checked. |
| Subagents | **Complete.** `PreToolUse` fires inside subagent loops too. |
| `Bash`, direct reference — `cat .env`, `git diff secrets/k`, `cp .env /tmp` | **Complete.** |
| `Bash`, obfuscated — `cat $(echo .e''nv)`, or a script that opens the file itself | **Not covered.** |

That last row is a real hole, and no hook can close it: by the time a shell
command runs, the hook has already made its decision from the command string.

To close it, run **`/claudeignore-harden`**. It converts your `.claudeignore` into
native `permissions.deny` rules and OS-level sandbox `denyRead` paths, which the
operating system enforces for every subprocess regardless of what the command
claims to do. It prints the JSON for you to apply; it never edits your settings.

---

## Pattern syntax

Gitignore syntax — see [`skills/claudeignore/references/pattern-syntax.md`](skills/claudeignore/references/pattern-syntax.md)
for the full table.

| Pattern | Matches |
|---------|---------|
| `.env` | `.env` at any depth |
| `/build` | `build` at the project root only |
| `secrets/` | the `secrets` directory and everything in it |
| `*.pem` | any `.pem` file, any depth |
| `logs/**/*.key` | `.key` files any distance under `logs/` |
| `!public.pem` | re-opens what an earlier pattern closed |

The last matching pattern wins, so `*.env` followed by `!.env.example` protects
every env file except the template.

Unlike native `permissions.deny` rules, which cannot carry allowlist exceptions,
`!` negation works here.

### It is an ACL, not a noise filter

Put secrets in `.claudeignore`. Put build output in `.gitignore`.

Ignoring `build/` here does not just hide it from searches — it blocks `cd build`
and `npm run build` too, because those commands reference a path that is off
limits. That is correct behaviour for an access-control list and the wrong tool
for reducing clutter.

### Machine-wide rules

`~/.claude/.claudeignore` applies to every project and is matched against
absolute paths:

```
~/.ssh/**
~/.aws/**
*.pem
```

Both files apply at once. Disable with `"use_global_ignore": false`.

---

## Configuration

`~/.claude/claudeignore.config.json`, created on first run:

```json
{
  "bash_inspection": true,
  "filter_search_results": true,
  "use_global_ignore": true,
  "announce_on_session_start": true,
  "on_error": "deny",
  "audit_log": true,
  "audit_log_path": "~/.claude/claudeignore.log"
}
```

| Option | Default | What it does |
|--------|---------|--------------|
| `bash_inspection` | `true` | Inspect Bash commands for ignored paths. Off = structured file tools only. |
| `filter_search_results` | `true` | Strip ignored paths from Grep/Glob output. |
| `use_global_ignore` | `true` | Also apply `~/.claude/.claudeignore`. |
| `announce_on_session_start` | `true` | Inject the active patterns at session start. |
| `on_error` | `"deny"` | Fail closed when an ignore file exists but cannot be evaluated. |
| `audit_log` | `true` | Append a JSONL entry per denial and per filtered result. |
| `audit_log_path` | `~/.claude/claudeignore.log` | Where that log goes. |

### Failing closed

A pattern that cannot be compiled — `[z-a]`, an invalid character range — denies
**every** tool call until it is fixed, and the denial names the offending pattern:

```
Blocked by .claudeignore (failing closed).

The claudeignore hook could not evaluate this call:
unusable .claudeignore pattern '[z-a]': bad character range z-a at position 9
```

This is deliberate. A security control that silently stops working is worse than
one that is loudly broken. Set `"on_error": "allow"` to invert it.

---

## Skills

| Skill | Use |
|-------|-----|
| `claudeignore` | Responding to denials, authoring patterns, explaining what is off-limits |
| `claudeignore-harden` | Generating native `permissions.deny` + sandbox `denyRead` config from your `.claudeignore` |

---

## Development

Pure stdlib, no dependencies. The pattern engine, path extraction, and result
filtering are separated from the hook entry points so they can be tested without
a live session:

```shell
python3 -m unittest discover -s plugins/claudeignore/tests -v
```

Exercise a hook directly with a real payload:

```shell
echo '{"tool_name":"Read","tool_input":{"file_path":"/proj/.env"},"cwd":"/proj"}' \
  | CLAUDE_PLUGIN_ROOT=plugins/claudeignore \
    python3 plugins/claudeignore/hooks/pre_tool_guard.py
```

Empty output means allowed. A JSON deny decision means blocked.

| Module | Responsibility |
|--------|----------------|
| `claudeignore_matcher.py` | Gitignore pattern engine. Pure — no filesystem access. |
| `claudeignore_discovery.py` | Finds ignore files, assembles the merged ruleset |
| `claudeignore_paths.py` | Extracts candidate paths from a `tool_input` |
| `claudeignore_filter.py` | Strips ignored paths out of search results |
| `claudeignore_config.py` | Config bootstrap and audit logging |
