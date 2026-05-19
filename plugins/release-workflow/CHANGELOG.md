# Changelog

All notable changes to this plugin will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

<!-- Next release entries go here -->

## [1.0.0] - 2026-05-19T00:00:00Z

### Added
- `create-release`: initial skill — orchestrates version detection, release branch creation, CI monitoring via `monitor-pipeline`, and PR creation via `github-pr`
- `monitor-pipeline`: initial skill — watches a GitHub Actions CI run on a specified branch and reports pass/fail for use by calling skills
