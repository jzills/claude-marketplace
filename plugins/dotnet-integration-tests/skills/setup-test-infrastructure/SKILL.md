---
name: setup-test-infrastructure
description: >
  Use this skill when the user wants to configure containers or Docker infrastructure for .NET integration tests.
  Trigger on: "set up containers for my tests", "configure docker for integration tests", "add testcontainers",
  "generate docker-compose for my tests", "set up test infrastructure", "what containers do I need",
  "configure test dependencies". Also invoked as a sub-skill when scaffolding a new integration test project.
version: 1.0.0
---

# .NET Integration Test Infrastructure Setup

You are configuring container-based infrastructure for a .NET integration test project.
Your job is to detect which services the source project depends on, then generate either
Testcontainers C# fixture classes or a `docker-compose.yml` — whichever is appropriate.

---

## Step 1 — Locate the Source Project

Ask the user for the path to their **source** project's `.csproj` file (the project under test, not the test project itself).
If the conversation already makes the path obvious (e.g. the user just showed you a file from it), use that path without asking.

Read the `.csproj` file and extract every `<PackageReference Include="...">` entry.

---

## Step 2 — Detect Required Services

Compare each package name against the lookup table in `references/package-service-map.md`.

For each matched package, record:
- The **service name** (e.g. PostgreSQL, Redis)
- The **Docker image** to use
- The **Testcontainers NuGet package** (e.g. `Testcontainers.PostgreSql`)
- The **Testcontainers builder class** (e.g. `PostgreSqlBuilder`)

If no packages match any row in the table, tell the user:
> "I didn't detect any known service dependencies in your `.csproj`. If your project connects to a service not listed here, let me know which one and I'll generate the configuration manually."

---

## Step 3 — Choose an Approach

Scan the same `.csproj` for any `<PackageReference>` whose `Include` value starts with `Testcontainers.`.

- **If one or more `Testcontainers.*` packages are already referenced** — use the **Testcontainers approach** (Step 4A).
- **If no `Testcontainers.*` packages are referenced** — use the **docker-compose approach** (Step 4B).

---

## Step 4A — Testcontainers Approach

Generate a C# fixture class for each detected service.

Follow the patterns in `references/testcontainers-patterns.md` precisely:

- Each fixture implements `IAsyncLifetime`.
- Containers start in `InitializeAsync` and are disposed in `DisposeAsync`.
- When there are **multiple services**, start them in parallel with `Task.WhenAll` inside a single combined fixture.
- Expose a `GetConnectionString()` (or equivalent) property so test classes can consume it without touching the container directly.
- Show the user how to inject the runtime connection string into `WebApplicationFactory` using the override pattern from the patterns reference.
- Include a `IntegrationTestBase` base class so individual test fixtures inherit lifecycle management without re-declaring it.

After generating the code, tell the user which NuGet packages to add to their test project:

```bash
dotnet add package Testcontainers.<Service> --version <latest>
```

List one command per detected service.

---

## Step 4B — Docker Compose Approach

Generate a single `docker-compose.yml` file containing a service block for each detected dependency.

Use the snippets from `references/docker-compose-templates.md`:
- Start with the standard compose header from the templates reference.
- Append the service snippet for each detected service.
- Place the file at the root of the **test project directory** (ask the user for this path if you don't already have it).

After generating the file, also tell the user:
> "If you'd prefer programmatic container management instead of docker-compose, add these NuGet packages to your test project and re-run this skill:"

List the Testcontainers NuGet package for each detected service, one per line.

---

## Step 5 — Confirm Output

After generating files, summarize what was created:

- List each file path written
- List each service detected and the approach used for it
- State any services that were detected but are **not** in the package map (so the user knows they need manual configuration)

---

## Notes

- Always use the **test project directory** as the output location for generated files, not the source project directory.
- Do not modify the source project's `.csproj` — only read it.
- If the user is running this as part of a larger scaffolding workflow (invoked from `scaffold-integration-project`), skip asking for paths — they will be provided as arguments in the invocation context.
- Prefer Alpine-based images where available — they are significantly smaller and faster to pull in CI.

---

## Using This Skill From Other Skills

When another skill needs to set up test infrastructure as part of a larger workflow, add this to the calling skill's SKILL.md:

```
**REQUIRED SUB-SKILL:** Invoke `setup-test-infrastructure` with args:
`"source csproj: <path-to-source.csproj>, test project dir: <path-to-test-project/>"`

The generated fixture files and/or docker-compose.yml will be available for subsequent steps.
```
