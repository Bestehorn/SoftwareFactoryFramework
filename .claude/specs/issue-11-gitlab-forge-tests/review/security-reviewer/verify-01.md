# Security review — VERIFY pass 01 over the implemented diff 83a1415..HEAD (lane: security-reviewer)

No A or B finding, and no C or D. The implemented code matches the reviewed design on every point of this lane:

- The test token's path. `read_test_token` (`test/forge_gitlab/ephemeral.py`) names only the path and `strerror` in
  each refusal, drops the cause (`from None`) and is never logged. `provision` keeps the token in a local and deletes
  it once `prepare_clone` returns. `_write_owner_only` is `Path.touch(mode=0o600, exist_ok=False)`, which is an
  `O_EXCL` create, then the write, for both `config/gitlab.json` and `.git/sff-forge-token`. `_exclude_config` appends
  `config/`. `push_branch` adds and commits only `forge/<branch>.txt`. `EphemeralProject` holds no token. `origin` has
  no userinfo. `_clone_config_values` returns only `hostname` and `project_id`.
- The helper. `CLONE_GIT_HELPER` is #10's `credential_helper_arguments` bound to
  `credential.https://gitlab.com.helper`. It opens with `-c credential.helper=`, its snippet answers `get` only
  (`test "$1" = get || return 0`), and it holds the file path, never the token. The support test resets git's helper
  list, adds a decoy helper ahead of the options, and compares the password as a bool without printing it.
- The product guard. `_is_ephemeral_project` passes only a `str` with a non-empty part before its last `/` and a last
  part starting `sff-test-`. The value reaches the URL through `registry._segment`, which is `quote(safe="")` with
  `.` and `..` refused, so `?`, `#`, `/` and `..` inside an accepted value stay one encoded `:id` segment. The guard
  runs before `Transport.from_config` and before `steward_delegate`. Its message holds the config file name and
  `json.dumps(project_id)` and reads no other key. `test_gitlab_wrapper_marker.py` asserts that no log record and no
  stderr line holds the token.
- Teardown and sweep. `delete_ephemeral` sends only when the created record's `(namespace, path)` equals
  `(bestehorn-sff-test, sff-test-<run id>)`. `is_leftover` requires the test group as namespace, the product prefix
  and an age past `LEFTOVER_AGE`, which excludes the projects shared into the group that the listing also returns.
  `delete_leftover` checks both conditions again and refuses a scheduled project. No forge test module sends an
  explicit `--path id=`.
- CI. The `pull_request` trigger (not `_target`) and `permissions: contents: read` stay in place. The new job has
  `persist-credentials: false`, and `SFF_GITLAB_TEST_TOKEN` appears only in the `env:` of the step that writes the
  credential. The documented token is a service account's PAT, Owner of the test group only.
- Subprocesses. `SubprocessWrapperRunner` and #10's `_invoke` build list argv with `sys.executable`. They use no
  shell, no `env` and `stdin=DEVNULL`, and they set a timeout. A `ForgeCommandError` message joins argv, which holds
  no token.

The open point from design iteration 01, C3 (unauthenticated git commands keep the configured helpers), is a ledger
row (`docs/findings-ledger.md`, "forge-gitlab git helper"). The implementation sends no unauthenticated remote
command: only `fetch` in `fetch_seed` and `push` in `push_branch` reach gitlab.com, and both run with
`authenticated=True`.

CLEAN
Verdict: READY — A 0, B 0, C 0, D 0
