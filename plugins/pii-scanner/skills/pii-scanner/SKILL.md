---
name: pii-scanner
description: >
  Scans prompts and pasted data for Personally Identifiable Information (PII)
  and either hard-rejects the request or warns and redacts before continuing.
  The plugin ships a UserPromptSubmit hook (pii_check.py) that runs automatically
  on every prompt for regex-detectable PII. This skill handles the Claude-side
  response when the hook fires, AND deeper semantic scanning for context-dependent
  PII the regex cannot catch.
  ALWAYS invoke this skill when: a systemMessage says PII was detected; the user
  asks to "scan for PII", "check for PII", "redact PII", or "sanitize this"; the
  user pastes records, CSVs, logs, JSON dumps, or any structured data that could
  contain personal information; or the task involves processing customer, patient,
  or employee data. When in doubt, invoke — a false positive is far cheaper than
  silently processing PII.
---

# PII Scanner

The plugin's `pii_check.py` hook runs before every prompt and handles regex-
detectable PII automatically. This skill covers two remaining cases:

1. **Hook fired** — the hook injected a `systemMessage`; follow its instructions.
2. **Direct invocation** — the user asked for a PII scan, or you detected a
   data-heavy context the hook may have missed.

Read `references/pii_categories.md` for the full PII taxonomy, hook-detected vs.
semantic-only types, and false-positive guidance.

---

## When the hook fires (systemMessage present)

The system message will say either:

- **`⛔ SECURITY BLOCK`** — refuse the request. Do NOT process, summarize, or
  analyze the prompt. Tell the user what PII *types* were found (not the values),
  and ask them to remove the data. Mention the `redact:` prefix as an option.

- **`⚠️  PII detected and redacted`** — use only the sanitized prompt between
  `--- SANITIZED PROMPT ---` markers. Do NOT reference or repeat the original
  values. Complete the user's task using the redacted text.

---

## Direct invocation / semantic scan

When the hook did not fire (or the user explicitly asked for a scan), perform a
semantic pass on the content:

### Step 1 — Detect

Scan the full text using both signals:

- **Regex patterns** — emails, phone numbers, SSNs, card numbers, IPs (see
  `references/pii_categories.md`). The hook already caught these if present,
  but double-check for anything it may have missed.

- **Semantic patterns** — names in data contexts, physical addresses, dates of
  birth combined with names, medical conditions linked to an individual,
  driver's licenses, national IDs. These require understanding context:
  `John` as a variable is not PII; `John Smith, DOB 1985-04-15` in a CSV row is.

If nothing is found, proceed normally. No need to announce a clean result unless
the user asked for a scan.

### Step 2 — Choose mode

| Context | Mode |
|---------|------|
| User says "redact", "sanitize", "clean up", "remove PII" | **Redact** |
| User says "scan", "check", "does this have PII?" | **Report only** |
| PII found while doing another task (no instruction) | **Block** |

Default to **Block** when the mode is ambiguous.

### Step 3 — Respond

**Block:**
```
⛔ PII detected — cannot proceed

Found:
- [type]: [brief location hint, no raw values]

Please remove or anonymize this data and resubmit.
Prefix with 'redact:' to have me replace it with typed placeholders.
```

**Redact:**
```
⚠️  PII redacted before processing

Replacements:
- [TYPE] × N (e.g. "…sent to [EMAIL]…")

Continuing with sanitized content.
---
[sanitized text]
```

**Report only:**
```
PII scan complete

Found:
- [type]: [count] instance(s) — [brief location hint, no raw values]

No processing was done. Remove the listed items before sharing externally.
```

---

## Config

The hook mode is controlled by `~/.claude/pii-scanner.config.json`:

```json
{"mode": "block"}   // hard-reject (default)
{"mode": "warn"}    // redact and continue
```

The file is auto-created from the plugin default on first run. Edit it to switch
modes globally. Use the `redact:` prompt prefix for a one-off warn mode override.
