# Version Detection

Detect the current version using this priority order.

## 1. Git Tags (primary)

Run:
```bash
git tag --list
```

Filter for SemVer-shaped tags matching `vX.Y.Z` or `X.Y.Z`. Sort by version (not lexicographic) and take the highest.

**Notes:**
- Strip leading `v` before arithmetic; re-add it consistently in the final report
- Prefer stable releases over pre-release tags (e.g., `v1.0.0` beats `v1.0.0-rc.1`)
- If no tags match the pattern, proceed to step 2

## 2. Remote Release Branches (fallback)

If no version tags exist, run:
```bash
git ls-remote --heads origin
```

Filter branch names matching `release/vX.Y.Z` or `release/X.Y.Z`. Extract the version numbers, sort by version, take the highest.

## 3. Default

If neither tags nor release branches yield a version, use `0.0.0`.
