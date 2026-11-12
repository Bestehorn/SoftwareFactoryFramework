# Requirements — issue #10: integration tests of the forge wrapper against ephemeral `sff-test-*` repositories (S4)

Tier: M. Kind: FEATURE. Scope: `prompt.md` and DL-001, GitHub only.

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Issue #10, Ask: "implement the ephemeral-repository integration tests per S4 (GitHub first), including the CI job
   and the guards, with the operator-provided token as an explicit prerequisite item."
3. User, 2026-11-12: "the org is called "bestehorn-sff-test"" (issue #10 comment 6828747536). The operator's other
   answers (the token, its file, the CI secret) are in `prompts.md`.

## Overview

Decision S4 (`docs/reports/self-hosting-proposal-2026-11-07.md` §5) has the forge-facing code tested against the real
forge through a repository each run creates and deletes itself, on every pull request. This change builds that for
GitHub: a session fixture with its two guarded deletion paths, an origin guard in the product wrapper, a CI job, and
the first real-forge tests of the slices #17, #27, #31 and #32 deferred to this issue.

Numbering: issue #10 AC-1 to AC-5 are Requirements 1 to 5 here, and UB-1 and UB-2 keep their numbers; Requirements 6
to 9 are the credential, the suite separation, the real-forge tests and the docs.

## Glossary

- **Forge suite** — the pytest tests of this change that talk to github.com; this repository's own, never shipped.
  A **run** is one pytest session of it; its **run id** is the run's own.
- **Test organization** — `bestehorn-sff-test`, the organization the forge suite's configuration names, and the test
  token's resource owner (`prompt.md`, operator facts).
- **Ephemeral repository** — the repository a run creates: `sff-test-<run id>` in the test organization.
- **`sff-test-*` name** — a repository name that starts with `sff-test-`.
- **Fixture clone** — the run's working clone of the ephemeral repository, in a temporary directory.
- **Test credential file** — `credentials/github-sff-testing-pat.txt`; the **test token** is the token it holds.
- **Product wrapper** — `src/payload/scripts/github_wrapper.py` with its package `github_api/`. The **toolchain
  wrapper** is the installed `scripts/github_wrapper.py`.
- **Test marker** — what the forge suite sets on each product-wrapper invocation it makes (Requirement 4).
- **Forge job** — the `.github/workflows/ci.yml` job of Requirement 5.

## Requirements

### Requirement 1 — One ephemeral repository per run (issue AC-1)

As the owner of the forge-facing code, I want every run to provision its own repository and remove it, so that the
wrapper is tested against the real forge and nothing outlives the run.

- AC-1.1 WHEN a run starts, THE forge suite SHALL create one private repository named `sff-test-<run id>` in the test
  organization, through the product wrapper's record `repos/create-in-org`
  (`src/payload/scripts/github_api/families/repos.py`) or its `Transport`, and every test of the run SHALL use that
  one repository.
- AC-1.2 Two runs, concurrent or one after the other, SHALL never have the same run id.
- AC-1.3 Before the first test, the ephemeral repository SHALL hold a seed commit on its default branch, with no file
  under `.github/workflows/`, and the fixture clone SHALL be a clone of it at that commit whose `origin` is the
  ephemeral repository and whose own `credentials/github-pat.txt` holds the test token.
- AC-1.4 WHEN a run ends, whether its tests passed, failed or raised an error, THE forge suite SHALL delete the
  ephemeral repository (record `repos/delete`) and remove the fixture clone, its credential file included.

### Requirement 2 — The teardown deletes only its own repository (issue AC-2)

As the owner of the test organization and of this backlog, I want the teardown's deletion to reach only the
repository its run created, so that a defect in the suite cannot delete anything else.

- AC-2.1 THE teardown SHALL send a deletion only for the repository whose owner is the test organization and whose
  name is `sff-test-<this run's id>`, and only after this run's creation of it succeeded.
- AC-2.2 IF the teardown's deletion target is any other repository (another owner, another name, another run's id),
  THEN THE forge suite SHALL send no request for it and SHALL raise an error naming the refused target.
- AC-2.3 IF this run's creation of its repository did not succeed, THEN THE teardown SHALL send no deletion request.

### Requirement 3 — The leftover sweep (issue AC-3)

As the owner of the test organization, I want each run to remove what crashed runs left behind, so that leftovers do
not accumulate.

- AC-3.1 WHEN a run starts, THE forge suite SHALL list the test organization's repositories (record
  `repos/list-for-org`, every page) and delete (record `repos/delete`) each one whose owner is the test organization,
  whose name is an `sff-test-*` name, and whose `created_at` is more than a day before the sweep. Issue #10's
  "created by the same token" is this organization: the token reaches no other owner (`prompt.md`, operator facts).
- AC-3.2 THE sweep SHALL send no deletion for any other repository: not one created a day or less before the sweep
  (a concurrent run's ephemeral repository among them), not one without an `sff-test-*` name, not one of another
  owner.

### Requirement 4 — The product wrapper's origin guard (issue AC-4)

As the owner of this backlog, I want the product wrapper to refuse every repository but an ephemeral one while the
forge suite drives it, so that a test that runs it in the wrong directory cannot act on a real repository.

- AC-4.1 WHILE the test marker is set, IF the `origin` that `_detect_repo` reads names a repository without an
  `sff-test-*` name, THEN THE product wrapper SHALL, for every subcommand (the delivery verbs and `call` included),
  send no request, write to standard error a message saying that the test marker is set and naming that owner and
  repository and no credential, and exit 2 (`EXIT_REFUSED`).
- AC-4.2 WHILE the test marker is set, WHEN the `origin` names a repository with an `sff-test-*` name, THE product
  wrapper SHALL behave as it does without the marker.
- AC-4.3 THE test marker SHALL be set by the forge suite on every product-wrapper invocation it makes, SHALL reach the
  wrapper whatever the working directory of the invocation, SHALL be no environment variable, and SHALL be absent
  from every invocation that is not the forge suite's and from every ordinary checkout. Its mechanism is
  `design.md`'s.

### Requirement 5 — The forge CI job (issue AC-5)

As a reviewer of a pull request, I want the forge suite run on it in its own job, and its failure to fail the
pipeline, so that a forge regression cannot merge unseen.

- AC-5.1 WHEN `.github/workflows/ci.yml` runs (on every pull request, on a push to `main` and on
  `workflow_dispatch`), THE workflow SHALL run the whole forge suite in one dedicated job with no `needs:` between it
  and `verify`.
- AC-5.2 THE forge job SHALL give the suite the test token from the repository Actions secret `SFF_TEST_TOKEN`
  through the test credential file of its checkout (Requirement 6), and its check SHALL be one command that reports
  every failing forge test of the run (the `ci.yml` header: no fail-fast, one command per check job).
- AC-5.3 IF `SFF_TEST_TOKEN` is not available to the run, THEN THE forge job SHALL fail with a message saying that the
  secret `SFF_TEST_TOKEN` is unavailable.
- AC-5.4 THE `report` job SHALL run after the forge job and `verify`, whatever their results, and its verdict SHALL
  fail when the forge job's result is anything other than success.

### Requirement 6 — The test credential

As the operator, I want the test token kept in one git-ignored file and exposed nowhere, so that the dedicated token
cannot leak and never mixes with the backlog's token.

- AC-6.1 THE forge suite SHALL read the test token only from the test credential file of the checkout that runs it
  or, when that checkout is a linked worktree without one, of the repository's main working tree (both git-ignored by
  `.gitignore` `credentials/*`).
- AC-6.2 IF the test credential file is missing, is empty or holds a placeholder, or does not hold one token (the
  refusals `github_wrapper.py` `_load_token` makes for `CREDENTIALS_FILE`), THEN THE run SHALL fail before any request
  with a message that names the file and none of its contents; no forge test SHALL be skipped for it.
- AC-6.3 THE test token SHALL appear in no argv, URL, log line, test report, `.git/config` or committed file, and no
  environment variable SHALL carry it except in the forge job's single workflow step whose `env:` block hands the
  secret `SFF_TEST_TOKEN` to the command that writes the test credential file (workflow-scoped configuration, as
  `no-environment-vars.md` CLARIFICATION treats a settings `env` block). The fixture's git operations (push, clone)
  SHALL authenticate with it under the same rule. Besides the test credential file, it SHALL be written only to the
  fixture clone's `credentials/github-pat.txt`.

### Requirement 7 — A separate suite

As a contributor, I want the default test run free of the network and the token, and the forge suite run whole
wherever it is run, so that neither suite can hide the other's failures.

- AC-7.1 THE default collection (`scripts/run_tests.py` with no path, which collects `pyproject.toml`
  `[tool.pytest.ini_options]` `testpaths`) and the `verify` matrix SHALL collect no forge test.
- AC-7.2 WHEN the forge suite's path is given to `scripts/run_tests.py`, THE runner SHALL collect and run every forge
  test; the forge job and a local run invoke the suite this way. Its location is `design.md`'s.
- AC-7.3 No skip, xfail, marker filter, deselection or `conftest.py` collection hook SHALL keep a forge test from
  running, or its failure from failing the run, when the forge suite runs.

### Requirement 8 — Real-forge tests of the deferred slices (`prompt.md` Scope 2 and 3)

As the owner of #17, #27, #31 and #32, I want each slice's commands exercised against the real forge, so that what the
fake host proves is confirmed by GitHub's own answers.

- AC-8.1 Each real-forge test SHALL run the product wrapper as a subprocess, with the fixture clone as its working
  directory and the test marker set, and SHALL assert each invocation's exit code and printed response against what
  the test knows in advance: the ephemeral repository's state as the fixture and the test made it, or the response
  GitHub documents.
- AC-8.2 #17 (today's subcommands on the new transport): an issue round trip (`create-issue`, `get-issue`,
  `comment-issue`, `label-add`, closing it with `update-issue`) and a pull-request round trip (a branch pushed with
  git from the fixture clone, `create-pr`, `get-pr`, `merge-pr`), each step's effect read back through the wrapper.
- AC-8.3 #27: at least one `repos` record and one `git` record through `call`, each response asserted against the
  seed commit (its SHA, its tree, the default branch).
- AC-8.4 #31: an `actions` record through `call`, asserted against a repository that runs no workflow; and for each
  of `checks`, `code-scanning`, `secret-scanning` and `dependabot`, either a record called and its answer asserted as
  GitHub documents it for this token and a private repository of a free organization, or, where GitHub documents no
  such answer, the family named with that reason in the slice test's docstring and not called.
- AC-8.5 #32: at least one record of each of `issues`, `pulls`, `reactions`, `search`, `activity` and `gists` through
  `call`; the `gists` record SHALL be one that reads and creates nothing.
- AC-8.6 No real-forge test SHALL create, change or delete anything outside the ephemeral repository, and no fake
  host or canned response SHALL stand in for github.com in the forge suite.

### Requirement 9 — Docs

As an operator or agent setting up or running the forge suite, I want its credential and its commands written down,
so that the suite can be run without reading its code.

- AC-9.1 A setup note for the test credential SHALL name the test credential file, the token kind (fine-grained), its
  resource owner (the test organization), its repository access ("All repositories"), every permission the forge
  suite's requests need as docs.github.com "Permissions required for fine-grained personal access tokens" lists them,
  the Actions secret `SFF_TEST_TOKEN`, and that only a machine that runs the forge suite locally needs the file. Where
  it lives is `design.md`'s.
- AC-9.2 `docs/forLLMConsumption.md` SHALL name the forge suite, its local command, its credential and its CI job, and
  `test/test_instruction_corpus_budget.py` `test_llm_map_within_cap` SHALL CONTINUE TO pass.
- AC-9.3 `docs/ProjectPlan.md` SHALL no longer list "the ephemeral-repository forge tests need their dedicated
  create/delete token" as known debt.

## Unchanged behaviour

- UB-1 (issue UB-1) The default collection and every `verify` leg SHALL CONTINUE TO pass with no network access and no
  test credential file, and the fake-host suites (`src/payload/test/test_github_*.py`, `test/test_github_*.py`) SHALL
  CONTINUE TO be the proof of every record the forge suite does not call.
- UB-2 (issue UB-2) `credentials/github-pat.txt` SHALL CONTINUE TO be the only credential the toolchain wrapper uses
  for this repository: the forge suite SHALL neither read nor write the `credentials/github-pat.txt` of the checkout
  that runs it.
- UB-3 WHILE the test marker is not set, THE product wrapper SHALL CONTINUE TO send the same requests, print the same
  output and return the same exit code for every argv as before this change; its existing tests
  (`src/payload/test/test_github_wrapper_compat.py`, `test/test_github_wrapper_fork_parity.py`,
  `test/test_github_wrapper_contract.py`, `test/test_github_wrapper_coverage.py` among them) SHALL CONTINUE TO pass
  with no assertion edited, and it SHALL CONTINUE TO import only the standard library
  (`test/test_github_wrapper_coverage.py` `test_the_wrapper_imports_only_the_standard_library`).
- UB-4 No toolchain file (`config/toolchain.json` and the files it lists, the installed `scripts/github_wrapper.py`,
  `scripts/run_tests.py` and `scripts/run_checks.py` among them) SHALL be edited by this change,
  `test/test_toolchain_integrity.py` SHALL CONTINUE TO pass, and nothing in this change SHALL depend on a product change
  reaching the toolchain before a promotion.

E2E: the forge suite is this change's end-to-end check: the product wrapper driven through its command line against
github.com, by the forge job on every pull request (Requirement 5). Nothing deploys.

## Residuals

- The merge steward and the delivery CI against a real forge: S4 names them, issue #10's work items do not.
- GitLab's ephemeral projects: #11.
- The token as recorded (Administration and Contents write) lacks what Requirement 8's issue, pull-request, Actions,
  scanning and Dependabot calls need (docs.github.com "Permissions required for fine-grained personal access tokens":
  Issues write, Pull requests write, Actions read, Code scanning alerts read, Secret scanning alerts read, Dependabot
  secrets read); granting them is the operator's step AC-9.1 names.
- The origin guard judges the repository name, as issue #10 AC-4 does, not the owner; the test token reaches no owner
  but the test organization.
