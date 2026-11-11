# Review latest — issue #28 design, iteration 01 (consolidated by the conductor)

Lanes: test-architect NOT-CLEAN (1 A, 3 B; 18 COVERED, 3 GAP), standards NOT-CLEAN (1 A, 1 B), best-practice
NOT-CLEAN (1 A, 1 B), security NOT-CLEAN (0 A, 1 B), devops NOT-CLEAN (0 A, 1 B), spec-review NOT-READY (1 A, 3 B).
Lane files: `review/<lane>/iteration-01.md`. Requirements are frozen; every fix restates or removes design text.

## Root causes (A/B), 12 findings → 6 causes

- **X1 (A) — array query names.** D4 strips a trailing `[]`; `registry._check_names` (run by `send` and `pages`)
  compares the name as written, so `--query state[]=open` raises `ValueError`, which `_run_command` does not catch.
  Fix: one rule in `registry.py` (a query name is compared without a trailing `[]`, the name sent as written), D4
  calls it; D8's `registry.py` row says so. [ST-A1, BP-A1, SR-A1, SEC-C3]
- **X2 (B) — paged records drop `accept` (and the version oracle cannot fail).** `registry.pages` → `Transport.pages`
  → `_page_items` always sends `ACCEPT_JSON`. Fix: `Transport.pages` takes `accept` (default `ACCEPT_JSON`, callers
  unchanged), `registry.pages` passes the record's; D8 gains a `transport.py` row; AC-1.2's tests use records with a
  non-default `api_version` and `accept`, one paged and one not. [BP-B1, TA-A1, SR-B1]
- **X3 (B) — Hypothesis in a shipped suite.** Move the AC-1.3 property test out of `src/payload/test/` into `test/`
  (#17 decision X1: shipped suites stay pytest-only); named arguments in the sketch. [ST-B1, DV-B1, SR-B3]
- **X4 (B) — `call` routes around two hook gates.** `gate_merge_steward` refuses only `merge-pr`, `gate_filing` only
  `create-issue` / `issue create`; `call pulls/merge` and `call issues/create` pass both. Decision (conductor): keep
  the guarantee inside this change's own module, not by editing the hooks — `call` refuses an operation id that a
  gated compatibility subcommand covers (`pulls/merge` → `merge-pr`, `issues/create` → `create-issue`), exit 2,
  naming the subcommand to use, with a test; Security Considerations gains a "Gates" bullet; Residuals records that a
  slice adding a trunk-writing record (`repos/merge`, `git/update-ref`, `git/create-ref`,
  `repos/create-or-update-file-contents`) must extend that refusal set or the gates. [SEC-B1]
- **X5 (B) — the reference reader.** D5's row rules drop named-variant rows (`{single_select}.…`) and keep the
  `(body)` constraint row as a field, so the contract test would misread sections such as
  `actions/review-custom-gates-for-run`, `projects/add-field-for-org`, `pulls/request-reviewers` and force slices to
  edit N. Fix: restate D5's rules so every section of the pinned reference reads as its table means. [SR-B2]
- **X6 (B) — oracles a wrong build passes.** Add to the Correctness Properties: a path value `expand` changes
  (`area/ui` → `area%2Fui`, `help wanted` → `help%20wanted`); one call with an undocumented path, query and body name
  together, each named; an AC-5.3 case whose record differs only by method. [TA-B1, TA-B2, TA-B3, SR-C5]

## C/D — apply in the same pass, no new round

- SR-C1 fill `owner`/`repo` defaults before the parameter checks. SR-C2 restate D3's "no `Link`" sentence. SR-C3 keep
  "JSON array" on one docstring line. SR-C4 the slice's list example passes every path value. SR-C6 the map-shaped
  body (`copilot/set-copilot-content-exclusion-for-organization`) to Residuals. SR-D1 leave `prompt.md` (conductor's).
- ST-C1 D8 states it supersedes #17 D2's "What a family's change edits" for part 2. ST-C2 D4's check raises (one
  exception type, caught by the entry script → exit 2); `EXIT_REFUSED` lives in `commands/_common.py`. ST-C3 the
  docstring test goes in `test_github_wrapper_compat.py` (adding a test there is allowed). ST-D1 named arguments.
- BP-C1 follow `gh api`: `-f/--raw-field N=TEXT` string, `-F/--field N=JSON` typed. BP-C2 one clause on
  comma-separated list filters.
- DV-C1 the map's `call` sentence goes before the "not installed" caveat, which says the fork has no `call`. DV-D1 the
  E2E bullet names `test_the_script_runs_by_path` as the by-path run.
- SEC-C1 the destructive-operations bullet says `owner`/`repo` default to `origin` and no prompt comes first. SEC-C2
  secret body values to the "value from a file" residual. SEC-D1 `json.dumps` also for argparse type-error text.
- TA-C1 page 2 served from a `/repositories/1/…` URL proves the `next` link is followed. TA-C2 the docstring test
  checks "indented JSON". TA-C3 `is_unreachable` examples that hit one condition each (`orgs/get`,
  `apps/get-authenticated`).

Next: one author pass over X1–X6 and every C/D above; delta review in iteration 02.

## Iteration 02 (delta)

test-architect CLEAN, TEST-READY (21 COVERED, 0 GAP); standards CLEAN; best-practice CLEAN; security CLEAN; devops CLEAN; spec-review READY. Every X1–X6 fix site APPLIED. The C/D items (TA-C4, TA-C5, SR-C1, SR-C2, SR-D1, SEC-C, BP-C, ST-C1, ST-C2, ST-D1) were applied in one author pass. Approved (DL-005).
