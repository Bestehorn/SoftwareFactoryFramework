# Design — issue #11: real-GitLab integration tests on ephemeral `sff-test-*` projects

Tier: M. Kind: FEATURE. Criteria: `requirements.md` (AC-1.1 to AC-9.2, UB-1 to UB-5). Precedent: issue #10's
`design.md` (D1 to D10, merged as 83a1415); each section below names what it reuses from it and where GitLab differs.
Test files are named in the legend of the Acceptance Criteria Mapping.

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Issue #11, work item: "Real-GitLab integration tests (needs a GitLab equivalent of #10)".
3. User, 2026-11-16: "Let's set up the GitLab test target for #11; walk me through the exact steps I need to perform
   on gitlab."
4. User, 2026-11-22: "Use gitlab.com" (issue #11). The operator's other answers (the group, the token, its file, the
   CI secret) are in `prompts.md`.

## Overview

- **The project guard** (D2): while `-X sff_test_marker` is set, `gitlab_wrapper.py` `_run` refuses a configured
  `project_id` that is not a path naming an `sff-test-*` project, before any request, exit 2.
- **The GitLab forge suite** (D1): `test/forge_gitlab/`, beside `test/forge/`, with its own `pytest.ini`. Run:
  `python scripts/run_tests.py --workers 1 test/forge_gitlab`.
- **The session fixture** (D9): `test/forge_gitlab/conftest.py` `ephemeral_project` over `ephemeral.py` `provision`:
  read the test token, prepare the clone, sweep leftovers, read the group's id, create `sff-test-<run id>`, fetch its
  seed, yield, then delete the project and remove the clone.
- **The GitLab forge job** (D5): `.github/workflows/ci.yml` `forge-gitlab`, beside `verify` and `forge`; `report`
  judges all three. **The slice tests** (D6) and **the setup note** (D7).

Data flow: a test calls `SubprocessWrapperRunner.run`, which starts `python -X sff_test_marker
src/payload/scripts/gitlab_wrapper.py <argv>` with the clone as working directory. `_load_config` reads the clone's
`config/gitlab.json` (`CONFIG_FILE` is relative to the working directory), `_refuse_unless_ephemeral` passes its
`project_id` `bestehorn-sff-test/sff-test-<run id>`, and `Transport.from_config` sends to gitlab.com; a
`/projects/:id` record takes that path as its `id` (`commands/call.py` `path_values`), sent as one segment
(`registry._segment`, `quote(..., safe="")`). Git commands go through `SubprocessGitRunner` with a per-command
credential helper (D3).

**Reused from #10 as settled**, loaded by path from `test/forge/ephemeral.py` under its own key `forge_ephemeral` with
the reuse rule of `test/forge/conftest.py` `_load_ephemeral`: `new_run_id`, `main_working_tree`, `remove_tree`,
`ForgeSuiteError` and its subclasses `ForgeSetupError`, `ForgeCommandError`, `ForgeTeardownRefusedError`,
`ForgeSweepRefusedError`, `Invocation`, `WrapperRunner`, `GitRunner`, `HELPER_SNIPPET` with `CONFIG_OPTION`,
`HELPER_RESET`, `CONFIG_ASSIGNMENT` and `SHELL_QUOTE`, `COMMIT_IDENTITY`, `CONTROLLER_WORKER_ID`, `LEFTOVER_AGE`,
`SUBPROCESS_TIMEOUT_SECONDS`. Also reused: the interpreter-option marker (#10 D2), the suite outside the default
`python_files` (D1), the credential file with the main-worktree fallback and the one CI step that writes it (D5, D8),
the teardown and sweep guards (D9), the `report` verdict (D5). No file under `test/forge/` is edited.

**Deviations, each where GitLab differs:** the guard judges the configured `project_id`, since nothing in the GitLab
wrapper reads a git `origin`, and raises its own exception type, since `main` maps every `GitLabAPIError` to exit 1
(D2); git reads the token from a file inside the clone's `.git/`, since the wrapper's clone credential is JSON (D3);
a deletion on gitlab.com only marks the project, so the sweep sends nothing for a marked one, and a creation needs the
group's numeric id (D9); the runner keeps the bytes of a binary answer (D10); the merge-request test waits for
GitLab's asynchronous mergeability check (D6).

## Design

### D1 — Suite location and separation (AC-7.1 to AC-7.3; UB-1, UB-4)

**Location.** `test/forge_gitlab/`, a sibling of `test/forge/`: `pytest.ini`, `conftest.py`, `ephemeral.py`,
`write_credential.py` and the test modules `forge_*.py` (D10). `pytest.ini` holds #10 D1's four keys verbatim
(`python_files = forge_*.py`, `addopts = -p no:cacheprovider`, `log_cli = true`, `log_cli_level = INFO`).

- **The run.** `python scripts/run_tests.py --workers 1 test/forge_gitlab`, in the GitLab forge job and locally. #10
  D1's reasoning holds for this path unchanged: the path is the common ancestor, so `test/forge_gitlab/pytest.ini` is
  the configfile and conftest loading stops there. `python scripts/run_tests.py --workers 1 test/forge` still finds
  `test/forge/pytest.ini` first and collects only `test/forge/` (UB-4).
- **The default collection.** `testpaths` recurses into `test/forge_gitlab`, where the default `python_files` matches
  no module. It imports `conftest.py`, which imports only the standard library and pytest at module level, defines one
  fixture and no hook, and loads `ephemeral.py` by path (key `forge_gitlab_ephemeral`); that module loads
  `test/forge/ephemeral.py` by path. Both run only standard-library imports and constants, so no `sys.path` changes and
  nothing is sent.
- **Not an exclusion**, as #10 D1: `pyproject.toml` is not edited, and nothing skips, xfails, deselects or hooks.
- **One project per run.** `--workers 1`, and `ephemeral_project` first calls this module's
  `refuse_distributed_run(worker_id=...)`: #10 D1's check against `CONTROLLER_WORKER_ID`, its message naming the GitLab
  command (the GitHub function's names `test/forge`).
- **Why not `test/forge/`.** `test/test_forge_suite_layout.py` `read_forge_modules` reads every `.py` file under
  `test/forge/` with GitHub-only rules (one `ephemeral.py`, the only module that may import `subprocess`), and `run_tests.py
  ... test/forge` would also run the GitLab tests, in the job holding only the GitHub secret (UB-4).
  `file-organization.md` puts tests in `test/`, which `test/test_layout.py`
  `test_python_lives_only_in_src_test_and_scripts` admits.

Alternatives: the GitLab modules in `test/forge/` (above); `test/forge/github/` and `test/forge/gitlab/` (moves the
GitHub files, UB-4); a shared base extracted from `test/forge/ephemeral.py` (edits the GitHub suite, which the by-path
reuse does not need).

### D2 — The test marker and the project guard (AC-4.1 to AC-4.3; UB-3)

**The marker** is #10 D2's interpreter option `-X sff_test_marker`, read from `sys._xoptions` (docs quoted there).

**The product wrapper** (`src/payload/scripts/gitlab_wrapper.py`; nothing imported from `github_wrapper.py`):

- `TEST_MARKER_OPTION = "sff_test_marker"`, `EPHEMERAL_PROJECT_PREFIX = "sff-test-"` (the values of `github_wrapper.py`
  `TEST_MARKER_OPTION` and `EPHEMERAL_REPOSITORY_PREFIX`), `PROJECT_PATH_SEPARATOR = "/"`.
- `_test_marker_set() -> bool`: `TEST_MARKER_OPTION in getattr(sys, "_xoptions", {})`.
- `_is_ephemeral_project(*, project_id: Any) -> bool`: `project_id` is a `str` holding `/`, the part before its last
  `/` is not empty, and the part after it starts with `EPHEMERAL_PROJECT_PREFIX`. A number, or a text without `/`, is
  not one.
- `_refuse_unless_ephemeral(*, project_id: Any) -> None`: when the marker is set and `_is_ephemeral_project` is false,
  raises `GitLabProjectRefusedError(f"The test marker (-X {TEST_MARKER_OPTION}) is set and {CONFIG_FILE} names the
  project {json.dumps(project_id)}, which is not a <namespace>/{EPHEMERAL_PROJECT_PREFIX}* path; nothing was sent")`.
  It reads no other key, so no credential reaches the message.
- `_run` calls it with `config[FIELD_PROJECT_ID]` right after each `_load_config()`: in the delivery-verb branch before
  `steward_delegate`, in the handler branch before `Transport.from_config`. argv is still parsed first, so a usage
  error exits 2 whatever the config.
- `gitlab_api/errors.py`: `class GitLabProjectRefusedError(GitLabAPIError)`; the module docstring says the entry script
  maps it to 2. `main` catches it before `GitLabAPIError`, logs it with `logger.error("%s", error)` (standard error,
  `format="%(message)s"`), and returns `EXIT_REFUSED` (`gitlab_api/commands/_common.py`).
- The module docstring's `Exit codes` paragraph and the docstrings of `_run` and `main` name this refusal.

**Why the path form.** The creation call runs under the clone's config before the project exists, and
`_refuse_incomplete` refuses an empty `project_id`; the path is known in advance and judged with no request, and
GitLab takes "The ID or URL-encoded path of the project" as `:id` (docs.gitlab.com/api/projects/#delete-a-project).
Without the marker the guard returns at once, reading no file and sending nothing: the fake-host tests run `main` in a
`tmp_path` holding only `config/gitlab.json`, `FakeGitLab.serve` raises on an unscripted request
(`src/payload/test/gitlab_wrapper_fixtures.py`), and `test_gitlab_wrapper_compat.py` `test_delivery_verb_through_main`
asserts none is sent (UB-3).

Alternatives: a read of the configured project judging its `path` (a request per invocation, and a numeric id is
unknown until the creation); a second key such as `project_path` (a key the guard would trust over the `project_id`
the requests use); judging a git `origin` as #10 does (the GitLab wrapper reads none); `_run` logging and returning
`EXIT_REFUSED` itself, the `call_operation` idiom (the exception keeps `_refuse_unless_ephemeral` testable alone,
`coding-standards.md` rule 5).

### D3 — Git authentication (AC-1.3, AC-6.3, AC-8.2)

**The helper.** `credential_helper_arguments(*, clone: Path) -> List[str]` of `test/forge_gitlab/ephemeral.py` returns
#10 D3's global options built from the reused `HELPER_SNIPPET`, with the key `credential.https://gitlab.com.helper`,
the username `GIT_USERNAME = "sff-forge-suite"` and the file `<clone>/.git/sff-forge-token`
(`CLONE_GIT_TOKEN_FILE`): the same reset of the helper list, the same single quoting of the forward-slash path and
the same `ForgeSetupError` for a path holding `'`. #10 D3's git-scm.com quotes and its platform note apply unchanged.

- GitLab: the username of a personal access token over HTTPS is "Any string that is not empty. GitLab does not validate
  this value." (docs.gitlab.com/user/profile/personal_access_tokens/), and "For a personal access token, `api` also
  grants complete read and write access to the registry and repository through Git-over-HTTP."
  (docs.gitlab.com/security/tokens/access_token_scopes/).
- **Why a second clone file.** The wrapper's credential in the clone is `config/gitlab.json`, JSON. The snippet reads
  the token with the shell built-ins `read` and `printf`, which read a one-line file but parse no JSON; a parser in the
  snippet would start an interpreter for every git command. The file lies inside `.git/`, the repository itself ("a
  `.git` directory at the root of the working tree", git-scm.com/docs/gitrepository-layout), not a tracked path, and
  goes with the clone; S `test_the_clone_commits_no_credential` shows `git add -A` stages neither file. AC-6.3 is
  restated to allow it.

**The clone** follows #10 D3's steps: `git init` in `<clone>`, the clone's two credential files (D8), `git remote add
origin https://gitlab.com/bestehorn-sff-test/<path>.git` (no userinfo, so `.git/config` holds no token), and after the
creation an authenticated `git fetch origin` and `git checkout -B <default branch> --track origin/<default branch>`.
A test pushes a branch through `push_branch` (D10). Every git command passes `COMMIT_IDENTITY`.

Alternatives: the helper parsing `config/gitlab.json` (above); #10's `credentials/` file in the working tree (one more
exclude line; `.git/` needs none); the token in the URL, `http.extraHeader`, `GIT_ASKPASS` or the `store` helper (#10
D3 Alternatives).

### D4 — The run id (AC-1.2)

`new_run_id` of `test/forge/ephemeral.py`, reused. `ephemeral_path(*, run_id) -> str` is the product's
`EPHEMERAL_PROJECT_PREFIX` then `run_id`; `ephemeral_full_path(*, run_id) -> str` is `TEST_GROUP`, `/`, then the
path. The path holds lowercase letters, digits and single `-`, starts with a letter and ends with a hex digit, which
GitLab's slug rule admits: "Must start and end with a letter (`a-zA-Z`) or digit (`0-9`). Must not contain consecutive
special characters. [...] Must contain only letters (`a-zA-Z`), digits (`0-9`), underscores (`_`), dots (`.`), or
dashes (`-`)." (docs.gitlab.com/user/reserved_names/). Were two ids equal, the later creation would fail on the taken
path: that run creates nothing and deletes nothing (AC-2.3), as #10 D4. A project marked for deletion gives up its path,
which becomes `<path>-deletion_scheduled-<project id>` (gitlab-org/gitlab
`app/services/namespaces/mark_for_deletion_base_service.rb` `suffixed_identifier`).

### D5 — The GitLab forge CI job (AC-5.1 to AC-5.4)

`.github/workflows/ci.yml` gains `forge-gitlab`, `report` changes, and the header comment names the new job; `verify`,
`forge`, `on:`, `concurrency` and `permissions` are unchanged. `ci.yml` is this project's own (#10 D5).

```yaml
  forge-gitlab:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: {persist-credentials: false}
      - uses: actions/setup-python@v5
        with: {python-version: '3.10'}
      - run: pip install -e ".[dev]"
      - name: Write the GitLab test credential file
        env:
          SFF_GITLAB_TEST_TOKEN: ${{ secrets.SFF_GITLAB_TEST_TOKEN }}
        run: python test/forge_gitlab/write_credential.py
      - run: python scripts/run_tests.py --workers 1 test/forge_gitlab

  report:
    needs: [verify, forge, forge-gitlab]
    # ...the existing steps, and in the verdict script, after the forge job's two lines:
          echo "forge-gitlab job: ${{ needs.forge-gitlab.result }}" | tee -a verdict.txt
          if [ "${{ needs.forge-gitlab.result }}" != "success" ]; then status=1; fi
```

- **No `needs:`** between `forge-gitlab` and `verify` or `forge` (AC-5.1); one check command, `run_tests.py` (no
  fail-fast, `-ra`; AC-5.2), as #10 D5.
- **The secret** reaches the one credential step through its `env:` block and from there only the test credential
  file of the checkout (D8); `persist-credentials: false` as #10 D5, whose docs quotes apply.
- **A missing secret** (AC-5.3): `write_credential.py` logs "the secret SFF_GITLAB_TEST_TOKEN is unavailable to this
  run" and exits 1, which fails the job before the suite runs.
- **The verdict** (AC-5.4): `report` fails unless each of `needs.forge.result` and `needs.forge-gitlab.result` is
  `success` ("Possible values are `success`, `failure`, `cancelled`, or `skipped`"; the job id may be dereferenced:
  "the property name must start with a letter or `_` and contain only alphanumeric characters, `-`, or `_`",
  docs.github.com "Contexts reference").
- **The test group** is `TEST_GROUP = "bestehorn-sff-test"` of `test/forge_gitlab/ephemeral.py` (DL-002), the one
  place the suite names it.
- **The GitHub layout test.** `test/test_forge_suite_layout.py` `test_the_report_judges_the_forge_job` pins `report`'s
  `needs` to exactly `verify` and `forge`; its expected set becomes `verify`, `forge` and `forge-gitlab`, and its other
  assertions stay: the `forge` guard is still required, no later `status=` line overwrites it (the GitLab guard line
  starts with `if`, which `STATUS_ASSIGNMENT` does not match), and `exit "$status"` stays last. No other test of the
  file changes: `test_the_forge_job_runs_beside_verify` reads `verify` and `forge`, both unchanged, and
  `test_the_secret_reaches_one_step` counts `SECRET_REFERENCE`, which matches `secrets.SFF_TEST_TOKEN` and not
  `secrets.SFF_GITLAB_TEST_TOKEN`. The new job's own expectations are G's (Testing Strategy).

Alternatives: the GitLab tests in the `forge` job (two secrets and one result, so `report` could not tell the forges
apart; AC-5.1 asks for a dedicated job); a matrix over the forges (rewrites `forge`, UB-4); a `run_checks.py` group
(toolchain, #10 D5).

### D6 — The real-GitLab tests per slice (AC-8.1 to AC-8.7) and the token's scope

Every F test takes `ephemeral_project`, runs the product wrapper through its `wrapper` (marker set, the clone as
working directory) and asserts each invocation's exit code and its printed JSON (`Invocation.json()`) or bytes. No
forge module gives `--path id=`, so every project record takes the configured project; the group listing is the
support module's `list_group_projects`. `N` is an iid an answer printed, `<hex>` a fresh `uuid.uuid4().hex`, `<b>` a
branch `forge-<purpose>-<hex>` that `push_branch` pushed with one new file, `<seed>` the seed commit, `P` the project's
full path.

| Module (slice) | Test | Invocations and what is asserted |
|---|---|---|
| F:fixture | `test_the_run_owns_a_private_seeded_project` | `call tenant-scale#retrieve-a-project`: `path_with_namespace` P, `visibility` `private`, `default_branch` the creation's; in the clone, `HEAD` equals `origin/<default branch>` and `<seed>`, `git ls-tree -r --name-only <seed>` names exactly `README.md`, `git remote get-url origin` is `https://gitlab.com/P.git`, the clone's `config/gitlab.json` holds `hostname` `gitlab.com` and `project_id` P (AC-1.1, AC-1.3) |
| F:fixture | `test_no_leftover_survives_the_sweep` | `list_group_projects`: no record that `is_leftover` at `swept_at` lacks `marked_for_deletion_on` (AC-3.1) |
| F:subcommands (#13) | `test_an_issue_and_label_round_trip` | `label create --name forge-<hex> --color #1F75CB` (`name`); `label list` (names it); `issue create --title T --description D` (`state` `opened`, `title` T); `issue show N` (T, D, opened); `issue comment N --body C` (`body` C); `issue label-add N --labels forge-<hex>` (`labels` name it); `issue show N` (the same); `issue close N` (`state` `closed`); `issue show N` (closed) |
| F:subcommands (#13) | `test_a_merge_request_round_trip` | `push_branch`; `mr create --source <b> --target <default branch> --title T` (`source_branch`, `target_branch`, `sha` the pushed commit, `state` `opened`); `wait_until_checked` (`mr get N` until `detailed_merge_status` is none of `unchecked`, `checking`, `preparing`; then `mergeable`); `mr merge N` (`state` `merged`); `mr get N` (`merged`) |
| F:subcommands (#13) | `test_delete_branch_removes_a_pushed_branch` | `push_branch`; `call create#retrieve-a-repository-branch --path branch=<b>` (`name`, `commit.id` the pushed commit); `delete-branch <b>` (`{"branch": <b>, "deleted": true}`); the same `call`: exit 1, standard error `answered 404` |
| F:subcommands (#13) | `test_no_pipeline_has_run` | `pipeline status`: `[]` (AC-1.3) |
| F:records | `test_the_repository_records_read_the_seed` | `call tenant-scale#retrieve-a-project` (`default_branch`); `call create#retrieve-a-commit --path sha=<seed>` (`id` `<seed>`, `parent_ids` `[]`); `call create#list-all-repository-trees-in-a-project --query ref=<seed>` (one entry: `name` `README.md`, `type` `blob`, `id` the blob of `git rev-parse <seed>:README.md`) |
| F:records | `test_the_issue_and_note_records` | `issue create`, `issue comment N --body C` (setup: `call` refuses `plan#create-an-issue`); `call plan#retrieve-a-project-issue --path issue_iid=N` (`iid`, `title`); `call plan#list-all-issue-notes --path issue_iid=N` (an item with `body` C) |
| F:records | `test_the_merge_request_records` | `push_branch`, `mr create` (setup); `call ai-coding#retrieve-a-merge-request --path merge_request_iid=N` (`source_branch` `<b>`, `sha`); `call ai-coding#retrieve-merge-request-commits --path merge_request_iid=N` (one item, `id` the pushed commit) |
| F:graphql (#44) | `test_the_work_items_of_the_project` | `issue create --title T` (setup); `call graphql#Project.workItems -f fullPath=P`: one node titled T, `iid` N as text, `state` `OPEN`, `workItemType.name` `Issue` |
| F:request_forms (#63) | `test_an_endpoint_named_by_endpoint` | `push_branch`, `mr create` (setup); `call plan#add-an-emoji-reaction-to-a-resource --endpoint 'POST /projects/:id/merge_requests/:merge_request_iid/award_emoji' --path merge_request_iid=N -f name=thumbsup` (`name` `thumbsup`, `awardable_type` `MergeRequest`); `call plan#list-all-emoji-reactions-for-a-resource --endpoint 'GET /projects/:id/merge_requests/:merge_request_iid/award_emoji' --path merge_request_iid=N` (one item, `thumbsup`) |
| F:request_forms (#63) | `test_a_format_suffix` | `call create#retrieve-file-archive-from-a-repository --path format=zip --query sha=<seed>`: exit 0, its bytes a zip archive (`zipfile`) whose one file ends `/README.md` and holds the text of `git show <seed>:README.md` |

- **Mergeability**: "The mergeability (`merge_status`) of each merge request is checked asynchronously when a request
  is made to this endpoint", and `unchecked` is "Git has not yet tested if a valid merge is possible."
  (docs.gitlab.com/api/merge_requests/), so the merge waits for a decided status.
- **The seed moves**: the merge-request round trip merges into the default branch, so F:records reads `<seed>` by its
  SHA, never by the branch.
- **#44**: work items are issues on a Free project, so a private Free project of a non-administrator serves
  `graphql#Project.workItems` (`graphql_only.py`, capability "Work items").
- **The forms of #63 not called** are named in `forge_request_forms.py`'s docstring with their reasons (AC-8.5,
  AC-8.6): a positional name given once per place is declared only by group records (`create#delete-a-group-ssh-certificate`
  and the `tenant-scale#...-for-an-enterprise-user` token records), outside the ephemeral project (AC-8.7), and the
  group SSH certificates API is "Tier: Premium, Ultimate" (`docs/api-reference/gitlab/rest/create.md`); of the
  container-registry records, `package#listing-all-container-repositories` needs "administrator credentials", and for
  `package#delete-image-tags-by-reference` GitLab documents no answer for a project without an image, beside "The
  `tag_delete` Container-Registry-Feature must be enabled" (docs.gitlab.com/api/container_registry/); `--header` is
  declared by `software-supply-chain-security#set-status-of-an-external-control`, "Tier: Ultimate"
  (`docs/api-reference/gitlab/rest/software-supply-chain-security.md`), and `openapi-only#the-nuget-symbol-file-download-endpoint-1`, "source:
  `openapi_v2.yaml` only", with no documented answer; a form-body member below its first bracket level is declared only
  by `gitlab-dedicated#import-a-project-from-an-aws-s3-bucket`, which `call` refuses before any request
  (`GATED_OPERATIONS`).

**The token's scope and role** (token: a personal access token of a group service account, operator facts):

| Grant | Covers |
|---|---|
| Scope `api` | every record and subcommand of D6 and D9: "Grants complete read and write access to the API for the token's scope"; git fetch and push: "For a personal access token, `api` also grants complete read and write access to the registry and repository through Git-over-HTTP." (docs.gitlab.com/security/tokens/access_token_scopes/) |
| Owner of the test group | `tenant-scale#delete-a-project`: "You must be an administrator or have the Owner role for the project." (docs.gitlab.com/api/projects/#delete-a-project); "If you assign a service account the Owner role for a group, the service account's personal access tokens also have the Owner role for that group." (docs.gitlab.com/user/profile/service_accounts/) |

Not needed: `read_api`, `read_repository`, `write_repository` (`api` covers them).

### D7 — The setup note (AC-9.1)

`docs/forge-suite.md` gains a section on the GitLab forge suite after the GitHub ones, which stay as they are. It names
the test group `bestehorn-sff-test` on gitlab.com, the group service account (the group's Settings > Service
accounts) as a member of the test group with the Owner role, its personal access token with the scope `api` and D6's
table, the test credential file `credentials/gitlab-sff-testing-pat.txt`, the Actions secret `SFF_GITLAB_TEST_TOKEN`,
that only a machine that runs the GitLab forge suite locally needs the file, the local command, and that each run's
project stays marked for deletion until gitlab.com removes it (Operability). No template ships (#10 D7).

### D8 — The test credential (AC-6.1 to AC-6.3; UB-2)

- **Lookup** (`find_test_credential(*, checkout: Path) -> Path`): `checkout/credentials/gitlab-sff-testing-pat.txt`
  when it is a file; else the same path under `main_working_tree(checkout=checkout)` (reused); else `ForgeSetupError`
  naming both paths and `docs/forge-suite.md`.
- **Reading** (`read_test_token(*, path: Path) -> str`): the file's bytes, decoded as ASCII (a byte outside it is
  refused), less one final `\n` or `\r\n`; empty text, text starting with the product's `PLACEHOLDER_MARKER`, or text
  the product's `_refuse_token_characters` refuses raises `ForgeSetupError` naming `path` and none of its contents
  (`from None`). The product is `product_wrapper()` (D10). It precedes every request (D9 step 2); a session fixture
  that raises errors every test that uses it, so none is skipped.
- **Writing** (D9 step 3): the clone's `config/gitlab.json` (`CLONE_CONFIG_FILE`) holds `json.dumps` of `hostname`
  `gitlab.com`, `project_id` P and `token`, keyed by the product's `FIELD_HOSTNAME`, `FIELD_PROJECT_ID`, `FIELD_TOKEN`;
  `CLONE_GIT_TOKEN_FILE` holds the token and `\n`. Each is created owner-only (`0o600`, `exist_ok=False`) and then
  written as bytes, under #10 D8's `tempfile.mkdtemp` workspace protection on Windows; `config/` is appended to the
  clone's `.git/info/exclude`, so no commit of the clone holds `config/gitlab.json`. The token is a local of
  `provision`, deleted after `prepare_clone`; no object the tests receive holds it, and nothing logs it.
- **CI** (`write_test_credential(*, token: str, checkout: Path) -> None`): an empty `token` raises `ForgeSetupError`
  saying that the secret `SFF_GITLAB_TEST_TOKEN` is unavailable to this run, writing nothing; otherwise it writes the
  checkout's test credential file with a final `\n`. `write_credential.py` `main` reads `SFF_GITLAB_TEST_TOKEN`, the
  one environment read of the change (AC-6.3), logs a refusal and returns 1.
- **UB-2**: the suite opens `config/gitlab.json` only under the clone.

### D9 — Provisioning, the sweep and the teardown guard (AC-1, AC-2, AC-3)

`provision(*, checkout, workspace, wrapper: WrapperRunner, git: GitRunner)` is a context manager yielding an
`EphemeralProject` (`run_id`, `group`, `path`, `full_path`, `project_id`, `default_branch`, `seed_sha`,
`seed_tree_sha`, `swept_at`, `clone`, `wrapper`, `git`). `ephemeral_project(worker_id)` (session scope) has #10's
shape: the distributed-run refusal, a `tempfile.mkdtemp` workspace, both runners bound to `<workspace>/clone`, and one
`yield` inside the one `with provision(...)` block.

1. Before the `try`: the run id, `path = ephemeral_path(...)`, `full_path = ephemeral_full_path(...)` (no request).
2. `read_test_token(path=find_test_credential(checkout=checkout))`.
3. `prepare_clone`: `<workspace>/clone` created, `git init`, the two credential files and the exclude line (D8),
   `git remote add origin` (D3).
4. `sweep_leftovers(wrapper=..., now=swept_at)`, `swept_at` the UTC now.
5. `read_test_group(*, wrapper) -> int`: `call tenant-scale#retrieve-a-group --path id=bestehorn-sff-test --query
   with_projects=false`; a non-zero exit raises `ForgeCommandError`, an answer whose `full_path` is not `TEST_GROUP` or
   whose `id` is no integer raises `ForgeSetupError`. A creation's `namespace_id` is a number: "Specify a group ID or
   subgroup ID" (docs.gitlab.com/api/projects/, "Create a project"; Type `integer` in
   `docs/api-reference/gitlab/rest/tenant-scale.md`).
6. `create_ephemeral(*, wrapper, group_id, path) -> CreatedProject`: `call tenant-scale#create-a-project -f
   name=<path> -f path=<path> -F namespace_id=<group id> -f visibility=private -F initialize_with_readme=true -F
   auto_devops_enabled=false`, each attribute declared by the record (`families/tenant_scale.py`), so `call`'s parameter
   check passes. `initialize_with_readme`: "Whether to create a Git repository with just a `README.md` file";
   `auto_devops_enabled`: "Enable Auto DevOps for this project" (ibid.), sent false so no Auto DevOps pipeline runs. A
   non-zero exit raises `ForgeCommandError` (nothing was created); the answer's `id`, `namespace.full_path`, `path` and
   `default_branch` (which the group's setting may choose) make the record, and a `visibility` other than `private`
   raises `ForgeSetupError` whose `details` keep the record, so step 8 deletes it (#10 D9 step 5).
7. `fetch_seed`: #10's fetch, checkout and `rev-parse`; a seed whose root holds `.gitlab-ci.yml`, the default CI
   configuration file (`ci_config_path` unset), raises `ForgeSetupError`. Then the yield.
8. In the `finally` around steps 2 to 7 and the yield: `delete_ephemeral(...)` of step 6's record (else `None`), then,
   in its own `finally`, `remove_tree(path=workspace)` (reused); a failure of either is raised.

**The teardown guard.** `delete_ephemeral(*, wrapper, created: Optional[CreatedProject], run_id: str) -> None`:

- `created` is `None`: returns, nothing sent (AC-2.3);
- `(created.namespace, created.path)` is not `(TEST_GROUP, ephemeral_path(run_id=run_id))`: raises
  `ForgeTeardownRefusedError` naming the refused `<namespace>/<path>` and this run's, nothing sent (AC-2.2);
- else `call tenant-scale#delete-a-project --path id=<namespace>/<path>`; a non-zero exit raises `ForgeCommandError`
  naming the target (AC-2.1, AC-1.4). Exit 0 is GitLab's answer for a project now marked: the endpoint "Marks a project
  for deletion. Projects are deleted at the end of the retention period", and `permanently_remove` is "Disabled on
  GitLab.com and Dedicated" (docs.gitlab.com/api/projects/#delete-a-project), so no permanent removal is asked for.

**The sweep.**

- `list_group_projects(*, wrapper) -> List[ProjectRecord]`: `call tenant-scale#list-projects --path
  id=bestehorn-sff-test` (`Paging.OFFSET`, every page read); a non-zero exit raises `ForgeCommandError`. No `active`
  filter: "When `false`, returns projects that are archived or marked for deletion" (docs.gitlab.com/api/groups/,
  "List projects"), so `active=true` would also drop an archived leftover, which AC-3.1 selects.
- `ProjectRecord.of(*, item)` reads `id`, `namespace.full_path`, `path`, `created_at` (ISO 8601, a final `Z` read as
  UTC, a fraction of a second allowed) and `marked_for_deletion_on` (absent or null: not scheduled); an item without the
  first four raises `ForgeCommandError`.
- `is_leftover(*, record, now) -> bool`: the namespace is `TEST_GROUP`, the path starts with the product's
  `EPHEMERAL_PROJECT_PREFIX`, and `now - record.created_at` exceeds `LEFTOVER_AGE`. `select_leftovers` keeps exactly
  those.
- `sweep_leftovers(*, wrapper, now)`: for each selected record, one already scheduled (`marked_for_deletion_on` set)
  is logged and sent nothing (AC-3.3); any other goes to `delete_leftover`.
- `delete_leftover(*, wrapper, record, now)`: a record that is no leftover at `now`, or is scheduled, raises
  `ForgeSweepRefusedError` naming it, nothing sent; else `call tenant-scale#delete-a-project --path
  id=<namespace>/<path>`. Exit 1 with standard error holding `answered 404` (a concurrent run's sweep marked it, which
  renamed it) or `answered 400` and `has already been marked for deletion` (the message of
  `mark_for_deletion_base_service.rb`: "#{resource_name.titleize} has already been marked for deletion") counts as
  handled; any other failure raises `ForgeCommandError`. Standard error carries `Transport._send`'s
  `"{method} {url} answered {status}: {error_text}"`, logged by `main` `_report`. Each deletion is logged by full path.

### D10 — Files and module layout

| File | Change |
|---|---|
| `src/payload/scripts/gitlab_wrapper.py` | D2: the constants, `_test_marker_set`, `_is_ephemeral_project`, `_refuse_unless_ephemeral`, its calls in `_run`, `main`'s mapping to `EXIT_REFUSED`; the docstrings |
| `src/payload/scripts/gitlab_api/errors.py` | D2: `GitLabProjectRefusedError`; the docstring |
| `src/payload/test/test_gitlab_wrapper_marker.py` | new: W |
| `test/forge_gitlab/pytest.ini` | new: D1 |
| `test/forge_gitlab/conftest.py` | new: loads `ephemeral.py` by path once per process; `ephemeral_project` (D9) |
| `test/forge_gitlab/ephemeral.py` | new: the reused symbols of `test/forge/ephemeral.py` (Overview), loaded by path; the constants of D3 to D9, `TEST_GROUP` included; the dataclasses `CreatedProject`, `ProjectRecord`, `EphemeralProject`; `SubprocessWrapperRunner`, `SubprocessGitRunner`; `product_wrapper()`; `push_branch`, `wait_until_checked`; the functions of D1, D3, D4, D8 and D9 |
| `test/forge_gitlab/write_credential.py` | new: the CI step's command (D8) |
| `test/forge_gitlab/forge_fixture.py`, `forge_subcommands.py`, `forge_records.py`, `forge_graphql.py`, `forge_request_forms.py` | new: D6, one module docstring per slice |
| `test/test_forge_gitlab_support.py`, `test/test_forge_gitlab_layout.py` | new: S, G |
| `test/test_forge_suite_layout.py` | `test_the_report_judges_the_forge_job`'s expected `needs` (D5) |
| `.github/workflows/ci.yml` | D5 |
| `docs/forge-suite.md` | D7 |
| `docs/forLLMConsumption.md` | its testing section names the GitLab forge suite `test/forge_gitlab/`, its local command, `credentials/gitlab-sff-testing-pat.txt`, `docs/forge-suite.md` and the `forge-gitlab` job, under its cap |

- `SubprocessWrapperRunner(*, directory)` is the one place the suite starts the product wrapper: `subprocess.run([
  sys.executable, "-X", <product TEST_MARKER_OPTION>, str(PRODUCT_WRAPPER), *arguments], cwd=directory,
  stdin=DEVNULL, capture_output=True, timeout=SUBPROCESS_TIMEOUT_SECONDS, check=False)`, no `env`, list argv, never a
  shell. Standard output is decoded as UTF-8 with `errors="surrogateescape"` and standard error with
  `errors="replace"`; `Invocation.stdout.encode(encoding="utf-8", errors="surrogateescape")` gives back the exact bytes
  of a body `print_bytes` wrote ("This code will then be turned back into the same byte when the 'surrogateescape'
  error handler is used when encoding the data", docs.python.org `library/codecs.html` "Error Handlers"). #10's runner
  decodes strictly, and F:request_forms' archive is no UTF-8 text.
- `SubprocessGitRunner(*, clone)`: #10's, with D3's helper options when `authenticated`.
- `product_wrapper()` loads `src/payload/scripts/gitlab_wrapper.py` by path on first use (key
  `forge_gitlab_product_wrapper`), never at import, and restores `sys.path` afterwards, as #10's loader does.
- `push_branch(*, git, default_branch, branch) -> str`: `git checkout -b <branch> <default branch>`, one new file
  committed by name (never `git add -A`), an authenticated `git push origin <branch>`, `git checkout <default branch>`;
  the commit's SHA.
- `wait_until_checked(*, wrapper, iid) -> Mapping[str, Any]`: `mr get <iid>` until `detailed_merge_status` is none of
  `unchecked`, `checking` and `preparing`, pausing between reads, bounded by a deadline (both constants of the
  module); the last answer; the deadline raises `ForgeCommandError` naming the last status.
- Named parameters, JSON fields through constants, `logging` (`coding-standards.md`).

**Not edited:** every file under `test/forge/`, `test/test_forge_support.py`, `pyproject.toml`, `gitlab_api/` but
`errors.py`, `gitlab_wrapper_fixtures.py`, `docs/ProjectPlan.md`, every toolchain file.

## Testing Strategy

- **The guard, in the default collection.** W runs `main(argv=...)` in-process through `gitlab_wrapper_fixtures`
  (`write_config`, `monkeypatch.chdir`, `FakeGitLab`, `install_socket_guard`, `load_wrapper`, `run_main`), with
  `monkeypatch.setitem(sys._xoptions, TEST_MARKER_OPTION, True)` or without it; one example runs the entry script as a
  subprocess with `-X sff_test_marker`, refused before any request.
- **The suite's logic, in the default collection.** S loads `test/forge_gitlab/ephemeral.py` by path; its runners are
  doubles (`RecordingWrapperRunner(WrapperRunner)`, `ScriptedGitRunner(GitRunner)`), its checkouts live in `tmp_path`,
  and only local git runs (`git init`, `git worktree add`, `git remote add`, `git add`, `git ls-files`, `git credential
  fill`). One Hypothesis property, where the criteria quantify over listed projects (AC-3.1 to AC-3.3); every other
  check is an example.
- **Separation and wiring, in the default collection.** G loads `test/test_forge_suite_layout.py` by path for its
  workflow reader (`read_workflow`, `job_named`, `steps_of`, `needs_of`, `run_of`, `run_commands`, `scalars_of`,
  `condition_of`), `collect_only`, `collected_tests` and its `ast` helpers, and applies them to `test/forge_gitlab/`,
  the `forge-gitlab` job and the docs. L keeps its tests, one expectation extended (D5); H is unedited.
- **The GitLab forge suite** (F) is the end-to-end check: the product wrapper driven through its command line against
  gitlab.com, by the GitLab forge job on every pull request, push to `main` and dispatch; locally D1's command. Its
  verdict on the PR's head is read through the wrapper's `get-pr-checks` and `get-run`.
- **Runner.** W, S, G and L: `python scripts/run_tests.py <these paths>`; in CI, `verify` leg `tests`.

## Correctness Properties

- **AC-1.1** — Integration, F:fixture `test_the_run_owns_a_private_seeded_project`. Example, S
  `test_provisioning_runs_in_order`: one provision records, in order, the listing, the group read, exactly one D9 step 6
  creation whose argv holds `-F namespace_id=<the group's id>`, `-f visibility=private`, `-F
  initialize_with_readme=true` and `-F auto_devops_enabled=false`, the fetch and the checkout, every wrapper invocation
  in the one clone directory. Example, S `test_a_distributed_run_is_refused`. Structural, G
  `test_the_session_fixture_wraps_one_provision` (L's `session_fixture_problems` on `ephemeral_project`).
- **AC-1.2** — Example, S `test_a_run_id_names_an_ephemeral_project`: ids of repeated calls are pairwise distinct, and
  the product's `_is_ephemeral_project` accepts `ephemeral_full_path`.
- **AC-1.3** — Integration, F:fixture `test_the_run_owns_a_private_seeded_project`, F:subcommands
  `test_no_pipeline_has_run`, F:records `test_the_repository_records_read_the_seed`. Example, S
  `test_provisioning_runs_in_order`: a scripted seed holding `.gitlab-ci.yml` raises `ForgeSetupError` before the yield,
  the deletion is still sent, and the workspace no longer exists.
- **AC-1.4** — Parametrized example, S `test_provisioning_runs_in_order`: whether the body returns or raises, exactly one
  `tenant-scale#delete-a-project` of this run's project is recorded and the workspace no longer exists; a deletion
  answering exit 1 raises `ForgeCommandError` and the workspace is still removed. Structural, G (AC-1.1's).
- **AC-2.1** — Example, S `test_the_teardown_deletes_only_this_runs_project`: one `call tenant-scale#delete-a-project
  --path id=bestehorn-sff-test/sff-test-<run id>` recorded.
- **AC-2.2** — Parametrized example, S `test_the_teardown_refuses_any_other_target`: another namespace, a path without
  the prefix, another run's id: `ForgeTeardownRefusedError` naming the refused target, nothing recorded.
- **AC-2.3** — Example, S `test_no_creation_no_deletion`: `created=None`, and a provision whose creation exits 1: no
  deletion recorded, the workspace removed.
- **AC-3.1, AC-3.2, AC-3.3** — Property, S `test_the_sweep_deletes_exactly_the_old_unscheduled_ephemeral_projects`:
  over listings of records (namespace the test group or another, a path with the prefix or not, `created_at` on either
  side of the one-day line, `marked_for_deletion_on` set or not), `sweep_leftovers` records one deletion per record
  with all four properties and none for any other, the expected set computed from the drawn values, never through
  `is_leftover` or `select_leftovers`, and no run raises. Example, S `test_the_sweep_boundaries_and_refusals`: exactly
  a day old is kept, just over is deleted; `answered 404` and the `answered 400` "has already been marked for
  deletion" count as handled, another `400` raises `ForgeCommandError`; `delete_leftover` of a non-leftover or a
  scheduled record raises `ForgeSweepRefusedError`, nothing recorded. Integration, F:fixture
  `test_no_leftover_survives_the_sweep`.
- **AC-4.1** — Parametrized example, W `test_the_marker_refuses_a_project_without_the_prefix`, over `call
  tenant-scale#retrieve-a-project`, `issue show 1`, `pipeline status`, `enqueue-pr 1` and `wait-landed 1`, each with
  `project_id` `1234`, `"1234"`, `"Bestehorn/SoftwareFactoryFramework"`, `"bestehorn-sff-test/other"` and
  `"sff-test-x"`: exit 2, no request recorded, `steward_delegate` not called, one log record naming the test marker and
  the configured project and not the configured token. Example, W
  `test_the_interpreter_option_reaches_the_entry_script`: the subprocess, in a `tmp_path` other than the repository,
  exits 2 and its standard error holds that message.
- **AC-4.2** — Example, W `test_the_marker_lets_an_ephemeral_project_through`: with `project_id`
  `bestehorn-sff-test/sff-test-x`, `call tenant-scale#retrieve-a-project` sends the same requests, prints the same output
  and exits as the same argv without the marker. Integration: every F test runs with the marker set.
- **AC-4.3** — Example, S `test_every_wrapper_invocation_carries_the_marker`: the argv starts `sys.executable, "-X",
  TEST_MARKER_OPTION, <PRODUCT_WRAPPER>`, `subprocess.run` receives no `env`, and a non-UTF-8 standard output comes back
  byte for byte. Example, W `test_the_marker_values_are_issue_10s`: equal to `github_wrapper.py`'s. Structural, G
  `test_the_gitlab_forge_tests_reach_only_the_ephemeral_project` (AC-8.7). W
  `test_without_the_marker_every_project_is_served`: exit 0, the request recorded.
- **AC-5.1** — Structural, G `test_the_gitlab_forge_job_runs_beside_verify`: `forge-gitlab` has no `needs:` and no
  `continue-on-error`, neither `verify` nor `forge` names it, its last step is `python scripts/run_tests.py --workers 1
  test/forge_gitlab`.
- **AC-5.2** — Structural, G `test_the_gitlab_secret_reaches_one_step`: `secrets.SFF_GITLAB_TEST_TOKEN` occurs once,
  in the `env:` of the step running `python test/forge_gitlab/write_credential.py`; the job's checkout has
  `persist-credentials: false`; its check commands are exactly AC-5.1's. G `test_nothing_keeps_a_gitlab_forge_test_from_running`
  (AC-7.3).
- **AC-5.3** — Example, S `test_a_missing_secret_fails_the_credential_step`: an empty token raises with "the secret
  SFF_GITLAB_TEST_TOKEN is unavailable to this run" and writes nothing; a token is written with a final line end;
  `write_credential.main` returns 1 on the refusal.
- **AC-5.4** — Structural, G `test_the_report_judges_the_gitlab_forge_job`: `report` needs `forge-gitlab`, runs `if:
  always()`, and its verdict sets a failing status unless `needs.forge-gitlab.result` is `success`, overwritten by no
  later `status=` line, then `exit "$status"`. L `test_the_report_judges_the_forge_job` (D5).
- **AC-6.1** — Example, S `test_the_test_credential_is_found_in_the_checkout_or_its_main_tree`: as #10's, with the
  GitLab file.
- **AC-6.2** — Parametrized example, S `test_a_bad_test_credential_fails_before_any_request`: missing, empty, a lone line
  end, `PASTE_TOKEN`, a token holding a space, a non-ASCII character, two lines: `ForgeSetupError` naming the path and
  not the text, no wrapper or git invocation recorded; a token with a final `\r\n` is accepted.
- **AC-6.3** — Example, S `test_the_token_is_written_only_to_the_clone`: after a scripted provision, the files of the
  test's tree holding the token are the test credential file, the clone's `config/gitlab.json` and
  `.git/sff-forge-token`; no recorded argv, no record `caplog` captured at `DEBUG`, and no `repr` of the yielded
  `EphemeralProject` holds it. Example, S `test_the_clone_commits_no_credential`: `prepare_clone` with the real git
  runner (local commands only), then `git add -A`: `git ls-files` names neither file. Example, S
  `test_the_credential_helper_answers_git_with_the_clone_token`: `git credential fill` with D3's options and
  `protocol=https`, `host=gitlab.com` answers `username=sff-forge-suite` and the file's token; the helper string holds
  no token. Structural, G `test_the_gitlab_secret_reaches_one_step`.
- **AC-7.1** — Example, G `test_the_default_configuration_collects_no_gitlab_forge_test`: `--collect-only -c
  pyproject.toml test/forge_gitlab` exits 5, "no tests collected", no import error.
- **AC-7.2** — Example, G `test_the_gitlab_forge_path_collects_every_gitlab_forge_test`: `--collect-only -q
  test/forge_gitlab` lists exactly the `test_` functions of `test/forge_gitlab/forge_*.py`.
- **AC-7.3** — Structural, G `test_nothing_keeps_a_gitlab_forge_test_from_running`: L's `skipping_outcomes` and
  `collection_hooks` find nothing in `test/forge_gitlab/`; its `pytest.ini` holds exactly #10's four keys.
- **AC-8.1** — Structural, G `test_the_gitlab_forge_tests_reach_only_the_ephemeral_project`; every F test asserts each
  invocation's exit code and its printed answer (D6).
- **AC-8.2** — Integration, F:subcommands' four tests.
- **AC-8.3** — Integration, F:records' three tests and F:fixture `test_the_run_owns_a_private_seeded_project`.
- **AC-8.4** — Integration, F:graphql `test_the_work_items_of_the_project`.
- **AC-8.5** — Integration, F:request_forms `test_an_endpoint_named_by_endpoint`, `test_a_format_suffix`. Structural,
  G `test_each_uncalled_form_is_named_with_its_reason` (AC-8.6).
- **AC-8.6** — Structural, G `test_each_uncalled_form_is_named_with_its_reason`: `forge_request_forms.py`'s docstring
  names each record D6 lists as not called with its reason, and no other string constant of the suite names one.
- **AC-8.7** — Structural, G `test_the_gitlab_forge_tests_reach_only_the_ephemeral_project`: only `ephemeral.py`
  imports `subprocess` or names `product_wrapper` or `PRODUCT_WRAPPER` (in `SubprocessWrapperRunner` and
  `product_wrapper` only), gives a string starting `id=` or holding `--path id=`, or names
  `tenant-scale#create-a-project` or `tenant-scale#delete-a-project`; no module reads an attribute `main`, loads
  `gitlab_wrapper_fixtures` or patches `urllib`.
- **AC-9.1** — Example, G `test_the_setup_note_names_the_gitlab_credential`: `docs/forge-suite.md` names
  `credentials/gitlab-sff-testing-pat.txt`, `bestehorn-sff-test`, "Service accounts", "Owner", `api`,
  `SFF_GITLAB_TEST_TOKEN`, the local command, and that only a machine running the GitLab forge suite locally needs the
  file.
- **AC-9.2** — Example, G `test_the_map_names_the_gitlab_forge_suite`: `docs/forLLMConsumption.md` names
  `test/forge_gitlab`, the local command, the credential file, `docs/forge-suite.md` and `forge-gitlab`; B
  `test_llm_map_within_cap`.
- **UB-1** — W, S and G run in `verify` with no network and no test credential file; the fake-host suites are unedited.
- **UB-2** — Example, S `test_the_token_is_written_only_to_the_clone`: a sentinel `config/gitlab.json` in the test's
  checkout keeps its content.
- **UB-3** — C, A, K, V and P pass unedited (P `test_standard_library_only` included); W
  `test_without_the_marker_every_project_is_served`.
- **UB-4** — H and L pass, L with D5's one expectation extended and none removed; L
  `test_the_forge_path_collects_every_forge_test` still lists exactly `test/forge/`'s tests; the diff touches no file
  under `test/forge/`.
- **UB-5** — I passes; the PR diff names no file `config/toolchain.json` lists.

## Security Considerations

- **The test token** lives in the git-ignored test credential file, the clone's `config/gitlab.json` and
  `.git/sff-forge-token` (D8) and, in CI, the one step's `env:` (D5); git receives it through the helper's pipe (D3),
  the wrapper in its own `PRIVATE-TOKEN` header. No argv, URL or log line holds it.
- **Blast radius.** The token reaches what the service account reaches, the test group by the operator's setup; the
  teardown and the sweep delete only what D9's guards select; the wrapper refuses any configured project but an
  `sff-test-*` path under the marker (D2), and only the support module may give `--path id=` (G). Git Credential
  Manager is never asked (D3), the workflow's `GITHUB_TOKEN` stays out of the checkout (D5), and the checkout's
  `config/gitlab.json` is never opened (UB-2).
- **The guard's bound.** It judges the configured project's last path segment, not its namespace (`requirements.md`
  Residuals), and not an explicit `--path id=`, which reaches any project the token reaches.
- **CI trust**, as #10: fork and Dependabot pull requests get no secret and fail the job (AC-5.3); a same-repository
  pull request or a dispatch runs its own branch's suite with the secret, bounded by the token's reach.
- **External input.** Project paths from the listing reach the wrapper only as `--path` values in a list argv (no
  shell), which `registry._segment` encodes.
- **Dependencies.** None added: the wrapper uses `sys` and `json`, which it imports already.

## Operability

- **Logs.** pytest's `-ra` summary lists every non-passing test; the suite logs each project it creates and deletes by
  full path, live in the job log (`log_cli`); a wrapper refusal is its standard-error line.
- **Deletion on gitlab.com.** Each run's project stays marked for deletion, read-only and renamed (D4), until gitlab.com
  removes it at the end of its retention period; the sweep skips it. The leftovers marked by the sweep follow the same
  path.
- **Rate limits.** One creation per run (AC-1.1); gitlab.com's documented per-user project-creation limit
  (docs.gitlab.com/user/gitlab_com/rate_limits/) bounds the runs a day of the one service account. A `429` that
  outlasts the transport's retries is a `GitLabRateLimitError`, exit 1: the run creates nothing and deletes nothing.
- **Leftovers.** An interrupted run (a cancelled CI run, a local Ctrl-C) leaves its project unmarked, deleted by the
  first run more than a day after its creation; an interrupted local run also leaves its workspace, as #10.
- **Rollback.** Revert the change: the job, the suite and the guard go together; a project from before the revert
  stays in the test group until the suite returns or gitlab.com removes a marked one; the operator deletes the secret
  `SFF_GITLAB_TEST_TOKEN` and revokes the token unless the suite is to return.

## Acceptance Criteria Mapping

In `src/payload/test/`: W = `test_gitlab_wrapper_marker.py` (new), C = `test_gitlab_wrapper_compat.py`, A = the
`test_gitlab_api_*` suites (with `test/`'s). In `test/`: S = `test_forge_gitlab_support.py` (new), G =
`test_forge_gitlab_layout.py` (new), L = `test_forge_suite_layout.py`, H = `test_forge_support.py`, K =
`test_gitlab_wrapper_contract.py`, V = `test_gitlab_wrapper_coverage.py`, P = `test_gitlab_api_properties.py`, I =
`test_toolchain_integrity.py`, B = `test_instruction_corpus_budget.py`. In `test/forge_gitlab/`: F:<module> =
`forge_<module>.py` (new).

| Criterion | Component | Tests |
|---|---|---|
| AC-1.1 | D9 `provision`, `read_test_group`, `create_ephemeral`; D1 `refuse_distributed_run` | F:fixture `test_the_run_owns_a_private_seeded_project`; S `test_provisioning_runs_in_order`, `test_a_distributed_run_is_refused`; G `test_the_session_fixture_wraps_one_provision` |
| AC-1.2 | D4 `ephemeral_path`, `ephemeral_full_path` | S `test_a_run_id_names_an_ephemeral_project` |
| AC-1.3 | D3 clone; D9 steps 6, 7 | F:fixture `test_the_run_owns_a_private_seeded_project`; F:subcommands `test_no_pipeline_has_run`; F:records `test_the_repository_records_read_the_seed`; S `test_provisioning_runs_in_order` |
| AC-1.4 | D9 step 8 | S `test_provisioning_runs_in_order`; G `test_the_session_fixture_wraps_one_provision` |
| AC-2.1 | D9 `delete_ephemeral` | S `test_the_teardown_deletes_only_this_runs_project` |
| AC-2.2 | D9 `delete_ephemeral` | S `test_the_teardown_refuses_any_other_target` |
| AC-2.3 | D9 `delete_ephemeral`, step 6 | S `test_no_creation_no_deletion` |
| AC-3.1 | D9 `list_group_projects`, `sweep_leftovers`, `is_leftover` | S `test_the_sweep_deletes_exactly_the_old_unscheduled_ephemeral_projects`, `test_the_sweep_boundaries_and_refusals`; F:fixture `test_no_leftover_survives_the_sweep` |
| AC-3.2 | D9 `is_leftover`, `delete_leftover` | S the same two tests |
| AC-3.3 | D9 `sweep_leftovers`, `delete_leftover` | S the same two tests |
| AC-4.1 | D2 `_refuse_unless_ephemeral`, `_run`, `main` | W `test_the_marker_refuses_a_project_without_the_prefix`, `test_the_interpreter_option_reaches_the_entry_script` |
| AC-4.2 | D2 `_is_ephemeral_project` | W `test_the_marker_lets_an_ephemeral_project_through`; every F test |
| AC-4.3 | D2 `-X`; D10 `SubprocessWrapperRunner` | S `test_every_wrapper_invocation_carries_the_marker`; W `test_the_marker_values_are_issue_10s`, `test_without_the_marker_every_project_is_served`; G `test_the_gitlab_forge_tests_reach_only_the_ephemeral_project` |
| AC-5.1 | D5 `forge-gitlab` | G `test_the_gitlab_forge_job_runs_beside_verify` |
| AC-5.2 | D5; D8 `write_test_credential`; D1 `pytest.ini` | G `test_the_gitlab_secret_reaches_one_step`, `test_nothing_keeps_a_gitlab_forge_test_from_running` |
| AC-5.3 | D5; D8 `write_credential.py` | S `test_a_missing_secret_fails_the_credential_step` |
| AC-5.4 | D5 `report` | G `test_the_report_judges_the_gitlab_forge_job`; L `test_the_report_judges_the_forge_job` |
| AC-6.1 | D8 `find_test_credential` | S `test_the_test_credential_is_found_in_the_checkout_or_its_main_tree` |
| AC-6.2 | D8 `read_test_token`; D9 step 2 | S `test_a_bad_test_credential_fails_before_any_request` |
| AC-6.3 | D3; D5; D8 | S `test_the_token_is_written_only_to_the_clone`, `test_the_clone_commits_no_credential`, `test_the_credential_helper_answers_git_with_the_clone_token`; G `test_the_gitlab_secret_reaches_one_step` |
| AC-7.1 | D1 | G `test_the_default_configuration_collects_no_gitlab_forge_test` |
| AC-7.2 | D1 `pytest.ini` | G `test_the_gitlab_forge_path_collects_every_gitlab_forge_test` |
| AC-7.3 | D1 | G `test_nothing_keeps_a_gitlab_forge_test_from_running` |
| AC-8.1 | D6; D10 `SubprocessWrapperRunner` | G `test_the_gitlab_forge_tests_reach_only_the_ephemeral_project`; every F test |
| AC-8.2 | D6 #13; D10 `push_branch`, `wait_until_checked` | F:subcommands `test_an_issue_and_label_round_trip`, `test_a_merge_request_round_trip`, `test_delete_branch_removes_a_pushed_branch`, `test_no_pipeline_has_run` |
| AC-8.3 | D6 `call` records | F:records `test_the_repository_records_read_the_seed`, `test_the_issue_and_note_records`, `test_the_merge_request_records`; F:fixture `test_the_run_owns_a_private_seeded_project` |
| AC-8.4 | D6 #44 | F:graphql `test_the_work_items_of_the_project` |
| AC-8.5 | D6 #63; D10 runner bytes | F:request_forms `test_an_endpoint_named_by_endpoint`, `test_a_format_suffix`; G `test_each_uncalled_form_is_named_with_its_reason` |
| AC-8.6 | D6 the uncalled forms | G `test_each_uncalled_form_is_named_with_its_reason` |
| AC-8.7 | D6; D9 | G `test_the_gitlab_forge_tests_reach_only_the_ephemeral_project` |
| AC-9.1 | D7 | G `test_the_setup_note_names_the_gitlab_credential` |
| AC-9.2 | D10 docs | G `test_the_map_names_the_gitlab_forge_suite`; B `test_llm_map_within_cap` |
| UB-1 | D1; W, S, G doubles | W, S, G in `verify`; the fake-host suites unedited |
| UB-2 | D8 | S `test_the_token_is_written_only_to_the_clone` |
| UB-3 | D2 | C, A, K, V, P unedited; W `test_without_the_marker_every_project_is_served` |
| UB-4 | D1; D5 | H, L (one expectation extended); the diff under `test/forge/` empty |
| UB-5 | none | I; the PR diff |

## Residuals

- The `requirements.md` Residuals stand.
- The findings-ledger rows naming "#11's run" (container-registry forms, `oauth/token/info`, Geo and SCIM paging,
  Workhorse upload forms) stay rows: no D6 test calls those records.
- The guard does not judge an explicit `--path id=` (Security Considerations); G confines it to the support module.
- `graphql#Project.workItems` carries the reference's note "**deprecated** in 15.9"; its removal would fail
  F:graphql until another work-item record replaces it.
- `report` keeps `if: always()` and the workflow's action pins stay as they are (#10 Residuals).
- An interrupted local run's workspace is removed only by `/close-session`'s temporary-directory sweep, as #10.
