# Bump Inference

## Priority

1. **Conventional commits** (primary) — inspect `git log <version>..HEAD`
2. **CHANGELOG.md Unreleased section** (fallback) — only if zero conventional commits found in the range

## Conventional Commits Decision Table

| Evidence in git log | Bump |
|---|---|
| Any commit with `BREAKING CHANGE:` footer | major |
| Any commit type ending in `!` (e.g. `feat!:`, `fix!:`) | major |
| Any `feat:` commit | minor |
| Only `fix:`, `perf:`, `refactor:`, `docs:`, `chore:`, `style:`, `test:` | patch |
| No conventional commits found | → use CHANGELOG fallback |

## CHANGELOG Fallback Decision Table

| Sections present in `## [Unreleased]` | Bump |
|---|---|
| `### Removed` present | major |
| `### Added` or `### Changed` present (no `### Removed`) | minor |
| Only `### Fixed` | patch |
| No Unreleased section or empty | → ask user |

## Precedence Rules

- Always use the **highest** bump found across all commits (major > minor > patch)
- Conventional commits take priority over CHANGELOG — fall back only if zero conventional commits exist in the range
- If both sources are inconclusive, prompt: "I couldn't determine the bump type automatically. Is this a major, minor, or patch release?"
