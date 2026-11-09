# Coding Standards (NO EXCEPTIONS)

1. **JSON field access via constants**, not string literals.
   - BAD: `obj["content"]`
   - GOOD: `FIELD_CONTENT = "content"; obj[FIELD_CONTENT]`
2. **Absolute imports only.** Resolve path issues by fixing the package layout in `pyproject.toml`,
   not by using relative imports.
3. **Logging, not print.** Use the `logging` module. Keep success-case logging minimal.
4. **Named parameters at all call sites.** BAD: `f(5, "abc")`; GOOD: `f(a=5, b="abc")`.
5. **Errors are exceptions.** Do not signal errors with empty lists, sentinel values, or zero.
   Custom exceptions take a `details=None` default kwarg.
6. **Group related exceptions** under a base class.
7. **Line length: 120.** Enforced by ruff: the profile in `src/hooks/ruff.toml`, extended by the root
   `ruff.toml`.
8. **`pathlib.Path` for filesystem.** Never `os.path.join`.
9. **OOP with abstractions.** Group related classes in a module. Use inheritance to avoid
   duplication. The inheritance hierarchy must be visible from class names.
10. **Modular functions.** Decompose into reusable, testable units.
