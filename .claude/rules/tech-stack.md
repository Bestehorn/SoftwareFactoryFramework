# Technology Stack

## Core
- Python 3.9+ standard library for everything this repository ships (`src/hooks/`,
  `src/payload/`); only the test suites need pytest. The code stays Python 3.9-compatible
  (ruff `target-version = "py39"`).
- pytest for every suite (`src/hooks/tests/`, `src/payload/test/`, `test/`), run through
  `scripts/run_tests.py`.
- Markdown and plain-text prompt material under `prompts/` and `clients/`.
- Hosted on GitHub; developed with Claude Code on Windows.

## Quality
- ruff (lint + format, line-length 120): the profile in `src/hooks/ruff.toml`, extended by the root
  `ruff.toml` for the rest of the repository's Python.
- bandit (security), detect-secrets (secret scan against `.secrets.baseline`).
- pre-commit, run through the tracked `.githooks/`.

## Preferred libraries
- dataclasses for models
- logging (not print)
- pathlib (not os.path)
- typing for all type hints

## Not shipped
- This repository's own tools are not bound by the standard-library rule: `scripts/api_reference/`
  uses PyYAML.
