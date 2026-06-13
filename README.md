<div align="center">
  <img src="assets/banner.svg" alt="claude-marketplace — Skills, workflows, and tools for Claude Code." width="800"/>
</div>

<br>

<div align="center">

A Claude Code plugin marketplace with skills for git workflows, code quality, safety, and more.

[![PR Validation](https://github.com/jzills/claude-marketplace/actions/workflows/pr.yml/badge.svg)](https://github.com/jzills/claude-marketplace/actions/workflows/pr.yml)
[![CodeQL](https://github.com/jzills/claude-marketplace/actions/workflows/codeql.yml/badge.svg)](https://github.com/jzills/claude-marketplace/actions/workflows/codeql.yml)
![Plugins](https://img.shields.io/badge/plugins-13-D97757)

</div>

## Getting started

Add this marketplace to Claude Code:

```shell
/plugin marketplace add jzills/claude-marketplace
```

Then install any plugin you need — see the full list below.

## Plugins

### Git & Workflow

| Plugin | Description | Install |
|--------|-------------|---------|
| `conventional-commits` | Enforces Conventional Commits format and branch naming when creating branches or committing | `/plugin install conventional-commits@jzills` |
| `github-pr` | Creates GitHub pull requests using the gh CLI with auto-generated titles and descriptions | `/plugin install github-pr@jzills` |
| `branching-strategy` | Describes GitFlow and trunk-based branching conventions; referenced by release-workflow, conventional-commits, and github-pr to determine base branches and merge targets | `/plugin install branching-strategy@jzills` |
| `semantic-versioning` | Determines the next semantic version number by inspecting git tags, release branches, and commit history | `/plugin install semantic-versioning@jzills` |
| `release-workflow` | Orchestrates a full release workflow: version detection, release branch, CI monitoring, and PR creation | `/plugin install release-workflow@jzills` |

### Testing

| Plugin | Description | Install |
|--------|-------------|---------|
| `dotnet-unit-tests` | Writes production-quality NUnit + Moq unit tests for C# / .NET code | `/plugin install dotnet-unit-tests@jzills` |
| `dotnet-integration-tests` | Writes, scaffolds, and configures infrastructure for production-quality NUnit integration tests for C# / .NET code | `/plugin install dotnet-integration-tests@jzills` |
| `python-pep8` | Reviews Python code for PEP 8 violations, auto-fixes style issues, writes PEP 8-compliant code, and explains style rules on demand | `/plugin install python-pep8@jzills` |

### Safety & Auditing

| Plugin | Description | Install |
|--------|-------------|---------|
| `shimmering-forest` | CVSS-based risk auditor that scores every tool call and blocks or warns based on configurable thresholds; defaults to CVSS 4.0 with CVSS 3.1 support | `/plugin install shimmering-forest@jzills` |

### Skill Management

| Plugin | Description | Install |
|--------|-------------|---------|
| `skill-changelog` | Maintains a versioned CHANGELOG.md inside any skill directory being created or modified | `/plugin install skill-changelog@jzills` |
| `auto-rewind` | Detects test failures and guides a `/rewind` to a clean checkpoint instead of fixing forward | `/plugin install auto-rewind@jzills` |
| `prompt-reviewer` | Reviews and refines prompts for clarity, specificity, token efficiency, and missing context. Supports default single-pass review, `--deep` guided dialogue, and `--variants` mode | `/plugin install prompt-reviewer@jzills` |

### Automation

| Plugin | Description | Install |
|--------|-------------|---------|
| `hermes-tweet` | Installs and operates Hermes Tweet for X/Twitter workflows in Hermes Agent | `/plugin install hermes-tweet@jzills` |

## Maintenance

**Update all plugins:**

```shell
/plugin marketplace update jzills
```

**Validate plugin structure:**

```shell
claude plugin validate .
```
