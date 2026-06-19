---
name: trunk
description: Use when the repository has been identified as trunk-based — no remote `develop` branch exists. Provides base branches and PR targets for all branch types.
---

# Trunk-Based Branching Conventions

## Branch Routing

| Branch type | Cut from | PR targets |
|-------------|----------|------------|
| All branches (`feature/*`, `fix/*`, `release/*`, `hotfix/*`, etc.) | trunk | trunk |

All work flows into a single trunk branch. Releases are cut as short-lived branches off trunk and PR back into trunk.

## Resolving the Trunk Branch Name

Never hardcode `main`. Resolve dynamically — the trunk may be `main`, `master`, or a custom name:

```bash
gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'
```

## Creating a Branch

```bash
trunk=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')
git checkout "$trunk" && git pull origin "$trunk"
git checkout -b <new-branch>
git push -u origin <new-branch>
```

## Detection Signal

This strategy was identified because `git ls-remote --heads origin develop` returned no output. If a `develop` branch is later added, switch to `branching-strategy:gitflow`.
