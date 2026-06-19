---
name: gitflow
description: Use when the repository has been identified as using GitFlow — a remote `develop` branch exists. Provides base branches, PR targets, and merge conventions for feature, release, and hotfix branches.
---

# GitFlow Branching Conventions

## Branch Routing

| Branch type | Cut from | PR targets | Notes |
|-------------|----------|------------|-------|
| `feature/*`, `fix/*`, `chore/*`, `refactor/*`, `docs/*`, `test/*`, `ci/*`, `perf/*`, `style/*` | `develop` | `develop` | Day-to-day work |
| `release/*` | `develop` | `main` (default branch) | Back-merge (`main` → `develop`) is CI/CD's responsibility post-merge |
| `hotfix/*` | `main` (default branch) | `main` (default branch) | Critical production fixes; CI/CD back-merges to `develop` |

## Creating a Branch

Always pull the base branch before cutting:

```bash
git checkout <base-branch> && git pull origin <base-branch>
git checkout -b <new-branch>
git push -u origin <new-branch>
```

## Resolving the Default Branch

GitFlow repos may use `main` or `master` as the production branch. Always resolve dynamically — never hardcode:

```bash
gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'
```

Use this value wherever `main` appears in the table above.

## Detection Signal

This strategy was identified because `git ls-remote --heads origin develop` returned output. If that is no longer true, switch to `branching-strategy:trunk`.
