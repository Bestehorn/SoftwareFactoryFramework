# Project Engineering Standards (Claude Code)

The rule files in `.claude/rules/` without `paths:` load into every session and every agent;
this file names each one with its core norm, and the rule file is the full text. Project
facts the rules cannot know go under "This project".

## Always
- The project venv for everything, recreated when broken (`use-venv.md`); never a shell
  environment variable — credentials are read from credentials/ (`no-environment-vars.md`).
- Absolute imports, logging not print, named parameters, `pathlib`, 120 columns, standard
  library only in everything shipped (`coding-standards.md`, `tech-stack.md`).
- Every claim backed by output, a file, a test or a documentation lookup, no hedge words
  (`no-guessing.md`); complete command output, never `tail`/`head` (`no-output-shortening.md`).
- Tests pass; never skip, xfail or delete one to go green (`tests-must-not-fail.md`).
- Pre-work: the `docs/forLLMConsumption.md` map, then grep the lessons and the ledger for the
  component, never read whole (`pre-work.md`); post-work: affected tests, the map under its
  cap, tmp/ empty — and the next step, not a stop (`post-activity.md`).
- The end-to-end check is a script the pipeline runs, never a human step (`always-test-e2e.md`);
  every remote operation goes through `scripts/github_wrapper.py` (`use-git-wrapper-scripts.md`).

## Fleet conventions (all agents and the main session)
- `continuous-work.md`: work until finished; only the four Proven Exceptions end a turn early;
  a question is five lines, recommended option first, asked at the START in one batch.
- `proportionality.md`: the ASK fixes the tier S/M/L and its byte caps; scope frozen at review.
- `parallel-by-default.md`: independent work in ONE message; a wait runs in the foreground,
  bounded, never by ending the turn.
- `native-tools-over-shell.md`: Read/Grep/Glob/Write/Edit for files, one shell call per step,
  suites through `scripts/run_tests.py`.
- `ci-owns-the-test-suite.md`: affected tests locally, the full suite in CI; commit often,
  push once; every failure of a red run fixed in one pass.
- `agent-state-convention.md` + `.claude/docs/run-identity.md`: the registry's run id, plain
  `Name: value` fields corrected by appending, the `DL-NNN` decision log.
- `issue-tracking.md`: the issue is the live record; it closes only with every item ticked.
- `issue-filing-discipline.md`: fix small observed defects; file only through issue-intake;
  zero filings is normal; the rest is a findings-ledger row.
- `keep-git-clean.md` and `no-ai-attribution.md`: no stale worktrees, branches or temp
  files; descriptive names and messages, never an AI trailer.
- Memory is compiled (`/compile-memory`): `test/test_instruction_corpus_budget.py` caps it.

## This project
- This repository DEVELOPS the framework and RUNS on an installed release of it
  (`project-specific.md`, `docs/reports/self-hosting-proposal-2026-11-07.md`). The PRODUCT is
  `prompts/`, `clients/`, `src/`, `templates/`. The TOOLCHAIN is every file listed in
  `config/toolchain.json` (installed from the release in `.claude/FRAMEWORK_COMMIT`): never edit
  it by hand — the `toolchain-paths` gate refuses it and `test/test_toolchain_integrity.py` fails.
  Change the product file; it reaches the toolchain when a release is tagged (`vYYYY.MM.DD[.N]`)
  and promoted with `prompts/update.txt` on a `framework-update-*` branch, which also regenerates
  `config/toolchain.json` (`python scripts/toolchain_manifest.py --release <tag>`).
- GitHub, merge mode direct (no `config/delivery.json`, no merge steward). The toolchain wrapper
  is a recorded deviation (the chess project's implementation) until the product wrapper rewrite
  is released; new subcommands go into `src/payload/scripts/github_wrapper.py`.
- Forge-facing tests use ephemeral `sff-test-*` repositories they create and delete, never this
  backlog. `mypy src` is clean with no override (`test/test_mypy_baseline.py`).
