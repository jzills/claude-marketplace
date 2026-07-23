---
name: claudeignore
description: >
  Handles the .claudeignore access-control file: how to respond when a tool call
  is denied by it, how to author and amend patterns, and how to explain what is
  currently off-limits. The plugin ships hooks (pre_tool_guard.py,
  post_tool_filter.py, session_announce.py) that enforce the file automatically —
  this skill covers the Claude-side behaviour around them.
  ALWAYS invoke this skill when: a tool call is denied with "Blocked by
  .claudeignore"; Grep or Glob output ends with a "[claudeignore] N result(s)
  hidden" notice; the user asks to "ignore", "hide", "protect", or "block" files
  from Claude; the user asks what is in .claudeignore or why a file cannot be
  read; or the user wants to create or edit a .claudeignore file.
---

# claudeignore

`.claudeignore` is an **access-control list, not a noise filter**. Everything it
matches becomes unreachable — no reading, no writing, no grepping, no shelling
out to `cat`. Use it for secrets and sensitive data. Use `.gitignore` for build
output; ignoring `build/` here will also block `cd build`, and that is working as
designed.

Read `references/pattern-syntax.md` for the full supported syntax and the
limitations of each enforcement surface.

---

## When a tool call is denied

The denial names the path, the pattern that matched, and the file it came from.

**Do not attempt a workaround.** Not another tool, not a shell command, not a
script that opens the file indirectly, not a subagent. Every route is covered by
the same rule, and trying is the exact behaviour the file exists to prevent.

Instead, tell the user plainly:

```
`config/prod.env` is covered by .claudeignore (pattern: `*.env`, from
/proj/.claudeignore), so I can't read it.

To let me at it, remove or narrow that pattern — e.g. `!config/prod.env` on a
following line re-opens just this file.
```

Then continue with whatever part of the task does not need that file. If the task
cannot proceed at all, say so and stop.

## When search results are filtered

Grep and Glob still run; results from ignored paths are stripped and a notice is
appended. Treat the remaining results as the complete answer. Do not try to
recover the hidden entries — mention that some were withheld if it is material to
the conclusion you are drawing.

## Authoring a .claudeignore

`assets/claudeignore.example` is a starting point covering the common cases —
env files, keys and certificates, cloud credentials, dumps and backups. Copy it
to the project root and trim it to what actually applies.

When adding patterns, prefer the narrowest thing that works:

| Goal | Pattern |
|------|---------|
| One file at the project root | `/config/prod.env` |
| A filename at any depth | `.env` |
| Everything under a directory | `secrets/**` |
| A file type anywhere | `*.pem` |
| All but one exception | `*.env` then `!.env.example` |

After editing, state which patterns changed and what they now cover. Changes take
effect on the next tool call — no restart needed.

## Machine-wide rules

`~/.claude/.claudeignore` applies to every project on the machine and is matched
against absolute paths. It is the right place for `~/.ssh/**`, `~/.aws/**`, and
`*.pem`. Suggest it when the user wants protection that outlives one repository.

## Verifying coverage

To check whether a path would be blocked without triggering a denial, read the
patterns and reason about them, or run the hook directly:

```bash
echo '{"tool_name":"Read","tool_input":{"file_path":"/abs/path"},"cwd":"/abs/project"}' \
  | python3 "${CLAUDE_PLUGIN_ROOT}/hooks/pre_tool_guard.py"
```

Empty output means the path is allowed; a JSON deny decision means it is blocked.

## Closing the Bash gap

The hooks cannot stop a shell command that hides its target — `cat $(echo .e''nv)`
— or a script that opens the file itself. When the user needs a guarantee rather
than a strong default, invoke the **claudeignore-harden** skill, which converts
`.claudeignore` into native `permissions.deny` rules and OS-level sandbox
`denyRead` paths.

## Config

`~/.claude/claudeignore.config.json`, created from the plugin default on first
run. `bash_inspection`, `filter_search_results`, `use_global_ignore`,
`announce_on_session_start`, `on_error`, `audit_log`, `audit_log_path`. See the
plugin README for what each does.
