---
name: scaffold-integration-project
description: >
  Use this skill when the user wants to create a new .NET integration test project from scratch.
  Trigger on: "create integration test project", "scaffold integration tests", "set up integration test project",
  "add integration tests to my solution", "create a test project for integration tests",
  "I don't have an integration test project yet", "bootstrap integration test infrastructure".
version: 1.0.0
---

# Scaffold Integration Project

## Overview

Creates a complete .NET integration test project from scratch — the `.csproj`, base classes, and container
configuration. Orchestrates the `setup-test-infrastructure` skill to detect and wire up service dependencies.

## Step 1 — Discover the source project

Look for `.csproj` files in the repository that are NOT test projects (i.e., do not contain `<IsTestProject>true</IsTestProject>`
or have names ending in `.Tests`, `.UnitTests`, or `.IntegrationTests`).

If exactly one candidate is found, confirm it with the user:

> "Found source project at `{path}`. Is this the project you want to test?"

If multiple candidates are found, list them and ask the user to select one.
If no candidates are found, ask the user to provide the path to their source `.csproj` directly.

Once the source `.csproj` is identified, read it and extract:

- `<TargetFramework>` — used to pin the test project's framework
- `<RootNamespace>` or `<AssemblyName>` (fall back to the filename without extension) — used to derive the test namespace
- All `<PackageReference>` entries — passed as context to `setup-test-infrastructure`

## Step 2 — Determine the test project location

Apply the default naming convention:

| Source path | Test project path |
|---|---|
| `src/MyApi/MyApi.csproj` | `tests/MyApi.IntegrationTests/MyApi.IntegrationTests.csproj` |
| `MyApi/MyApi.csproj` | `tests/MyApi.IntegrationTests/MyApi.IntegrationTests.csproj` |

Present the derived path to the user:

> "I'll create the test project at `{derived-path}`. Press Enter to confirm or provide a different path."

Use the confirmed path for all remaining steps.

## Step 3 — Create the test `.csproj`

1. Copy the template from `assets/integration-test-project.csproj`.
2. Replace `<TargetFramework>net9.0</TargetFramework>` with the framework extracted from the source project.
3. Add `<RootNamespace>{SourceAssemblyName}.IntegrationTests</RootNamespace>` inside `<PropertyGroup>`.
4. Write the file to the confirmed test project path.

## Step 4 — Set up test infrastructure

**REQUIRED SUB-SKILL:** Announce to the user:

> "Now invoking setup-test-infrastructure to configure container dependencies."

Invoke `setup-test-infrastructure` with args:
`"source project: {path-to-source-csproj}"`

The sub-skill will inspect the source project's package references, detect which services are needed
(databases, message brokers, caches, etc.), and either add Testcontainers packages to the test `.csproj`
or generate a `docker-compose.yml`. It will also generate a more complete `IntegrationTestBase` that owns
the container lifecycle and injects connection strings.

## Step 5 — Generate base classes

Create the following C# files in the test project directory.

### `CustomWebApplicationFactory.cs`

```csharp
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;

namespace {RootNamespace};

public class CustomWebApplicationFactory<TProgram> : WebApplicationFactory<TProgram>
    where TProgram : class
{
    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.UseEnvironment("Testing");
    }
}
```

> **Note:** The `ConfigureWebHost` override is intentionally minimal. The `setup-test-infrastructure`
> skill (Step 4) will have already generated a more complete `IntegrationTestBase` that owns container
> lifecycle and injects connection strings — do not duplicate that logic here.

Replace `{RootNamespace}` with `{SourceAssemblyName}.IntegrationTests`.

### `GlobalUsings.cs`

```csharp
global using FluentAssertions;
global using NUnit.Framework;
global using System.Net;
global using System.Net.Http;
global using System.Net.Http.Json;
```

## Step 6 — Update the solution file (if present)

Search for a `.sln` file in the repository root and its immediate parent directories.

If one is found, add the new test project to the solution:

```bash
dotnet sln {path-to-sln} add {path-to-test-csproj}
```

Report the result. If no `.sln` file is found, skip this step silently.

## Step 7 — Verify

Run restore to confirm the project loads cleanly:

```bash
dotnet restore {path-to-test-csproj}
```

Report success or surface any package resolution errors for the user to address.

## Completion

Tell the user:

> "Integration test project scaffolded at `{test-project-path}`. Run the `write-integration-tests` skill to generate your first test file."
