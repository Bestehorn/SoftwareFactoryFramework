# Prompt — issue #10: integration-test the forge wrappers against ephemeral sff-test-* repositories (S4)

Tier: M — a session fixture, two deletion paths with guards, a wrapper origin guard and a CI job, across the test
tree, the product wrapper and the workflow, with a design choice in each (issue #10 "Tier: M"; DL-001).

Kind: FEATURE.

## Goal

Decision S4 (`docs/reports/self-hosting-proposal-2026-11-07.md` §5, §10) requires the forge-facing code to be tested
against a real forge through ephemeral repositories that every test run creates and deletes itself, on every PR.
None of it exists: nothing in `src/` creates or deletes a repository, and `.github/workflows/ci.yml` has no forge job.

> implement the ephemeral-repository integration tests per S4 (GitHub first), including the CI job and the guards,
> with the operator-provided token as an explicit prerequisite item. (issue #10, Ask)

The draft criteria of issue #10 are the ask: AC-1 (session fixture: create a private `sff-test-<run id>`
repository, seed it, clone it into a temporary directory with its own `credentials/` file, delete it at session end
whether the tests passed or failed), AC-2 (delete only a repository created in this run whose name is
`sff-test-<this run's id>`), AC-3 (at run start, delete the `sff-test-*` repositories older than a day created by
the same token, and no other), AC-4 (while the test marker is set, the development wrapper refuses an `origin` that
is not an `sff-test-*` repository), AC-5 (on every PR, CI runs the forge tests in their own job, in parallel with the
others, with the dedicated token from a CI secret), UB-1 (the fake-host unit tests and the `verify` matrix keep
running without network access or the new token), UB-2 (`credentials/github-pat.txt` stays the only credential the
toolchain wrapper uses for this repository).

## Operator facts (issue #10 comments 6820424075, 6820621970, 6828747536)

- The token is fine-grained, its resource owner the organization `bestehorn-sff-test`, repository access "All
  repositories", permissions Administration write and Contents write. "Created by the same token" therefore means
  "in that organization": the token reaches no other owner.
- Local credential: `credentials/github-sff-testing-pat.txt` (git-ignored by `.gitignore` `credentials/*`). CI: the
  repository Actions secret `SFF_TEST_TOKEN` (the operator is adding it).
- Repositories are created under the organization (`POST /orgs/{org}/repos`, record `repos/create-in-org`), not under
  the user.

## Scope

1. AC-1 to AC-5, UB-1, UB-2 as above, GitHub only.
2. The first real-repository tests run the PRODUCT wrapper `src/payload/scripts/github_wrapper.py` (the rewrite is
   finished: #12 and #14 closed) as a subprocess in the fixture's clone; it targets `origin` of its working
   directory and reads that directory's `credentials/github-pat.txt` (`_detect_repo`, `_load_token`).
3. The real-forge items closed issues deferred to this one, each "on #10's fixture; the rest by #28's method": #17
   (today's subcommands on the new transport), #27 (`repos`, `git`), #31 (`actions`, `checks`, `code-scanning`,
   `dependabot`, `secret-scanning`), #32 (`issues`, `pulls`, `reactions`, `search`, `activity`, `gists`). One or a few
   representative real-forge tests per slice; the fake-host suites stay the proof for the rest. An operation a free
   organization's private repository cannot serve is tested as GitHub's documented answer, or left out with the
   reason, never faked.
4. Docs: `docs/forLLMConsumption.md`, the `docs/ProjectPlan.md` debt line, the credential's setup note.

## Constraints

- UB-1 and `tests-must-not-fail.md` together: the default collection (`scripts/run_tests.py` without paths, the CI
  `verify` matrix) never needs the network or the token, and no skip, xfail, marker filter or conftest collection
  hook keeps a forge test from running. The forge tests are a SEPARATE SUITE that a dedicated CI job runs on every PR
  and whose failure fails the pipeline. The design picks its location and mechanism and states why it is not an
  exclusion dodge. Precedents: the vendored hook suite `.claude/hooks/tests` (outside `testpaths`, its own check
  entry, `run_checks.py` `hook_suite_argv`) and the on-request `e2e` group (`e2e_argv`).
- The toolchain is not edited (`config/toolchain.json`; `scripts/run_checks.py`, `scripts/run_tests.py` and
  `scripts/github_wrapper.py` are installed copies). `.github/workflows/ci.yml` is this repository's own
  (`config/toolchain.json` `not_installed` `templates/ci/*`), so the job goes there. Nothing may depend on a product
  change reaching the toolchain before a promotion.
- `ci.yml`'s contract (its header): no fail-fast, one command per check job, and a report job that always runs and
  decides — it must fail when the forge job fails.
- No environment variable carries the token or the marker (`no-environment-vars.md`). The token never appears in an
  argv, a URL, a log line, a `.git/config` or a committed file; the temporary clone, its credential file included,
  is removed at session end.
- Every remote operation goes through a wrapper (`use-git-wrapper-scripts.md`): the fixture's create, delete and list
  calls use the product wrapper's records (`repos/create-in-org`, `repos/delete`, `repos/list-for-org`) or its
  `Transport`; no `gh`, no curl. Git itself (clone, push) is allowed and must authenticate without exposing the token.
- One repository per run, not per test (rate limits). No workflow file in the seed, so the test repository runs no
  Actions. No human step (`always-test-e2e.md`).
- Shipped code stays standard library; the forge suite is this repository's own test (pytest), never shipped.

## Out of scope

GitLab (#11). The merge steward and the delivery CI against a real forge (S4 names them; this issue's work items do
not) — a residual. Changing the toolchain.

## The issue's open questions

1. Which wrapper the first real test exercises: the product wrapper (Scope 2).
2. How the forge tests stay out of the default `tests` group: the design decides (Constraints, first bullet).
3. The local credential's name: `credentials/github-sff-testing-pat.txt` (the operator's). Whether a `*.template`
   stub ships with it: the design decides.
