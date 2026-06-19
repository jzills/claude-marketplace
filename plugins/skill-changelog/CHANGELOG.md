# Changelog

All notable changes to this plugin will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

<!-- Next release entries go here -->

## [1.1.0] - 2026-05-19T00:00:00Z

### Added
- `skill-changelog`: Location Detection algorithm — resolves symlinks with `readlink -f`, then walks up the tree looking for `.claude-plugin/plugin.json` to determine whether CHANGELOG.md belongs at the plugin root or next to SKILL.md
- `skill-changelog`: plugin-level entry format guidance — prefix skill name on each bullet when CHANGELOG is shared across multiple skills

### Changed
- `skill-changelog`: Standing Rule steps 1, 3, 4 updated to reference "resolved CHANGELOG location" instead of the skill directory
- `skill-changelog`: opt-in mode description updated to reflect resolved location logic
- `skill-changelog`: Behavior Reference table extended with two new rows for plugin context
