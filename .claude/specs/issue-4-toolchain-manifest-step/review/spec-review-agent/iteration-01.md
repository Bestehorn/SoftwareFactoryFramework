# Spec review — issue-4-toolchain-manifest-step — iteration 01 (tier S, combined lenses)

## Findings

### B1 — prompt.md names six framework paths the layout guard cannot resolve
Severity: B
Location: prompt.md § Scope (the ask), the install-layout parenthesis
Defect: after `clients/claude/{agents,commands,docs,rules}/X` the six sources are written `<tree>/X` (common docs,
common phases, hooks, payload, githooks, docs templates); `X` is no placeholder to `test/test_layout.py` `resolves`
(only `$<{[` and `*` are), so `test_every_framework_path_named_in_a_live_file_exists` reports all six once the spec
directory is tracked — and it will be: `clients/claude/agents/issue-work-orchestrator.md` § DOCUMENT commits "all
worktree changes (spec + code + tests + evidence …)", and `.claude/specs/` is neither git-ignored nor in `HISTORICAL`.
Replaying the guard's regex and `resolves` over the spec directory: change.md, decision-log.md, prompts.md and
qa_log.md clean; prompt.md six misses.
Material-because: regression — CI's `tests` group goes red on `test/test_layout.py`.
Proposed-edit: in prompt.md § Scope replace each `/X` of the parenthesis with `/<f>` (the notation of change.md
AC-2); in change.md § Tests replace "Synthetic paths" with "Test and tool paths" (the tool is a tracked live file too).

### B2 — AC-5's zero-exit case, as written, exits non-zero
Severity: B
Location: change.md § Tests, AC-5 line
Defect: "`--check` on the committed manifest exits zero" passes no `--installed`, so by AC-1 (default: today) the
regeneration's `installed` differs from the committed `2026-11-09` on every later day: the case is red after the
implementation and AC-5's zero branch has no passing test.
Material-because: AC-5 (exit zero when the regeneration equals the manifest) is contradicted by its only test.
Proposed-edit: replace "`--check` on the committed manifest exits zero" with "`--check --installed 2026-11-09` on the
committed manifest exits zero".

### C1 — three specified branches have no test
Severity: C
Location: change.md § Tests, AC-2, UB-2 and AC-4 lines
Defect: AC-2's "exit non-zero naming them and write nothing" is tested only as a raise of the pure derivation;
UB-2's "a pattern matching no release source" drop has no case; AC-4's "LF" is invisible to a CRLF-normalised
compare (on Windows `Path.write_text` translates `\n` to `os.linesep`).
Proposed-edit: append to the AC-2 line "; the CLI on a copy lacking one `not_installed` entry exits 2, the copy
unchanged"; to the UB-2 line "; an unmatched `templates/config/*` is dropped"; to the AC-4 line "; no CR byte".

### C2 — exit 1 is shared by "differs" and a crash
Severity: C
Location: change.md § Files, `scripts/toolchain_manifest.py`
Defect: "exit 1 when `--check` finds a difference, 2 on a derivation error" leaves a failing git call (tag absent
from the clone) unassigned; an uncaught exception exits 1, which a `--check` caller reads as "differs".
Proposed-edit: replace "2 on a derivation error" with "2 on any tool error, git included".

### C3 — the prescribed git command takes any tree-ish and quotes unusual names
Severity: C
Location: change.md AC-3
Defect: `git ls-tree -r --name-only <tag> --` accepts a branch, or a value starting with `-`, as `<tag>`, and
without `-z` git quotes "unusual" path names per `core.quotePath` (git-ls-tree, OUTPUT FORMAT). Security lens: an
argv list with no shell, and no `ls-tree` option writes a file or runs a program — robustness, not a flaw.
Proposed-edit: replace `git ls-tree -r --name-only <tag> --` with `git ls-tree -r -z --name-only refs/tags/<tag> --`.

### C4 — two repository precedents the Files entry does not name
Severity: C
Location: change.md § Files, `scripts/toolchain_manifest.py`
Defect: `scripts/run_checks.py` `BANDIT_PATHS` covers `scripts/` with no severity floor, so `import subprocess`
(B404) and the git call (B603, B607) fail CI's `security` group unless annotated as `scripts/ci_outage_mode.py`
does; a report logged at INFO is dropped by the default WARNING level unless the CLI configures logging as
`scripts/github_wrapper.py` does (`logging.basicConfig(level=logging.INFO, …)`).
Proposed-edit: none in change.md (no headroom); the implementer follows the two precedents.

### D1 — cuts that keep change.md under its cap
Severity: D
Location: change.md § Ask; § Tasks
Defect: change.md is 7,903 of 8,000 B; the edits above add about 190 B. The Ask's second sentence restates § Files
and DL-001; both tasks spell out the Validates list; task 1.1 spells out the fixture's path expression.
Proposed-edit: replace "Decided route (DL-001): the committed tool … step 7." with "Route: DL-001."; write both
Validates lists as "AC-1–AC-5, UB-1, UB-2"; in 1.1 replace the `Path(__file__)…` expression with "the repository's
`scripts/toolchain_manifest.py`". Net change about zero.

## Coverage

| Criterion | Test (change.md § Tests) | Gap |
|---|---|---|
| AC-1 | derivation sets tag and date; update.txt step 7 and map text checks; AC-4 CLI rewrite | default date untested (single value) |
| AC-2 | synthetic: mapping table, `templates/ci/*` drop, unmapped and collision raise, added/removed report | CLI exit 2 and write-nothing (C1) |
| AC-3 | `ast` imports within `sys.stdlib_module_names`; AC-4 reads the real tag | tag vs HEAD listing indistinguishable today (no installable-tree path added or removed since `v2026.11.09`); backstop `test/test_toolchain_integrity.py` |
| AC-4 | integration, real tag, parsed JSON and normalised text | LF (C1) |
| AC-5 | integration: equal case, differing case byte-identical | equal case broken (B2) |
| UB-1 | integrity and gate tests unmodified; AC-4 proves `files` | none |
| UB-2 | synthetic: exact entry dropped, deviation dropped, others keep reason and order | pattern drop (C1) |

## Judged without finding

- The tool lies outside the installable trees, so no derivation lists it in `files`; `scripts/` is in
  `test_python_lives_only_in_src_test_and_scripts`'s allowed prefixes.
- Replaying the AC-2 table over `git ls-tree` of `v2026.11.09` with the nine current and five new `not_installed`
  entries yields exactly the committed 110 `files`, no unmapped source, every entry used; the committed blob is
  LF, ASCII and byte-equal to `json.dumps(indent=2, ensure_ascii=False)` plus a newline: AC-4 is reachable.
- CI has the tag: `fetch-depth: 0` is "all history for all branches and tags" (actions/checkout README), which the
  integrity test already relies on.
- Python: CI and mypy pin 3.10, so `sys.stdlib_module_names` (3.10+) serves a repository test; the root
  `ruff.toml` extends the py39 target over `scripts/`.
- E2E not applicable: agreed (`always-test-e2e.md`, tooling).

## Verdict

NOT-READY — NOT-CLEAN (0 A, 2 B)
