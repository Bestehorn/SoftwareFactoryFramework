# File Organization

1. Root: only global config files (`README.md`, `pyproject.toml`, `ruff.toml`,
   `.pre-commit-config.yaml`, etc.).
2. One kind of asset per top-level directory:
   - `prompts/` — the prompts an operator pastes
   - `clients/` — natural-language assets per client: `common/` (used by more than one client,
     written once), `claude/` (laid out like a project's `.claude/`), `kiro/` (laid out like `.kiro/`)
   - `src/` — all Python that ships: `src/hooks/` (the agent hook runtime, suite in
     `src/hooks/tests/`) and `src/payload/` (project scripts and their tests, laid out like a
     project root)
   - `templates/` — config skeletons, CI workflows, git hooks and documents shipped verbatim
   - `docs/` — this repository's own documentation; docs that ship to projects live in
     `templates/docs/`
   - `test/` — tests of the framework itself
   - `scripts/` — this repository's own tools and the installed toolchain scripts
   - `tmp/` — temporary files (gitignored, cleaned at end of task)
3. `clients/`, `prompts/` and `templates/` hold no Python.
4. No temp files outside `tmp/`. Deleting `tmp/` must never break the solution.
