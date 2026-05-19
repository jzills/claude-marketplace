---
name: dotnet-unit-tests
description: >
  Use this skill whenever the user asks you to write, generate, add, or scaffold unit tests for C# or .NET code.
  Trigger on: "write tests for this", "add unit tests", "test this class", "generate tests", "cover this with tests",
  "write NUnit tests", "mock this dependency", "how do I test this", "add test coverage",
  "write a test for this method", or any request that involves C#/.NET testing.
  Also trigger proactively when the user shows you a C# class or method and asks you to improve, review, or complete it —
  if there are no tests, offer to write them.
---

# .NET Unit Test Writer

You are writing production-quality unit tests for C# code using **NUnit** and **Moq**.
Tests should be readable, maintainable, and actually catch bugs — not just satisfy a coverage metric.

---

## Project Setup

If no test project exists, scaffold one:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net9.0</TargetFramework>
    <IsPackable>false</IsPackable>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="NUnit" Version="4.*" />
    <PackageReference Include="NUnit3TestAdapter" Version="4.*" />
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.*" />
    <PackageReference Include="Moq" Version="4.*" />
    <PackageReference Include="FluentAssertions" Version="6.*" />
  </ItemGroup>
</Project>
```

---

## Test Structure: AAA

Every test follows **Arrange / Act / Assert**. Separate the three sections with blank lines.
Skip `// Arrange` comments unless the test is unusually long — well-named variables make the sections self-evident.

```csharp
[Test]
public void Withdraw_WhenBalanceSufficient_DeductsAmount()
{
    var account = new BankAccount(initialBalance: 100m);

    account.Withdraw(30m);

    account.Balance.Should().Be(70m);
}
```

---

## Naming Convention

Use the format: `MethodName_Condition_ExpectedOutcome`

- `Calculate_WhenInputIsNegative_ThrowsArgumentException`
- `GetUser_WhenUserExists_ReturnsUserDto`
- `ProcessOrder_WhenStockIsEmpty_PublishesOutOfStockEvent`
- `Save_Always_PersistsToRepository` (use `Always` when there is no meaningful condition)

This makes failures self-documenting — the test name alone tells you exactly what broke.

---

## Fixture Setup

NUnit creates a **new instance per test**, so use `[SetUp]` for per-test construction and `[OneTimeSetUp]` only for genuinely expensive shared resources.

```csharp
[TestFixture]
public class OrderServiceTests
{
    private Mock<IOrderRepository> _repositoryMock;
    private Mock<IEventBus> _eventBusMock;
    private OrderService _sut;

    [SetUp]
    public void SetUp()
    {
        _repositoryMock = new Mock<IOrderRepository>();
        _eventBusMock = new Mock<IEventBus>();
        _sut = new OrderService(_repositoryMock.Object, _eventBusMock.Object);
    }
}
```

Recreate mocks in `[SetUp]`, not as field initializers — this prevents state leaking between tests.

---

## Mocking with Moq

Mock dependencies that cross a boundary: databases, HTTP clients, clocks, file systems, external services.
Do not mock types you own unless they are genuinely expensive or non-deterministic.

```csharp
[Test]
public async Task PlaceOrder_WhenValid_SavesAndPublishes()
{
    var order = new Order { Id = Guid.NewGuid(), Total = 50m };
    _repositoryMock.Setup(r => r.SaveAsync(order)).Returns(Task.CompletedTask);

    await _sut.PlaceOrderAsync(order);

    _repositoryMock.Verify(r => r.SaveAsync(order), Times.Once);
    _eventBusMock.Verify(e => e.PublishAsync(It.IsAny<OrderPlacedEvent>()), Times.Once);
}
```

**Common Moq patterns:**

```csharp
// Return a value
_mock.Setup(x => x.GetByIdAsync(1)).ReturnsAsync(someEntity);

// Return null
_mock.Setup(x => x.FindAsync(99)).ReturnsAsync((Entity?)null);

// Throw an exception
_mock.Setup(x => x.SaveAsync(It.IsAny<Entity>())).ThrowsAsync(new DbException());

// Match any argument of a type
_mock.Setup(mock => mock.Publish(It.IsAny<OrderEvent>()));

// Capture an argument for deeper inspection
Entity? captured = null;
_mock.Setup(mock => mock.SaveAsync(It.IsAny<Entity>()))
     .Callback<Entity>(e => captured = e)
     .Returns(Task.CompletedTask);
```

---

## Parameterized Tests

Use `[TestCase]` to cover boundary conditions and multiple inputs without duplicating test bodies.

```csharp
[TestCase(0)]
[TestCase(-1)]
[TestCase(int.MinValue)]
public void Divide_WhenDivisorIsInvalid_ThrowsArgumentException(int divisor)
{
    var calc = new Calculator();

    Action act = () => calc.Divide(10, divisor);

    act.Should().Throw<ArgumentException>();
}
```

Use `[TestCaseSource]` when the inputs are complex objects or need to be built programmatically.

---

## Assertions with FluentAssertions

FluentAssertions produces failure messages that tell you exactly what went wrong, which saves significant debugging time.

```csharp
// Value equality
result.Should().Be(42);
result.Should().NotBe(0);

// Nullability
result.Should().BeNull();
result.Should().NotBeNull();

// Collections
items.Should().HaveCount(3);
items.Should().Contain(item => item.IsActive);
items.Should().BeEquivalentTo(expected); // deep equality, order-insensitive

// Strings
name.Should().StartWith("Order_").And.HaveLength(12);

// Exceptions (sync)
Action act = () => _sut.Process(null);
act.Should().Throw<ArgumentNullException>().WithMessage("*parameter*");

// Exceptions (async)
Func<Task> act = () => _sut.ProcessAsync(order);
await act.Should().ThrowAsync<InvalidOperationException>().WithMessage("*out of stock*");
```

---

## Async Tests

Always `await` async methods under test. NUnit supports `async Task` test methods natively.

```csharp
[Test]
public async Task GetUserAsync_WhenNotFound_ReturnsNull()
{
    _repositoryMock.Setup(r => r.FindByIdAsync(99)).ReturnsAsync((User?)null);

    var result = await _sut.GetUserAsync(99);

    result.Should().BeNull();
}
```

---

## Code Style

**Lambda parameters:** Use the type name (singular) rather than `x`.
This makes the intent clear without needing to look up what `x` refers to.

```csharp
// Preferred
items.Should().Contain(item => item.IsActive);
_mock.Setup(repo => repo.SaveAsync(It.IsAny<Entity>()));

// Avoid
items.Should().Contain(x => x.IsActive);
_mock.Setup(x => x.SaveAsync(It.IsAny<Entity>()));
```

---

## What NOT to Do

- Do not test private methods directly — test them through the public API
- Do not assert on internal implementation details unless verifying observable side effects
- Do not use `Thread.Sleep` — if timing matters, inject a clock abstraction (`IClock`) and mock it
- Do not share mutable mock state between tests — always reset in `[SetUp]`
- Do not write a test that can never fail
- Do not mock `DateTime.Now` or `Guid.NewGuid()` directly — wrap them behind an interface and mock that

---

## Output Format

When generating tests for a class:

1. **Read the class under test** — understand every public method, its parameters, return types, and injected dependencies
2. **Identify test cases** — happy paths, edge cases, error conditions, async behavior, null inputs
3. **Write a complete, compilable test file** — include all `using` statements, the correct namespace, and `[TestFixture]` class scaffold
4. **Name the test class** `{ClassName}Tests` and place it in the same namespace as the class under test, plus `.Tests`

Always output the full file, not isolated snippets, unless the user explicitly asks for just one test.
