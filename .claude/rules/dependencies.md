---
paths:
  - "**/*.py"
---
# Dependency Management

When adding/removing imports:

1. Shipped code (`src/hooks/`, `src/payload/`) is Python 3.9+ standard library only
   (`tech-stack.md`); only the test suites need pytest. A third-party import there is a dependency
   change for every project that installs the file — flag it explicitly as a design change.
2. Review `pyproject.toml` for needed changes. Locations:
   - Production -> `[project.dependencies]`
   - Dev tools -> `[project.optional-dependencies.dev]`
3. Flag every dependency change explicitly.
4. After changes: `pip install -e ".[dev]"` inside the venv (`use-venv.md`).
