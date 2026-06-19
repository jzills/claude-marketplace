# PEP 8 Rules Reference

Source: https://peps.python.org/pep-0008/

## Table of Contents
1. [Code Layout](#code-layout)
2. [String Quotes](#string-quotes)
3. [Whitespace in Expressions and Statements](#whitespace)
4. [Trailing Commas](#trailing-commas)
5. [Comments](#comments)
6. [Naming Conventions](#naming-conventions)
7. [Programming Recommendations](#programming-recommendations)
8. [Function and Variable Annotations](#annotations)

---

## Code Layout

### Indentation
- Use **4 spaces** per indentation level.
- Continuation lines must align wrapped elements vertically, or use a hanging indent.

```python
# Aligned with opening delimiter
foo = long_function_name(var_one, var_two,
                         var_three, var_four)

# Hanging indent (add 4 extra spaces to distinguish from body)
def long_function_name(
        var_one, var_two,
        var_three, var_four):
    print(var_one)
```

- **Never mix tabs and spaces.** Spaces are the preferred method.

### Maximum Line Length
- Limit all lines to **79 characters**.
- Docstrings and comments: **72 characters**.
- Teams may agree on up to 99 characters for code, keeping docstrings/comments at 72.
- Use backslash `\` or implicit continuation inside `()`, `[]`, `{}` to wrap long lines.

```python
# Good — break before the operator
income = (gross_wages
          + taxable_interest
          + (dividends - qualified_dividends))
```

### Blank Lines
- Surround top-level function and class definitions with **two blank lines**.
- Method definitions inside a class: **one blank line**.
- Use blank lines sparingly inside functions to indicate logical sections.

```python
class MyClass:
    def method_one(self):
        pass

    def method_two(self):
        pass


def top_level_function():
    pass
```

### Imports
- Each import on its own line:
  ```python
  # Good
  import os
  import sys

  # Bad
  import os, sys
  ```
- `from X import A, B` on one line is fine.
- Group imports in this order, separated by blank lines:
  1. Standard library imports
  2. Third-party library imports
  3. Local application/library imports
- Use absolute imports; avoid wildcard imports (`from module import *`).
- Explicit relative imports (`from . import module`) are acceptable.

### Module-Level Dunder Names
- Place `__all__`, `__author__`, `__version__`, etc. after the module docstring but **before** any imports (except `__future__`).

```python
"""Module docstring."""

from __future__ import annotations

__all__ = ["MyClass"]
__version__ = "1.0.0"

import os
```

---

## String Quotes

- Single and double quotes are equivalent — pick one style and be **consistent** within a file.
- Use the opposite quote type inside a string to avoid escaping:
  ```python
  # Preferred over "It\'s a test"
  "It's a test"
  ```
- Triple-quoted strings always use **double quotes** (`"""`).

---

## Whitespace

### Avoid Extraneous Whitespace
```python
# Bad
spam( ham[ 1 ], { eggs: 2 } )
foo [0]
dct ['key'] = lst [index]

# Good
spam(ham[1], {eggs: 2})
foo[0]
dct['key'] = lst[index]
```

- No space before a comma, semicolon, or colon.
- No space before the opening parenthesis of a function call or indexing.
- No trailing whitespace anywhere.

### Operators
- Surround binary operators with a **single space** on each side: `=`, `+=`, `==`, `<`, `>`, `in`, `not in`, `is`, `is not`, `and`, `or`, `not`.
- When combining operators of different precedence, add space around the **lowest-priority** operator:
  ```python
  # Good
  x = x*2 - 1
  hypot2 = x*x + y*y
  c = (a+b) * (a-b)
  ```
- No space around `=` in keyword arguments or default parameter values **unless** a type annotation is present:
  ```python
  def munge(sep=None): ...          # no spaces
  def munge(sep: str = None): ...   # spaces required with annotation
  ```
- Space around `->` in return annotations:
  ```python
  def munge() -> None: ...
  ```

### Other
- Avoid compound statements on one line: `if foo: bar` — put them on separate lines.
- Don't write `if/for/while` with the body on the same line.

---

## Trailing Commas

- Required for single-element tuples: `FILES = ("setup.cfg",)`
- Helpful when elements are on separate lines (makes future additions cleaner):
  ```python
  FILES = [
      "setup.cfg",
      "tox.ini",
  ]
  ```

---

## Comments

### General
- Keep comments up to date when code changes.
- Write in complete sentences; capitalize the first word.
- English preferred for open-source code.

### Block Comments
- Apply to the code that follows, at the same indentation level.
- Each line starts with `# ` (hash and single space).
- Separate paragraphs with a line containing only `#`.

### Inline Comments
- Use sparingly. Separate from the statement by at least **two spaces**.
- Start with `# ` (hash and single space).
- Don't state the obvious:
  ```python
  x = x + 1  # Bad: Increment x
  x = x + 1  # Good: Compensate for border
  ```

### Docstrings (PEP 257)
- Write docstrings for **all public** modules, functions, classes, and methods.
- One-liner: closing `"""` on the same line.
  ```python
  def kos_root():
      """Return the pathname of the KOS root directory."""
  ```
- Multi-line: summary line, blank line, elaboration; closing `"""` on its own line.
  ```python
  def complex(real=0.0, imag=0.0):
      """Form a complex number.

      Keyword arguments:
      real -- the real part (default 0.0)
      imag -- the imaginary part (default 0.0)
      """
  ```

---

## Naming Conventions

### Styles at a Glance
| Style | Example | Use for |
|---|---|---|
| `lowercase` | `module` | modules, packages |
| `lower_case_with_underscores` | `my_variable` | functions, variables, methods, arguments |
| `UPPER_CASE_WITH_UNDERSCORES` | `MAX_RETRIES` | constants |
| `CapWords` | `MyClass` | classes, type variables, exceptions |
| `_single_leading` | `_internal` | weak "internal use" signal |
| `single_trailing_` | `class_` | avoid keyword conflicts |
| `__double_leading` | `__name_mangled` | name mangling in classes |
| `__dunder__` | `__init__` | magic objects — never invent new ones |

### Specific Rules
- **Avoid** single-character names `l` (lowercase L), `O` (uppercase o), `I` (uppercase i) — they are indistinguishable from numerals in some fonts.
- **Packages/modules**: short, all-lowercase; underscores acceptable but discouraged.
- **Classes**: CapWords. Built-in exceptions also use CapWords with an `Error` suffix.
- **Type variables**: CapWords, short (e.g., `T`, `AnyStr`). Add `_co`/`_contra` for covariant/contravariant.
- **Functions and variables**: `lowercase_with_underscores`.
- **Constants**: `ALL_CAPS_WITH_UNDERSCORES`, defined at module level.
- **Instance methods**: first argument is always `self`.
- **Class methods**: first argument is always `cls`.
- **Private**: prefix with `_` (single) for internal, `__` (double) to invoke name mangling.

---

## Programming Recommendations

### Comparisons
```python
# None
if x is None: ...        # good
if x is not None: ...    # good
if x == None: ...        # bad

# Booleans
if greeting: ...         # good
if greeting == True: ... # bad
if greeting is True: ... # bad (unless you specifically mean True, not truthy)

# Type checks
if isinstance(x, int): ... # good
if type(x) is int: ...     # acceptable when exact type matters
if type(x) == int: ...     # bad

# Empty sequences
if seq: ...              # good (truthy check)
if len(seq) == 0: ...    # bad
```

### Exceptions
- Derive custom exceptions from `Exception`, not `BaseException`.
- Catch **specific** exceptions, not bare `except:`.
  ```python
  # Good
  try:
      ...
  except ValueError as e:
      ...

  # Bad
  try:
      ...
  except:
      ...
  ```
- Use `raise X from Y` when replacing an exception explicitly.
- Keep `try` blocks minimal — only the code that can raise, not follow-on processing.
- Use `with` statements for resource management (files, locks, connections).

### Functions
- Use `def` statements, not lambda assigned to a variable:
  ```python
  # Good
  def double(x):
      return x * 2

  # Bad
  double = lambda x: x * 2
  ```
- Be consistent with `return` statements: either all paths return a value, or none do. Use explicit `return None` at the end if any branch returns a value.

### String Operations
```python
# Good
if filename.startswith("test_"): ...
if filename.endswith(".py"): ...

# Bad
if filename[:5] == "test_": ...
```

### Context Managers
- Use `with` for any resource that has a defined acquire/release lifecycle.
- When a context manager does more than acquire/release, wrap it in a function.

### Flow Control in `finally`
- Avoid `return`, `break`, or `continue` inside `finally` blocks — they silently discard active exceptions.

---

## Annotations

### Function Annotations (PEP 484)
```python
def greeting(name: str) -> str:
    return "Hello " + name
```
- Space after `:`, none before.
- Space around `->`.
- Annotations are optional metadata for type checkers — they don't affect runtime behavior.

### Variable Annotations (PEP 526)
```python
code: int
message: str = "Hello"
```
- Space after `:`, none before.
- One space around `=` when a value is assigned.
