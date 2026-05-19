# shimmering-forest

A Claude Code plugin that acts as a risk auditor for every tool call. Operations are scored using a model anchored to the [CVSS v3.1 specification](https://www.first.org/cvss/v3.1/specification-document) and either blocked, warned about, or silently allowed based on your configured thresholds.

Every single tool call goes through the hook — nothing is skipped unless you explicitly add it to the exceptions list.

---

## Installation

**1. Copy or symlink the plugin directory:**

```bash
cp -r shimmering-forest ~/.claude/plugins/shimmering-forest
# or symlink to pick up updates automatically:
ln -s /path/to/shimmering-forest ~/.claude/plugins/shimmering-forest
```

**2. Enable in `~/.claude/settings.json`:**

```json
{
  "enabledPlugins": {
    "shimmering-forest": true
  }
}
```

**3. (Optional) Pre-create your config before the first session:**

```bash
cp ~/.claude/plugins/shimmering-forest/config/default-config.json \
   ~/.claude/shimmering-forest.config.json
```

If you skip this, the plugin bootstraps the config automatically on the first tool call.

---

## How It Works

A `PreToolUse` hook intercepts every tool call before it executes. The hook:

1. Reads the tool name and input from stdin (JSON)
2. Checks the exceptions list — skips entirely if matched
3. Scores the operation 0.0–10.0 using five weighted CVSS-inspired dimensions
4. Classifies the score into a severity tier
5. Compares the tier against your configured thresholds
6. **Blocks**, **warns**, or **allows** — then writes an entry to the audit log

---

## Scoring Model

Scores are produced by a weighted sum of five dimensions, each rated 0.0–1.0. The weights are adapted from CVSS v3.1.

| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| Integrity Impact (II) | 3.0 | Modifies or destroys data, especially irreversibly |
| Confidentiality Impact (CI) | 2.5 | Exposes or destroys secrets, credentials, or PII |
| Availability Impact (AI) | 2.0 | Disrupts system or service availability |
| Scope (SC) | 1.5 | Affects resources beyond the immediate target |
| Privileges Required (PR) | 1.0 | Requires elevated privileges (sudo/root) |

**Maximum score: 10.0** (all dimensions at 1.0)

### Severity Tiers

Bands match CVSS v3.1 exactly:

| Tier | Score Range | Default Action |
|------|-------------|----------------|
| Critical | 9.0 – 10.0 | Block |
| High | 7.0 – 8.9 | Block |
| Medium | 4.0 – 6.9 | Warn |
| Low | 0.1 – 3.9 | Allow silently |
| Info | 0.0 | Allow silently |

---

## What Gets Scored

### Bash Commands

Patterns are evaluated in priority order (Critical → High → Medium → Low). First match wins. `sudo`/`su` prefix adds PR=1.0 (+1.0 to final score).

**Critical — blocked by default**

| Pattern | Examples |
|---------|---------|
| Recursive force deletion | `rm -rf`, `find ... -delete`, `shred` |
| Disk-level erasure | `mkfs`, `wipefs`, `blkdiscard`, `dd of=` |
| Destructive git | `git push --force`, `git push -f`, `git reset --hard`, `git clean -fd` |
| Data truncation | `truncate -s 0` |
| Infrastructure destruction | `terraform destroy` |
| Database destruction | `DROP DATABASE`, `DROP TABLE`, `DROP SCHEMA` |

**High — blocked by default**

| Pattern | Examples |
|---------|---------|
| Any pipe to a shell | `base64 -d payload \| bash`, `cat script \| sh`, `curl url \| bash` |
| Any pipe to an interpreter | `... \| python3`, `... \| node`, `... \| perl`, `... \| ruby` |
| Shell -c execution | `bash -c "..."`, `sh -c "..."` |
| Code evaluation | `eval`, `exec` |
| Git remote / destructive | `git push`, `git branch -D`, `git push --delete`, `git tag -d` |
| Process termination | `kill`, `pkill`, `killall` |
| Service stop/disable | `systemctl stop`, `systemctl disable`, `service X stop` |
| Firewall manipulation | `iptables -F`, `ufw disable/reset`, `firewall-cmd --panic-on` |
| User/auth management | `useradd`, `userdel`, `usermod`, `passwd`, `crontab -r` |
| History destruction | `history -c`, `history -w` |
| Container destruction | `docker rm`, `docker rmi`, `docker volume rm`, `docker system prune` |
| Orchestration deletion | `kubectl delete` |
| Infrastructure apply | `terraform apply`, `ansible-playbook` |

**Medium — warned, not blocked by default**

| Pattern | Examples |
|---------|---------|
| Git local changes | `git commit`, `git merge`, `git rebase`, `git stash drop` |
| Package installation | `npm install`, `pip install`, `apt install`, `brew install`, `cargo install` |
| Service start/restart | `systemctl start/restart`, `service X restart` |
| Permission changes | `chmod`, `chown` |
| Interpreter execution | `python3 ...`, `node ...`, `ruby ...`, `perl ...` |
| Script/build execution | `bash script.sh`, `make`, `cargo run`, `go run` |
| Container operations | `docker build`, `docker run`, `docker exec`, `docker pull` |
| Orchestration writes | `kubectl apply`, `kubectl create`, `kubectl patch`, `kubectl scale` |
| Infrastructure reads | `terraform plan`, `terraform init` |

**Info — always allowed silently**

| Pattern | Examples |
|---------|---------|
| Git read-only | `git status`, `git log`, `git diff`, `git show`, `git fetch` |
| Filesystem inspection | `ls`, `cat`, `grep`, `find` (no -delete), `head`, `tail`, `wc` |
| System info | `pwd`, `which`, `ps`, `df`, `du`, `uname`, `whoami`, `date`, `hostname` |
| Help/version | `--help`, `--version`, `man` |

**Unknown commands** (no pattern match) default to **Medium** — warned but not blocked.

---

### Write / Edit Tool (file paths)

**Critical — blocked by default**

| Path pattern | Examples |
|-------------|---------|
| System directories | `/etc/`, `/usr/`, `/bin/`, `/sbin/`, `/boot/`, `/lib/` |
| SSH credentials | `~/.ssh/` |
| Cloud credentials | `~/.aws/` |
| Crypto keys | `~/.gnupg/`, `~/.gpg/` |
| Key/cert files | `*.pem`, `*.key`, `*.ppk`, `id_rsa`, `id_ed25519`, `id_ecdsa` |
| Auth dotfiles | `~/.netrc`, `~/.pgpass`, `~/.npmrc`, `~/.pypirc`, `~/.docker/config.json` |
| Secret files | `*.token`, `*.secret`, `client_secret*.json`, `service_account*.json` |
| Env/secret files | `.env` (root-level), `credentials`, `secrets` |

**High — blocked by default**

| Path pattern | Examples |
|-------------|---------|
| Claude Code config | `~/.claude/settings.json`, `~/.claude/settings.local.json` |
| Container/infra | `docker-compose.yml`, `Dockerfile`, `*.tf`, `*.tfvars` |
| CI/CD pipelines | `.github/workflows/`, `kubernetes*.yaml`, `k8s/*.yaml` |
| Env overrides | `.env.production`, `.env.staging` |
| Web server config | `nginx.conf`, `apache*.conf` |
| System auth | `sudoers`, `authorized_keys`, `known_hosts`, `/crontab` |
| Shell startup files | `~/.bashrc`, `~/.zshrc`, `~/.bash_profile`, `~/.profile`, `~/.zshenv` |
| Git config/hooks | `~/.gitconfig`, `.git/config`, `.git/hooks/` |

**Medium — warned, not blocked by default**

Source code and config files: `*.py`, `*.js`, `*.ts`, `*.go`, `*.rs`, `*.java`, `*.cs`, `*.cpp`, `*.sh`, `*.bash`, `*.json`, `*.yaml`, `*.toml`, `*.ini`, `*.sql`, and similar.

**Low — always allowed silently**

Documentation and text: `*.md`, `*.txt`, `*.rst`, `*.csv`, `*.html`, `*.css`, `*.svg`, `*.log`.

**Unknown file types** default to **Medium**.

---

### Other Tools

| Tool | Score | Tier |
|------|-------|------|
| `Read` | 0.0 | Info (excepted by default) |
| `WebSearch` | 0.3 | Info |
| `WebFetch` | 0.8 | Low |
| Any unrecognized tool | 3.0 | Low |

---

## Configuration

The config file lives at `~/.claude/shimmering-forest.config.json` and is created automatically on first run.

```json
{
  "block_threshold": "High",
  "warn_threshold": "Medium",
  "show_all_scores": false,
  "block_mode": "hard",
  "audit_log": true,
  "audit_log_path": "~/.claude/shimmering-forest.log",
  "exceptions": {
    "tool_names": ["Read"],
    "command_patterns": []
  }
}
```

### Options

**`block_threshold`** — Severity at which operations are blocked. Any operation scoring at or above this tier is stopped before execution.

Valid values: `"Critical"`, `"High"`, `"Medium"`, `"Low"`, `"Info"`
Default: `"High"` (blocks Critical and High)

**`warn_threshold`** — Severity at which Claude is warned. Any operation scoring at or above this tier (but below `block_threshold`) causes a warning message to be injected into Claude's context.

Default: `"Medium"` (warns on Medium)

**`show_all_scores`** — When `true`, every single tool call outputs its score to Claude's context, even Info-level operations. Useful for understanding what scores look like before tightening thresholds.

Default: `false`

**`block_mode`** — Controls what happens when an operation reaches `block_threshold`.

- `"hard"` (default): Hard block — exits with code 2, Claude Code shows an error and cannot proceed.
- `"soft"`: Soft block — injects a message into Claude's context instructing it to ask the user for explicit confirmation before proceeding. Claude still has the choice to comply.

**`audit_log`** — Whether to write a JSONL log entry for every scored operation.

Default: `true`

**`audit_log_path`** — Path to the audit log file. Supports `~`.

Default: `"~/.claude/shimmering-forest.log"`

**`exceptions.tool_names`** — List of tool names to skip entirely (not scored, not logged).

Default: `["Read"]`

**`exceptions.command_patterns`** — List of regex patterns matched against the Bash command string or file path. If any pattern matches, the operation is skipped.

Example — whitelist read-only git commands:
```json
"command_patterns": ["^git\\s+(status|log|diff|branch|show)"]
```

---

## Block Behavior

### Hard block (default)

Claude Code receives an error and cannot execute the operation:

```
[shimmering-forest] Risk score 9.0 (Critical) exceeds block threshold High.
Tool: Bash | Rule: bash-critical
Dimensions: II=1.0 CI=1.0 AI=1.0 SC=1.0 PR=0.0
To allow, lower block_threshold in ~/.claude/shimmering-forest.config.json
```

### Soft block

A message is injected into Claude's context:

```
[shimmering-forest] SOFT BLOCK: Risk score 9.0 (Critical) — Bash (bash-critical).
This operation exceeds the block threshold (High). Do NOT proceed until the user
explicitly confirms they want to run this command.
```

### Warn

A warning is injected into Claude's context (operation still executes):

```
[shimmering-forest] WARNING: Risk score 4.0 (Medium) — Bash (bash-medium).
Threshold to block: High. Dimensions: II=1.0 CI=0.0 AI=0.0 SC=0.7 PR=0.0. Proceed with caution.
```

---

## Audit Log

Every scored operation is appended to the log as a JSON line, regardless of decision:

```json
{
  "ts": "2026-05-07T18:29:31.306Z",
  "session_id": "abc123",
  "tool_name": "Bash",
  "score": 9.0,
  "severity": "Critical",
  "decision": "block",
  "rule": "bash-critical",
  "dims": {"II": 1.0, "CI": 1.0, "AI": 1.0, "SC": 1.0, "PR": 0.0},
  "subject": "rm -rf /home/user/data",
  "cwd": "/home/user"
}
```

`subject` is the Bash command (first 200 chars) or file path. `rule` is the internal pattern name that matched.

---

## `/risk-audit` Command

Use `/risk-audit` from Claude Code to inspect your current config and recent log entries.

```
/risk-audit         — show config + last 10 log entries
/risk-audit 50      — show last 50 log entries
```

Displays:
- Current threshold and exception settings
- CVSS severity band reference table
- Log entries as a table (time, tool, score, severity, decision, subject)
- Summary statistics: blocked/warned/allowed counts, highest score seen, most-scored tool

---

## Common Recipes

**Allow `git push` without a prompt (lower block to Critical only):**
```json
{ "block_threshold": "Critical", "warn_threshold": "High" }
```

**Whitelist a specific command pattern:**
```json
{
  "exceptions": {
    "tool_names": ["Read"],
    "command_patterns": ["^git\\s+push\\s+origin\\s+main$"]
  }
}
```

**See every score in Claude's context (useful when tuning):**
```json
{ "show_all_scores": true }
```

**Use soft blocks instead of hard blocks:**
```json
{ "block_mode": "soft" }
```

**Turn off audit logging:**
```json
{ "audit_log": false }
```

---

## Score Reference

| Operation | Score | Tier | Default action |
|-----------|-------|------|----------------|
| `git status` | 0.0 | Info | Allow |
| `ls /tmp` | 0.0 | Info | Allow |
| `cat README.md` | 0.0 | Info | Allow |
| `which python3` | 0.0 | Info | Allow |
| Write `README.md` | 1.05 | Low | Allow |
| `npm install` | 4.0 | Medium | Warn |
| `python3 script.py` | 4.0 | Medium | Warn |
| `make build` | 4.0 | Medium | Warn |
| `docker build` | 4.0 | Medium | Warn |
| Write `app.py` | 4.2 | Medium | Warn |
| `git commit` | 4.05 | Medium | Warn |
| `chmod 755 script.sh` | 4.05 | Medium | Warn |
| `git push` | 7.0 | High | **Block** |
| `git branch -D feature` | 7.0 | High | **Block** |
| `iptables -F` | 7.0 | High | **Block** |
| `userdel bob` | 7.0 | High | **Block** |
| `docker rm -f app` | 7.0 | High | **Block** |
| `kubectl delete pod` | 7.0 | High | **Block** |
| `base64 -d payload \| bash` | 7.0 | High | **Block** |
| `bash -c "..."` | 7.0 | High | **Block** |
| Write `~/.bashrc` | 7.0 | High | **Block** |
| Write `.gitconfig` | 7.0 | High | **Block** |
| `sudo git push` | 8.0 | High | **Block** |
| `rm -rf /data` | 9.0 | Critical | **Block** |
| `git push --force` | 9.0 | Critical | **Block** |
| `git reset --hard` | 9.0 | Critical | **Block** |
| `mkfs.ext4 /dev/sda` | 9.0 | Critical | **Block** |
| `terraform destroy` | 9.0 | Critical | **Block** |
| `DROP DATABASE prod` | 9.0 | Critical | **Block** |
| Write `~/.ssh/id_rsa` | 9.0 | Critical | **Block** |
| Write `~/.npmrc` | 9.0 | Critical | **Block** |
| `sudo rm -rf /` | 10.0 | Critical | **Block** |
