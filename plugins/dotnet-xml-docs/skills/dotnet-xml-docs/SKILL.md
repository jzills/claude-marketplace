---
name: dotnet-xml-docs
description: >
  Use when writing, reviewing, or generating XML documentation comments (///)
  for C# or .NET code. Trigger on: "add XML docs", "document this class",
  "write doc comments", "add IntelliSense comments", "document the API",
  "add triple-slash comments", "add summary comments", or any request involving
  /// documentation in C#/.NET. Also trigger proactively when the user asks to
  review or complete a public API surface that lacks documentation.
---

# .NET XML Documentation Writer

You are writing production-quality XML documentation comments for C# public APIs.
Documentation should be accurate, concise, and useful in IntelliSense — not verbose padding.

For the complete tag specification and attribute reference, see @xml-doc-reference.md.

---

## Tag Quick Reference

| Tag | Applied to | Purpose |
|-----|-----------|---------|
| `<summary>` | Any member | One-sentence description (required for all public members) |
| `<remarks>` | Any member | Supplemental detail beyond the summary |
| `<param>` | Methods, constructors | Documents a single parameter |
| `<returns>` | Methods | Describes the return value |
| `<exception>` | Methods, properties | Documents a thrown exception |
| `<typeparam>` | Generic types/methods | Documents a type parameter |
| `<value>` | Properties | Describes what the property represents |
| `<example>` | Any member | Usage example, typically contains `<code>` |
| `<see>` | Inline | Inline cross-reference to another member or URL |
| `<seealso>` | Top-level | Generates a "See Also" section |
| `<inheritdoc>` | Overrides/implementations | Inherits docs from base or interface |
| `<para>` | Inside other tags | Double-spaced paragraph break |
| `<c>` | Inline | Inline monospace code |
| `<code>` | Block | Multi-line code block |
| `<list>` | Block | Bulleted, numbered, or table list |
| `<br/>` | Inline | Single-spaced line break |

---

## Core Patterns

### Type and method documentation

```csharp
/// <summary>
/// Processes a payment and returns the resulting transaction.
/// </summary>
/// <remarks>
/// Retries up to three times on transient failures before throwing.
/// </remarks>
/// <param name="request">The payment details to process.</param>
/// <returns>A <see cref="Transaction"/> representing the completed payment.</returns>
/// <exception cref="PaymentDeclinedException">Thrown when the payment is declined.</exception>
/// <exception cref="ArgumentNullException">Thrown when <paramref name="request"/> is <see langword="null"/>.</exception>
public Transaction ProcessPayment(PaymentRequest request)
```

### Generic types and methods

```csharp
/// <summary>
/// A thread-safe pool of reusable <typeparamref name="T"/> instances.
/// </summary>
/// <typeparam name="T">The type of object to pool. Must be a class with a parameterless constructor.</typeparam>
public class ObjectPool<T> where T : class, new()
```

### Properties

```csharp
/// <summary>
/// Gets or sets the maximum number of concurrent connections.
/// </summary>
/// <value>The connection limit. Defaults to <c>100</c>.</value>
public int MaxConnections { get; set; }
```

### Inheriting from interface or base class

```csharp
/// <inheritdoc/>
public override string ToString()

// Or inherit from a specific member:
/// <inheritdoc cref="IDisposable.Dispose"/>
public void Dispose()
```

### Cross-references

```csharp
// Code member reference (compiler-verified):
/// See <see cref="PaymentService.ProcessPayment"/> for the synchronous version.

// Language keyword:
/// Returns <see langword="null"/> if the user is not found.

// External URL:
/// See <see href="https://learn.microsoft.com/dotnet/csharp">C# Guide</see> for background.

// "See Also" section:
/// <seealso cref="Transaction"/>
/// <seealso cref="PaymentRequest"/>
```

### Usage examples

```csharp
/// <example>
/// <code>
/// var pool = new ObjectPool&lt;Connection&gt;();
/// var conn = pool.Rent();
/// try { /* use conn */ }
/// finally { pool.Return(conn); }
/// </code>
/// </example>
```

### Lists inside remarks

```csharp
/// <remarks>
/// Supported modes:
/// <list type="bullet">
///   <item><term>Fast</term><description>Low latency, higher memory usage.</description></item>
///   <item><term>Balanced</term><description>Default mode for most workloads.</description></item>
///   <item><term>Efficient</term><description>Lower memory, higher latency.</description></item>
/// </list>
/// </remarks>
```

---

## Rules

- Write `<summary>` as a complete sentence ending with a period.
- Document every public parameter, return value, and thrown exception.
- Use `cref` for code references — the compiler validates them. Use `href` for external URLs.
- Prefer `List{T}` brace syntax over `List&lt;T&gt;` in cref attributes — it's less noisy.
- Don't write `<remarks>` just to repeat the summary. Only add it when there's genuinely more to say.
- Don't document obvious things: `<param name="value">The value.</param>` adds nothing.
- Keep `<summary>` to one sentence. Move longer explanations to `<remarks>`.

---

## Output Format

When documenting a class:

1. **Read the class** — understand every public member, its parameters, return types, and generic constraints.
2. **Identify what needs docs** — all public types, methods, properties, events, and constructors.
3. **Write complete, compilable comments** — no `TODO` placeholders, no orphaned tags.
4. **Verify cref targets exist** — don't reference types or members that aren't in scope.

Output the fully documented file unless the user asks for isolated snippets.
