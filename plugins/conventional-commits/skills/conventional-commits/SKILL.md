---
name: conventional-commits
description: Enforces Conventional Commits message format and branch naming conventions when the user wants to create a branch, make a commit, commit and push, or any combination of git branching/committing tasks. Trigger this skill whenever the user says things like "create a branch", "make a commit", "commit my changes", "commit and push", "create a branch and commit", "branch off and commit", "push this up", "commit everything", "stage and commit", or any variant involving git branch creation or committing. Also trigger when the user describes a change they made and wants it committed, even if they don't use the exact words "commit" or "branch". This skill ensures branch names follow the type/description pattern and commit messages follow the type(scope): description format.
---

# Conventional Commits & Branch Naming

Help the user create well-structured git branches and commit messages following the Conventional Commits specification. The goal is consistent, readable git history that tools (changelogs, semantic versioning) can parse automatically.

## Commit Types

Pick the type that best matches the nature of the change:

| Type | When to use |
|------|-------------|
| `feat` | A new feature or capability |
| `fix` | A bug fix |
| `docs` | Documentation only changes |
| `style` | Formatting, whitespace — no logic change |
| `refactor` | Code restructuring without adding features or fixing bugs |
| `test` | Adding or correcting tests |
| `chore` | Build process, tooling, dependency updates, housekeeping |
| `ci` | CI/CD configuration changes |
| `perf` | Performance improvements |

## Branch Naming

Format: `type/short-description`

- Use the same type prefix as the commit
- Keep the description short (2–4 words), lowercase, hyphen-separated
- No ticket numbers unless the user specifically asks

**Examples:**
- `feat/user-authentication`
- `fix/null-pointer-login`
- `chore/update-dependencies`
- `refactor/extract-payment-service`
- `docs/api-usage-guide`

## Commit Message Format

```
type(scope): short description

[optional body]

[optional footer]
```

- **type**: one of the types above
- **scope**: optional, the area of the codebase affected (e.g. `auth`, `api`, `ui`) — omit if it's unclear or too broad
- **short description**: imperative mood, lowercase, no period, under 72 chars (e.g. "add login endpoint", not "Added login endpoint" or "adds login endpoint")
- **body**: optional, explain *why* not *what* — only include if the short description isn't enough
- **footer**: optional, e.g. `BREAKING CHANGE: ...` or `Closes #123`

**Examples:**
- `feat(auth): add JWT-based login endpoint`
- `fix(cart): prevent duplicate item insertion`
- `chore: upgrade eslint to v9`
- `refactor(db): extract repository layer from controllers`
- `docs(api): add rate limiting documentation`

## Workflow

### Step 1: Understand the change

If the user hasn't described what they changed, ask one brief question: "What did you change?" Don't ask multiple questions at once.

If the change is already clear from context, skip straight to Step 2.

### Step 2: Determine type and scope

Infer the type and scope from the description. If it's genuinely ambiguous between two types, briefly note both options and pick the more specific one — don't ask unless it really matters.

### Step 3: Create the branch (if requested)

Check the current branch first:

```bash
git branch --show-current
```

If the user wants a new branch (they said "create a branch", "branch off", etc.), determine the correct base branch before creating it:

```bash
git ls-remote --heads origin develop
```

- Non-empty → **REQUIRED SUB-SKILL:** Invoke `branching-strategy:gitflow` to confirm the base branch (typically `develop` for feature branches).
- Empty → **REQUIRED SUB-SKILL:** Invoke `branching-strategy:trunk` to resolve the trunk branch name.

Create the branch from the resolved base branch:

```bash
git checkout <base-branch> && git pull origin <base-branch>
git checkout -b type/short-description
```

If they're already on an appropriately named branch, skip this.

### Step 4: Stage and commit

Check what's unstaged:

```bash
git status --short
```

Stage everything relevant (or what the user specified):

```bash
git add -A
```

Or if the user specified files:

```bash
git add path/to/file
```

Commit with a conventional message:

```bash
git commit -m "type(scope): description"
```

For multi-line commits (body needed), use a heredoc:

```bash
git commit -m "$(cat <<'EOF'
type(scope): short description

Longer explanation of why this change was made.
EOF
)"
```

### Step 5: Push (if requested)

If the user asked to push, push the branch:

```bash
git push -u origin type/short-description
```

If they're on an existing tracked branch:

```bash
git push
```

## Handling Ambiguity

- If the user's description maps clearly to a type, just use it — don't ask for confirmation unless something is genuinely unclear
- If there are unstaged changes unrelated to what the user described, note them and ask before staging everything
- If the user is already on a well-named branch that matches convention, don't rename it — just commit

## What to show the user

After completing the workflow, show:
1. The branch name used (or created)
2. The exact commit message used
3. Whether the push succeeded (if applicable)

Keep it brief — one short block is enough. The user can see the git output; they don't need it narrated back to them.
