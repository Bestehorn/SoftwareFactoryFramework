# Project-Specific Rules

This repository develops the framework it also runs. Every file belongs to one of two halves; know
which one you are touching.

| | Product | Toolchain |
|---|---|---|
| Paths | `prompts/`, `clients/`, `src/`, `templates/` | `CLAUDE.md`, `.claude/`, `.githooks/`, the installed files in `scripts/`, `test/test_instruction_corpus_budget.py`, `.github/workflows/` |
| Role | what issues and PRs change | the installed copy every session runs on |
| Changed by | issues and PRs | promotion only |

1. **Never edit a toolchain file by hand.** The toolchain is installed from a release tag of this
   same repository, pinned in `.claude/FRAMEWORK_COMMIT` and listed in `config/toolchain.json`.
   Make the change in the product file it comes from — `src/payload/scripts/` for `scripts/`,
   `src/hooks/` for `.claude/hooks/`, `clients/claude/` for the fleet rules, agents and commands,
   `templates/ci/` for `.github/workflows/` — and it reaches the toolchain only when a release is
   promoted with `prompts/update.txt`.
2. **A product change takes effect for you only after release and promotion.** The rules, hooks and
   scripts you run are the release named in `.claude/FRAMEWORK_COMMIT`, whatever has been merged
   since.
3. **Forge-facing code** (the wrappers, the merge steward, the delivery CI) is integration-tested
   against ephemeral `sff-test-*` repositories the tests create and delete — never against this
   repository or its backlog.
4. This repository's own tools (`scripts/api_reference/`, `test/test_layout.py`) are project files,
   not toolchain.

Rationale: `docs/reports/self-hosting-proposal-2026-11-07.md`.
