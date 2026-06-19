# Changelog

## 1.0.0

- Initial release
- `UserPromptSubmit` hook for always-on regex-based PII detection
- Two modes: `block` (hard-reject) and `warn` (redact and continue)
- Per-prompt `redact:` prefix override
- Auto-bootstraps `~/.claude/pii-scanner.config.json` from plugin default
- PII coverage: emails, phone numbers, SSNs, credit/debit cards (Luhn-validated),
  routing numbers (labelled), IBANs, public IPv4s, MRNs, passports
- Skill for Claude-side semantic scanning and hook-response handling
