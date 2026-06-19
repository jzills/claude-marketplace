#!/usr/bin/env python3
"""PII Scanner — UserPromptSubmit hook for Claude Code.

Reads the user's prompt from the Claude Code hook JSON payload on stdin,
detects PII using pattern matching, and injects a systemMessage that either:

  block mode (default) — instructs Claude to refuse the request and list
                         what PII was found (without repeating the values).

  warn mode            — redacts PII in-place, then tells Claude to use
                         the sanitized version and lists what was replaced.

Configuration: ~/.claude/pii-scanner.config.json
  {"mode": "block"}   hard-reject (default)
  {"mode": "warn"}    redact and continue

Per-prompt override: prefix the message with "redact:" to force warn mode
for a single submission without changing the global config.

Always exits 0. The systemMessage key in stdout JSON is processed by
Claude Code and injected into Claude's context before the user prompt.
"""

import json
import os
import re
import shutil
import sys
from typing import List, Tuple

# ---------------------------------------------------------------------------
# PII patterns  (compiled_regex, pii_type, placeholder)
# ---------------------------------------------------------------------------

def _build_patterns() -> List[Tuple[re.Pattern, str, str]]:
    raw = [
        # Contact info
        (
            r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
            "EMAIL", "[EMAIL]",
        ),
        (
            r"(?<!\d)(\+1[\s.\-]?)?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]\d{4}(?!\d)",
            "PHONE", "[PHONE]",
        ),
        # Identity numbers
        (
            r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b",
            "SSN", "[SSN]",
        ),
        (
            r"\b[A-Z]{1,2}\d{6,9}\b",
            "PASSPORT", "[PASSPORT]",
        ),
        # Financial — credit/debit cards (Luhn-validated below)
        (
            r"\b(?:4\d{12}(?:\d{3})?|5[1-5]\d{14}|3[47]\d{13}"
            r"|6(?:011|5\d{2})\d{12}|3(?:0[0-5]|[68]\d)\d{11})\b",
            "CARD_NUMBER", "[CARD_NUMBER]",
        ),
        # Routing numbers (only when labelled to avoid false positives)
        (
            r"\brouting(?:\s+(?:number|#|no\.?))?\s*:?\s*(\d{9})\b",
            "ROUTING_NUMBER", "[ROUTING_NUMBER]",
        ),
        # IBAN
        (
            r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b",
            "IBAN", "[IBAN]",
        ),
        # Health
        (
            r"\bMRN[-:\s]?\d{5,10}\b",
            "MEDICAL_RECORD", "[MEDICAL_RECORD]",
        ),
        # IPv4 — private ranges excluded below
        (
            r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
            r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b",
            "IP_ADDRESS", "[IP_ADDRESS]",
        ),
    ]
    return [(re.compile(p, re.IGNORECASE), t, ph) for p, t, ph in raw]


PATTERNS = _build_patterns()

# ---------------------------------------------------------------------------
# False-positive exclusion
# ---------------------------------------------------------------------------

_EXCLUDED_EMAILS = re.compile(
    r"(user|test|foo|bar|admin|noreply|no-reply|example|sample|placeholder)"
    r"@(example|test|foo|bar|localhost|domain)\.",
    re.IGNORECASE,
)

_PRIVATE_IP = re.compile(
    r"^(127\.|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.|0\.0\.0\.0|255\.255)",
)


def _luhn(number: str) -> bool:
    digits = [int(d) for d in number if d.isdigit()]
    if len(digits) < 13:
        return False
    odd = digits[-1::-2]
    even = digits[-2::-2]
    return (sum(odd) + sum(sum(divmod(d * 2, 10)) for d in even)) % 10 == 0


def _is_false_positive(pii_type: str, match_text: str) -> bool:
    if pii_type == "EMAIL" and _EXCLUDED_EMAILS.search(match_text):
        return True
    if pii_type == "IP_ADDRESS" and _PRIVATE_IP.match(match_text):
        return True
    if pii_type == "CARD_NUMBER" and not _luhn(match_text):
        return True
    return False


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

Finding = Tuple[str, str, str]  # (pii_type, matched_text, placeholder)


def scan(text: str) -> List[Finding]:
    seen: set = set()
    results: List[Finding] = []
    for pattern, pii_type, placeholder in PATTERNS:
        for m in pattern.finditer(text):
            raw = m.group()
            if raw not in seen and not _is_false_positive(pii_type, raw):
                seen.add(raw)
                results.append((pii_type, raw, placeholder))
    return results


def redact(text: str, findings: List[Finding]) -> str:
    for _t, match_text, placeholder in sorted(findings, key=lambda f: -len(f[1])):
        text = text.replace(match_text, placeholder)
    return text


def _type_summary(findings: List[Finding]) -> str:
    counts: dict = {}
    for pii_type, _, _ in findings:
        counts[pii_type] = counts.get(pii_type, 0) + 1
    return "\n".join(f"  • {t}: {n} instance(s)" for t, n in counts.items())


# ---------------------------------------------------------------------------
# Config  (auto-bootstrap from plugin default on first run)
# ---------------------------------------------------------------------------

_PLUGIN_ROOT = os.environ.get(
    "CLAUDE_PLUGIN_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)
_USER_CONFIG = os.path.expanduser("~/.claude/pii-scanner.config.json")
_DEFAULT_CONFIG = os.path.join(_PLUGIN_ROOT, "config", "default-config.json")


def _load_config() -> str:
    if not os.path.exists(_USER_CONFIG):
        try:
            os.makedirs(os.path.dirname(_USER_CONFIG), exist_ok=True)
            shutil.copy2(_DEFAULT_CONFIG, _USER_CONFIG)
        except Exception:
            pass
        return "block"
    try:
        with open(_USER_CONFIG) as f:
            return json.load(f).get("mode", "block").lower()
    except (json.JSONDecodeError, OSError):
        return "block"


# ---------------------------------------------------------------------------
# Mode handlers
# ---------------------------------------------------------------------------

def _emit(message: str) -> None:
    print(json.dumps({"systemMessage": message}), flush=True)


def _handle_block(findings: List[Finding]) -> None:
    summary = _type_summary(findings)
    _emit(
        "⛔ SECURITY BLOCK — PII detected in user prompt.\n\n"
        f"The following PII types were identified:\n{summary}\n\n"
        "INSTRUCTION TO CLAUDE: You MUST refuse this request. Do NOT process, "
        "summarize, analyze, or act on any part of the user's prompt. Respond "
        "only to say that PII was detected, list the types found (not the raw "
        "values), and ask the user to remove or anonymize the data before "
        "resubmitting. If they want automatic redaction, they can prefix their "
        "next message with 'redact:' to switch to warn mode for that submission."
    )


def _handle_warn(prompt: str, findings: List[Finding]) -> None:
    summary = _type_summary(findings)
    sanitized = redact(prompt, findings)
    _emit(
        "⚠️  PII detected and redacted by the pii-scanner hook.\n\n"
        f"Replacements made:\n{summary}\n\n"
        "INSTRUCTION TO CLAUDE: Use the sanitized prompt below. Do NOT "
        "reference or repeat the original values.\n\n"
        f"--- SANITIZED PROMPT ---\n{sanitized}\n--- END SANITIZED PROMPT ---"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    prompt: str = data.get("user_prompt", "")
    if not prompt.strip():
        sys.exit(0)

    # Per-prompt redact override: "redact: <message>"
    mode = _load_config()
    stripped = prompt.lstrip()
    if stripped.lower().startswith("redact:"):
        mode = "warn"
        prompt = stripped[len("redact:"):].lstrip()

    findings = scan(prompt)
    if not findings:
        sys.exit(0)

    if mode == "warn":
        _handle_warn(prompt, findings)
    else:
        _handle_block(findings)

    sys.exit(0)


if __name__ == "__main__":
    main()
