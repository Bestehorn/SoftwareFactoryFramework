# Design — issue #10: integration tests of the forge wrapper against ephemeral `sff-test-*` repositories (S4)

Tier: M. Kind: FEATURE. Criteria: `requirements.md` (AC-1.1 to AC-9.3, UB-1 to UB-4, frozen). D1 to D7 are the
decisions the issue left open; D8 to D10 complete the design. Test files are named in the legend of the Acceptance
Criteria Mapping.

## User Prompts

1. User, 2026-11-10 (the `/auto-work` command; its full text is `.claude/commands/auto-work.md`): "Work this project's
   open-issue backlog AUTONOMOUSLY, end to end, following `.claude/agents/issue-work-orchestrator.md` exactly."
2. Issue #10, Ask: "implement the ephemeral-repository integration tests per S4 (GitHub first), including the CI job
   and the guards, with the operator-provided token as an explicit prerequisite item."
3. User, 2026-11-12: "the org is called "bestehorn-sff-test"" (issue #10 comment 6828747536). The operator's other
   answers (the token, its file, the CI secret) are in `prompts.md`.

## Overview

- **The origin guard** (D2): while the interpreter option `-X sff_test_marker` is set, `github_wrapper.py` `main`
  refuses an `origin` whose name does not start with `sff-test-`, before any request, exit 2.
- **The forge suite** (D1): `test/forge/`, with its own `pytest.ini`; its modules `forge_*.py` match no default
  `python_files` pattern. Run: `python scripts/run_tests.py --workers 1 test/forge`.
- **The session fixture** (D9): `test/forge/conftest.py` `ephemeral_repository` over `test/forge/ephemeral.py`
  `provision`: read the test token, prepare the clone, sweep leftovers, create `sff-test-<run id>`, fetch its seed,
  yield, then delete the repository and remove the clone.
- **The forge job** (D5): `.github/workflows/ci.yml` `forge`, beside `verify`; `report` judges both.
- **The slice tests** (D6) and **the credential note** (D7).

Data flow: a forge test calls `SubprocessWrapperRunner.run`, which starts `python -X sff_test_marker
src/payload/scripts/github_wrapper.py <argv>` with the clone as working directory; `_load_token` reads the clone's
`credentials/github-pat.txt`, `_detect_repo` its `origin`, the guard passes, and the request goes to github.com. Git
commands go through `SubprocessGitRunner` with a per-command credential helper (D3).

Patterns followed: test support loaded by path, never collected by name (`src/payload/test/github_wrapper_fixtures.py`;
`test/test_github_wrapper_fork_parity.py`'s loader); a suite outside the default collection with its own command
(`run_checks.py` `hook_suite_argv`); a refusal raised as `GitHubAPIError` inside `main`'s existing refusal block
(`_load_token`, `_detect_repo`). One deviation: the forge job's check is the `run_tests.py` command above,
not a `run_checks.py` group, because `run_checks.py` is toolchain (D5 Alternatives); a local `run_checks.py` does not
run the forge suite.

## Design

### D1 — Suite location and separation (AC-7.1 to AC-7.3; UB-1)

**Location.** `test/forge/` (`testing.md` rule 1: `test/` holds this repository's own tests).

**Mechanism.** `test/forge/pytest.ini`: `[pytest]`, `python_files = forge_*.py`, `addopts = -p no:cacheprovider` (no
cache written beside the suite, as `hook_suite_argv` does), `log_cli = true`, `log_cli_level = INFO` (each creation
and deletion reaches the job log as it is logged: "pytest will output logging records as they are emitted directly
into the console", docs.pytest.org `how-to/logging.html`). The test modules are `forge_*.py`; the support files are
`conftest.py`, `ephemeral.py` and `write_credential.py` (D10).

- **The forge run.** `python scripts/run_tests.py --workers 1 test/forge`, in the forge job and locally.
  `run_tests.py` passes the path through (`build_command`, `parse_known_args`). The path is the common ancestor, so
  `test/forge/pytest.ini` is the configfile (docs.pytest.org `reference/customize.html`: the search runs from "the
  shared parent directory of all specified filesystem paths" upward, and "Options from multiple configfiles
  candidates are never merged - the first match wins"); `python_files` is `forge_*.py`, every forge module is
  collected, and conftest loading stops there ("the cutoff defaults to the directory containing the config file",
  `how-to/writing_plugins.html`).
- **The default collection** (`run_tests.py` with no path; the `verify` leg `tests`). `pyproject.toml` is the
  configfile; `testpaths` recurses into `test/forge`, where the default `python_files` (`test_*.py`, `*_test.py`)
  matches no module, as it matches no `github_wrapper_fixtures.py`. It imports `test/forge/conftest.py`, which
  defines one fixture and no hook, and imports only the standard library and pytest at module level: it loads
  `ephemeral.py` by path, because under `--import-mode=importlib` "Testing utility modules in the tests directories
  ... are not importable" (`explanation/pythonpath.html`).

**Why this is not an exclusion.** `pyproject.toml` `[tool.pytest.ini_options]` is not edited: no `testpaths` change,
no `norecursedirs`, `--ignore`, `-m`, `-k` or `collect_ignore`. No forge module ever matched the default convention,
so no run loses a test it collected before. The suite runs whole on every pull request in the forge job, whose failure
fails the pipeline (D5), and nothing in `test/forge/` skips, xfails, deselects or hooks collection (L
`test_nothing_keeps_a_forge_test_from_running`).

**One repository per run.** pytest-xdist: "tests in different processes requesting a high-level scoped fixture (for
example `session`) will execute the fixture code more than once" (pytest-xdist.readthedocs.io `how-to.html`). The
forge command therefore passes `--workers 1`, for which `build_command` adds no `-n`, and `ephemeral_repository`
first calls `refuse_distributed_run(worker_id=...)` with xdist's `worker_id` fixture ("master" when xdist is not
distributing): any other value raises `ForgeSetupError` saying to run the suite with `--workers 1`.

Alternatives: `test/forge/test_*.py` with `norecursedirs` or `--ignore` in `pyproject.toml` (an exclusion in
`[tool.pytest.ini_options]`, which `tests-must-not-fail.md` forbids); `testpaths` narrowed by a glob (the same
exclusion, and a later subdirectory of `test/` would drop out unseen); a top-level directory outside `testpaths`
(`file-organization.md` puts tests in `test/`, and `test/test_layout.py`
`test_python_lives_only_in_src_test_and_scripts` refuses Python elsewhere); `forge_*.py` with `-o python_files=` on
the command line (the module convention would belong to the command, not to the suite's own configuration);
`test/e2e/` (`run_checks.py` `e2e_argv`, a post-merge group that runs only on request and that `ci.yml` does not run,
whereas S4 runs the suite on every pull request; `test/forge/` is this project's equivalent); a `forge` group in
`run_checks.py` (D5 Alternatives).

### D2 — The test marker and the origin guard (AC-4.1 to AC-4.3; UB-3)

**The marker** is the CPython interpreter option `-X sff_test_marker`, given by the suite to the interpreter that
runs the entry script. docs.python.org `using/cmdline.html` `-X`: "It also allows passing arbitrary values and
retrieving them through the sys._xoptions dictionary"; `library/sys.html` `sys._xoptions`: "A dictionary of the
various implementation-specific flags passed through the -X command-line option. Option names are either mapped to
their values, if given explicitly, or to True", "Added in version 3.2". It belongs to one process: no environment
variable, the same in any working directory, and no file of a checkout can set it.

**The product wrapper** (`src/payload/scripts/github_wrapper.py`):

- `TEST_MARKER_OPTION = "sff_test_marker"`, `EPHEMERAL_REPOSITORY_PREFIX = "sff-test-"`.
- `_test_marker_set() -> bool`: `TEST_MARKER_OPTION in getattr(sys, "_xoptions", {})` (an interpreter without
  `sys._xoptions` has no marker).
- `_refuse_unless_ephemeral(*, owner: str, repo: str) -> None`: when the marker is set and `repo` does not start with
  `EPHEMERAL_REPOSITORY_PREFIX`, raises `GitHubAPIError(message=f"The test marker (-X {TEST_MARKER_OPTION}) is set and
  the origin names {shown}/{repo}, which is not an {EPHEMERAL_REPOSITORY_PREFIX}* repository; nothing was sent")`.
  `owner` and `repo` are `_detect_repo`'s groups of `GITHUB_REPOSITORY_PATTERN`; `shown` is
  `owner.rpartition(USERINFO_SEPARATOR)[2]`, the idiom of `_without_userinfo`, because the owner group of an origin
  whose userinfo ends in `github.com:` holds the rest of that userinfo.
- `main` calls it inside its existing `try`, right after `owner, repo = _detect_repo()`. The existing
  `logger.error("%s", exc)` writes the message to standard error (`ERROR: ` and the message, `LOG_FORMAT`) and `main`
  returns `EXIT_REFUSED` before the delivery-verb branch (`steward_delegate`) and `_run_command` (which builds the
  `Transport`), so no subcommand, the delivery verbs and `call` included, sends anything.
- The docstrings of `main` and of the module's exit paragraph name this refusal.

Without the marker `_refuse_unless_ephemeral` returns at once; `_build_parser` is untouched, so the requests, output
and exit codes are unchanged (UB-3) and P compares the same parsers.

Alternatives: a command-line option (changes the parser P compares, UB-3); a launcher calling `main` with a keyword
(changes `main`'s signature, and the suite would not run the entry script itself); an environment variable (forbidden
by `no-environment-vars.md` and AC-4.3); a marker file in the clone (a property of a directory, which an ordinary
checkout could carry).

### D3 — Git authentication (AC-1.3, AC-6.3, AC-8.2)

**The helper.** `credential_helper_arguments(*, clone: Path) -> List[str]` returns, for each authenticated git
command (fetch, push), the global options

```
-c credential.helper=
-c credential.https://github.com.helper=!f() { test "$1" = get || return 0; read -r t < '<clone>/credentials/github-pat.txt' || test -n "$t"; printf 'username=x-access-token\npassword=%s\n' "$t"; }; f
```

with `<clone>` the clone's absolute path in forward-slash form (`Path.as_posix()`), single-quoted so a space ("Code
Workspace") is literal; a path holding `'` raises `ForgeSetupError` before any git command.

- git-scm.com/docs/gitcredentials: "If the helper string begins with "!", it is considered a shell snippet, and
  everything after the "!" becomes the command"; "If `credential.helper` is configured to the empty string, this
  resets the helper list to empty"; a `credential.<URL>` context matches when "both protocols are the same and both
  hosts are the same" ("CREDENTIAL CONTEXTS"), so the helper answers only for `https://github.com`; a helper "will
  have one "operation" argument appended" (`get`, `store`, `erase`), and for `get` writes `username=` and
  `password=` lines on standard output. git-scm.com/docs/git `-c`: "Pass a configuration parameter to the command."
- docs.github.com "Managing your personal access tokens": "the username is not used to authenticate you. Instead,
  the personal access token is used to authenticate you."
- The token goes from the clone's file through the shell built-ins `read` and `printf` to git's pipe: no argv holds
  it (the helper string holds only the path), no URL, no environment variable, and nothing is written. The empty
  value first empties the helper list, so no configured helper (Git Credential Manager on Windows) is asked to
  `store` it; the snippet answers `store` and `erase` with nothing.
- Platforms: git runs a `!` helper with a POSIX shell — `/bin/sh` (dash) on the ubuntu runner, the `sh` Git for
  Windows ships; `read` and `printf` are built-ins of both (dash(1) "Builtins"; GNU Bash manual "Bash Builtin
  Commands"). S `test_the_credential_helper_answers_git_with_the_clone_token` runs the helper through `git credential
  fill` (`protocol=https`, `host=github.com`) on each platform the default collection runs on.

**The clone** is made by git clone's own steps ("creates remote-tracking branches for each branch in the cloned
repository ... and creates and checks out an initial branch", git-scm.com/docs/git-clone), split so that the file the
helper reads exists before the first authenticated command ("Cloning into an existing directory is only allowed if
the directory is empty", ibid.): `git init` in the created `<clone>`, the clone's credential file (D9), `git remote
add origin https://github.com/bestehorn-sff-test/<name>.git`, and after the creation an authenticated `git fetch
origin` and `git checkout -B <default branch> --track origin/<default branch>`. The origin URL carries no userinfo, so
`.git/config` holds no token. The pull-request test pushes its branch with an authenticated `git push origin
<branch>`. Every git command passes the suite's commit identity with `-c user.name=` and `-c user.email=` (constants
of `ephemeral.py`; a runner has no global identity).

Alternatives: the token in the URL's userinfo (in argv and `.git/config`); `http.extraHeader` (in argv;
`--config-env` reads an environment variable); `GIT_ASKPASS` (an environment variable); the `store` helper or `git
credential approve` (a second copy on disk); `git clone` with the helper reading the test credential file (that file
is the operator's text; the clone's file holds exactly the token `_one_token` accepted from it).

### D4 — The run id (AC-1.2)

`new_run_id() -> str`: the UTC time as `%Y%m%d%H%M%S`, `-`, then `uuid.uuid4().hex`. It holds digits, lowercase hex
and `-` and no `.`, so `GITHUB_REPOSITORY_PATTERN` (`[^/.]+`) reads `sff-test-<run id>` back as the repository name.
Two runs differ in the random part. Were two ids ever equal, the later `repos/create-in-org` would fail on the
existing name: that run creates nothing and therefore deletes nothing (AC-2.3), so two runs never share a repository.
`ephemeral_name(*, run_id) -> str` is `EPHEMERAL_REPOSITORY_PREFIX + run_id`.

Alternatives: the time alone (two runs started in one second collide); `github.run_id` (CI only, and it reaches the
suite only through an environment variable); the process id (reused).

### D5 — The forge CI job (AC-5.1 to AC-5.4)

`.github/workflows/ci.yml` gains the job `forge` and changes `report`; `verify`, `on:`, the workflow `concurrency` and
`permissions` are unchanged. `ci.yml` is not toolchain: `config/toolchain.json` lists no workflow, its `not_installed`
entry `templates/ci/*` records `ci.yml` as this project's own, and `templates/ci/` holds no source for it.

```yaml
  forge:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: {persist-credentials: false}
      - uses: actions/setup-python@v5
        with: {python-version: '3.10'}
      - run: pip install -e ".[dev]"
      - name: Write the test credential file
        env:
          SFF_TEST_TOKEN: ${{ secrets.SFF_TEST_TOKEN }}
        run: python test/forge/write_credential.py
      - run: python scripts/run_tests.py --workers 1 test/forge

  report:
    runs-on: ubuntu-latest
    needs: [verify, forge]
    if: always()                  # WITHOUT this, a failed verify leg or forge job skips the verdict
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.10'}
      - uses: actions/download-artifact@v4
        with: {path: reports/, merge-multiple: true}
      - name: Consolidated verdict
        run: |
          python scripts/run_checks.py --summary-from reports | tee verdict.txt
          status=${PIPESTATUS[0]}
          echo "forge job: ${{ needs.forge.result }}" | tee -a verdict.txt
          if [ "${{ needs.forge.result }}" != "success" ]; then status=1; fi
          cat verdict.txt >> "$GITHUB_STEP_SUMMARY"
          exit "$status"
```

- **No `needs:`** between `forge` and `verify`: they run in parallel (AC-5.1). The header comment's contract holds:
  one check command (`run_tests.py`, which refuses fail-fast flags, `reject_failfast`, and lists every non-passing
  test, `REPORT_ARGS` `-ra`; AC-5.2).
- **The secret** reaches the one credential step through its `env:` block, GitHub's documented way into a `run` step
  ("Avoid passing secrets between processes from the command line", docs.github.com "Using secrets in GitHub
  Actions"), and from there only the test credential file of the checkout (D8). `persist-credentials: false` keeps
  the `GITHUB_TOKEN` out of the checkout's git config ("The auth token is persisted in the local git config ... Set
  `persist-credentials: false` to opt-out", `actions/checkout` README).
- **A missing secret** (AC-5.3): "If a secret has not been set, the return value of an expression referencing the
  secret ... will be an empty string", and "Secrets cannot be directly referenced in `if:` conditionals" (ibid.), so
  `write_credential.py` judges it: an empty value logs "the secret SFF_TEST_TOKEN is unavailable to this run" and
  exits 1, which fails the job before the suite runs.
- **The verdict** (AC-5.4): `report` runs after both whatever their results, still merges `verify`'s
  `checks-*.json` (`summarize_from`), and fails unless `needs.forge.result` is `success` ("Possible values are
  success, failure, cancelled, or skipped", docs.github.com "Contexts reference" `needs`). A forge job that dies
  before writing anything is judged by that result, since it writes no `checks-*.json`.
- **Concurrency.** The workflow's group `ci-${{ github.ref }}` applies: a superseded pull-request run is cancelled, a
  run on `main` never is. Runs of different refs proceed together; their run ids keep their repositories apart, and the
  sweep spares any repository a day old or less. What a cancelled run leaves is in Operability, Leftovers.
- **The test organization** is the constant `TEST_ORGANIZATION = "bestehorn-sff-test"` of `ephemeral.py`, the one
  place the suite names it. Alternative: a configuration file (a second file and a parser for one value).

Alternatives: a `forge` group in `run_checks.py` (toolchain; no such group can exist before a promotion); the suite in
the `verify` matrix (`verify` would need the network and the secret, against UB-1); a `checks-forge.json` written by
the suite for `summarize_from` (a job that dies early writes none); a job-level concurrency group (run ids already keep
concurrent runs apart).

### D6 — The real-forge tests per slice (AC-8.1 to AC-8.6) and the token's permissions

Every test takes `ephemeral_repository`, runs the product wrapper through its `wrapper` (marker set, the clone as
working directory) and asserts each invocation's exit code and its printed JSON (`Invocation.json()`). No `--path
owner=` or `--path repo=` is given, so every repository record targets the clone's `origin`. `N` is the number an
answer printed; `<hex>` is a fresh `uuid.uuid4().hex` of the test.

| Module (slice) | Test | Invocations and what is asserted |
|---|---|---|
| F:fixture | `test_the_run_owns_a_private_seeded_repository` | `call repos/get`: `full_name` `bestehorn-sff-test/sff-test-<run id>`, `private` true; in the clone, `HEAD` equals `origin/<default branch>`, `git ls-tree -r --name-only HEAD` names nothing under `.github/workflows/`, `git remote get-url origin` is the repository's URL, `credentials/github-pat.txt` exists (AC-1.1, AC-1.3) |
| F:fixture | `test_no_leftover_survives_the_sweep` | `call repos/list-for-org --path org=bestehorn-sff-test`: no item `is_leftover` with `now=swept_at` (AC-3.1) |
| F:subcommands (#17) | `test_an_issue_round_trip` | `call issues/create-label -f name=forge-label`; `create-issue --title T --body B` (`state` open, `title` T); `get-issue N` (T, B, open); `comment-issue N --body C` (`body` C); `get-issue-comments N` (one comment, C); `label-add N --labels forge-label` (names it); `get-issue N` (its `labels` name it); `update-issue N --state closed` (closed); `get-issue N` (closed) |
| F:subcommands (#17) | `test_a_pull_request_round_trip` | git: a branch `forge-pull-request` from the seed, one file committed, pushed, the default branch checked out again; `create-pr --head forge-pull-request --base <default branch> --title T --body B` (`head.ref`, `head.sha` the pushed commit, `base.ref`, open); `get-pr N` (same, `merged` false); `merge-pr N` (`merged` true); `get-pr N` (`merged` true, closed) |
| F:repos_git (#27) | `test_the_repository_record_names_the_seed_branch` | `call repos/get`: `default_branch` is the one the creation answered and the clone checked out |
| F:repos_git (#27) | `test_the_git_records_read_the_seed_commit` | `call git/get-commit --path commit_sha=<seed sha>`: `sha`, `tree.sha` the seed's; `call git/get-tree --path tree_sha=<seed tree>`: one entry, `README.md` (`auto_init`: "Pass true to create an initial commit with empty README.", docs.github.com "Create an organization repository") |
| F:ci_security (#31) | `test_no_workflow_has_run` | `call actions/list-workflow-runs-for-repo`: `[]` |
| F:ci_security (#31) | `test_code_scanning_answers_as_documented` | `call code-scanning/list-alerts-for-repo`: exit 1, standard error names `HTTP 403` ("Response if GitHub Advanced Security is not enabled for this repository", docs.github.com "List code scanning alerts for a repository") and not "Resource not accessible by personal access token", the missing-permission answer (`docs/api-reference/github/conventions.md` "Authentication") |
| F:ci_security (#31) | `test_secret_scanning_answers_as_documented` | `call secret-scanning/list-alerts-for-repo`: exit 1, `HTTP 404` ("Repository is public, or secret scanning is disabled for the repository, or the resource is not found", docs.github.com "List secret scanning alerts for a repository") |
| F:ci_security (#31) | `test_dependabot_lists_no_secret` | `call dependabot/list-repo-secrets`: `[]` (the repository holds no Dependabot secret) |
| F:collaboration (#32) | `test_issue_and_reaction_records` | `create-issue` (setup, as `call` refuses `issues/create`); `call issues/get --path issue_number=N` (`number`, `title`); `call reactions/create-for-issue --path issue_number=N -f content=+1` (`content` `+1`); `call reactions/list-for-issue --path issue_number=N` (one item, `+1`) |
| F:collaboration (#32) | `test_pulls_search_activity_and_gists_records` | `call pulls/list --query state=all --query head=bestehorn-sff-test:forge-absent-<hex>`: `[]`; `call search/repos --query q=<hex>`: `[]`; `call activity/list-stargazers-for-repo`: `[]`; `call gists/get --path gist_id=<hex>`: exit 1, `HTTP 404` (docs.github.com "Get a gist": `404` "Resource not found"), a read that creates nothing |

- **`checks`** is named in `forge_ci_security.py`'s docstring with its reason and not called (AC-8.4): GitHub lists
  "Using fine-grained personal access token to call the Checks API" among the token kind's gaps (docs.github.com
  "Managing your personal access tokens"; `conventions.md` "no Checks API").
- **`dependabot`**: `list-repo-secrets` has a documented answer on any repository; the alerts record's documented
  `403` "Forbidden" does not tell a disabled feature from a missing permission.
- **`search`**: a query for a fresh random text has a known answer; GitHub documents no indexing delay for a new
  private repository, so nothing asserts that the repository is found.
- **`gists`**: account permissions "can only be used when the current user is the resource owner" (docs.github.com
  "Managing your personal access tokens"), so an organization's token reaches no user gist; `gists/list-public`
  would page every public gist, since `call` reads every page of a `Paging.LINK` record.

**The token's permissions** (docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens;
token: fine-grained, resource owner `bestehorn-sff-test`, "All repositories"):

| Repository permission | Access | Today | Records and git operations that need it |
|---|---|---|---|
| Administration | write | granted | `repos/create-in-org`, `repos/delete` |
| Contents | write | granted | git fetch and push; `git/get-commit`, `git/get-tree`; `merge-pr` (`pulls/merge`); `activity/list-stargazers-for-repo` |
| Metadata | read | in place (run 43256615628's `repos/get`) | `repos/get`, `repos/list-for-org` |
| Issues | write | to grant | `issues/create-label`, `create-issue`, `get-issue`, `comment-issue`, `get-issue-comments`, `label-add`, `update-issue`, `issues/get`, `reactions/create-for-issue`, `reactions/list-for-issue` |
| Pull requests | write | to grant | `create-pr`, `get-pr`, `pulls/list` |
| Actions | read | to grant | `actions/list-workflow-runs-for-repo` |
| Code scanning alerts | read | to grant | `code-scanning/list-alerts-for-repo` |
| Secret scanning alerts | read | to grant | `secret-scanning/list-alerts-for-repo` |
| Dependabot secrets | read | to grant | `dependabot/list-repo-secrets` |

`search/repos` and `gists/get` need none (neither is on the page). Not needed: Workflows (no workflow file is pushed),
Dependabot alerts (not called), Checks (not grantable to this token kind).

### D7 — The credential's setup note; no template (AC-9.1)

The note is `credentials/README.md`, tracked by `.gitignore` `!credentials/README.md`: beside the file it describes,
and it gives every checkout a `credentials/` directory. It names the test credential file, the token kind
(fine-grained), its resource owner (`bestehorn-sff-test`), its repository access ("All repositories"), D6's permission
table, the Actions secret `SFF_TEST_TOKEN`, the local command, and that only a machine that runs the forge suite
locally needs the file (CI writes it from the secret). No `credentials/github-sff-testing-pat.txt.template` ships.

Alternatives: a template stub (a placeholder file the suite must refuse, AC-6.2, and this repository ships no
`github-pat.txt.template` either); the note under `docs/` (away from the directory the operator works in).

### D8 — The test credential (AC-6.1 to AC-6.3; UB-2)

- **Lookup** (`find_test_credential(*, checkout: Path) -> Path`, `checkout` the working tree holding the suite,
  `CHECKOUT`): `checkout/credentials/github-sff-testing-pat.txt` when it is a file; else, for a linked worktree, which
  has no git-ignored files, the same path under the main working tree, the parent of `git rev-parse
  --path-format=absolute --git-common-dir` run in `checkout`; else `ForgeSetupError` naming both paths.
- **Reading** (`read_test_token(*, path: Path) -> str`): the refusals `_load_token` makes for `CREDENTIALS_FILE`,
  through the product wrapper's own `_one_token` and `PLACEHOLDER` (`product_wrapper()`, D10): a file that is not one
  token, empty, or the placeholder raises `ForgeSetupError` naming the path and none of its contents. It precedes
  every request (D9 step 2; AC-6.2); a session fixture that raises errors every test that uses it, so none is
  skipped.
- **Writing** (D9 step 3): the clone's `credentials/github-pat.txt` holds the token and `\n`, written as bytes
  (`Path.write_bytes`), file mode `0o600`, and `credentials/` is appended to the clone's `.git/info/exclude`, so no
  commit of the pull-request test can hold it. `0o600` is owner-only on POSIX; on Windows, where one "can only set the
  file's read-only flag" (docs.python.org `os.chmod`), the protection is the `tempfile.mkdtemp` workspace's (D9),
  owner-only on a CPython with the CVE-2024-4030 fix, 3.12.4 and later and the 2024 security releases of 3.9 to 3.11
  ("os.mkdir() on Windows now accepts mode of 0o700 to restrict the new directory to the current user", python.org
  3.9.20 release notes). The token is a local of `provision` only; no object the tests receive holds it, and nothing
  logs or prints it.
- **CI** (`write_test_credential(*, token: str, checkout: Path) -> None`): an empty `token` raises `ForgeSetupError`
  saying that the secret `SFF_TEST_TOKEN` is unavailable to this run, writing nothing; otherwise it writes
  `checkout/credentials/github-sff-testing-pat.txt`. `write_credential.py` `main` calls it with the value of
  `SFF_TEST_TOKEN` — the one environment read of the change, the step AC-6.3 names — logs a refusal and returns 1.
- **UB-2**: the suite reads and writes `credentials/github-pat.txt` only under the clone (`CLONE_CREDENTIAL_FILE`).

### D9 — Provisioning, the sweep and the teardown guard (AC-1, AC-2, AC-3)

`provision(*, checkout, workspace, wrapper: WrapperRunner, git: GitRunner)` is a context manager yielding an
`EphemeralRepository` (`run_id`, `owner`, `name`, `default_branch`, `seed_sha`, `seed_tree_sha`, `swept_at`, `clone`,
`wrapper`, `git`; `swept_at` is the `now` step 4 passed to `sweep_leftovers`). `ephemeral_repository` (session scope)
calls it with a `tempfile.mkdtemp` workspace — not pytest's `tmp_path_factory`, whose directories outlive the session
— and the runners bound to `<workspace>/clone`.

1. Before the `try`: `run_id = new_run_id()`, `name = ephemeral_name(run_id=run_id)` (no request).
2. `read_test_token(path=find_test_credential(checkout=checkout))`.
3. `prepare_clone`: `<workspace>/clone` created with `Path.mkdir`, then `git init`, the clone's credential file and
   exclude line (D8), `git remote add origin`.
4. `sweep_leftovers(wrapper=..., now=swept_at)`, `swept_at` the UTC now.
5. `create_ephemeral(wrapper=..., name=name) -> CreatedRepository`: `call repos/create-in-org --path
   org=bestehorn-sff-test -f name=<name> -F private=true -F auto_init=true`; a non-zero exit raises
   `ForgeCommandError` (nothing was created); the answer's `owner.login`, `name`, `default_branch` make the record,
   and a `private` that is not true raises `ForgeSetupError` after the record is kept, so step 7 deletes it.
6. `fetch_seed`: D3's fetch and checkout; `seed_sha` (`git rev-parse HEAD`), `seed_tree_sha` (`HEAD^{tree}`); a path
   under `.github/workflows/` in `git ls-tree -r --name-only HEAD` raises `ForgeSetupError`. Then the yield.
7. In the `finally` around steps 2 to 6 and the yield: `delete_ephemeral(wrapper=..., created=<step 5's record, else
   None>, run_id=run_id)`, then, in its own `finally`, `remove_tree(path=workspace)`, which clears the read-only
   attribute git gives its object files on Windows before retrying a refused removal. A failure of either is raised,
   so the session ends in an error.

**The teardown guard.** `delete_ephemeral(*, wrapper, created: Optional[CreatedRepository], run_id: str) -> None`:

- `created` is `None` (step 5 never succeeded): returns, nothing sent (AC-2.3);
- `(created.owner, created.name)` is not `("bestehorn-sff-test", ephemeral_name(run_id=run_id))`: raises
  `ForgeTeardownRefusedError` naming the refused `owner/name` and this run's, nothing sent (AC-2.2);
- else `call repos/delete --path owner=<owner> --path repo=<name>`; a non-zero exit raises `ForgeCommandError`
  naming the target (AC-2.1, AC-1.4).

**The sweep.** `RepositoryRecord.of(item=<item>)` reads `owner.login`, `name` and `created_at`
(`%Y-%m-%dT%H:%M:%SZ`, UTC); an item without them raises `ForgeCommandError`. `is_leftover(*, record, now) -> bool`:
the owner is `TEST_ORGANIZATION`, the name starts with `EPHEMERAL_REPOSITORY_PREFIX`, and `now - record.created_at`
exceeds `LEFTOVER_AGE` (`timedelta(days=1)`). `select_leftovers(*, records, now)` keeps exactly those.
`sweep_leftovers(*, wrapper, now)` runs `call repos/list-for-org --path org=bestehorn-sff-test` (`call` reads every
page of this `Paging.LINK` record), a non-zero exit raising `ForgeCommandError`, then `delete_leftover` for each
selected record. `delete_leftover(*, wrapper, record, now)` raises `ForgeSweepRefusedError` naming the record, nothing
sent, when `is_leftover` is false; else sends `call repos/delete` for it, and takes exit 1 with `HTTP 404` on
standard error as already deleted (a concurrent run's sweep); any other failure raises `ForgeCommandError`. Each
deletion is logged by full name (AC-3.1, AC-3.2).

### D10 — Files and module layout

| File | Change |
|---|---|
| `src/payload/scripts/github_wrapper.py` | D2: `TEST_MARKER_OPTION`, `EPHEMERAL_REPOSITORY_PREFIX`, `_test_marker_set`, `_refuse_unless_ephemeral`, its call in `main`; the docstrings |
| `src/payload/test/test_github_wrapper_marker.py` | new: W |
| `test/forge/pytest.ini` | new: D1 |
| `test/forge/conftest.py` | new: loads `ephemeral.py` by path once per process (`sys.modules` holds it, as P's loader holds the fake host); the session fixture `ephemeral_repository` (D9) |
| `test/forge/ephemeral.py` | new: the constants D3 to D9 name (except `TEST_MARKER_OPTION` and `EPHEMERAL_REPOSITORY_PREFIX`, which it reads from `product_wrapper()`, as it reads `_one_token` and `PLACEHOLDER`), the commit identity and a subprocess timeout; `ForgeSuiteError` (`details=None`) and its subclasses `ForgeSetupError`, `ForgeCommandError`, `ForgeTeardownRefusedError`, `ForgeSweepRefusedError`; the dataclasses `Invocation`, `RepositoryRecord`, `CreatedRepository`, `EphemeralRepository`; `WrapperRunner` (abstract `run(*, arguments) -> Invocation`) and `SubprocessWrapperRunner`; `GitRunner` (abstract `run(*, arguments, authenticated=False) -> Invocation`) and `SubprocessGitRunner`; `product_wrapper()`; the functions of D1, D3, D4, D8 and D9 |
| `test/forge/write_credential.py` | new: the CI step's command (D8) |
| `test/forge/forge_fixture.py`, `forge_subcommands.py`, `forge_repos_git.py`, `forge_ci_security.py`, `forge_collaboration.py` | new: D6, one module docstring per slice |
| `test/test_forge_support.py`, `test/test_forge_suite_layout.py` | new: S, L |
| `.github/workflows/ci.yml` | D5 |
| `credentials/README.md` | new: D7 |
| `docs/forLLMConsumption.md` | the `Testing` section names the forge suite (`test/forge/`), its local command, the test credential file and its setup note `credentials/README.md`, and the forge job, under its cap |
| `docs/ProjectPlan.md` | the debt line "the ephemeral-repository forge tests need their dedicated create/delete token" removed |

- `SubprocessWrapperRunner(*, directory)` is the one place the suite starts the product wrapper:
  `subprocess.run([sys.executable, "-X", TEST_MARKER_OPTION, str(PRODUCT_WRAPPER), *arguments], cwd=directory,
  stdin=DEVNULL, capture_output=True, text=True, encoding="utf-8", timeout=..., check=False)`, no `env` keyword.
  `SubprocessGitRunner(*, clone)` runs `git`, D3's helper options when `authenticated`, the identity options, `-C
  <clone>` and the arguments, the same way. Both pass a list argv, never a shell.
- `product_wrapper()` loads `src/payload/scripts/github_wrapper.py` by path on first use, never at import, so the
  default collection's import of `conftest.py` changes no `sys.path`.
- Every function takes named parameters, JSON fields are read through constants, and the suite logs through
  `logging` (`coding-standards.md`).

**Not edited:** `pyproject.toml`, `github_api/` (every record the suite sends exists), `github_wrapper_fixtures.py`,
every toolchain file (`config/toolchain.json` and what it lists).

## Testing Strategy

- **The guard, in the default collection.** W runs `main(argv=...)` in-process, as C does (`load_wrapper`,
  `github_wrapper_fixtures.enter_project`, `FakeGitHub`, on which an unrouted request fails the test), with
  `monkeypatch.setitem(sys._xoptions, TEST_MARKER_OPTION, True)` or without it; one example runs the entry script as a
  subprocess with `-X sff_test_marker` and a non-ephemeral origin, refused before any request.
- **The suite's logic, in the default collection.** S loads `test/forge/ephemeral.py` by path. Its runners are test
  doubles: `RecordingWrapperRunner(WrapperRunner)` records each argv and answers from a script, and
  `ScriptedGitRunner(GitRunner)` does the same for git; S's own checkouts live in `tmp_path`, and only local git runs
  (`git init`, `git worktree add`, `git credential fill`). One Hypothesis property, where the criteria quantify over
  repositories (AC-3.1, AC-3.2); everything else is an example.
- **Separation and wiring, in the default collection.** L runs `python -m pytest --collect-only -q` as a subprocess
  on `test/forge` (no fixture is set up), reads the forge modules with `ast`, and reads `ci.yml`, the note and the
  docs as text.
- **The forge suite** (F) is the end-to-end check: the product wrapper driven through its command line against
  github.com, by the forge job on every pull request, push to `main` and dispatch; locally D1's command. Its verdict
  on the PR's head is read through the wrapper's `get-pr-checks` and `get-run`.
- **Runner.** W, S and L: `python scripts/run_tests.py <these paths>`; in CI, `verify` leg `tests`.

## Correctness Properties

- **AC-1.1** — Integration, F:fixture `test_the_run_owns_a_private_seeded_repository` (D6). Example, S
  `test_provisioning_runs_in_order`: one provision records, in order, the listing, exactly one D9 step 5 creation,
  the fetch and the checkout, every wrapper invocation in the one clone directory. Example, S
  `test_a_distributed_run_is_refused`: `refuse_distributed_run(worker_id="gw0")` raises `ForgeSetupError` naming
  `--workers 1`; `worker_id="master"` returns. Structural, L `test_the_session_fixture_wraps_one_provision`: by `ast`
  of `test/forge/conftest.py`, `ephemeral_repository` is decorated `pytest.fixture(scope="session")`, calls
  `refuse_distributed_run` with its own `worker_id` parameter (`worker_id=worker_id`) before `provision`, and its one
  `yield` lies inside the `with provision(...)` block.
- **AC-1.2** — Example, S `test_a_run_id_is_unique_and_names_a_repository`: ids from repeated calls are pairwise
  distinct and of D4's form; `GITHUB_REPOSITORY_PATTERN` reads the origin URL of `ephemeral_name` back as
  `("bestehorn-sff-test", ephemeral_name(...))`.
- **AC-1.3** — Integration, F:fixture `test_the_run_owns_a_private_seeded_repository` and F:repos_git
  `test_the_git_records_read_the_seed_commit` (D6). Example, S `test_provisioning_runs_in_order`: a scripted tree
  naming `.github/workflows/ci.yml` raises `ForgeSetupError` before the yield, the deletion is still sent, and the
  workspace no longer exists.
- **AC-1.4** — Parametrized example, S `test_provisioning_runs_in_order`: whether the body returns or raises, after
  the context exactly one `repos/delete` of this run's repository is recorded and the workspace no longer exists; a
  deletion answering exit 1 raises `ForgeCommandError` and the workspace is still removed. Structural, L
  `test_the_session_fixture_wraps_one_provision` (AC-1.1).
- **AC-2.1** — Example, S `test_the_teardown_deletes_only_this_runs_repository`: a record of this run's name records
  one `call repos/delete --path owner=bestehorn-sff-test --path repo=sff-test-<run id>`.
- **AC-2.2** — Parametrized example, S `test_the_teardown_refuses_any_other_target`: another owner, a name without
  the prefix, another run's id: `ForgeTeardownRefusedError` whose message names the refused `owner/name`, nothing
  recorded.
- **AC-2.3** — Example, S `test_no_creation_no_deletion`: `created=None`, and a provision whose creation answers exit
  1: no `repos/delete` recorded, and after the provision the workspace no longer exists.
- **AC-3.1, AC-3.2** — Property, S `test_the_sweep_deletes_exactly_the_old_ephemeral_repositories`: over listings of
  records (owner the test organization or another, a name with the prefix or not, `created_at` on either side of the
  one-day line), `sweep_leftovers` records one `repos/delete` per record that has all three properties and none for
  any other (the expected set computed from the strategy's drawn owner, prefix and age side, never through
  `is_leftover` or `select_leftovers`). Example, S `test_the_sweep_boundaries_and_refusals`: exactly a day old is
  kept, just over is deleted; an `HTTP 404` answer counts as deleted; `delete_leftover` of a non-leftover raises
  `ForgeSweepRefusedError`, nothing recorded. Integration, F:fixture `test_no_leftover_survives_the_sweep`.
- **AC-4.1** — Parametrized example, W `test_the_marker_refuses_an_origin_without_the_prefix`, over `call repos/get`,
  `get-issue 1`, `list-runs`, `enqueue-pr 1` and `wait-landed 1` with origin `Bestehorn/SoftwareFactoryFramework`:
  exit 2, no request recorded, `steward_delegate` not called, one log record naming the test marker and
  `Bestehorn/SoftwareFactoryFramework` and not the configured token; with origin
  `https://github.com:<sentinel>@example.com/repo`, the same refusal and no log record holds the sentinel. Example, W
  `test_the_interpreter_option_reaches_the_entry_script`: the subprocess exits 2 and its standard error holds that
  message.
- **AC-4.2** — Example, W `test_the_marker_lets_an_ephemeral_origin_through`: with origin
  `bestehorn-sff-test/sff-test-x`, `call repos/get` sends the same requests, prints the same output and exits as the
  same argv without the marker. Integration: every F test runs with the marker set.
- **AC-4.3** — Example, S `test_every_wrapper_invocation_carries_the_marker`: `SubprocessWrapperRunner`'s argv starts
  `sys.executable, "-X", TEST_MARKER_OPTION, <PRODUCT_WRAPPER>` and `subprocess.run` receives no `env`; L
  `test_the_forge_tests_reach_only_the_ephemeral_repository`, by `ast` of the `.py` files of `test/forge/`: only
  `ephemeral.py` imports `subprocess` or names `product_wrapper`, `PRODUCT_WRAPPER` is named, outside its definition,
  only in `SubprocessWrapperRunner` and `product_wrapper`, and no file reads an attribute `main`. W's
  subprocess example runs in a directory other than the repository. W `test_without_the_marker_every_origin_is_served`:
  without the option the same origin is served (exit 0, the request recorded).
- **AC-5.1** — Structural, L `test_the_forge_job_runs_beside_verify`: `ci.yml` has a `forge` job with no `needs:`,
  `verify` names no `forge`, `on:` holds exactly `push` (`branches: [main]`), `pull_request` and `workflow_dispatch`,
  and the forge job's last step is `python
  scripts/run_tests.py --workers 1 test/forge`. Integration: the PR's run lists the job.
- **AC-5.2** — Structural, L `test_the_secret_reaches_one_step`: `secrets.SFF_TEST_TOKEN` occurs once, in the `env:`
  of the step running `python test/forge/write_credential.py`; the forge checkout has `persist-credentials: false`;
  one check command (AC-5.1's). Structural, L `test_nothing_keeps_a_forge_test_from_running`: `pytest.ini` holds no
  fail-fast option (AC-7.3).
- **AC-5.3** — Example, S `test_a_missing_secret_fails_the_credential_step`: `write_test_credential(token="", ...)`
  raises with "the secret SFF_TEST_TOKEN is unavailable to this run" and writes nothing; a token is written followed
  by a line end; `write_credential.main` returns 1 on the refusal.
- **AC-5.4** — Structural, L `test_the_report_judges_the_forge_job`: `report` has `needs: [verify, forge]`,
  `if: always()`, runs `--summary-from reports`, and sets a failing status unless `needs.forge.result` is `success`.
- **AC-6.1** — Example, S `test_the_test_credential_is_found_in_the_checkout_or_its_main_tree`: a `git init` checkout
  with the file finds its own; a `git worktree add` worktree of it without the file finds the main tree's; the worktree
  given its own file, holding a token other than the main tree's, finds its own; neither raises naming both paths.
- **AC-6.2** — Parametrized example, S `test_a_bad_test_credential_fails_before_any_request`: missing, empty, the
  placeholder, two tokens on two lines: `provision` raises `ForgeSetupError` naming the path and not the file's text,
  no wrapper or git invocation recorded.
- **AC-6.3** — Example, S `test_the_token_is_written_only_to_the_clone`: after a scripted provision, the files of the
  test's tree holding the token are the test credential file and the clone's `credentials/github-pat.txt`, no
  recorded argv holds it, `.git/info/exclude` names `credentials/`, no record `caplog` captured at `DEBUG` during the
  provision holds it, nor does the `repr` of the yielded `EphemeralRepository`. Example, S
  `test_the_credential_helper_answers_git_with_the_clone_token`: `git credential fill` with D3's options, given
  `protocol=https` and `host=github.com`, answers
  `username=x-access-token` and the clone file's token, the helper string holds no token, and a path holding `'`
  raises. Structural, L `test_the_secret_reaches_one_step`.
- **AC-7.1** — Example, L `test_the_default_configuration_collects_no_forge_test`: `--collect-only` on `test/forge`
  with `-c pyproject.toml` exits 5, "no tests collected", with no import error.
- **AC-7.2** — Example, L `test_the_forge_path_collects_every_forge_test`: `--collect-only -q test/forge` lists
  exactly the `test_` functions `ast` finds in `test/forge/forge_*.py`.
- **AC-7.3** — Structural, L `test_nothing_keeps_a_forge_test_from_running`: in no `.py` file of `test/forge/`, by
  `ast`, a `pytest.` attribute `skip`, `skipif`, `xfail`, `importorskip` or `exit`, one of these imported from
  `pytest`, or `SkipTest`; `conftest.py` defines no `pytest_` function and no `collect_ignore`; `pytest.ini`, read with
  `configparser`, holds exactly the `[pytest]` keys `python_files` = `forge_*.py`, `addopts` = `-p no:cacheprovider`,
  `log_cli` = `true` and `log_cli_level` = `INFO`.
- **AC-8.1** — Structural, L `test_the_forge_tests_reach_only_the_ephemeral_repository`; every F test asserts each
  invocation's exit code and its printed JSON (D6).
- **AC-8.2** — Integration, F:subcommands `test_an_issue_round_trip`, `test_a_pull_request_round_trip` (D6).
- **AC-8.3** — Integration, F:repos_git `test_the_repository_record_names_the_seed_branch`,
  `test_the_git_records_read_the_seed_commit` (D6).
- **AC-8.4** — Integration, F:ci_security's four tests (D6); its docstring names `checks` with its reason.
- **AC-8.5** — Integration, F:collaboration's two tests (D6).
- **AC-8.6** — Structural, L `test_the_forge_tests_reach_only_the_ephemeral_repository`: the forge modules give no
  `--path owner=` or `--path repo=`, import no `github_wrapper_fixtures` and patch no `urllib`; repository creation and
  deletion occur only in `ephemeral.py`.
- **AC-9.1** — Example, L `test_the_setup_note_names_the_credential`: `credentials/README.md` names the file,
  "fine-grained", `bestehorn-sff-test`, "All repositories", each permission of D6's table, `SFF_TEST_TOKEN`, and that
  only a machine running the suite locally needs the file.
- **AC-9.2** — Example, L `test_the_map_names_the_forge_suite`: `docs/forLLMConsumption.md` names `test/forge`, the
  local command, the test credential file and the forge job; B `test_llm_map_within_cap`.
- **AC-9.3** — Example, L `test_the_debt_line_is_gone`: `docs/ProjectPlan.md` no longer holds the debt line.
- **UB-1** — W, S and L run in `verify` with no network and no test credential file (W on `FakeGitHub` and a refusal,
  S on doubles and local git in `tmp_path`, L on `--collect-only`); the fake-host suites are unedited.
- **UB-2** — Example, S `test_the_token_is_written_only_to_the_clone`: a sentinel `credentials/github-pat.txt` in the
  test's checkout keeps its content, and the clone's `credentials/github-pat.txt` holds the test token, not the
  sentinel's text.
- **UB-3** — C, P, K and V pass unedited (V `test_the_wrapper_imports_only_the_standard_library` included); W
  `test_without_the_marker_every_origin_is_served`.
- **UB-4** — I passes; the PR diff names no file `config/toolchain.json` lists.

## Security Considerations

- **The test token** lives in the git-ignored test credential file, the clone's credential file (D8) and, in CI, the
  one step's `env:` (D5); git receives it through the helper's pipe (D3). GitHub masks secrets in logs; the suite
  does not rely on it.
- **Blast radius.** The token's resource owner is the test organization only; the teardown and the sweep delete only
  what D9's guards select; the wrapper refuses any non-ephemeral `origin` under the marker (D2). Git Credential
  Manager is never asked (D3), the workflow's `GITHUB_TOKEN` stays out of the checkout (D5), and the checkout's
  `credentials/github-pat.txt` is never touched (UB-2).
- **CI trust.** Fork and Dependabot pull requests get no secret ("secrets are not passed to the runner when a
  workflow is triggered from a forked repository"; "Secrets are not available to workflows triggered by Dependabot
  events", docs.github.com "Using secrets in GitHub Actions"), so their forge job fails (AC-5.3). A same-repository
  pull request or a `workflow_dispatch` on any branch runs that branch's own suite and `ci.yml` with the secret, so
  its bound is the token's reach, every repository of `bestehorn-sff-test`, not D9's guards.
- **External input.** Repository names from the listing reach the wrapper only as `--path` values in a list argv (no
  shell), which `registry.expand` encodes.
- **Dependencies.** None added: the wrapper uses `sys`; the suite uses pytest, pytest-xdist and Hypothesis, already
  in the `dev` extra.

## Operability

- **Logs.** pytest's `-ra` summary lists every non-passing forge test; the suite logs each repository it creates and
  deletes by full name, printed live into the job log (`log_cli`, D1); a wrapper refusal is its `ERROR:` line. A
  permission the token lacks fails the test that needs it with GitHub's `403` "Resource not accessible by personal
  access token".
- **Leftovers.** An interrupted run (a cancelled or superseded CI run, a local Ctrl-C) does not finish its teardown.
  Its repository is deleted by the first run more than a day after its creation; an interrupted local run also
  leaves its workspace, the clone and its credential file, in the temporary directory.
- **Rollback.** Revert the change: the job, the suite with its sweep, and the guard go together. A leftover from
  before the revert stays in `bestehorn-sff-test` until the suite returns; the secret and the token stay only while
  the suite is to return; otherwise the operator deletes the secret `SFF_TEST_TOKEN` and revokes the token.

## Acceptance Criteria Mapping

In `src/payload/test/`: W = `test_github_wrapper_marker.py` (new), C = `test_github_wrapper_compat.py`. In `test/`:
S = `test_forge_support.py` (new), L = `test_forge_suite_layout.py` (new), P = `test_github_wrapper_fork_parity.py`,
K = `test_github_wrapper_contract.py`, V = `test_github_wrapper_coverage.py`, I = `test_toolchain_integrity.py`,
B = `test_instruction_corpus_budget.py`. In `test/forge/`: F:<module> = `forge_<module>.py` (new).

| Criterion | Component | Tests |
|---|---|---|
| AC-1.1 | D9 `provision`, `create_ephemeral`; D1 `refuse_distributed_run` | F:fixture `test_the_run_owns_a_private_seeded_repository`; S `test_provisioning_runs_in_order`, `test_a_distributed_run_is_refused`; L `test_the_session_fixture_wraps_one_provision` |
| AC-1.2 | D4 `new_run_id`, `ephemeral_name` | S `test_a_run_id_is_unique_and_names_a_repository` |
| AC-1.3 | D3 clone; D9 `fetch_seed` | F:fixture `test_the_run_owns_a_private_seeded_repository`; F:repos_git `test_the_git_records_read_the_seed_commit`; S `test_provisioning_runs_in_order` |
| AC-1.4 | D9 step 7, `remove_tree` | S `test_provisioning_runs_in_order`; L `test_the_session_fixture_wraps_one_provision` |
| AC-2.1 | D9 `delete_ephemeral` | S `test_the_teardown_deletes_only_this_runs_repository` |
| AC-2.2 | D9 `delete_ephemeral` | S `test_the_teardown_refuses_any_other_target` |
| AC-2.3 | D9 `delete_ephemeral`, step 5 | S `test_no_creation_no_deletion` |
| AC-3.1 | D9 `sweep_leftovers`, `select_leftovers`, `is_leftover` | S `test_the_sweep_deletes_exactly_the_old_ephemeral_repositories`, `test_the_sweep_boundaries_and_refusals`; F:fixture `test_no_leftover_survives_the_sweep` |
| AC-3.2 | D9 `is_leftover`, `delete_leftover` | S `test_the_sweep_deletes_exactly_the_old_ephemeral_repositories`, `test_the_sweep_boundaries_and_refusals` |
| AC-4.1 | D2 `_refuse_unless_ephemeral`, `main` | W `test_the_marker_refuses_an_origin_without_the_prefix`, `test_the_interpreter_option_reaches_the_entry_script` |
| AC-4.2 | D2 | W `test_the_marker_lets_an_ephemeral_origin_through`; every F test |
| AC-4.3 | D2 `-X`; D10 `SubprocessWrapperRunner` | S `test_every_wrapper_invocation_carries_the_marker`; L `test_the_forge_tests_reach_only_the_ephemeral_repository`; W `test_the_interpreter_option_reaches_the_entry_script`, `test_without_the_marker_every_origin_is_served` |
| AC-5.1 | D5 `forge` | L `test_the_forge_job_runs_beside_verify` |
| AC-5.2 | D5; D8 `write_test_credential`; D1 `pytest.ini` | L `test_the_secret_reaches_one_step`, `test_nothing_keeps_a_forge_test_from_running` |
| AC-5.3 | D5; D8 `write_test_credential`, `write_credential.py` | S `test_a_missing_secret_fails_the_credential_step` |
| AC-5.4 | D5 `report` | L `test_the_report_judges_the_forge_job` |
| AC-6.1 | D8 `find_test_credential` | S `test_the_test_credential_is_found_in_the_checkout_or_its_main_tree` |
| AC-6.2 | D8 `read_test_token`; D9 step 2 | S `test_a_bad_test_credential_fails_before_any_request` |
| AC-6.3 | D3; D5; D8 | S `test_the_token_is_written_only_to_the_clone`, `test_the_credential_helper_answers_git_with_the_clone_token`; L `test_the_secret_reaches_one_step` |
| AC-7.1 | D1 | L `test_the_default_configuration_collects_no_forge_test` |
| AC-7.2 | D1 `pytest.ini` | L `test_the_forge_path_collects_every_forge_test` |
| AC-7.3 | D1 | L `test_nothing_keeps_a_forge_test_from_running` |
| AC-8.1 | D6; D10 `SubprocessWrapperRunner` | L `test_the_forge_tests_reach_only_the_ephemeral_repository`; every F test |
| AC-8.2 | D6 #17 | F:subcommands `test_an_issue_round_trip`, `test_a_pull_request_round_trip` |
| AC-8.3 | D6 #27 | F:repos_git `test_the_repository_record_names_the_seed_branch`, `test_the_git_records_read_the_seed_commit` |
| AC-8.4 | D6 #31 | F:ci_security `test_no_workflow_has_run`, `test_code_scanning_answers_as_documented`, `test_secret_scanning_answers_as_documented`, `test_dependabot_lists_no_secret`; the module docstring (`checks`) <!-- pragma: allowlist secret --> |
| AC-8.5 | D6 #32 | F:collaboration `test_issue_and_reaction_records`, `test_pulls_search_activity_and_gists_records` |
| AC-8.6 | D6 | L `test_the_forge_tests_reach_only_the_ephemeral_repository` |
| AC-9.1 | D7 | L `test_the_setup_note_names_the_credential` |
| AC-9.2 | D10 docs | L `test_the_map_names_the_forge_suite`; B `test_llm_map_within_cap` |
| AC-9.3 | D10 docs | L `test_the_debt_line_is_gone` |
| UB-1 | D1; W, S, L doubles | W, S, L in `verify`; the fake-host suites unedited |
| UB-2 | D8 | S `test_the_token_is_written_only_to_the_clone` |
| UB-3 | D2 | C, P, K, V unedited; W `test_without_the_marker_every_origin_is_served` |
| UB-4 | none | I; the PR diff |

## Residuals

- The `requirements.md` Residuals stand; D6's Dependabot secrets read was asked for (issue #10 comment 6829880820).
- Fork and Dependabot pull requests fail the forge job (AC-5.3); no protected environment guards `SFF_TEST_TOKEN`.
- `report` keeps `if: always()`, not GitHub's recommended `if: ${{ !cancelled() }}` (docs.github.com "Expressions").
- The workflow's action pins declare the deprecated Node 20 runtime (GitHub changelog 2025-09-19).
- Without the marker `_detect_repo` accepts an owner group holding `@`, and the request path carries it (UB-3).
- A `403` names no permission: the wrapper prints no `X-Accepted-GitHub-Permissions` header.
- The token's expiry and rotation are named nowhere; an expired token fails every forge job.
- Nothing in this change removes the workspace an interrupted local run leaves in the temporary directory; in a
  session, whose temporary directory is the scoped `tmp/os-temp`, `reap_agent_temp.py --scoped-temp` empties it.
- `project-specific.md` and the map's "Two halves" call `.github/workflows/` promotion-only (D5: `ci.yml` is not).
