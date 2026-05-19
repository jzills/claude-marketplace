# Changelog

All notable changes to this skill will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

<!-- Next release entries go here -->

## [1.0.0] - 2026-05-19T00:00:00Z

### Added
- Initial skill: determines next semantic version from git tags, release branches, and commit history
- `references/version-detection.md`: version source priority algorithm (git tags → remote release branches → 0.0.0 default)
- `references/bump-inference.md`: conventional commits and CHANGELOG-based bump inference tables with precedence rules
