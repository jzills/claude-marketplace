"""Config loading and audit logging for the claudeignore hooks.

Follows the convention used by the other hook plugins in this marketplace: the
plugin default is copied to ~/.claude/<plugin>.config.json on first run, and the
user edits that copy.
"""

import json
import os
import shutil
from datetime import datetime, timezone

PLUGIN_ROOT = os.environ.get(
    "CLAUDE_PLUGIN_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)
USER_CONFIG_PATH = os.path.expanduser("~/.claude/claudeignore.config.json")
DEFAULT_CONFIG_PATH = os.path.join(PLUGIN_ROOT, "config", "default-config.json")
GLOBAL_IGNORE_PATH = os.path.expanduser("~/.claude/.claudeignore")

DEFAULTS = {
    "bash_inspection": True,
    "filter_search_results": True,
    "use_global_ignore": True,
    "announce_on_session_start": True,
    "on_error": "deny",
    "audit_log": True,
    "audit_log_path": "~/.claude/claudeignore.log",
}


def merge_defaults(config: dict) -> dict:
    merged = dict(DEFAULTS)
    merged.update(config or {})
    return merged


def load_config() -> dict:
    if not os.path.exists(USER_CONFIG_PATH):
        try:
            os.makedirs(os.path.dirname(USER_CONFIG_PATH), exist_ok=True)
            shutil.copy2(DEFAULT_CONFIG_PATH, USER_CONFIG_PATH)
        except OSError:
            pass
        return dict(DEFAULTS)
    try:
        with open(USER_CONFIG_PATH) as handle:
            return merge_defaults(json.load(handle))
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULTS)


def global_ignore_path(config: dict):
    """The machine-wide ignore file, or None when disabled or absent."""
    if not config.get("use_global_ignore", True):
        return None
    return GLOBAL_IGNORE_PATH if os.path.exists(GLOBAL_IGNORE_PATH) else None


def write_audit_log(config: dict, entry: dict) -> None:
    if not config.get("audit_log", True):
        return
    path = os.path.expanduser(config.get("audit_log_path", DEFAULTS["audit_log_path"]))
    entry = dict(entry)
    entry["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a") as handle:
            handle.write(json.dumps(entry) + "\n")
    except OSError:
        pass
