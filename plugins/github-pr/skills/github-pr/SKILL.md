---
name: github-pr
description: Creates GitHub pull requests for the authenticated user using the gh CLI. Use this skill whenever the user wants to open a PR, submit their work for review, push a branch and create a pull request, or says anything like "make a PR", "open a pull request", "create a PR", "submit for review", "push this up and PR it", or "ready to merge". Also trigger when the user has finished a feature or fix and mentions reviewing, merging, or sharing their changes — even if they don't say "pull request" explicitly. This skill handles branch detection, base branch selection, title/description generation from git history, and draft PR mode.
---

# GitHub Pull Request Creator

You are helping the user open a pull request on GitHub. Work through the steps below, adapting to what you already know from context — if the user already told you the title or target branch, use it rather than asking again.

## Prerequisites

Verify `gh` is installed and authenticated before doing anything else:

```bash
gh auth status
```

If not authenticated, tell the user: "You need to authenticate first — run `gh auth login` in your terminal. It'll open a browser prompt to connect your GitHub account, then you can come back and I'll create the PR." Stop there.

## Step 1: Gather branch context

Run these together to understand the current state:

```bash
git branch --show-current
git remote get-url origin
gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'
git status --short
```

From this, determine:
- **Current branch** — this becomes the PR's head branch
- **Base branch** — use the GitHub default branch returned by `gh repo view` above. Only fall back to `origin/HEAD` detection if the `gh` command fails, and only ask the user if both methods fail.
- **Commit summary** — all commits since the branch diverged from base:

```bash
git log --oneline $(git merge-base HEAD origin/$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name') 2>/dev/null)..HEAD 2>/dev/null | head -20
```

If there are uncommitted changes, mention them and ask if the user wants to commit them first before opening the PR.

## Step 2: Ensure the branch is pushed

Check whether the current branch has a remote tracking branch:

```bash
git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>&1
```

If there's no upstream (you'll see an error like "no upstream configured"), push the branch:

```bash
git push -u origin HEAD
```

If the branch is behind the remote, tell the user and ask how they want to proceed before continuing.

## Step 3: Generate a PR title and description

Use the commit history to draft both. The goal is something a reviewer would find useful — clear about what changed and why.

**Title generation rules:**
- If there's only one commit, use it (cleaned up) as the title
- If there are multiple commits, synthesize a title that captures the overall change (e.g., "Add OAuth2 login flow" not "various auth changes")
- Keep it under 72 characters
- Use present tense imperative ("Add", "Fix", "Remove", not "Added", "Fixed", "Removed")

**Description: check for a repo template first**

```bash
test -f .github/PULL_REQUEST_TEMPLATE.md && cat .github/PULL_REQUEST_TEMPLATE.md
```

- If the file exists, read it and use it as the body structure. Fill in every placeholder section using the commit history and changed files — do not leave placeholder text unfilled.
- If the file does not exist, fall back to the built-in template below:

```
## Summary
<1–3 bullets describing what changed and why>

## Changes
<bullet list of the significant commits or files changed, if non-obvious>

## Test plan
<how to verify this works — fill in if you can infer it, otherwise leave a placeholder>
```

Generate a draft and show it to the user before creating the PR. Ask: "Does this look right, or would you like to adjust the title or description?"

If the user says it's fine or makes only small edits, proceed. If they want a full rewrite, let them provide it.

## Step 4: Ask about draft mode

Ask once: "Should this be a regular PR or a draft?" 

If the user doesn't answer or says "regular", open a regular PR. If they say "draft" or "not ready for review", add `--draft`.

Skip this question if context already makes it clear (e.g., user said "draft PR" upfront).

## Step 5: Create the PR

```bash
gh pr create \
  --base <base-branch> \
  --head <current-branch> \
  --title "<title>" \
  --body "<description>" \
  [--draft]
```

After creating, output:
- The PR URL (so the user can click it)
- A one-line summary: branch → base, number of commits, draft or not

## Edge cases to handle

**Detached HEAD**: Tell the user they're not on a named branch and ask them to check out one before continuing.

**Already-open PR**: `gh pr view` will show it. Tell the user a PR already exists and show the URL — offer to update the description if they want.

**No commits ahead of base**: Tell the user the branch has no new commits compared to `<base>` and ask if they're on the right branch.

**Push rejected**: Show the error message verbatim and suggest they pull first or check if the branch has diverged.

**No remote configured**: Tell the user there's no git remote and they'll need to set one up before creating a PR.

**Private/no-access repo**: The `gh` error will explain it. Surface it clearly and don't retry silently.

## Co-authorship

Never add `Co-Authored-By: Claude ...` (or any variant) to commit messages or PR bodies. The user does not want Claude attributed in commits or PRs.

## Tone

Be direct and efficient. The user is trying to ship something — don't ask unnecessary questions or add ceremony. If something is obvious from context, just do it. Surface decisions only when they genuinely require input.
