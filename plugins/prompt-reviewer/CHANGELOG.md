# Changelog

All notable changes to this skill will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

<!-- Next release entries go here -->

## [1.0.0] - 2026-06-06

### Added
- Initial release
- Default mode: single-pass 5-dimension analysis (clarity, specificity, token efficiency, missing context, scope) with one optimized rewrite
- `--deep` mode: guided 3-question dialogue to understand intent and constraints before refining
- `--variants` mode: generates three rewrites — concise, detailed, and balanced (recommended)
- Auto-suggests `--deep` for prompts longer than ~200 words or clearly multi-part system prompts
