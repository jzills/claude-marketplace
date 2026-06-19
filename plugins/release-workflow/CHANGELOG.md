# Changelog

All notable changes to this plugin will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

<!-- Next release entries go here -->

## [1.1.0] - 2026-05-19T00:00:00Z

### Changed
- `create-release`: Step 2 now detects the branching strategy via `git ls-remote --heads origin develop` and delegates to `branching-strategy:gitflow` or `branching-strategy:trunk` to determine the correct base branch — replaces the hardcoded `git checkout main`
- `create-release`: Step 4 now resolves the default branch dynamically via `gh repo view --json defaultBranchRef` before opening the release PR, rather than assuming `main`

## [1.0.0] - 2026-05-19T00:00:00Z

### Added
- `create-release`: initial skill — orchestrates version detection, release branch creation, CI monitoring via `monitor-pipeline`, and PR creation via `github-pr`
- `monitor-pipeline`: initial skill — watches a GitHub Actions CI run on a specified branch and reports pass/fail for use by calling skills
