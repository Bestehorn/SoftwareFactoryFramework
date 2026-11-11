# SoftwareFactoryFramework — map for an AI assistant

A map, not a manual: purpose, layout, the invariants a change must respect, and how to run things. Detail lives in
the files it points at. Cap: 40,000 bytes (`test/test_instruction_corpus_budget.py`).

## Purpose
An engineering framework for AI-assisted software projects. Pasting one of its prompts into Claude Code or Kiro sets
up a project, or brings an existing one up to the framework's current state: git hooks, check and test scripts, CI,
rules, agents, slash commands, agent hooks and docs. This repository develops the framework AND is set up by it.

## Two halves (read this first)
| Half | Where | Changed by |
|---|---|---|
| **Product** — what this repository develops and ships | `prompts/`, `clients/`, `src/`, `templates/` | issues, PRs, CI |
| **Toolchain** — what sessions here run on | the installed copy: `CLAUDE.md`, `.claude/`, `.githooks/`, `scripts/` (installed files), `test/test_instruction_corpus_budget.py`, `.github/workflows/` | promotion only: a release tag, then `prompts/update.txt` against this repository |

`config/toolchain.json` lists every installed file with its product source; `.claude/FRAMEWORK_COMMIT` names the
release it came from. The promotion's manifest step, in the marker's commit, regenerates the manifest from the tag:
`python scripts/toolchain_manifest.py --release <tag>` (`--check` writes nothing and exits 1 when it differs). A
hand edit of a toolchain file is refused by the `toolchain-paths` gate and fails `test/test_toolchain_integrity.py`.
Edit the product file; the change reaches the toolchain at the next promotion.
Design and rationale: `docs/reports/self-hosting-proposal-2026-11-07.md`.

## Layout
- `prompts/` — `setup-claude.txt`, `setup-kiro.txt`, `update.txt` (what an operator pastes; also the specification).
- `clients/common/` — prose more than one client uses (spec-workflow phases, `delivery.md`, `review-contract.md`).
- `clients/claude/`, `clients/kiro/` — per-client assets, laid out like a project's `.claude/` and `.kiro/`.
- `src/hooks/` — the agent hook runtime (dispatcher `hooks.py`, `hooklib.py`, discovered `gate_*.py`) and its suite.
- `src/payload/` — the project scripts and their tests, laid out like a project root (`scripts/`, `test/`, `src/`).
- `src/payload/scripts/github_api/` — the package of the product GitHub wrapper, copied with its entry script
  `github_wrapper.py`: the transport, the registry of operation records (one `families/` module per REST family of
  `docs/api-reference/github/`, plus `graphql_only.py`) and the subcommand modules in `commands/`. Suites:
  `src/payload/test/test_github_api_*.py`, `src/payload/test/test_github_wrapper_compat.py`; in `test/`,
  `test_github_wrapper_coverage.py` (every API-reference operation covered by a record or pending) and
  `test_github_wrapper_fork_parity.py`. The product wrapper calls any declared record by its operation ID:
  `python scripts/github_wrapper.py call issues/get --path issue_number=5` (`--path`, `--query`, `-f/--raw-field`,
  `-F/--field`, and `--input FILE` for the two bodies that are not JSON, `repos/upload-release-asset` and
  `markdown/render-raw`; a refusal exits 2). `test/test_github_wrapper_contract.py` checks each record against its
  `rest/<category>.md` section. Not yet installed here: sessions run the fork, which has no `call`
  (`config/toolchain.json`).
- `src/payload/scripts/gitlab_api/` — the package of the product GitLab wrapper, copied with its entry script
  `gitlab_wrapper.py`: the transport, the registry of operation records (one `families/` module per REST family of
  `docs/api-reference/gitlab/`, plus `graphql_only.py`) and the subcommand modules in `commands/`. Suites:
  `src/payload/test/test_gitlab_api_*.py`, `src/payload/test/test_gitlab_wrapper_compat.py`; in `test/`,
  `test_gitlab_wrapper_coverage.py` (every API-reference operation covered by a record or pending). The product
  wrapper calls any declared record by its operation ID:
  `python scripts/gitlab_wrapper.py call plan#retrieve-a-project-issue --path issue_iid=5` (`--path`, `--query`,
  `-f/--raw-field`, `-F/--field`, `--file`; a GraphQL record's variables with `-f`/`-F`; a refusal exits 2).
  `test/test_gitlab_wrapper_contract.py` checks each record against its `rest/<stage>.md` section. A GraphQL-only
  capability is a record of `graphql_only.py`, called the same way:
  `python scripts/gitlab_wrapper.py call graphql#Project.workItems -f fullPath=group/project` (`-f`/`-F` give the
  document's variables, `--file NAME=PATH` an `Upload` variable's file). `test/test_gitlab_graphql_contract.py` checks
  each document against `graphql/`. Not installed here: the repository is on GitHub (`config/toolchain.json`).
- `templates/` — config skeletons, CI templates, git hooks, `docs/` shipped verbatim. No Python.
- `docs/reports/`, `docs/design/agents/` — this repository's own records; `docs/README.md` maps the old layout.
- `test/` — this repository's own tests: `test_layout.py` (layout guard), `test_toolchain_integrity.py`,
  `test_session_title.py` (the issue-work commands may rename their desktop session: tool allowlisted, rule present).
- `scripts/api_reference/` — this repository's own generator of `docs/api-reference/` (the forge API reference).
- `archive/` — git-ignored, local only.

## Invariants
- Everything shipped is Python 3.9+ standard library; Python lives only in `src/`, `test/`, `scripts/`.
- An installable tree mirrors its install destination; `src/payload/<path>` installs at `<path>` in a project.
- Every framework path a live file names must exist (`test/test_layout.py`).
- No AI attribution in commits, PRs, issues or branches (`.claude/rules/no-ai-attribution.md`).

## Testing — where tests run
- Locally, the AFFECTED tests while you work: `python scripts/run_tests.py <paths>` (bounded workers, no fail-fast).
- CI runs every check and the full suite: `.github/workflows/ci.yml` → `python scripts/run_checks.py --group <g>`.
- Never as a commit gate. The pre-push hook runs mypy, and the suite only while CI-OUTAGE MODE is declared.
- The product suites: `src/hooks/tests/` (hook runtime), `src/payload/test/` (shipped scripts; the steward suite
  is slow, minutes). Forge-facing integration tests use ephemeral `sff-test-*` repositories, never this backlog.

## Common commands
- `python scripts/run_tests.py <paths>` — affected tests; no paths = all three suites (pyproject `testpaths`).
- `python scripts/run_checks.py` — the whole pipeline locally, one pass, every failure listed.
- `python scripts/ci_outage_mode.py status` — CI-outage marker.
- `python .claude/hooks/hooks.py selftest` — proves the installed hooks start and decide.
- `python scripts/github_wrapper.py <subcommand>` — every remote operation (needs `credentials/github-pat.txt`).
- `git config core.hooksPath .githooks` (or `bash scripts/setup-hooks.sh`) — once per clone.
