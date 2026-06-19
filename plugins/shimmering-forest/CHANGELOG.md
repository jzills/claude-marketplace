# Changelog

All notable changes to this plugin will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

<!-- Next release entries go here -->

## [1.0.0] - 2026-05-19T00:00:00Z

### Added
- `risk-audit`: initial skill — displays shimmering-forest risk auditor configuration and recent audit log entries
- `hooks/risk_auditor.py`: CVSS v3.1-inspired hook that scores every tool call and blocks or warns based on configurable severity thresholds
- `config/default-config.json`: default risk thresholds and block/warn configuration
