# Testcontainers Patterns for NUnit

All patterns use **Testcontainers .NET v3.x** and **NUnit**. Copy and adapt as needed.

---

## 1. Single Container Fixture

One container per fixture, started once for the entire test class using `[OneTimeSetUp]` / `[OneTimeTearDown]`.

```csharp
using NUnit.Framework;
using Testcontainers.PostgreSql;

[TestFixture]
public class PostgresFixture : IAsyncLifetime
{
    private readonly PostgreSqlContainer _postgres = new PostgreSqlBuilder()
        .WithImage("postgres:16-alpine")
        .WithDatabase("testdb")
        .WithUsername("testuser")
        .WithPassword("testpassword")
        .Build();

    public async Task InitializeAsync()
    {
        await _postgres.StartAsync();
    }

    public async Task DisposeAsync()
    {
        await _postgres.DisposeAsync();
    }

    public string ConnectionString => _postgres.GetConnectionString();
}
```

---

## 2. Multiple Containers in One Fixture

Start all containers in parallel to keep test suite startup time low.

```csharp
using NUnit.Framework;
using Testcontainers.PostgreSql;
using Testcontainers.Redis;
using Testcontainers.RabbitMq;

public class InfrastructureFixture : IAsyncLifetime
{
    private readonly PostgreSqlContainer _postgres = new PostgreSqlBuilder()
        .WithImage("postgres:16-alpine")
        .Build();

    private readonly RedisContainer _redis = new RedisBuilder()
        .WithImage("redis:7-alpine")
        .Build();

    private readonly RabbitMqContainer _rabbitMq = new RabbitMqBuilder()
        .WithImage("rabbitmq:3-management-alpine")
        .Build();

    public async Task InitializeAsync()
    {
        await Task.WhenAll(
            _postgres.StartAsync(),
            _redis.StartAsync(),
            _rabbitMq.StartAsync()
        );
    }

    public async Task DisposeAsync()
    {
        await Task.WhenAll(
            _postgres.DisposeAsync().AsTask(),
            _redis.DisposeAsync().AsTask(),
            _rabbitMq.DisposeAsync().AsTask()
        );
    }

    public string PostgresConnectionString => _postgres.GetConnectionString();
    public string RedisConnectionString    => _redis.GetConnectionString();
    public string RabbitMqConnectionString => _rabbitMq.GetConnectionString();
}
```

---

## 3. Injecting Container Connection Strings into WebApplicationFactory

Override `ConfigureWebHost` to swap out the real connection string with the container's runtime value.
This pattern works for any service — substitute the configuration key and connection string accordingly.

```csharp
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Microsoft.EntityFrameworkCore;

public class IntegrationWebApplicationFactory : WebApplicationFactory<Program>
{
    private readonly string _postgresConnectionString;

    public IntegrationWebApplicationFactory(string postgresConnectionString)
    {
        _postgresConnectionString = postgresConnectionString;
    }

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureServices(services =>
        {
            // Remove the real DbContext registration
            services.RemoveAll<DbContextOptions<AppDbContext>>();
            services.RemoveAll<AppDbContext>();

            // Register using the test container's connection string
            services.AddDbContext<AppDbContext>(options =>
                options.UseNpgsql(_postgresConnectionString));
        });
    }
}
```

For non-EF services (e.g. Redis, RabbitMQ), override `IConfiguration` directly:

```csharp
protected override void ConfigureWebHost(IWebHostBuilder builder)
{
    builder.ConfigureAppConfiguration((_, config) =>
    {
        config.AddInMemoryCollection(new Dictionary<string, string?>
        {
            ["ConnectionStrings:Redis"]   = _redisConnectionString,
            ["ConnectionStrings:RabbitMq"] = _rabbitMqConnectionString,
        });
    });
}
```

---

## 4. NUnit Fixture Inheritance Pattern

A base class that owns the container fixture and `WebApplicationFactory`.
Individual test classes inherit it and get a configured `HttpClient` with zero boilerplate.

```csharp
using NUnit.Framework;

public abstract class IntegrationTestBase
{
    protected InfrastructureFixture Infrastructure { get; private set; } = null!;
    protected IntegrationWebApplicationFactory Factory { get; private set; } = null!;
    protected HttpClient Client { get; private set; } = null!;

    [OneTimeSetUp]
    public async Task BaseOneTimeSetUp()
    {
        Infrastructure = new InfrastructureFixture();
        await Infrastructure.InitializeAsync();

        Factory = new IntegrationWebApplicationFactory(
            Infrastructure.PostgresConnectionString
        );

        Client = Factory.CreateClient();
    }

    [OneTimeTearDown]
    public async Task BaseOneTimeTearDown()
    {
        Client.Dispose();
        await Factory.DisposeAsync();
        await Infrastructure.DisposeAsync();
    }
}

// Individual test class — no lifecycle code needed
[TestFixture]
public class OrdersEndpointTests : IntegrationTestBase
{
    [Test]
    public async Task GetOrders_WhenEmpty_ReturnsEmptyList()
    {
        var response = await Client.GetAsync("/api/orders");

        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var orders = await response.Content.ReadFromJsonAsync<List<OrderDto>>();
        orders.Should().BeEmpty();
    }
}
```

---

## Container-Specific Connection String Properties

| Container Type | Property / Method |
|---|---|
| `PostgreSqlContainer` | `.GetConnectionString()` |
| `MsSqlContainer` | `.GetConnectionString()` |
| `RedisContainer` | `.GetConnectionString()` |
| `RabbitMqContainer` | `.GetConnectionString()` |
| `MongoDbContainer` | `.GetConnectionString()` |
| `KafkaContainer` | `.GetBootstrapAddress()` |
| `ElasticsearchContainer` | `.GetConnectionString()` |

---

## NuGet Package Versions (as of 2025)

```
Testcontainers                  3.x
Testcontainers.PostgreSql       3.x
Testcontainers.MsSql            3.x
Testcontainers.Redis            3.x
Testcontainers.RabbitMq         3.x
Testcontainers.MongoDb          3.x
Testcontainers.Kafka            3.x
Testcontainers.Elasticsearch    3.x
```

Always check [NuGet](https://www.nuget.org/packages?q=Testcontainers) for the latest patch version before adding packages.
