# Requirements — issue #11: real-GitLab integration tests on ephemeral `sff-test-*` projects

Tier: M. Kind: FEATURE. Scope: `prompt.md` and DL-001 to DL-003, gitlab.com only.

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Issue #11, work item: "Real-GitLab integration tests (needs a GitLab equivalent of #10)".
3. User, 2026-11-16: "Let's set up the GitLab test target for #11; walk me through the exact steps I need to perform
   on gitlab."
4. User, 2026-11-21: "There is no "Service Accounts" submenu in the settings of the group"
5. User, 2026-11-22: "The group URL is https://gitlab.aws.dev/bestehorn-sff-test" (issue #11)
6. User, 2026-11-22: "Use gitlab.com" (issue #11).

## Overview

Decision S4 (`docs/reports/self-hosting-proposal-2026-11-07.md` §5) has the forge-facing code tested against the real
forge through a project each run creates and deletes itself, on every pull request. Issue #10 built that for GitHub
(`.claude/specs/issue-10-forge-integration-tests/`). This change builds its GitLab twin: a session fixture with its two
guarded deletion paths, a project guard in the product GitLab wrapper, a CI job, and the first gitlab.com tests of the
wrapper's subcommands (#13), its `call` records, its GraphQL-only capabilities (#44) and its request forms (#63).

Numbering: Requirements 1 to 9 and UB-1 and UB-2 restate issue #10's for GitLab; UB-3 to UB-5 are this change's.

## Glossary

- **GitLab forge suite** — the pytest tests of this change that talk to gitlab.com; this repository's own, never
  shipped. A **run** is one pytest session of it; its **run id** is the run's own.
- **Test group** — the top-level gitlab.com group the suite's configuration names (working value `bestehorn-sff-test`,
  DL-002); the test token reaches no other group (`prompt.md`, operator facts).
- **Ephemeral project** — the project a run creates: path `sff-test-<run id>` in the test group.
- **`sff-test-*` path** — a project path that starts with `sff-test-`.
- **Fixture clone** — the run's working clone of the ephemeral project, in a temporary directory.
- **Test credential file** — `credentials/gitlab-sff-testing-pat.txt`; the **test token** is the token it holds.
- **Product GitLab wrapper** — `src/payload/scripts/gitlab_wrapper.py` with its package `gitlab_api/`. Its
  **configured project** is the `project_id` of the `config/gitlab.json` of its working directory (`CONFIG_FILE`,
  `_load_config`).
- **Test marker** — issue #10's test marker (`github_wrapper.py` `TEST_MARKER_OPTION`), set by the GitLab forge suite
  on each product GitLab wrapper invocation it makes.
- **GitLab forge job** — the `.github/workflows/ci.yml` job of Requirement 5. The **GitHub forge suite** is
  `test/forge/` as issue #10 built it; the `forge` job runs it.

## Requirements

### Requirement 1 — One ephemeral project per run (issue #10 AC-1)

As the owner of the GitLab wrapper, I want every run to provision its own project and remove it, so that the wrapper
is tested against gitlab.com and nothing outlives the run.

- AC-1.1 WHEN a run starts, THE GitLab forge suite SHALL create one private project with the path `sff-test-<run id>`
  in the test group, through the product GitLab wrapper's record `tenant-scale#create-a-project`
  (`src/payload/scripts/gitlab_api/families/tenant_scale.py`) or its `Transport` (`gitlab_api/transport.py`), and
  every test of the run SHALL use that one project.
- AC-1.2 Two runs, concurrent or one after the other, SHALL never have the same run id.
- AC-1.3 Before the first test, the ephemeral project SHALL hold a seed commit on its default branch with no
  `.gitlab-ci.yml`, no pipeline SHALL run in it, and the fixture clone SHALL be a clone of it at that commit whose
  `origin` is the ephemeral project and whose own `config/gitlab.json` holds `hostname` `gitlab.com`, the ephemeral
  project as `project_id` and the test token as `token`.
- AC-1.4 WHEN a run ends, whether its tests passed, failed or raised an error, THE GitLab forge suite SHALL delete the
  ephemeral project (record `tenant-scale#delete-a-project`) and remove the fixture clone, its `config/gitlab.json`
  included. Whether the deletion also removes a project gitlab.com first marks for deletion is `design.md`'s.

### Requirement 2 — The teardown deletes only its own project (issue #10 AC-2)

As the owner of the test group and of this backlog, I want the teardown's deletion to reach only the project its run
created, so that a defect in the suite cannot delete anything else.

- AC-2.1 THE teardown SHALL send a deletion only for the project this run's creation returned, whose namespace is the
  test group and whose path is `sff-test-<this run's id>`, and only after that creation succeeded.
- AC-2.2 IF the teardown's deletion target is any other project (another namespace, another path, another run's id),
  THEN THE GitLab forge suite SHALL send no request for it and SHALL raise an error naming the refused target.
- AC-2.3 IF this run's creation of its project did not succeed, THEN THE teardown SHALL send no deletion request.

### Requirement 3 — The leftover sweep (issue #10 AC-3)

As the owner of the test group, I want each run to remove what crashed runs left behind, so that leftovers do not
accumulate.

- AC-3.1 WHEN a run starts, THE GitLab forge suite SHALL list the test group's projects (record
  `tenant-scale#list-projects`, every page) and delete (record `tenant-scale#delete-a-project`) each one whose
  namespace is the test group, whose path is an `sff-test-*` path, and whose `created_at` is more than a day before
  the sweep.
- AC-3.2 THE sweep SHALL send no deletion for any other project: not one created a day or less before the sweep (a
  concurrent run's ephemeral project among them), not one without an `sff-test-*` path, not one of another namespace.
- AC-3.3 IF a project AC-3.1 selects is one GitLab has already scheduled for deletion, THEN THE sweep SHALL NOT treat
  it as a failure, and the run SHALL go on. Whether the sweep removes such a project permanently is `design.md`'s.

### Requirement 4 — The product GitLab wrapper's project guard (issue #10 AC-4)

As the owner of this backlog, I want the product GitLab wrapper to refuse every project but an ephemeral one while the
GitLab forge suite drives it, so that a test that runs it in the wrong directory cannot act on a real project.

- AC-4.1 WHILE the test marker is set, IF `config/gitlab.json` passes `_load_config` and its `project_id` is not an
  `sff-test-*` project path (`design.md` D2), THEN THE product GitLab wrapper SHALL, for every subcommand (the delivery
  verbs and `call` included), send no request other than, at most, a read of the configured project, write to standard
  error a message saying that the test marker is set and naming the configured project and no credential, and exit 2.
  A configuration `_load_config` refuses exits 1 with nothing sent, as it does without the marker.
- AC-4.2 WHILE the test marker is set, WHEN the configured project's path is an `sff-test-*` path, THE product GitLab
  wrapper SHALL print the same output, return the same exit code and send the same requests, besides at most that
  read, as it does without the marker. How the wrapper knows the path of the configured project is `design.md`'s.
- AC-4.3 THE test marker SHALL be set by the GitLab forge suite on every product GitLab wrapper invocation it makes,
  SHALL reach the wrapper whatever the working directory of the invocation, SHALL be no environment variable, and
  SHALL be absent from every invocation that is not a forge suite's and from every ordinary checkout.

### Requirement 5 — The GitLab forge CI job (issue #10 AC-5)

As a reviewer of a pull request, I want the GitLab forge suite run on it in its own job, and its failure to fail the
pipeline, so that a GitLab regression cannot merge unseen.

- AC-5.1 WHEN `.github/workflows/ci.yml` runs (on every pull request, on a push to `main` and on `workflow_dispatch`),
  THE workflow SHALL run the whole GitLab forge suite in one dedicated job with no `needs:` between it and `verify` or
  the `forge` job.
- AC-5.2 THE GitLab forge job SHALL give the suite the test token from the repository Actions secret
  `SFF_GITLAB_TEST_TOKEN` through the test credential file of its checkout (Requirement 6), and its check SHALL be one
  command that reports every failing GitLab forge test of the run (the `ci.yml` header: no fail-fast, one command per
  check job).
- AC-5.3 IF `SFF_GITLAB_TEST_TOKEN` is not available to the run, THEN THE GitLab forge job SHALL fail with a message
  saying that the secret `SFF_GITLAB_TEST_TOKEN` is unavailable.
- AC-5.4 THE `report` job SHALL run after `verify`, the `forge` job and the GitLab forge job, whatever their results,
  and its verdict SHALL fail when the GitLab forge job's result is anything other than success.

### Requirement 6 — The test credential

As the operator, I want the test token kept in one git-ignored file and exposed nowhere, so that the dedicated token
cannot leak and never mixes with a checkout's own GitLab configuration.

- AC-6.1 THE GitLab forge suite SHALL read the test token only from the test credential file of the checkout that runs
  it or, when that checkout is a linked worktree without one, of the repository's main working tree (both git-ignored
  by `.gitignore` `credentials/*`).
- AC-6.2 IF the test credential file is missing, or its text, less one final line end, is empty, starts with `PASTE_`
  or holds a character outside `!` to `~` (the checks `gitlab_wrapper.py` `_refuse_incomplete` and
  `_refuse_token_characters` make of the `token` of `CONFIG_FILE`), THEN THE run SHALL fail before any request with a
  message that names the file and none of its contents; no GitLab forge test SHALL be skipped for it.
- AC-6.3 THE test token SHALL appear in no argv, URL, log line, test report, `.git/config` or committed file (a commit
  of the fixture clone included), and no environment variable SHALL carry it except in the GitLab forge job's single
  workflow step whose `env:` block hands the secret `SFF_GITLAB_TEST_TOKEN` to the command that writes the test
  credential file (workflow-scoped configuration, as `no-environment-vars.md` CLARIFICATION treats a settings `env`
  block). The fixture's git operations (push, clone) SHALL authenticate with it under the same rule. Besides the test
  credential file, it SHALL be written only to the fixture clone's `config/gitlab.json` and to one file inside the
  fixture clone's `.git/` directory, which the fixture's git credential helper reads.

### Requirement 7 — A separate suite

As a contributor, I want the default test run free of the network and the token, and the GitLab forge suite run whole
wherever it is run, so that no suite can hide another's failures.

- AC-7.1 THE default collection (`scripts/run_tests.py` with no path, which collects `pyproject.toml`
  `[tool.pytest.ini_options]` `testpaths`) and the `verify` matrix SHALL collect no GitLab forge test.
- AC-7.2 WHEN the GitLab forge suite's path is given to `scripts/run_tests.py`, THE runner SHALL collect and run every
  GitLab forge test; the GitLab forge job and a local run invoke the suite this way. Its location, its own directory
  or beside the GitHub forge suite in `test/forge/`, is `design.md`'s.
- AC-7.3 No skip, xfail, marker filter, deselection or `conftest.py` collection hook SHALL keep a GitLab forge test
  from running, or its failure from failing the run, when the GitLab forge suite runs.

### Requirement 8 — Real-GitLab tests of the wrapper (`prompt.md` Scope 2)

As the owner of the GitLab slices, I want each slice's commands exercised against gitlab.com, so that what the fake
host proves is confirmed by GitLab's own answers.

- AC-8.1 Each real-GitLab test SHALL run the product GitLab wrapper as a subprocess, with the fixture clone as its
  working directory and the test marker set, and SHALL assert each invocation's exit code and printed response against
  what the test knows in advance: the ephemeral project's state as the fixture and the test made it, or the response
  GitLab documents.
- AC-8.2 #13 (today's subcommands on the transport): an issue round trip (`issue create`, `issue show`,
  `issue comment`, `issue label-add`, `issue close`), labels (`label create`, `label list`), a merge-request round
  trip (a branch pushed with git from the fixture clone, `mr create`, `mr get`, `mr merge`), `delete-branch` of a
  branch pushed with git, each step's effect read back through the wrapper, and `pipeline status` asserted against a
  project that runs no pipeline.
- AC-8.3 REST records through `call` (`gitlab_api/commands/call.py`, `call <operation-id>`): at least one record each
  of GitLab's Projects API (`tenant_scale.py`), of its commits or repository-tree API (`create.py`), each such response
  asserted against the seed commit (its SHA, its tree, the default branch), of its Issues or Notes API (`plan.py`), and
  of its Merge requests API (`ai_coding.py`).
- AC-8.4 #44: one capability of `gitlab_api/graphql_only.py` that a private Free-tier project of a non-administrator
  serves, through `call graphql#<field>`, its answer asserted against the ephemeral project's state.
- AC-8.5 #63: for each request form the `call.py` module docstring lists for issue #63 (`--endpoint`, a positional
  name given once per place, a `[.format]` suffix, a container-registry record, `--header`, a form-body member below
  its first bracket level), either a record the ephemeral project serves called with that form and its answer
  asserted, or the form handled as AC-8.6 says.
- AC-8.6 An operation the ephemeral project cannot serve (administrator-only, Premium-only, OAuth-only) SHALL either be
  called and its answer asserted as GitLab documents it for this token and a private Free-tier project, or, where
  GitLab documents no such answer, be named with that reason in the docstring of its test module and not called.
- AC-8.7 No real-GitLab test SHALL create, change or delete anything outside the ephemeral project, and no fake host or
  canned response SHALL stand in for gitlab.com in the GitLab forge suite.

### Requirement 9 — Docs

As an operator or agent setting up or running the GitLab forge suite, I want its credential and its commands written
down, so that the suite can be run without reading its code.

- AC-9.1 `docs/forge-suite.md` SHALL carry, beside the GitHub setup, the GitLab setup: the test group, a group service
  account (the group's Settings > Service accounts) that is a member of the test group with the Owner role, its
  personal access token with the scope `api`, the test credential file, the Actions secret `SFF_GITLAB_TEST_TOKEN`,
  that only a machine that runs the GitLab forge suite locally needs the file, and the suite's local command.
- AC-9.2 `docs/forLLMConsumption.md` SHALL name the GitLab forge suite, its local command, its credential and its CI
  job, and `test/test_instruction_corpus_budget.py` `test_llm_map_within_cap` SHALL CONTINUE TO pass.

`docs/ProjectPlan.md` lists no debt for these tests and is not changed.

## Unchanged behaviour

- UB-1 (issue #10 UB-1) The default collection and every `verify` leg SHALL CONTINUE TO pass with no network access and
  no test credential file, and the fake-host suites (`src/payload/test/test_gitlab_*.py`, `test/test_gitlab_*.py`)
  SHALL CONTINUE TO be the proof of every record the GitLab forge suite does not call.
- UB-2 (issue #10 UB-2) `config/gitlab.json` SHALL CONTINUE TO be the product GitLab wrapper's only credential source:
  the GitLab forge suite SHALL neither read nor write the `config/gitlab.json` of the checkout that runs it.
- UB-3 WHILE the test marker is not set, THE product GitLab wrapper SHALL CONTINUE TO send the same requests and
  return the same exit code for every argv as before this change, and to print the same output, except that its help
  text (the module docstring, `build_parser`'s description) now also names the marker refusal; its existing tests
  (`src/payload/test/test_gitlab_wrapper_compat.py`, the `test_gitlab_api_*` suites of `src/payload/test/` and
  `test/`, `test/test_gitlab_wrapper_contract.py`, `test/test_gitlab_wrapper_coverage.py` among them) SHALL CONTINUE TO
  pass with no assertion edited, and it SHALL CONTINUE TO import only the standard library
  (`test/test_gitlab_api_properties.py` `test_standard_library_only`).
- UB-4 The GitHub forge suite and the `forge` job SHALL CONTINUE TO behave as before this change: the same
  `test/forge/` tests, unedited, run by the `forge` job with the secret `SFF_TEST_TOKEN` and the credential file
  `credentials/github-sff-testing-pat.txt`, and a `report` verdict that fails unless the `forge` job succeeded. Every
  existing call of `test/forge/ephemeral.py` SHALL behave as before: the file SHALL change only by keyword-only
  parameters that default to today's values (its GitHub constants; `credential_helper_arguments` for
  `SubprocessGitRunner`), their use in the six bodies and the docstrings that describe them (`design.md` D10), and no
  other file under `test/forge/` SHALL change. Their tests (`test/test_forge_support.py`,
  `test/test_forge_suite_layout.py`) SHALL CONTINUE TO pass with no assertion removed or weakened; the one workflow
  expectation that names `report`'s exact `needs` is extended by the GitLab forge job.
- UB-5 No toolchain file (`config/toolchain.json` and the files it lists, `scripts/run_tests.py` and
  `scripts/run_checks.py` among them) SHALL be edited by this change, `test/test_toolchain_integrity.py` SHALL CONTINUE
  TO pass, and nothing in this change SHALL depend on a product change reaching the toolchain before a promotion.

E2E: the GitLab forge suite is this change's end-to-end check: the product GitLab wrapper driven through its command
line against gitlab.com, by the GitLab forge job on every pull request (Requirement 5). Nothing deploys.

## Residuals

- gitlab.aws.dev and any self-managed instance: its load balancer redirects every request to the corporate sign-in,
  so no token reaches GitLab (DL-003).
- Administrator-only and Premium-only APIs: a private Free-tier project of a non-administrator serves none (AC-8.6).
- The findings-ledger rows that name "#11's run" stay rows, except one a test of Requirement 8 answers.
- The merge steward and the delivery CI on GitLab: S4 names them, issue #11's work item does not.
- The project guard judges the project's path, not its namespace, as issue #10's guard judges the repository name.
- The test group's path is DL-002's working value until the operator names the group, and the GitLab forge job fails
  (AC-5.3) until the operator stores the token as `SFF_GITLAB_TEST_TOKEN`.
