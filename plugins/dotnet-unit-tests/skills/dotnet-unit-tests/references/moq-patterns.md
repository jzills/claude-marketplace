# Moq Common Patterns

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
