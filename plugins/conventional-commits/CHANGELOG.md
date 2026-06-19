# Changelog

All notable changes to this skill will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

<!-- Next release entries go here -->

## [1.1.0] - 2026-05-19T00:00:00Z

### Changed
- Step 3 now detects the branching strategy before creating a new branch: if `git ls-remote --heads origin develop` returns output, invokes `branching-strategy:gitflow` and cuts the branch from `develop`; otherwise invokes `branching-strategy:trunk` and cuts from the resolved trunk branch — ensures feature branches are created from the correct base in both GitFlow and trunk-based repos

## [1.0.0] - 2026-05-18T00:00:00Z

### Added
- Initial skill creation enforcing Conventional Commits message format and branch naming conventions
- Branch naming guide: `type/short-description` pattern with full type reference table
- Commit message format: `type(scope): description` with optional body and footer
- Step-by-step workflow: understand change → determine type → create branch → stage and commit → push
- Ambiguity handling guidance for unrelated unstaged changes and already-named branches
