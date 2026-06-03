#!/usr/bin/env python3
"""
shimmering-forest risk auditor
Scores every Claude Code tool call using a CVSS-inspired model.

CVSS 4.0 (default): https://www.first.org/cvss/v4.0/specification-document
CVSS 3.1 (legacy):  https://www.first.org/cvss/v3.1/specification-document

Severity bands (both versions):
  Critical  9.0 – 10.0
  High      7.0 – 8.9
  Medium    4.0 – 6.9
  Low       0.1 – 3.9
  None/Info 0.0        (4.0 uses "None", 3.1 uses "Info")
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Scoring weights — CVSS 3.1 key names used internally for computation.
# In CVSS 4.0 mode keys are translated before output/logging:
#   II → VI  (Vulnerable System Integrity)
#   CI → VC  (Vulnerable System Confidentiality)
#   AI → VA  (Vulnerable System Availability)
#   SC → SI  (Subsequent System Integrity)
#   PR → PR  (Privileges Required — unchanged)
# Weights are numerically identical across versions.
# ---------------------------------------------------------------------------
WEIGHTS = {
    "II": 3.0,   # 3.1: Integrity Impact    / 4.0: Vulnerable System Integrity (VI)
    "CI": 2.5,   # 3.1: Confidentiality     / 4.0: Vulnerable System Confidentiality (VC)
    "AI": 2.0,   # 3.1: Availability        / 4.0: Vulnerable System Availability (VA)
    "SC": 1.5,   # 3.1: Scope               / 4.0: Subsequent System Integrity (SI)
    "PR": 1.0,   # Privileges Required (unchanged)
}
MAX_SCORE = sum(WEIGHTS.values())  # 10.0

# 4.0 key names for output/logging (same weights, translated keys)
DIM_MAP_31_TO_40 = {"II": "VI", "CI": "VC", "AI": "VA", "SC": "SI", "PR": "PR"}

SEVERITY_TIERS = [
    ("Critical", 9.0),
    ("High",     7.0),
    ("Medium",   4.0),
    ("Low",      0.1),
]
# "None" (CVSS 4.0) and "Info" (CVSS 3.1) are both valid zero-severity labels.
# Both appear in the order so threshold configs can use either name.
SEVERITY_ORDER = ["None", "Info", "Low", "Medium", "High", "Critical"]

# ---------------------------------------------------------------------------
# Bash command patterns — evaluated in priority order, first match wins
# ---------------------------------------------------------------------------
BASH_CRITICAL = [
    # Destructive file/directory removal
    r'\brm\b.*\s-[a-zA-Z]*r[a-zA-Z]*f\b',
    r'\brm\b.*\s-[a-zA-Z]*f[a-zA-Z]*r\b',
    r'\bfind\b.*\s-delete\b',
    r'\bfind\b.*\s--delete\b',
    r'\bshred\b',
    # Disk-level destruction
    r'\bdd\b.*\bof=',
    r'\bmkfs\b',
    r'\bwipefs\b',
    r'\bblkdiscard\b',
    r'\b>\s*/dev/(s?da\d*|nvme\d+n\d+)\b',
    # Destructive git
    r'\bgit\s+push\s+.*--force\b',
    r'\bgit\s+push\s+.*\s-f\b',
    r'\bgit\s+push\s+-f\b',
    r'\bgit\s+reset\s+--hard\b',
    r'\bgit\s+clean\s+.*-[a-zA-Z]*[fd]',
    r'\btruncate\s+.*-s\s+0\b',
    # Infrastructure destruction
    r'\bterraform\s+destroy\b',
    # Database destruction
    r'\bDROP\s+(DATABASE|TABLE|SCHEMA)\b',
]

BASH_HIGH = [
    # Arbitrary code execution via pipes (catches base64|bash, curl|bash, etc.)
    r'\|\s*(bash|sh|zsh|fish|dash)\b',
    r'\|\s*python3?\b',
    r'\|\s*(node|perl|ruby)\b',
    # Shell -c execution (wraps arbitrary commands)
    r'\b(bash|sh|zsh|dash)\s+-c\b',
    # Classic remote-execution patterns (kept for clarity)
    r'\bcurl\b.*\|\s*(bash|sh)\b',
    r'\bwget\b.*\|\s*(bash|sh)\b',
    # Code evaluation
    r'\beval\b',
    r'\bexec\s+',
    # Git remote/destructive operations
    r'\bgit\s+push\b',
    r'\bgit\s+branch\s+.*-D\b',
    r'\bgit\s+push\s+.*--delete\b',
    r'\bgit\s+tag\s+.*-d\b',
    # Process termination
    r'\bnpm\s+run\b',
    r'\bkill\s+',
    r'\bpkill\b',
    r'\bkillall\b',
    # Service management (stop/disable)
    r'\bservice\s+\w+\s+stop\b',
    r'\bsystemctl\s+(stop|disable)\b',
    # Firewall manipulation
    r'\biptables\b.*(-F\b|--flush\b)',
    r'\bufw\s+(disable|delete|reset)\b',
    r'\bfirewall-cmd\b.*--panic-on\b',
    # Cron/user/auth management
    r'\bcrontab\s+-r\b',
    r'\bpasswd\b',
    r'\buseradd\b',
    r'\buserdel\b',
    r'\busermod\b',
    # History destruction
    r'\bhistory\s+.*-[cw]\b',
    # Container/orchestration destructive ops
    r'\bdocker\s+(rm\b|rmi\b)',
    r'\bdocker\s+volume\s+rm\b',
    r'\bdocker\s+network\s+rm\b',
    r'\bdocker\s+system\s+prune\b',
    r'\bkubectl\s+delete\b',
    # Infrastructure apply (modifies shared state)
    r'\bterraform\s+apply\b',
    r'\bansible-playbook\b',
]

BASH_MEDIUM = [
    # Git local-state changes
    r'\bgit\s+commit\b',
    r'\bgit\s+merge\b',
    r'\bgit\s+rebase\b',
    r'\bgit\s+cherry-pick\b',
    r'\bgit\s+stash\s+drop\b',
    r'\bgit\s+push\s+.*--tags\b',
    # Package installation
    r'\bnpm\s+install\b',
    r'\bpip3?\s+install\b',
    r'\bapt(-get)?\s+(install|remove|purge)\b',
    r'\bbrew\s+install\b',
    r'\bcargo\s+install\b',
    r'\bgo\s+install\b',
    # Service management (start/restart)
    r'\bsystemctl\s+(start|restart)\b',
    r'\bservice\s+\w+\s+restart\b',
    # Permission changes
    r'\bchmod\b',
    r'\bchown\b',
    # Interpreter execution (arbitrary code, unknown content)
    r'\bpython3?\s',
    r'\bnode\s',
    r'\bruby\s',
    r'\bperl\s',
    # Script/build execution
    r'\b(bash|sh|zsh)\s+\S+\.sh\b',
    r'\bmake\b',
    r'\bcargo\s+run\b',
    r'\bgo\s+run\b',
    # Container operations (non-destructive)
    r'\bdocker\s+(build|run|exec|start|stop|pull)\b',
    r'\bkubectl\s+(apply|create|patch|replace|run|expose|scale|rollout)\b',
    r'\bterraform\s+(plan|init|import)\b',
]

BASH_LOW = [
    # Git read-only operations
    r'\bgit\s+(status|log|diff|show|describe|rev-parse|remote|fetch)\b',
    r'\bgit\s+branch(\s+-[a-eghij-zA-EG-Z]|\s*$)',   # branch listing only (not -D/-d with target)
    r'\bgit\s+tag(\s+-l|\s*$)',                        # tag listing only
    # Filesystem inspection
    r'\b(ls|ll|la|dir)\b',
    r'\bcat\b',
    r'\bgrep\b',
    r'\bfind\b',
    r'\bhead\b',
    r'\btail\b',
    r'\bwc\b',
    r'\bpwd\b',
    # System info
    r'\bwhich\b',
    r'\bwhereis\b',
    r'\btype\b',
    r'\bprintenv\b',
    r'\bdf\b',
    r'\bdu\b',
    r'\bps\b',
    r'\btop\b',
    r'\bhtop\b',
    r'\buname\b',
    r'\bhostname\b',
    r'\bdate\b',
    r'\buptime\b',
    r'\bwhoami\b',
    r'\bman\b',
    r'\b--help\b',
    r'\b--version\b',
    r'\becho\b',
    # NOTE: python3 -c and node -e intentionally removed — now Medium
]

BASH_PRIVILEGE = re.compile(r'^\s*(sudo|su\s)', re.IGNORECASE)

# ---------------------------------------------------------------------------
# File path patterns for Write/Edit tools
# ---------------------------------------------------------------------------
PATH_CRITICAL = [
    # System directories
    r'^/etc/',
    r'^/usr/',
    r'^/bin/',
    r'^/sbin/',
    r'^/boot/',
    r'^/lib/',
    r'^/lib64/',
    # SSH / cloud / crypto credential directories
    r'[/~]\.ssh/',
    r'[/~]\.aws/',
    r'[/~]\.gnupg/',
    r'[/~]\.gpg/',
    # Key/cert file patterns
    r'\.pem$',
    r'\.(key|ppk)$',
    r'\bid_rsa\b',
    r'\bid_ed25519\b',
    r'\bid_ecdsa\b',
    r'\bid_dsa\b',
    # Auth/credential dotfiles
    r'(^|/|~/)\.env$',
    r'(^|/|~/)\.netrc$',
    r'(^|/|~/)\.pgpass$',
    r'(^|/|~/)\.npmrc$',
    r'(^|/|~/)\.pypirc$',
    r'(^|/|~/)\.docker/config\.json$',
    r'(^|/|~/)credentials$',
    r'(^|/|~/)secrets?\b',
    # Token/secret file patterns
    r'\.(token|secret)$',
    r'client_secret.*\.json$',
    r'service.?account.*\.json$',
]

PATH_HIGH = [
    # Claude Code config
    r'[/~]\.claude/settings(\.local)?\.json$',
    # Container/infrastructure definitions
    r'docker-compose\.ya?ml$',
    r'Dockerfile$',
    r'\.tf$',
    r'\.tfvars$',
    r'\.github/workflows/',
    r'kubernetes.*\.ya?ml$',
    r'(^|/)k8s/.*\.ya?ml$',
    # Environment overrides (non-root .env.X files)
    r'(^|/)\.env\.\w+$',
    # Web server / system configs
    r'nginx\.conf$',
    r'(apache2?|httpd).*\.conf$',
    r'/crontab$',
    r'\.crontab$',
    r'sudoers',
    r'authorized_keys$',
    r'known_hosts$',
    # Shell startup / profile files (run on every shell open)
    r'(^|/|~/)\.bashrc$',
    r'(^|/|~/)\.zshrc$',
    r'(^|/|~/)\.zshenv$',
    r'(^|/|~/)\.bash_profile$',
    r'(^|/|~/)\.bash_login$',
    r'(^|/|~/)\.profile$',
    r'(^|/|~/)\.zprofile$',
    # Git config (can inject hooks/aliases)
    r'(^|/|~/)\.gitconfig$',
    r'(^|/)\.git/config$',
    r'(^|/)\.git/hooks/',
]

PATH_MEDIUM_RE = re.compile(
    r'\.(py|js|ts|jsx|tsx|go|rs|java|cs|cpp|c|h|rb|php|swift|kt|'
    r'sql|sh|bash|zsh|fish|ps1|json|ya?ml|toml|ini|cfg|conf)$',
    re.IGNORECASE,
)

PATH_LOW_RE = re.compile(
    r'\.(md|txt|rst|csv|log|html|css|svg|xml|lock)$',
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def compute_score(dims: dict) -> float:
    raw = sum(dims.get(k, 0.0) * w for k, w in WEIGHTS.items())
    return min(round(raw, 2), 10.0)


def zero_dims() -> dict:
    return {k: 0.0 for k in WEIGHTS}


def translate_dims(dims: dict, cvss_version: str) -> dict:
    if cvss_version == "3.1":
        return dims
    return {DIM_MAP_31_TO_40[k]: v for k, v in dims.items()}


def classify(score: float, cvss_version: str = "4.0") -> str:
    for name, threshold in SEVERITY_TIERS:
        if score >= threshold:
            return name
    return "None" if cvss_version == "4.0" else "Info"


def severity_gte(a: str, b: str) -> bool:
    try:
        return SEVERITY_ORDER.index(a) >= SEVERITY_ORDER.index(b)
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Tool-specific analyzers
# ---------------------------------------------------------------------------

def analyze_bash(command: str) -> tuple:
    dims = zero_dims()
    rule = "bash-unknown"

    has_privilege = bool(BASH_PRIVILEGE.search(command))
    if has_privilege:
        dims["PR"] = 1.0

    for pattern in BASH_CRITICAL:
        if re.search(pattern, command, re.IGNORECASE | re.MULTILINE):
            # II=1.0 CI=1.0 AI=1.0 SC=1.0 → 9.0 (Critical)
            dims.update({"II": 1.0, "CI": 1.0, "AI": 1.0, "SC": 1.0})
            rule = "bash-critical"
            break

    if rule == "bash-unknown":
        for pattern in BASH_HIGH:
            if re.search(pattern, command, re.IGNORECASE | re.MULTILINE):
                # II=1.0 CI=0.5 AI=1.0 SC=0.5 → 7.0 (High)
                dims.update({"II": 1.0, "CI": 0.5, "AI": 1.0, "SC": 0.5})
                rule = "bash-high"
                break

    if rule == "bash-unknown":
        for pattern in BASH_MEDIUM:
            if re.search(pattern, command, re.IGNORECASE | re.MULTILINE):
                # II=1.0 SC=0.7 → 4.05 (Medium)
                dims.update({"II": 1.0, "SC": 0.7})
                rule = "bash-medium"
                break

    if rule == "bash-unknown":
        for pattern in BASH_LOW:
            if re.search(pattern, command, re.IGNORECASE | re.MULTILINE):
                rule = "bash-low"
                break

    if rule == "bash-unknown":
        # II=1.0 SC=0.7 → 4.05 (Medium) — unknown commands treated cautiously
        dims.update({"II": 1.0, "SC": 0.7})

    return compute_score(dims), dims, rule


def analyze_path(file_path: str) -> tuple:
    dims = zero_dims()
    expanded = os.path.expanduser(file_path)

    for pattern in PATH_CRITICAL:
        if re.search(pattern, expanded, re.IGNORECASE):
            # II=1.0 CI=1.0 AI=1.0 SC=1.0 → 9.0 (Critical)
            dims.update({"II": 1.0, "CI": 1.0, "AI": 1.0, "SC": 1.0})
            return compute_score(dims), dims, "write-critical"

    for pattern in PATH_HIGH:
        if re.search(pattern, expanded, re.IGNORECASE):
            # II=1.0 CI=0.5 AI=1.0 SC=0.5 → 7.0 (High)
            dims.update({"II": 1.0, "CI": 0.5, "AI": 1.0, "SC": 0.5})
            return compute_score(dims), dims, "write-high"

    if PATH_MEDIUM_RE.search(expanded):
        # II=1.0 SC=0.5 AI=0.2 → 4.15 (Medium)
        dims.update({"II": 1.0, "SC": 0.5, "AI": 0.2})
        return compute_score(dims), dims, "write-medium"

    if PATH_LOW_RE.search(expanded):
        # II=0.3 SC=0.1 → 1.05 (Low)
        dims.update({"II": 0.3, "SC": 0.1})
        return compute_score(dims), dims, "write-low"

    # Unknown file type — cautious default (Medium)
    dims.update({"II": 1.0, "SC": 0.7})
    return compute_score(dims), dims, "write-unknown"


def score_tool(tool_name: str, tool_input: dict) -> tuple:
    if tool_name == "Bash":
        return analyze_bash(tool_input.get("command", ""))
    if tool_name in ("Write", "Edit", "MultiEdit"):
        return analyze_path(tool_input.get("file_path", ""))
    if tool_name == "Read":
        return 0.0, zero_dims(), "read-info"
    if tool_name == "WebFetch":
        dims = zero_dims()
        dims.update({"SC": 0.3, "CI": 0.1})
        return compute_score(dims), dims, "webfetch-low"
    if tool_name == "WebSearch":
        dims = zero_dims()
        dims["SC"] = 0.2
        return compute_score(dims), dims, "websearch-info"
    # Unknown tool — cautious default
    dims = zero_dims()
    dims.update({"II": 0.2, "AI": 0.1, "SC": 0.2})
    return compute_score(dims), dims, "unknown-tool"


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PLUGIN_ROOT = os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
USER_CONFIG_PATH = os.path.expanduser("~/.claude/shimmering-forest.config.json")
DEFAULT_CONFIG_PATH = os.path.join(PLUGIN_ROOT, "config", "default-config.json")

DEFAULTS = {
    "cvss_version": "4.0",
    "block_threshold": "High",
    "warn_threshold": "Medium",
    "show_all_scores": False,
    "block_mode": "hard",
    "audit_log": True,
    "audit_log_path": "~/.claude/shimmering-forest.log",
    "exceptions": {"tool_names": ["Read"], "command_patterns": []},
}


def load_config() -> dict:
    if not os.path.exists(USER_CONFIG_PATH):
        try:
            import shutil
            os.makedirs(os.path.dirname(USER_CONFIG_PATH), exist_ok=True)
            shutil.copy2(DEFAULT_CONFIG_PATH, USER_CONFIG_PATH)
        except Exception:
            pass
        return dict(DEFAULTS)
    try:
        with open(USER_CONFIG_PATH) as f:
            cfg = json.load(f)
        for k, v in DEFAULTS.items():
            if k not in cfg:
                cfg[k] = v
        if cfg.get("cvss_version") not in ("3.1", "4.0"):
            cfg["cvss_version"] = "4.0"
        return cfg
    except Exception:
        return dict(DEFAULTS)


# ---------------------------------------------------------------------------
# Exception checking
# ---------------------------------------------------------------------------

def is_excepted(tool_name: str, subject: str, config: dict) -> bool:
    exc = config.get("exceptions", {})
    if tool_name in exc.get("tool_names", []):
        return True
    for pat in exc.get("command_patterns", []):
        try:
            if re.search(pat, subject or "", re.IGNORECASE):
                return True
        except re.error:
            pass
    return False


# ---------------------------------------------------------------------------
# Decision
# ---------------------------------------------------------------------------

def decide(severity: str, config: dict) -> str:
    if severity_gte(severity, config.get("block_threshold", "High")):
        return "block"
    if severity_gte(severity, config.get("warn_threshold", "Medium")):
        return "warn"
    return "allow"


# ---------------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------------

def write_audit_log(config: dict, entry: dict) -> None:
    if not config.get("audit_log", False):
        return
    log_path = os.path.expanduser(config.get("audit_log_path", "~/.claude/shimmering-forest.log"))
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def dims_str(dims: dict) -> str:
    return " ".join(f"{k}={v:.1f}" for k, v in dims.items())


def block_output(score: float, severity: str, tool_name: str, rule: str, dims: dict, config: dict) -> None:
    block_mode = config.get("block_mode", "hard")
    block_threshold = config.get("block_threshold", "High")

    sep = "─" * 54
    if block_mode == "soft":
        print(
            f"\n{sep}\n"
            f"  shimmering-forest  SOFT BLOCK\n"
            f"{sep}\n"
            f"  Risk Score : {score:.1f} / 10.0  ({severity})\n"
            f"  Threshold  : {block_threshold}\n"
            f"  Tool       : {tool_name}\n"
            f"  Rule       : {rule}\n"
            f"  Dimensions : {dims_str(dims)}\n"
            f"\n"
            f"  Do NOT proceed until the user explicitly confirms.\n"
            f"{sep}",
            file=sys.stdout,
            flush=True,
        )
        sys.exit(0)
    else:
        print(
            f"\n{sep}\n"
            f"  shimmering-forest  BLOCKED\n"
            f"{sep}\n"
            f"  Risk Score : {score:.1f} / 10.0  ({severity})\n"
            f"  Threshold  : {block_threshold}\n"
            f"  Tool       : {tool_name}\n"
            f"  Rule       : {rule}\n"
            f"  Dimensions : {dims_str(dims)}\n"
            f"\n"
            f"  To allow   : lower block_threshold in\n"
            f"               ~/.claude/shimmering-forest.config.json\n"
            f"{sep}",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(2)


def warn_output(score: float, severity: str, tool_name: str, rule: str, dims: dict, config: dict) -> None:
    block_threshold = config.get("block_threshold", "High")
    sep = "─" * 54
    print(
        f"\n{sep}\n"
        f"  shimmering-forest  WARNING\n"
        f"{sep}\n"
        f"  Risk Score : {score:.1f} / 10.0  ({severity})\n"
        f"  Threshold  : {block_threshold}\n"
        f"  Tool       : {tool_name}\n"
        f"  Rule       : {rule}\n"
        f"  Dimensions : {dims_str(dims)}\n"
        f"\n"
        f"  Proceed with caution.\n"
        f"{sep}",
        file=sys.stdout,
        flush=True,
    )


def info_output(score: float, severity: str, tool_name: str, rule: str) -> None:
    print(
        f"[shimmering-forest] SCORE: {score:.1f} ({severity}) — {tool_name} ({rule})",
        file=sys.stdout,
        flush=True,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except Exception:
        sys.exit(0)

    session_id = data.get("session_id", "")
    tool_name  = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    cwd        = data.get("cwd", "")

    config = load_config()

    if tool_name == "Bash":
        subject = tool_input.get("command", "")
    elif tool_name in ("Write", "Edit", "MultiEdit"):
        subject = tool_input.get("file_path", "")
    else:
        subject = ""

    if is_excepted(tool_name, subject, config):
        sys.exit(0)

    cvss_version = config.get("cvss_version", "4.0")
    score, dims_raw, rule = score_tool(tool_name, tool_input)
    dims = translate_dims(dims_raw, cvss_version)
    severity = classify(score, cvss_version)
    decision = decide(severity, config)

    write_audit_log(config, {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "session_id": session_id,
        "tool_name": tool_name,
        "cvss_version": cvss_version,
        "score": score,
        "severity": severity,
        "decision": decision,
        "rule": rule,
        "dims": dims,
        "subject": subject[:200],
        "cwd": cwd,
    })

    if decision == "block":
        block_output(score, severity, tool_name, rule, dims, config)
    elif decision == "warn":
        warn_output(score, severity, tool_name, rule, dims, config)
    elif config.get("show_all_scores", False):
        info_output(score, severity, tool_name, rule)

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
