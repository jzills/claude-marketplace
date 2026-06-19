# Integration Test Patterns for NUnit

All patterns use **NUnit**, **Testcontainers .NET v3.x**, **FluentAssertions**, and **Microsoft.AspNetCore.Mvc.Testing**.
Copy and adapt as needed. Every pattern assumes `IntegrationTestBase` (from the `setup-test-infrastructure` skill) is available.

---

## Pattern 1: ASP.NET Core Endpoint Test with Testcontainers

A full example testing a `ProductsController` via `HttpClient` backed by a real PostgreSQL container.

```csharp
using System.Net;
using System.Net.Http.Json;
using FluentAssertions;
using Microsoft.Extensions.DependencyInjection;
using NUnit.Framework;
using MyProject.Api;
using MyProject.Api.Data;
using MyProject.Api.Models;

namespace MyProject.IntegrationTests.Endpoints;

[TestFixture]
public class ProductsEndpointTests : IntegrationTestBase
{
    // IDs seeded per test — cleaned up in TearDown
    private readonly List<Guid> _seededIds = new();

    [TearDown]
    public async Task TearDown()
    {
        if (_seededIds.Count == 0)
            return;

        using var scope = Factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        var seeded = db.Products.Where(product => _seededIds.Contains(product.Id));
        db.Products.RemoveRange(seeded);
        await db.SaveChangesAsync();
        _seededIds.Clear();
    }

    // --- happy path ---

    [Test]
    public async Task GetProduct_WhenProductExists_Returns200WithBody()
    {
        var productId = await SeedProductAsync(name: "Widget", price: 9.99m);

        var response = await Client.GetAsync($"/api/products/{productId}");

        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var body = await response.Content.ReadFromJsonAsync<ProductDto>();
        body.Should().NotBeNull();
        body!.Id.Should().Be(productId);
        body.Name.Should().Be("Widget");
        body.Price.Should().Be(9.99m);
    }

    [Test]
    public async Task CreateProduct_WhenPayloadIsValid_Returns201WithLocation()
    {
        var payload = new CreateProductRequest { Name = "Gadget", Price = 49.99m };

        var response = await Client.PostAsJsonAsync("/api/products", payload);

        response.StatusCode.Should().Be(HttpStatusCode.Created);
        response.Headers.Location.Should().NotBeNull();

        var body = await response.Content.ReadFromJsonAsync<ProductDto>();
        body.Should().NotBeNull();
        body!.Id.Should().NotBeEmpty();
        body.Name.Should().Be("Gadget");
        body.Price.Should().Be(49.99m);

        // track for cleanup
        _seededIds.Add(body.Id);
    }

    // --- not-found ---

    [Test]
    public async Task GetProduct_WhenProductDoesNotExist_Returns404()
    {
        var nonExistentId = Guid.NewGuid();

        var response = await Client.GetAsync($"/api/products/{nonExistentId}");

        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
    }

    // --- validation ---

    [Test]
    public async Task CreateProduct_WhenNameIsMissing_Returns400()
    {
        var payload = new CreateProductRequest { Name = string.Empty, Price = 9.99m };

        var response = await Client.PostAsJsonAsync("/api/products", payload);

        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
    }

    // --- authorization ---

    [Test]
    public async Task DeleteProduct_WhenUserIsUnauthenticated_Returns401()
    {
        var productId = await SeedProductAsync(name: "ToDelete", price: 1.00m);

        var response = await Client.DeleteAsync($"/api/products/{productId}");

        response.StatusCode.Should().Be(HttpStatusCode.Unauthorized);
    }

    // --- helper ---

    private async Task<Guid> SeedProductAsync(string name, decimal price)
    {
        using var scope = Factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();

        var product = new Product { Id = Guid.NewGuid(), Name = name, Price = price };
        db.Products.Add(product);
        await db.SaveChangesAsync();

        _seededIds.Add(product.Id);
        return product.Id;
    }
}
```

**Key points:**
- Inherit from `IntegrationTestBase` — `Client` and `Factory` are provided.
- Seed via `Factory.Services.CreateScope()` so you control the data precisely.
- Track seeded IDs and delete them in `[TearDown]` — never leave test data behind.
- Assert both the status code and the response body shape.

---

## Pattern 2: EF Core Repository Test with Testcontainers

A full example testing a `ProductRepository` directly against a real PostgreSQL database.

**Prerequisite:** Your entity must have an `IsTestData` bool property. If it doesn't, use Strategy B from Pattern 3 instead.

```csharp
using FluentAssertions;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using NUnit.Framework;
using MyProject.Api.Data;
using MyProject.Api.Models;
using MyProject.Api.Repositories;

namespace MyProject.IntegrationTests.Repositories;

[TestFixture]
public class ProductRepositoryTests : IntegrationTestBase
{
    private AppDbContext _db = null!;
    private ProductRepository _sut = null!;
    private IServiceScope _scope = null!;

    [SetUp]
    public async Task SetUp()
    {
        _scope = Factory.Services.CreateScope();
        _db = _scope.ServiceProvider.GetRequiredService<AppDbContext>();
        _sut = new ProductRepository(_db);
        await Task.CompletedTask;
    }

    [TearDown]
    public async Task TearDown()
    {
        // Remove any rows created during the test
        var testRows = _db.Products.Where(product => product.IsTestData);
        _db.Products.RemoveRange(testRows);
        await _db.SaveChangesAsync();

        _scope.Dispose();
    }

    [Test]
    public async Task GetByIdAsync_WhenProductExists_ReturnsProduct()
    {
        var seeded = new Product
        {
            Id = Guid.NewGuid(),
            Name = "Widget",
            Price = 9.99m,
            IsTestData = true
        };
        _db.Products.Add(seeded);
        await _db.SaveChangesAsync();

        var result = await _sut.GetByIdAsync(seeded.Id);

        result.Should().NotBeNull();
        result!.Id.Should().Be(seeded.Id);
        result.Name.Should().Be("Widget");
        result.Price.Should().Be(9.99m);
    }

    [Test]
    public async Task GetByIdAsync_WhenProductDoesNotExist_ReturnsNull()
    {
        var nonExistentId = Guid.NewGuid();

        var result = await _sut.GetByIdAsync(nonExistentId);

        result.Should().BeNull();
    }

    [Test]
    public async Task GetAllAsync_Always_ReturnsOnlyNonDeletedProducts()
    {
        var active = new Product { Id = Guid.NewGuid(), Name = "Active",  Price = 1m, IsDeleted = false, IsTestData = true };
        var deleted = new Product { Id = Guid.NewGuid(), Name = "Deleted", Price = 2m, IsDeleted = true,  IsTestData = true };
        _db.Products.AddRange(active, deleted);
        await _db.SaveChangesAsync();

        var results = await _sut.GetAllAsync();

        results.Should().Contain(product => product.Id == active.Id);
        results.Should().NotContain(product => product.Id == deleted.Id);
    }

    [Test]
    public async Task SaveAsync_Always_PersistsToDatabase()
    {
        var product = new Product
        {
            Id = Guid.NewGuid(),
            Name = "New Product",
            Price = 19.99m,
            IsTestData = true
        };

        await _sut.SaveAsync(product);

        var persisted = await _db.Products.FindAsync(product.Id);
        persisted.Should().NotBeNull();
        persisted!.Name.Should().Be("New Product");
        persisted.Price.Should().Be(19.99m);
    }
}
```

**Key points:**
- Create a fresh `IServiceScope` per test in `[SetUp]` and dispose it in `[TearDown]`.
- Mark test rows with an `IsTestData = true` flag (or an equivalent sentinel field) so cleanup is surgical.
- Resolve the `DbContext` from the scope — this ensures EF's change tracker is isolated per test.

---

## Pattern 3: Data Seeding and Cleanup

Two strategies for keeping tests independent. Choose one consistently within a project.

### Strategy A — Transaction Rollback

Wrap each test in a database transaction. Roll it back in `[TearDown]` so no rows are committed.
This is the fastest strategy but requires the SUT to participate in the ambient transaction.

```csharp
using FluentAssertions;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Storage;
using Microsoft.Extensions.DependencyInjection;
using NUnit.Framework;
using MyProject.Api.Data;
using MyProject.Api.Models;

namespace MyProject.IntegrationTests;

[TestFixture]
public class TransactionalTestExample : IntegrationTestBase
{
    private IServiceScope _scope = null!;
    private AppDbContext _db = null!;
    private IDbContextTransaction _transaction = null!;

    [SetUp]
    public async Task SetUp()
    {
        _scope = Factory.Services.CreateScope();
        _db = _scope.ServiceProvider.GetRequiredService<AppDbContext>();
        _transaction = await _db.Database.BeginTransactionAsync();
    }

    [TearDown]
    public async Task TearDown()
    {
        await _transaction.RollbackAsync();
        _transaction.Dispose();
        _scope.Dispose();
    }

    [Test]
    public async Task ExampleTest_Always_DoesNotPersistAfterRollback()
    {
        _db.Products.Add(new Product { Id = Guid.NewGuid(), Name = "Temporary" });
        await _db.SaveChangesAsync(); // saved to the transaction, not yet committed

        var count = await _db.Products.CountAsync();

        count.Should().BeGreaterThan(0); // visible within this transaction
        // After TearDown rolls back, this row will not exist in the database
    }
}
```

**When to use:** Works well for repository-layer tests where the SUT uses the same `DbContext`.
Does not work for HTTP-layer tests where the server creates its own `DbContext` in a separate scope.

---

### Strategy B — Explicit Cleanup by Sentinel Field

Add a marker to every test-seeded row. Delete by that marker in `[TearDown]`.
This works at any layer — HTTP, repository, or direct DB — because cleanup is unconditional.

```csharp
using FluentAssertions;
using Microsoft.Extensions.DependencyInjection;
using NUnit.Framework;
using MyProject.Api.Data;
using MyProject.Api.Models;

namespace MyProject.IntegrationTests;

[TestFixture]
public class SentinelCleanupExample : IntegrationTestBase
{
    // A fixed CorrelationId that marks all rows seeded by this test class
    private static readonly Guid TestCorrelationId = Guid.Parse("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee");

    [TearDown]
    public async Task TearDown()
    {
        using var scope = Factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();

        var testRows = db.Products.Where(product => product.CorrelationId == TestCorrelationId);
        db.Products.RemoveRange(testRows);
        await db.SaveChangesAsync();
    }

    [Test]
    public async Task CreateProduct_WhenValid_PersistsWithCorrelationId()
    {
        var payload = new CreateProductRequest
        {
            Name = "Sentinel Widget",
            Price = 1.00m,
            CorrelationId = TestCorrelationId
        };

        var response = await Client.PostAsJsonAsync("/api/products", payload);

        response.StatusCode.Should().Be(HttpStatusCode.Created);
        // TearDown will delete the row regardless of whether this assertion passes or fails
    }
}
```

**When to use:** Preferred for HTTP-layer tests. Works even when the SUT creates rows in its own DB scope.
Requires the domain model to have a sentinel field (`IsTestData`, `CorrelationId`, or similar).

---

## Pattern 4: Testing Message Consumers

A full example that publishes a message to RabbitMQ, waits for the consumer to process it, and then asserts the side effect in the database.

```csharp
using System.Net;
using FluentAssertions;
using Microsoft.Extensions.DependencyInjection;
using NUnit.Framework;
using RabbitMQ.Client;
using System.Text;
using System.Text.Json;
using MyProject.Api.Data;
using MyProject.Api.Messages;

namespace MyProject.IntegrationTests.Consumers;

[TestFixture]
public class OrderPlacedConsumerTests : IntegrationTestBase
{
    private IConnection _rabbitConnection = null!;
    private IChannel _channel = null!;

    [SetUp]
    public async Task SetUpBrokerFixture()
    {
        var factory = new ConnectionFactory
        {
            Uri = new Uri(Infrastructure.RabbitMqConnectionString)
        };
        _rabbitConnection = await factory.CreateConnectionAsync();
        _channel = await _rabbitConnection.CreateChannelAsync();
        await _channel.QueueDeclareAsync(queue: "order.placed", durable: true, exclusive: false, autoDelete: false);
    }

    [TearDown]
    public async Task TearDown()
    {
        await _channel.DisposeAsync();
        await _rabbitConnection.DisposeAsync();

        using var scope = Factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        var testRows = db.Orders.Where(order => order.IsTestData);
        db.Orders.RemoveRange(testRows);
        await db.SaveChangesAsync();
    }

    [Test]
    public async Task Consumer_WhenOrderPlacedMessageReceived_PersistsOrderToDatabase()
    {
        var orderId = Guid.NewGuid();
        var message = new OrderPlacedMessage { OrderId = orderId, Total = 99.99m, IsTestData = true };
        await PublishMessageAsync("order.placed", message);

        var order = await WaitUntilAsync(
            condition: async () =>
            {
                using var scope = Factory.Services.CreateScope();
                var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
                return await db.Orders.FindAsync(orderId);
            },
            until: order => order is not null,
            timeout: TimeSpan.FromSeconds(10)
        );

        order.Should().NotBeNull();
        order!.OrderId.Should().Be(orderId);
        order.Total.Should().Be(99.99m);
        order.Status.Should().Be(OrderStatus.Confirmed);
    }

    [Test]
    public async Task Consumer_WhenOrderPlacedMessageReceived_PublishesOrderConfirmedEvent()
    {
        var orderId = Guid.NewGuid();
        var message = new OrderPlacedMessage { OrderId = orderId, Total = 10.00m, IsTestData = true };
        await PublishMessageAsync("order.placed", message);

        // Wait for the downstream event to appear — check via HTTP or DB side effect
        var response = await WaitUntilAsync(
            condition: () => Client.GetAsync($"/api/orders/{orderId}"),
            until: res => res.StatusCode == HttpStatusCode.OK,
            timeout: TimeSpan.FromSeconds(10)
        );

        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }

    // --- helpers ---

    private async Task PublishMessageAsync<T>(string queue, T message)
    {
        var json = JsonSerializer.Serialize(message);
        var body = Encoding.UTF8.GetBytes(json);
        var props = new BasicProperties { ContentType = "application/json", DeliveryMode = DeliveryModes.Persistent };
        await _channel.BasicPublishAsync(exchange: string.Empty, routingKey: queue, basicProperties: props, body: body);
    }

    /// <summary>
    /// Polls <paramref name="condition"/> up to <paramref name="timeout"/>, returning as soon as
    /// <paramref name="until"/> is satisfied. Throws <see cref="TimeoutException"/> if the
    /// condition is never met within the allowed window.
    /// </summary>
    private static async Task<T> WaitUntilAsync<T>(
        Func<Task<T>> condition,
        Func<T, bool> until,
        TimeSpan timeout,
        TimeSpan? pollInterval = null)
    {
        var interval = pollInterval ?? TimeSpan.FromMilliseconds(200);
        var deadline = DateTime.UtcNow + timeout;

        while (DateTime.UtcNow < deadline)
        {
            var result = await condition();
            if (until(result))
                return result;

            await Task.Delay(interval);
        }

        throw new TimeoutException(
            $"Condition was not satisfied within {timeout.TotalSeconds:F1} seconds.");
    }
}
```

**Key points:**
- Use `[SetUp]` / `[TearDown]` for the broker connection in derived classes — do not redeclare `[OneTimeSetUp]` for container lifecycle (the base class owns that).
- `WaitUntilAsync` is the canonical alternative to `Thread.Sleep` — poll at a short interval, fail fast with a clear timeout error.
- Assert the **side effect** (DB row, downstream event, cache entry), not the internal consumer behavior.
- Always mark test-triggered data with a sentinel field so cleanup is deterministic.
- Pattern 4 uses **RabbitMQ.Client v7** async API: `IChannel`, `CreateChannelAsync()`, `BasicPublishAsync()`, and `BasicProperties` record initializer syntax.
