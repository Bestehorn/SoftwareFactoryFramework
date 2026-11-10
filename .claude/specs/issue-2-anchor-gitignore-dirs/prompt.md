# Prompt — issue #2: the setup prompts recommend an unanchored `reports/` ignore

Tier: S — a value change (ignore lines plus their comments) in one section of two prompt files; no new interface.

Kind: BUGFIX.

## Goal

PART 3 (`.gitignore`) of `prompts/setup-claude.txt` and of `prompts/setup-kiro.txt` recommends `reports/`.
Git matches a slash-free directory pattern at any depth, so the line also ignores `docs/reports/`; this
repository lost new report files that way until its own `.gitignore` was anchored to `/reports/`. The reports
`run_checks.py` (`--reports-dir`, default `reports`) and `run_tests.py` (`--junit reports/junit.xml`) write
land only in the root `reports/`, so `/reports/` ignores everything the line is for and nothing else.

## Scope (the ask)

- Anchor `reports/` to `/reports/` in both PART 3 blocks, with a one-line comment saying the anchor keeps
  `docs/reports/` (and any other nested `reports/`) tracked.
- One pass over the other slash-free directory entries of the setup-kiro PART 3 block (setup-claude's block
  adds only `reports/` beyond its `.claude/...` and `credentials/*` lines, which already contain a slash and so
  are anchored). Decided (DL-001): anchor the packaging directories that a Python build tool writes only at the
  project root — `lib/`, `lib64/`, `var/`, `downloads/`, `eggs/`, `develop-eggs/`, `parts/`, `sdist/`,
  `wheels/` — because an unanchored `lib/` also swallows a nested source directory such as a TypeScript CDK
  app's `cdk/lib/`. Keep `build/`, `dist/`, `venv/`, `.venv/`, `ENV/`, `tmp/` and the cache directories
  unanchored: a nested one of those (a frontend's `build/`, a nested venv, a tool's temp directory) is
  generated output that should stay ignored.
- PART 3 says "Read existing entries, add only those missing". Decided (DL-001): both blocks add one sentence
  telling the project to REPLACE an existing slash-free form of an entry the block anchors (`reports/` →
  `/reports/`, `lib/` → `/lib/`, …), since an existing project otherwise keeps the swallowing line forever;
  every other entry is still only added when missing.
- A test under `test/` that extracts each PART 3 fenced block, applies it as the `.gitignore` of a scratch git
  repository, and asserts with `git check-ignore --no-index` that `reports/junit.xml` and
  `reports/checks-lint.json` are ignored and `docs/reports/x.md` is not; for the setup-kiro block also that
  `cdk/lib/stack.ts` is not ignored and `lib/x.py` is.

## Out of scope

- This repository's own `.gitignore` (already anchored; its comment already records why).
- `src/payload/scripts/run_checks.py` / `run_tests.py` defaults (unchanged: UB-1).

## Integration points

- `prompts/setup-claude.txt` — `## PART 3 — .gitignore`, the fenced block and the "Apply Rule 1" sentence.
- `prompts/setup-kiro.txt` — `## PART 3 — .gitignore`, the fenced block and the "Apply Rule 1" sentence.
- `test/test_layout.py` — `test_a_new_file_in_a_tracked_directory_is_not_ignored` (this repository's own
  guard; unchanged).

## Tests

Every acceptance criterion and unchanged-behaviour clause is pinned by a test in the new module.
E2E: not applicable — prompt text; no runtime behaviour of a deployed system changes. CI's `tests` group runs
the new test.
