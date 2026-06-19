---
name: python-pep8
description: >
  Enforce PEP 8 style in Python code. Use this skill whenever the user shows you Python code
  and asks you to review, lint, format, clean up, or fix style issues — even if they don't
  say "PEP 8" explicitly. Also trigger when the user asks "is this good Python?", "check my
  code style", "format this", "clean this up", or "what's wrong with this Python?". Trigger
  proactively when writing new Python code to ensure it is PEP 8 compliant from the start.
  Also use when the user asks "what does PEP 8 say about X?", "how should I name this?",
  or any question about Python style conventions.
---

# Python PEP 8 Style Guide

This skill covers four modes — pick the one that fits the user's request:

1. **Review** — audit existing code and report violations
2. **Fix** — rewrite code to be PEP 8 compliant
3. **Generate** — write new Python code that follows PEP 8 from the start
4. **Explain** — answer questions about specific PEP 8 rules

---

## Step 1: Detect Available Tools

Before reviewing or fixing code, check which tools are installed. Run these in parallel:

```bash
command -v ruff   2>/dev/null && echo "ruff available"
command -v black  2>/dev/null && echo "black available"
command -v flake8 2>/dev/null && echo "flake8 available"
```

**Tool preference order:** ruff > black (for formatting) > flake8 > manual review.

If none are found, proceed with inline analysis using the rules in `references/pep8-rules.md`.

---

## Mode: Review

Goal: identify every PEP 8 violation and explain it clearly.

### With ruff (preferred)
```bash
ruff check <file-or-directory>
```
Report each violation with: rule code, line number, the offending line, and a plain-English explanation.

### With flake8
```bash
flake8 <file-or-directory>
```
Same reporting approach.

### Manual review
Read `references/pep8-rules.md` for the full rule set. Work through the code systematically:
1. Code layout (indentation, line length, blank lines, imports)
2. Whitespace in expressions and statements
3. Naming conventions
4. Comments and docstrings
5. Programming recommendations

**Report format** — use a numbered list grouped by category:

```
## PEP 8 Review: filename.py

### Code Layout
1. Line 12: Line is 94 characters (max 79). Consider breaking it at the operator.
2. Line 23–24: Two blank lines required before a top-level function definition.

### Naming
3. Line 8: Variable `MyValue` should be `snake_case` → `my_value`.
```

Always explain *why* a rule exists, not just that it was violated.

---

## Mode: Fix

Goal: rewrite the code to be fully PEP 8 compliant.

### With ruff (preferred — handles formatting + lint fixes)
```bash
ruff format <file>   # formatting (like black)
ruff check --fix <file>   # auto-fixable lint issues
```

### With black (formatting only)
```bash
black <file>
```
Then run `ruff check` or `flake8` to catch remaining lint issues.

### Manual fix
Apply all violations found in the review. When editing:
- Preserve the code's behavior exactly — only change style
- Re-read the result after editing to catch cascading issues (e.g., a line-length fix that misaligns continuation lines)

After fixing, confirm the file is clean by running the linter again (or doing a final manual pass).

---

## Mode: Generate

When writing new Python code, follow PEP 8 by default without waiting to be asked:

- 4-space indentation, no tabs
- Lines ≤ 79 characters (docstrings/comments ≤ 72)
- Two blank lines around top-level definitions; one blank line between methods
- `snake_case` for functions, variables, and modules; `CapWords` for classes; `ALL_CAPS` for constants
- Imports at the top, grouped: stdlib → third-party → local, each group separated by a blank line
- Docstrings on all public modules, classes, and functions using `"""`
- No trailing whitespace; no unused imports; no wildcard imports
- Use `is`/`is not` for `None` comparisons; use `isinstance()` for type checks

See `references/pep8-rules.md` for the complete rules when a situation isn't covered above.

---

## Mode: Explain

When the user asks about a specific rule:

1. State the rule clearly in one sentence
2. Show a **bad** example and a **good** example
3. Explain the reasoning — readability, consistency, or a specific problem the rule avoids
4. Cite the relevant PEP 8 section from `references/pep8-rules.md` if helpful

**Example format:**

> **Rule:** Surround top-level function and class definitions with two blank lines.
>
> ```python
> # Bad
> def foo():
>     pass
> def bar():
>     pass
>
> # Good
> def foo():
>     pass
>
>
> def bar():
>     pass
> ```
>
> *Why:* Two blank lines act as a visual separator that makes the top-level structure of a module scannable at a glance.

---

## Key Rules Quick Reference

| Area | Rule |
|---|---|
| Indentation | 4 spaces; no tabs |
| Line length | 79 chars (72 for docstrings/comments) |
| Blank lines | 2 before top-level defs; 1 between methods |
| Imports | One per line; grouped stdlib/third-party/local |
| Strings | Pick single or double and be consistent; triple-quoted use `"""` |
| Whitespace | No extra spaces inside `()`, `[]`, `{}`; space around binary ops |
| Naming | `snake_case` functions/vars, `CapWords` classes, `ALL_CAPS` constants |
| `None` comparison | `x is None` / `x is not None` (never `==`) |
| Type checks | `isinstance(x, T)` not `type(x) == T` |
| Empty sequences | `if seq:` not `if len(seq) == 0:` |
| Docstrings | Required on all public APIs; closing `"""` on same line for one-liners |

For the full rule set with examples, read `references/pep8-rules.md`.
