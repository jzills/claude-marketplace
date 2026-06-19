---
name: risk-audit
description: View the shimmering-forest risk auditor's current configuration and recent audit log entries. Use when the user types "/risk-audit", asks to "show risk audit config", "check risk thresholds", "view audit log", "show blocked operations", or "what is shimmering-forest configured to block".
argument-hint: "[last N]"
allowed-tools: [Read, Bash]
---

# Risk Audit Viewer

You are helping the user inspect the `shimmering-forest` risk auditor plugin.

## Arguments

The user invoked this with: $ARGUMENTS

If the argument is a number N (e.g. `/risk-audit 20`), show the last N log entries.
If no argument is given, show the last 10 entries and the current config.

## Step 1 — Read the config

Read `~/.claude/shimmering-forest.config.json`.

If the file does not exist, tell the user:
> No user config found. The plugin is using built-in defaults.

Then display the defaults:

| Setting | Default |
|---------|---------|
| block_threshold | High |
| warn_threshold | Medium |
| show_all_scores | false |
| block_mode | hard |
| audit_log | true |
| audit_log_path | ~/.claude/shimmering-forest.log |
| Excepted tools | Read |
| Excepted patterns | (none) |

If the file exists, display it as a formatted table:

| Setting | Value |
|---------|-------|
| cvss_version | {cvss_version} |
| block_threshold | {block_threshold} |
| warn_threshold | {warn_threshold} |
| show_all_scores | {show_all_scores} |
| block_mode | {block_mode} |
| audit_log | {audit_log} |
| audit_log_path | {audit_log_path} |
| Excepted tools | {exceptions.tool_names joined by ", "} |
| Excepted patterns | {count of exceptions.command_patterns} custom patterns |

Also show the severity bands for reference. Adjust the tier label based on `cvss_version`:
- CVSS 4.0: show "None" for the 0.0 tier and list dimension names as VI / VC / VA / SI / PR
- CVSS 3.1: show "Info" for the 0.0 tier and list dimension names as II / CI / AI / SC / PR

| Tier | Score Range | Default Action |
|------|-------------|----------------|
| Critical | 9.0–10.0 | Block |
| High | 7.0–8.9 | Block |
| Medium | 4.0–6.9 | Warn |
| Low | 0.1–3.9 | Allow |
| None / Info | 0.0 | Allow |

## Step 2 — Read recent log entries

Run the following to get the last N entries in reverse-chronological order (most recent first):

```bash
tail -n {N} {audit_log_path} | tac
```

If the file does not exist, say:
> No audit log found yet — no operations have been scored in this installation.

If it exists, each line is a JSON object. Parse and display as a table, most recent entry at the top:

| Time | Tool | Score | Severity | Decision | Subject |
|------|------|-------|----------|----------|---------|
| {ts} | {tool_name} | {score} | {severity} | {decision} | {subject, truncated to 60 chars} |

## Step 3 — Summary statistics

From the displayed entries, compute and show:
- Total entries shown
- Breakdown by decision: X blocked, Y warned, Z allowed
- Highest risk score seen and which tool/rule produced it
- Most commonly scored tool

## Step 4 — Offer next steps

End with:
> To change thresholds, edit `~/.claude/shimmering-forest.config.json`.
> To whitelist a command pattern, add a regex to `exceptions.command_patterns`.
> To whitelist a tool entirely, add its name to `exceptions.tool_names`.

If any blocked entries are shown, add:
> Use `/risk-audit 50` to see more history.

If the user's prompt asked specifically about a blocked operation (e.g. "is git push blocked?"), also offer the two concrete options for allowing it:

1. **Raise the block threshold** — e.g. set `block_threshold` to `"Critical"` so only scores ≥ 9.0 are blocked:
   ```json
   { "block_threshold": "Critical", "warn_threshold": "High" }
   ```
2. **Whitelist the specific command** — add a regex to `exceptions.command_patterns`:
   ```json
   { "exceptions": { "command_patterns": ["^git\\s+push\\b"] } }
   ```
