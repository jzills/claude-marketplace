# Changelog

All notable changes to this plugin will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

<!-- Next release entries go here -->

## [1.0.0] - 2026-05-19T00:00:00Z

### Added
- `auto-rewind`: initial skill — detects test failures and guides a rewind to a clean checkpoint instead of fixing forward
- `hooks/run-tests.sh`: hook script that runs tests and emits `[AUTO-REWIND]` markers on failure to trigger the skill
