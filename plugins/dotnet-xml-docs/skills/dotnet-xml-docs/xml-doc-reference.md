# .NET XML Documentation Reference

Full specification for XML documentation comments in C# / .NET.

---

## Comment Formats

```csharp
// Single-line
/// <summary>Description</summary>

// Multiline (compiler normalizes leading asterisks)
/**
 * <summary>Description</summary>
 */
```

---

## General Tags

### `<summary>`
Brief description. Appears in IntelliSense, Object Browser, and generated docs.
```xml
<summary>Initializes a new instance of <see cref="MyClass"/>.</summary>
```

### `<remarks>`
Supplemental detail beyond the summary.
```xml
<remarks>
    <para>First paragraph with additional context.</para>
    <para>Second paragraph if needed.</para>
</remarks>
```

---

## Member Tags

### `<param>`
Documents a single method or constructor parameter. `name` must match the signature exactly.
```xml
<param name="timeout">The maximum time to wait, in milliseconds.</param>
```

### `<returns>`
Describes what a method returns.
```xml
<returns>The created entity, or <see langword="null"/> if creation failed.</returns>
```

### `<typeparam>`
Documents a generic type parameter.
```xml
<typeparam name="T">The element type. Must implement <see cref="IComparable{T}"/>.</typeparam>
```

### `<exception>`
Documents an exception a method can throw. `cref` is compiler-verified.
```xml
<exception cref="ArgumentNullException">Thrown when <paramref name="input"/> is <see langword="null"/>.</exception>
<exception cref="InvalidOperationException">Thrown when the service is not initialized.</exception>
```

### `<value>`
Describes what a property represents (distinct from its summary).
```xml
<value>The interval between retries, in seconds. Defaults to <c>5</c>.</value>
```

---

## Inline Formatting Tags

### `<c>` — inline code
```xml
Pass <c>true</c> to enable strict mode.
```

### `<code>` — code block
```xml
<example>
    <code>
    var result = service.Compute(42);
    Console.WriteLine(result);
    </code>
</example>
```

### `<para>` — paragraph break (double-spaced)
```xml
<remarks>
    <para>First paragraph.</para>
    <para>Second paragraph.</para>
</remarks>
```

### `<br/>` — line break (single-spaced)
```xml
Line one.<br/>Line two.
```

### `<paramref>` — reference a parameter inline
```xml
/// If <paramref name="count"/> is zero, the method returns immediately.
```

### `<typeparamref>` — reference a type parameter inline
```xml
/// Returns the default value of <typeparamref name="T"/>.
```

---

## Reference Tags

### `<see>` — inline cross-reference

| Attribute | Purpose |
|-----------|---------|
| `cref` | Code member reference (compiler-verified) |
| `href` | External URL |
| `langword` | Language keyword |

```xml
<see cref="PaymentService.ProcessAsync"/>
<see cref="List{T}"/>                      <!-- prefer braces over &lt;T&gt; -->
<see href="https://example.com">Docs</see>
<see langword="null"/>
<see langword="true"/>
<see langword="async"/>
```

Common `langword` values: `null`, `true`, `false`, `abstract`, `sealed`, `static`, `virtual`, `ref`, `in`, `out`, `async`, `await`.

### `<seealso>` — "See Also" section
Cannot be nested inside `<summary>`. Generates a "See Also" section in output.
```xml
<seealso cref="Transaction"/>
<seealso href="https://example.com">External docs</seealso>
```

---

## Reuse Tags

### `<inheritdoc>`
Inherit documentation from a base class, interface, or specified member.
```xml
<inheritdoc/>                              <!-- inherit from overridden member -->
<inheritdoc cref="IDisposable.Dispose"/>   <!-- inherit from specific member -->
<inheritdoc path="/summary"/>              <!-- inherit only the summary tag (XPath) -->
```

Explicitly defined tags override inherited ones.

### `<include>`
Include documentation from an external XML file.
```xml
<include file="docs/shared.xml" path="doc/members/member[@name='M:Namespace.Type.Method']"/>
```

External XML structure:
```xml
<?xml version="1.0"?>
<doc>
  <members>
    <member name="M:Namespace.Type.Method">
      <summary>Shared documentation.</summary>
    </member>
  </members>
</doc>
```

---

## List Tag

```xml
<list type="bullet|number|table">
    <listheader>                            <!-- optional header row -->
        <term>Column 1</term>
        <description>Column 2</description>
    </listheader>
    <item>
        <term>Label</term>                  <!-- omit term for plain bullet/number -->
        <description>Explanation</description>
    </item>
</list>
```

### `type` values

| Value | Renders as |
|-------|-----------|
| `bullet` | Bulleted list |
| `number` | Numbered list |
| `table` | Two-column table |

---

## Example Tag

```xml
<example>
    Description of the scenario.
    <code>
    var client = new ApiClient("https://api.example.com");
    var result = await client.GetAsync&lt;User&gt;(userId);
    </code>
</example>
```

---

## HTML Tags (Compiler-Validated)

| Tag | Purpose |
|-----|---------|
| `<b>` | Bold |
| `<i>` | Italic |
| `<u>` | Underline |
| `<br/>` | Line break |
| `<a href="url">` | Hyperlink |

Prefer `<c>` over `<tt>` (deprecated) for inline code.

---

## Special Character Escaping

| Character | Escape |
|-----------|--------|
| `<` | `&lt;` |
| `>` | `&gt;` |
| `&` | `&amp;` |
| `"` (in attributes) | `&quot;` |

Generic type references in `cref`:
```xml
<see cref="Dictionary{TKey,TValue}"/>   <!-- preferred: brace notation -->
<see cref="Dictionary&lt;TKey,TValue&gt;"/>  <!-- also valid but noisy -->
```

---

## Compiler Verification

These tags are validated by the C# compiler:

| Tag / Attribute | What is verified |
|-----------------|-----------------|
| `<param name="x">` | Parameter `x` exists on the member |
| `<typeparam name="T">` | Type parameter `T` exists |
| `<exception cref="T">` | Type `T` exists and is in scope |
| `cref` attribute | Referenced member or type exists |
| `<include file="..." path="...">` | File exists; XPath is valid |
| `<inheritdoc>` | Inferred base member exists |

Warnings are emitted for public members missing `<summary>` when `GenerateDocumentationFile` is enabled (`CS1591`).

---

## Member ID String Format

The compiler writes ID strings to the generated XML file using this format:

```
{prefix}:{fully.qualified.name}[({parameters})]
```

| Prefix | Meaning |
|--------|---------|
| `N:` | Namespace |
| `T:` | Type (class, struct, interface, enum, delegate) |
| `F:` | Field |
| `P:` | Property or indexer |
| `M:` | Method, constructor, operator |
| `E:` | Event |
| `!` | Unresolved reference (error) |

Examples:
```
T:MyApp.Services.PaymentService
M:MyApp.Services.PaymentService.ProcessAsync(MyApp.Models.PaymentRequest)
M:MyApp.Services.PaymentService.#ctor                     (constructor)
P:MyApp.Services.PaymentService.MaxRetries
M:MyApp.Collections.ObjectPool`1.Rent                     (generic: backtick + count)
```

Parameter encoding:
- `System.Int32@` — ref/out parameter
- `System.String*` — pointer
- `T[]` — array
- `T[0:,0:]` — 2D array
- `` `2 `` — generic with 2 type parameters

---

## MSBuild Configuration

```xml
<PropertyGroup>
  <!-- Enable XML doc generation -->
  <GenerateDocumentationFile>true</GenerateDocumentationFile>

  <!-- Optional: specify output path -->
  <DocumentationFile>bin\$(Configuration)\$(AssemblyName).xml</DocumentationFile>

  <!-- Suppress CS1591 if you don't want warnings for undocumented public members -->
  <NoWarn>$(NoWarn);1591</NoWarn>
</PropertyGroup>
```

---

## Best Practices

- `<summary>` should be a complete sentence ending with a period.
- Document every public parameter, return value, and possible exception.
- Use `cref` for code members and `href` for external URLs — never mix them.
- Prefer `List{T}` brace notation in `cref` over HTML-escaped angle brackets.
- `<remarks>` is only worth adding when there is genuinely more to say than the summary covers.
- Avoid restating the member name in the summary: `/// <summary>Gets the name.</summary>` on `GetName()` adds nothing.
- Partial classes: put documentation on the defining declaration; the compiler merges it.
- `<inheritdoc/>` is appropriate for interface implementations and override methods — don't rewrite what the interface already documents.
