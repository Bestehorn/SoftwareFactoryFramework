# Prompt — issue #11: real-GitLab integration tests on ephemeral sff-test-* projects

Tier: M — the GitLab twin of #10: a session fixture with two guarded deletion paths, an origin guard in the product
GitLab wrapper, a CI job and real-forge tests, across the test tree, the product wrapper and the workflow, with a
design choice in each (DL-001).

Kind: FEATURE.

## Goal

Issue #11's last open work item is "Real-GitLab integration tests (needs a GitLab equivalent of #10)". Decision S4
(`docs/reports/self-hosting-proposal-2026-11-07.md` §5) has the forge-facing code tested against a real forge through
ephemeral projects every run creates and deletes itself, on every pull request. #10 built that for GitHub
(`.claude/specs/issue-10-forge-integration-tests/`, merged as 83a1415); nothing exercises the product GitLab wrapper
`src/payload/scripts/gitlab_wrapper.py` (package `gitlab_api/`) against a real GitLab. Every GitLab slice (#13, #15,
#35 to #44, #46, #63) left its real-instance check to this run.

The ask is #10's criteria, restated for GitLab: AC-1 a session fixture creates one private `sff-test-<run id>` project
in the test group, seeds it, clones it into a temporary directory with its own `config/gitlab.json`, and deletes it at
session end whatever the result; AC-2 the teardown deletes only the project this run created; AC-3 at run start, the
`sff-test-*` projects of the test group older than a day are deleted, and no other; AC-4 while the test marker is set,
the product GitLab wrapper refuses a project that is not an `sff-test-*` one; AC-5 on every pull request CI runs the
suite in its own job with the dedicated token from a CI secret, and its failure fails the pipeline. UB-1 the fake-host
suites and the `verify` matrix keep running without network or token; UB-2 the checkout's own `config/gitlab.json`
is neither read nor written by the suite.

## Operator facts (issue #11 comments 6923784402, 7061531929, 7077139116, 7077150394; prompts.md)

- Host: gitlab.com. The operator first named https://gitlab.aws.dev/bestehorn-sff-test; every request there, with a
  `PRIVATE-TOKEN`, a `Bearer` or git basic auth, is answered `302` by the instance's load balancer to the corporate
  sign-in (`idp.federate.amazon.com`), so no token reaches GitLab; the operator then chose gitlab.com ("Use
  gitlab.com").
- Test group: a private top-level gitlab.com group the operator creates; its path is reported by the operator. Working
  value `bestehorn-sff-test` (DL-002), corrected when the operator names it.
- Token: a personal access token of a group service account (Settings > Service accounts), scope `api`, the account a
  member of the group with the Owner role (deleting a project needs Owner). It reaches only that group.
- Local credential: `credentials/gitlab-sff-testing-pat.txt` (git-ignored by `.gitignore` `credentials/*`); CI: the
  repository Actions secret `SFF_GITLAB_TEST_TOKEN`. Never `config/gitlab.json`, which this repository does not
  git-ignore.

## Scope

1. AC-1 to AC-5, UB-1, UB-2 as above, gitlab.com only. Project creation, deletion and the leftover listing go through
   the product GitLab wrapper's records or its transport (`gitlab_api/transport.py`); git clone and push from the
   fixture clone authenticate without exposing the token.
2. The real-forge tests run the PRODUCT GitLab wrapper as a subprocess in the fixture clone, which targets the clone's
   `config/gitlab.json` (`CONFIG_FILE`, `_load_config`). One or a few representative tests per slice, the fake-host
   suites staying the proof for the rest: today's subcommands on the transport (#13: an issue round trip, a
   merge-request round trip from a pushed branch, labels, branches, pipelines on a project that runs none); REST
   records through `call` from the project, repository, issues and merge-request families; one GraphQL-only
   capability (#44); the request forms of #63 that a private Free-tier project serves. An operation the project
   cannot serve (administrator-only, Premium-only, OAuth-only) is tested as GitLab's documented answer or left out
   with the reason, never faked.
3. Docs: `docs/forge-suite.md` (the GitLab token and secret beside the GitHub ones), `docs/forLLMConsumption.md`,
   `docs/ProjectPlan.md` if it lists the GitLab real-instance tests as debt.

## Constraints

- #10's design is the precedent for every mechanism it settled: the separate suite outside `testpaths`, the
  interpreter-option test marker (`-X sff_test_marker`, `_refuse_unless_ephemeral`), the run id, the credential file
  with the main-worktree fallback, the credential written in CI by one step from the secret, the report job's verdict.
  Reuse it; deviate only where GitLab differs (the wrapper reads a configured project id, not a git `origin`; gitlab.com
  delays project deletion), and say why.
- `tests-must-not-fail.md`: no skip, xfail, marker filter or collection hook keeps a forge test from running; the
  default collection needs no network and no token.
- The toolchain is not edited (`config/toolchain.json`); `.github/workflows/ci.yml` is this repository's own.
- No environment variable carries the token or the marker except the one CI step whose `env:` maps the secret to the
  command that writes the credential file (`no-environment-vars.md`). The token appears in no argv, URL, log line,
  `.git/config` or committed file; the temporary clone and its `config/gitlab.json` are removed at session end.
- One project per run, not per test (gitlab.com rate limits). No `.gitlab-ci.yml` in the seed, so no pipeline runs.
  No human step (`always-test-e2e.md`).
- The GitHub forge suite, its job and its tests keep their behaviour. Shipped code stays standard library; the suite
  is this repository's own pytest, never shipped.

## Out of scope

gitlab.aws.dev and any self-managed instance. Administrator-only and Premium-only APIs. The merge steward and the
delivery CI on GitLab. The findings-ledger rows that name "#11's run" are settled only where a scoped test happens to
answer them; the rest stay rows. Changing the toolchain.

## The issue's open questions

1. "A generic, reference-driven operation layer, or hand-written subcommands per operation?" — settled by #13 and #28.
2. "Which GitLab instance and token do real-forge tests use?" — gitlab.com, a group service account's `api` token
   (Operator facts).

Implementation is test-first with captured red and green evidence; the forge suite is the change's end-to-end check,
run by its CI job on every pull request.
