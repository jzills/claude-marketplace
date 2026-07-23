---
name: claudeignore-harden
description: >
  Converts a .claudeignore file into the equivalent native Claude Code
  configuration — permissions.deny rules and OS-level sandbox denyRead paths —
  and prints it for the user to apply. This closes the one gap the claudeignore
  hooks cannot cover: a shell command that hides its target, or a script that
  opens the file itself.
  ALWAYS invoke this skill when: the user runs /claudeignore-harden; asks how to
  make .claudeignore "actually enforced", "airtight", "OS-level", or "impossible
  to bypass"; asks about the Bash gap or obfuscated commands; or asks to convert
  .claudeignore into permission rules or sandbox settings.
---

# claudeignore-harden

The `claudeignore` hooks deny every tool call that names an ignored path. What
they cannot see is a shell command that hides its target (`cat $(echo .e''nv)`)
or a subprocess that opens the file itself (`python -c "print(open('.env').read())"`).

Two native Claude Code layers close that gap. This skill generates both.

**Print the configuration. Never write it to a settings file yourself** — these
are the user's security settings, and applying them is their call. Show the JSON,
say which file it belongs in, and let them paste it.

---

## Step 1 — Read the ignore file

Read `.claudeignore` from the project root (and `~/.claude/.claudeignore` if the
user wants machine-wide rules covered). Collect the active patterns, skipping
blanks and comments. Note any `!` negations separately — they need different
handling in each layer.

## Step 2 — Permission deny rules

`permissions.deny` uses the same gitignore pattern spec, so most patterns carry
over verbatim. Emit a `Read(...)` and an `Edit(...)` rule for each:

```json
{
  "permissions": {
    "deny": [
      "Read(.env)",
      "Edit(.env)",
      "Read(secrets/**)",
      "Edit(secrets/**)"
    ]
  }
}
```

Belongs in `.claude/settings.json` (checked in, shared with the team) or
`.claude/settings.local.json` (personal).

Three things to get right:

- **Both rules are needed.** A `Read` deny also blocks `Edit` on the same path,
  but `Write` and `NotebookEdit` are not covered by it. An `Edit` deny rule covers
  every file-editing tool.
- **Negations do not translate.** A deny rule cannot carry an allowlist
  exception, so `*.env` + `!.env.example` cannot be expressed. Emit the broad deny
  and tell the user which exceptions it will swallow, or emit narrower rules that
  enumerate the files instead.
- **Anchoring differs from the ignore file.** In permission rules `/path` is
  relative to the settings file, `//path` is absolute, and `~/path` is
  home-relative. A bare pattern still matches at any depth.

This layer already covers built-in file tools plus the Bash file commands Claude
Code recognizes — `cat`, `head`, `tail`, `sed`. It does not cover arbitrary
subprocesses. That is step 3.

## Step 3 — Sandbox denyRead

The sandbox enforces at the OS level, so it holds for every subprocess regardless
of what the command claims to do:

```json
{
  "sandbox": {
    "enabled": true,
    "filesystem": {
      "denyRead": ["./.env", "./secrets"],
      "allowRead": ["./.env.example"]
    }
  }
}
```

Notes to pass on:

- **Path syntax differs again.** Sandbox paths are conventional: `/abs/path`,
  `~/home/path`, `./project-relative`. **Globs are not supported** — convert
  `secrets/**` to the directory `./secrets`, and expand a pattern like `*.pem`
  into the specific directories that hold them, or accept that this layer covers
  it less precisely than the hook does.
- **`!` negations map to `allowRead`.** An exact `denyRead` still wins inside a
  broader `allowRead`, but a narrower `allowRead` re-opens part of a `denyRead`
  region — which is exactly what a negation means.
- **It applies to Bash only.** Read, Edit, and Write go through the permission
  system, which is why step 2 is not optional.
- **Platform**: macOS, Linux, and WSL2. Not native Windows. On Linux and WSL2 it
  needs `bubblewrap` and `socat` installed; `/sandbox` reports what is missing.

## Step 4 — Present it

Give the user one block per settings file, then a short summary of what each
layer buys:

| Layer | Covers | Bypassable by |
|-------|--------|---------------|
| claudeignore hooks | All tools, Grep/Glob results, MCP servers, symlinks | Obfuscated shell commands, scripts that open files themselves |
| `permissions.deny` | Built-in file tools, recognized Bash file commands | Arbitrary subprocesses |
| sandbox `denyRead` | Every Bash subprocess, at the OS level | Nothing, while the sandbox is on |

Point out that the three layers stack rather than replace each other: deny rules
are evaluated regardless of what a hook returns, and sandbox filesystem
restrictions merge with `Read`/`Edit` deny rules into the final boundary. Keeping
`.claudeignore` as the source of truth and re-running this skill after editing it
is the intended workflow.

Finish by reminding the user that the generated config does **not** auto-update
when `.claudeignore` changes — re-run `/claudeignore-harden` after edits.
