# Changelog

All notable changes to this skill will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

<!-- Next release entries go here -->

## [1.0.0] - 2026-05-19T00:00:00Z

### Added
- `setup-test-infrastructure`: initial skill — detects service dependencies from `.csproj` package references, then generates either Testcontainers C# fixture classes or a `docker-compose.yml` depending on whether Testcontainers packages are already present
- `setup-test-infrastructure`: `references/package-service-map.md` — lookup table mapping NuGet package patterns to Docker images, Testcontainers NuGet packages, and builder class names for PostgreSQL, SQL Server, RabbitMQ, Redis, MongoDB, Kafka, and Elasticsearch
- `setup-test-infrastructure`: `references/testcontainers-patterns.md` — concrete C# patterns for single-container fixtures, multi-container parallel startup, WebApplicationFactory integration, and NUnit inheritance-based test base classes using Testcontainers .NET v3.x
- `setup-test-infrastructure`: `references/docker-compose-templates.md` — ready-to-use `docker-compose.yml` snippets for all supported services including health checks, credentials, and a complete multi-service example
