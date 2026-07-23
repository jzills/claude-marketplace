# Changelog

## 1.0.0

- Initial release
- `PreToolUse` hook denying any tool call that resolves to a `.claudeignore` path
- `PostToolUse` hook stripping ignored paths out of Grep and Glob results via
  `updatedToolOutput`, with a notice reporting how many were hidden
- `SessionStart` hook announcing the active patterns so denials are not a surprise
- Gitignore pattern engine supporting anchoring, `**`, character classes,
  directory-only rules, and `!` negation with last-match-wins ordering
- Project `.claudeignore` discovered by walking up from the cwd, stopping at the
  git root; merged with an optional machine-wide `~/.claude/.claudeignore`
- Symlinks checked against both the link path and its target
- Bash commands inspected by shlex tokenization, with a wildcard-free literal
  backstop matched on path-segment boundaries
- MCP and unrecognized tools covered by a recursive scan of string arguments
- Fails closed when an ignore file exists but cannot be evaluated; the denial
  names the offending pattern
- Inert with no `.claudeignore` present — every hook exits immediately
- Auto-bootstraps `~/.claude/claudeignore.config.json` from the plugin default
- `claudeignore` skill for denial handling and pattern authoring
- `claudeignore-harden` skill converting `.claudeignore` into native
  `permissions.deny` rules and OS-level sandbox `denyRead` paths
