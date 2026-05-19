# Changelog

All notable changes to this skill will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

<!-- Next release entries go here -->

## [1.4.0] - 2026-04-30T00:00:00Z

### Added
- Co-authorship rule: never add `Co-Authored-By: Claude ...` to commit messages or PR bodies

## [1.3.0] - 2026-04-28T00:00:00Z

### Changed
- Base branch is now resolved via `gh repo view --json defaultBranchRef` (the GitHub default branch) instead of falling back to hardcoded `main`/`master`. The `origin/HEAD` and hardcoded fallbacks are only used if `gh repo view` fails.
- Updated the commit-log command in Step 1 to use the GitHub default branch when computing the divergence point

## [1.2.0] - 2026-04-27T22:10:00Z

### Changed
- Step 3 now checks for `.github/PULL_REQUEST_TEMPLATE.md` before generating the PR description. If the file exists, its structure is used as the body template (with all placeholders filled from commit history). Falls back to the built-in Summary/Changes/Test plan template when no repo template is present.

## [1.1.0] - 2026-04-27T21:40:00Z

### Changed
- Auth failure message now explains what `gh auth login` does and instructs the user to return afterward, making the error more actionable for first-time users

### Removed
- "The skill outputs the PR URL after creation" assertion from eval 3 in `evals/evals.json` — this assertion always failed due to eval constraints (can't run `gh pr create` in tests) and provided no signal about skill quality

## [1.0.0] - 2026-04-27T20:00:00Z

### Added
- Initial skill release
- Step-by-step PR creation workflow: auth check, branch detection, push check, title/description generation from git log, draft mode, and `gh pr create` execution
- Auto-detects base branch from `origin/HEAD`, falling back to `main` then `master`
- Generates structured PR descriptions with Summary, Changes, and Test plan sections
- Handles edge cases: detached HEAD, already-open PR, no commits ahead of base, push rejected, no remote configured
- Evaluation suite with 3 test cases covering feature PRs, draft PRs, and non-default base branches
