# Package Service Map

Use this table to map `<PackageReference>` entries from a `.csproj` to the container service they require.

Match package names using simple substring or prefix matching against the **Package Pattern** column.
A single `.csproj` may match multiple rows — generate infrastructure for each unique service detected.

| Package Pattern | Service | Docker Image | Testcontainers NuGet | Testcontainers Class |
|---|---|---|---|---|
| `Npgsql` | PostgreSQL | `postgres:16-alpine` | `Testcontainers.PostgreSql` | `PostgreSqlBuilder` |
| `Npgsql.EntityFrameworkCore.PostgreSQL` | PostgreSQL | `postgres:16-alpine` | `Testcontainers.PostgreSql` | `PostgreSqlBuilder` |
| `Microsoft.EntityFrameworkCore.Npgsql` | PostgreSQL | `postgres:16-alpine` | `Testcontainers.PostgreSql` | `PostgreSqlBuilder` |
| `Microsoft.Data.SqlClient` | SQL Server | `mcr.microsoft.com/mssql/server:2022-latest` | `Testcontainers.MsSql` | `MsSqlBuilder` |
| `Microsoft.EntityFrameworkCore.SqlServer` | SQL Server | `mcr.microsoft.com/mssql/server:2022-latest` | `Testcontainers.MsSql` | `MsSqlBuilder` |
| `System.Data.SqlClient` | SQL Server | `mcr.microsoft.com/mssql/server:2022-latest` | `Testcontainers.MsSql` | `MsSqlBuilder` |
| `RabbitMQ.Client` | RabbitMQ | `rabbitmq:3-management-alpine` | `Testcontainers.RabbitMq` | `RabbitMqBuilder` |
| `MassTransit.RabbitMQ` | RabbitMQ | `rabbitmq:3-management-alpine` | `Testcontainers.RabbitMq` | `RabbitMqBuilder` |
| `StackExchange.Redis` | Redis | `redis:7-alpine` | `Testcontainers.Redis` | `RedisBuilder` |
| `Microsoft.Extensions.Caching.StackExchangeRedis` | Redis | `redis:7-alpine` | `Testcontainers.Redis` | `RedisBuilder` |
| `MongoDB.Driver` | MongoDB | `mongo:7` | `Testcontainers.MongoDb` | `MongoDbBuilder` |
| `Confluent.Kafka` | Kafka | `confluentinc/cp-kafka:latest` | `Testcontainers.Kafka` | `KafkaBuilder` |
| `MassTransit.Kafka` | Kafka | `confluentinc/cp-kafka:latest` | `Testcontainers.Kafka` | `KafkaBuilder` |
| `Elasticsearch.Net` | Elasticsearch | `docker.elastic.co/elasticsearch/elasticsearch:8.12.0` | `Testcontainers.Elasticsearch` | `ElasticsearchBuilder` |
| `NEST` | Elasticsearch | `docker.elastic.co/elasticsearch/elasticsearch:8.12.0` | `Testcontainers.Elasticsearch` | `ElasticsearchBuilder` |
| `Elastic.Clients.Elasticsearch` | Elasticsearch | `docker.elastic.co/elasticsearch/elasticsearch:8.12.0` | `Testcontainers.Elasticsearch` | `ElasticsearchBuilder` |

## Matching Rules

- Match is case-insensitive.
- A package matches a row if the `<PackageReference Include="...">` value **contains** the pattern string.
- When multiple rows map to the same **Service**, deduplicate — only generate one container/service block per service.
- Kafka requires Zookeeper in docker-compose mode. See `docker-compose-templates.md` for the combined snippet.
