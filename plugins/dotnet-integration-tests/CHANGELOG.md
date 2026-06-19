# Changelog

All notable changes to this skill will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

<!-- Next release entries go here -->

## [1.2.0] - 2026-05-19T12:00:00Z

### Fixed
- `write-integration-tests`: Pattern 4 updated from legacy RabbitMQ.Client v5/v6 API (`IModel`, `CreateModel()`, `BasicPublish()`) to v7 async API (`IChannel`, `CreateChannelAsync()`, `BasicPublishAsync()`, `BasicProperties` record initializer)
- `write-integration-tests`: Pattern 4 `[OneTimeSetUp]` conflict with `IntegrationTestBase` resolved — renamed broker setup to `SetUpBrokerFixture` with `[SetUp]` so derived classes don't redeclare `[OneTimeSetUp]`; `[TearDown]` now disposes broker resources and cleans DB rows
- `write-integration-tests`: Pattern 2 `[SetUp]` changed from sync `void` to `async Task` for consistency with async test practices; prerequisite note about `IsTestData` field added before the code block
- `write-integration-tests`: Pattern 4 lambda parameter in `WaitUntilAsync` call renamed from `response` to `res` to avoid shadowing the outer `response` variable
- `write-integration-tests`: Pattern 3 Strategy A code block now includes `using MyProject.Api.Models;` so the `Product` reference compiles
- `write-integration-tests`: Pattern 4 now includes `using System.Net;` and uses unqualified `HttpStatusCode.OK` consistently with Pattern 1
- `write-integration-tests`: SKILL.md `[OneTimeSetUp]` restriction clarified — the restriction applies only to container lifecycle; per-fixture `[SetUp]`/`[TearDown]` in derived classes is explicitly allowed
- `write-integration-tests`: SKILL.md "Infrastructure Sub-skill" section relabelled as "Step 4" so the flow reads Step 4 → Step 4A → Step 4B without an unnumbered gap

## [1.1.0] - 2026-05-19T00:00:00Z

### Added
- `write-integration-tests`: initial skill — writes production-quality NUnit integration tests for ASP.NET Core controllers, EF Core repositories, and message consumers; performs a pre-flight check for an existing test project and container approach (Testcontainers or docker-compose) before generating tests; invokes `setup-test-infrastructure` as a sub-skill when no container fixture exists
- `write-integration-tests`: `references/integration-test-patterns.md` — four concrete C# patterns covering WebApplicationFactory endpoint tests, EF Core repository tests with scoped DbContext, data seeding and cleanup (transaction-rollback and sentinel-field strategies), and message-consumer tests with a `WaitUntilAsync` polling helper

## [1.0.0] - 2026-05-19T00:00:00Z

### Added
- `setup-test-infrastructure`: initial skill — detects service dependencies from `.csproj` package references, then generates either Testcontainers C# fixture classes or a `docker-compose.yml` depending on whether Testcontainers packages are already present
- `setup-test-infrastructure`: `references/package-service-map.md` — lookup table mapping NuGet package patterns to Docker images, Testcontainers NuGet packages, and builder class names for PostgreSQL, SQL Server, RabbitMQ, Redis, MongoDB, Kafka, and Elasticsearch
- `setup-test-infrastructure`: `references/testcontainers-patterns.md` — concrete C# patterns for single-container fixtures, multi-container parallel startup, WebApplicationFactory integration, and NUnit inheritance-based test base classes using Testcontainers .NET v3.x
- `setup-test-infrastructure`: `references/docker-compose-templates.md` — ready-to-use `docker-compose.yml` snippets for all supported services including health checks, credentials, and a complete multi-service example
