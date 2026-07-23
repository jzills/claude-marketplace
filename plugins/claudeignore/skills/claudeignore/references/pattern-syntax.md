# .claudeignore pattern syntax

A subset of the [gitignore specification](https://git-scm.com/docs/gitignore).
If you can write a `.gitignore`, you can write a `.claudeignore`.

## Rules

| Syntax | Meaning |
|--------|---------|
| `# comment` | Ignored. Blank lines are ignored too. |
| `.env` | Matches `.env` at **any depth** — no separator in the pattern. |
| `/build` | Leading `/` anchors to the directory holding the `.claudeignore`. |
| `src/generated` | A separator in the middle also anchors it. `app/src/generated` is not matched. |
| `secrets/` | Trailing `/` matches directories only, and everything inside them. |
| `*.pem` | `*` matches within one path segment. |
| `secrets/**` | `**` spans directories. |
| `logs/**/*.key` | `**` in the middle matches zero or more directories. |
| `key?.pem` | `?` matches exactly one character. |
| `key[0-9].pem` | Character classes work, including `[!abc]` for negation. |
| `!public.pem` | Re-opens a path an earlier pattern closed. |
| `\#literal` | Backslash escapes a leading `#` or `!`. |

**The last matching pattern wins**, so ordering matters:

```
*.env          # everything closed
!.env.example  # except this one
```

One divergence from git, matching git's own documented behaviour: a path under an
excluded **directory** cannot be re-opened. `secrets/` followed by
`!secrets/public.txt` leaves the file blocked. Close the individual files instead
of the directory when you need an exception.

## Where the file lives

**Project** — the nearest `.claudeignore` at or above the working directory. The
search stops at the git root, so it never picks up a file from outside the
repository. Patterns are relative to the directory containing the file.

**Machine-wide** — `~/.claude/.claudeignore`, matched against absolute paths:

```
~/.ssh/**          # anchored at your home directory
/etc/shadow        # anchored at the filesystem root
*.pem              # any depth, anywhere on the machine
```

Both apply at once. Disable the global file with `"use_global_ignore": false`.

## What each surface guarantees

| Surface | Coverage |
|---------|----------|
| `Read`, `Write`, `Edit`, `MultiEdit`, `NotebookRead`, `NotebookEdit` | **Complete.** Denied before the tool runs. |
| `Glob`, `Grep` | **Complete.** Denied when the search root is ignored; matching results stripped from the output otherwise. |
| MCP servers and unrecognized tools | **Complete for path-shaped arguments.** Every string value in the payload is checked. |
| Symlinks | **Complete.** Both the link and its target are checked. |
| `Bash`, direct reference — `cat .env`, `git diff secrets/k`, `cp .env /tmp` | **Complete.** |
| `Bash`, obfuscated — `cat $(echo .e''nv)`, or a script that opens the file itself | **Not covered.** Use the `claudeignore-harden` skill. |

A bare word in a Bash command only counts as a path when it is path-shaped
(contains `/`, or starts with `.` or `~`) or names something that exists on disk.
That is what keeps `npm run build` from being read as touching a file called
`build` — but note that if `build/` really is ignored and the directory exists,
the command *is* blocked. Another reason to keep build output out of this file.

## Errors

A pattern that cannot be compiled — `[z-a]`, an invalid character range — makes
the hook **fail closed**: every tool call is denied until it is fixed, and the
denial names the offending pattern. This is deliberate; a security control that
silently stops working is worse than one that is loudly broken. Set
`"on_error": "allow"` to fail open instead.
