# PII Categories Reference

Based on GDPR Article 4(1), NIST SP 800-188, CCPA, and HIPAA Safe Harbor.

## Contact Information
| Type | Examples | Hook placeholder |
|------|----------|-----------------|
| Full name | John Smith, Jane Doe | `[NAME]` (semantic only — no regex) |
| Email address | user@example.com | `[EMAIL]` |
| Phone number | +1 (555) 123-4567 | `[PHONE]` |
| Physical address | 123 Main St, Springfield, IL | `[ADDRESS]` (semantic only) |
| IP address | 203.0.113.42 | `[IP_ADDRESS]` |

## Identity Numbers
| Type | Format | Hook placeholder |
|------|--------|-----------------|
| US Social Security Number | 123-45-6789 | `[SSN]` |
| Passport number | A12345678 | `[PASSPORT]` |
| Driver's license | varies by jurisdiction | `[DRIVERS_LICENSE]` (semantic only) |
| National ID / TIN | country-specific | `[NATIONAL_ID]` (semantic only) |

## Financial Data
| Type | Format | Hook placeholder |
|------|--------|-----------------|
| Credit/debit card number | 4111 1111 1111 1111 (Luhn-validated) | `[CARD_NUMBER]` |
| Bank routing number | 021000021 (when labelled) | `[ROUTING_NUMBER]` |
| IBAN | GB82WEST12345698765432 | `[IBAN]` |

## Health / Biometric
| Type | Examples | Hook placeholder |
|------|----------|-----------------|
| Medical record number | MRN-987654 | `[MEDICAL_RECORD]` |
| Diagnosis linked to a person | "Patient Jane has diabetes" | `[HEALTH_INFO]` (semantic only) |
| Biometric identifier | fingerprint hash | `[BIOMETRIC]` (semantic only) |
| Date of birth (with name) | 1985-04-15 | `[DOB]` (semantic only) |

## Detection Notes

### Hook-detected (regex, always-on)
The `pii_check.py` hook runs on every prompt and catches:
- Emails (excluding common test/placeholder addresses)
- US phone numbers
- SSNs (`\d{3}-\d{2}-\d{4}`)
- Credit/debit card numbers (Luhn-validated)
- Labelled routing numbers
- IBANs
- Public IPv4 addresses (private ranges excluded)
- MRN-prefixed medical record numbers

### Skill-detected (semantic, Claude-level)
When Claude processes a prompt (either because the hook let it through, or because
the user explicitly asked for a PII scan), Claude should also check semantically for:
- Full names in a data context (not variable names or fictional characters)
- Physical addresses
- Dates of birth combined with names
- Medical conditions linked to a named individual
- Driver's licenses and national IDs (regex varies too much by locale)

### Common false positives
- `user@example.com`, `test@test.com` — placeholder emails (excluded by hook)
- `192.168.x.x`, `10.x.x.x`, `127.0.0.1` — private/loopback IPs (excluded by hook)
- Phone numbers in prose like "call 1-800-FLOWERS" — may trigger; acceptable false positive
- 16-digit numbers that fail Luhn — not flagged as card numbers
- Fictional names in clearly creative writing — skip if context makes it unambiguous
