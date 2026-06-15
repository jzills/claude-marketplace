<div align="center">
  <img src="assets/banner.svg" alt="claude-marketplace — Skills, workflows, and tools for Claude Code." width="800"/>
</div>

# claude-marketplace

A Claude Code plugin marketplace (`jzills`) with plugins for git workflows, .NET testing, and skill management.

## Add this marketplace

```shell
/plugin marketplace add jzills/claude-marketplace
```

## Available plugins

| Plugin | Description |
|--------|-------------|
| `conventional-commits` | Enforces Conventional Commits format and branch naming when creating branches or committing |
| `dotnet-unit-tests` | Writes production-quality NUnit + Moq unit tests for C# / .NET code |
| `github-pr` | Creates GitHub pull requests using the gh CLI with auto-generated titles and descriptions |
| `skill-changelog` | Maintains a versioned CHANGELOG.md inside any skill directory being created or modified |
| `auto-rewind` | Detects test failures and guides a `/rewind` to a clean checkpoint instead of fixing forward |
| `shimmering-forest` | CVSS v3.1-inspired risk auditor that scores every tool call and blocks or warns based on configurable thresholds |

## Install a plugin

```shell
/plugin install conventional-commits@jzills
/plugin install dotnet-unit-tests@jzills
/plugin install github-pr@jzills
/plugin install skill-changelog@jzills
/plugin install auto-rewind@jzills
/plugin install shimmering-forest@jzills
```

## Update

```shell
/plugin marketplace update jzills
```

## Validate

```shell
claude plugin validate .
```
