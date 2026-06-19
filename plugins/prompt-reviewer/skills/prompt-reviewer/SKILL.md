---
name: prompt-reviewer
description: >
  Review and refine prompts to improve clarity, specificity, token efficiency, and missing context.
  Use this skill whenever the user hands you a prompt as an artifact and asks for feedback —
  regardless of the target model (Claude, ChatGPT, Midjourney, system prompts, etc.).
  Trigger when the user says "review this prompt", "improve my prompt", "refine this prompt",
  "make this prompt better", "is this prompt clear", "check this system prompt",
  "optimize this prompt", "fix my prompt", "critique this prompt", or any similar phrasing
  where a prompt is the subject of review rather than the instruction itself.
  Supports three modes: default (single-pass), --deep (guided dialogue), --variants (three rewrites).
  Also trigger when the user uses "--deep" or "--variants" flags alongside a prompt.
version: 1.0.0
---

# Prompt Reviewer

This skill reviews prompts as artifacts — whether written for Claude, ChatGPT, Midjourney, system prompts, or any other AI tool — and returns an improved version.

Three modes are available:
- **Default** (no flag): single-pass analysis + one optimized rewrite
- **`--deep`**: guided dialogue to understand context before refining
- **`--variants`**: generates three rewrites with different trade-offs

---

## Step 1: Detect Mode

Check whether the user included a flag:

- No flag → run **Default mode**
- `--deep` present → run **Deep mode**
- `--variants` present → run **Variants mode**
- No prompt provided → ask: "Please share the prompt you'd like me to review."

If no flag is present and the prompt is longer than ~200 words or is clearly a multi-part system prompt, suggest `--deep` before proceeding:

> "This looks like a complex prompt — I can run `--deep` for a guided review that asks about your intent and constraints first. Want that, or should I proceed with the default single-pass review?"

If the user does not explicitly confirm `--deep`, proceed with Default mode.

---

## Default Mode

Analyze the prompt across five dimensions. For each, give a one-line finding: mark ✓ (no issue) or describe the specific problem.

| Dimension | What to check |
|-----------|--------------|
| **Clarity** | Is the intent unambiguous? Could it be misread? |
| **Specificity** | Are there vague terms (e.g., "good", "helpful", "brief") that should be made precise? |
| **Token efficiency** | Redundant phrasing, filler words, restating the same constraint twice? |
| **Missing context** | What does the model need that isn't there? (audience, format, constraints, examples) |
| **Scope** | Too broad (model won't know where to start) or too narrow (over-constrains the response)? |

**Output format:**

```
## Prompt Review

**Original:**
> [quoted original prompt]

**Analysis:**
- Clarity: [finding]
- Specificity: [finding]
- Token efficiency: [finding]
- Missing context: [finding]
- Scope: [finding]

**Rewritten:**
[optimized prompt]

**What changed:**
- [change 1]
- [change 2]
- [change 3 if needed]
```

---

## Deep Mode (`--deep`)

Ask three questions one at a time. Wait for each answer before asking the next.

If the user has already answered any of these questions in their initial message, skip those questions and proceed with the information provided.

**Question 1:**
> "What model or tool will this prompt be sent to? (e.g., Claude, ChatGPT, Midjourney, a system prompt, etc.)"

**Question 2:**
> "What should the model produce — what does a great response look like?"

**Question 3:**
> "Any constraints I should know about? (length, tone, output format, things to avoid)"

Once you have all three answers, run the same five-dimension analysis as Default mode, framing each finding in context of the stated goal and constraints. Use the same output format as Default mode.

---

## Variants Mode (`--variants`)

Run the five-dimension analysis internally. Do not output any analysis section, summary of findings, or intermediate reasoning — go directly to the three variants.

**Output format:**

```
## Prompt Variants

**Original:**
> [quoted original prompt]

**Variant 1 — Concise**
[Minimized version: strip filler, collapse redundancy, every word earns its place]

*Best for:* [one sentence on when this variant works best]

---

**Variant 2 — Detailed**
[Comprehensive version: explicit about format, audience, constraints, and examples — nothing left implicit]

*Best for:* [one sentence on when this variant works best]

---

**Variant 3 — Balanced** ⭐ Recommended
[Middle ground: clear and specific without being exhaustive]

*Best for:* [one sentence on when this variant works best]
```

Label Variant 3 as recommended. If the original prompt is clearly for an API or cost-sensitive context (e.g., a system prompt with explicit token constraints), label Variant 1 as recommended instead.

---

## Key Principles

- **Never rewrite for rewriting's sake.** If the original prompt is already clear and specific, say so. A good review sometimes concludes "this prompt is solid — minor tweak only."
- **Preserve intent.** The refined prompt should do what the original intended, just more effectively.
- **Flag model-specific conventions.** Midjourney prompts differ from Claude system prompts — when relevant, add a note after the **Rewritten** section explaining any model-specific choices made.
- **Token efficiency ≠ shorter is always better.** A longer prompt is correct when added words prevent ambiguity or reduce back-and-forth.
