# Best-practice review — VERIFY pass 01 (delta over 590e4a9..59d5928)

No documentation MCP server covers pytest, git, GitHub or CPython; sources are the official pages below, fetched
2026-11-12.

I found no A or B finding. Every lens item matches its documentation:

- pytest-xdist `worker_id`: "When `xdist` is disabled (running with `-n0` for example), then `worker_id` will return
  `"master"`", and a session fixture "will execute the fixture code more than once" under workers
  (pytest-xdist.readthedocs.io how-to). `scripts/run_tests.py` `build_command` adds no `-n` for `--workers 1`, so the
  fixture sees `master`. The session fixture depends only on the session-scoped `worker_id`, and its body wraps a
  `with` around the `yield`. Both are documented fixture patterns.
- pytest configfile: "`pytest.ini`: will always match and take precedence", searched from the common ancestor of the
  args (docs.pytest.org reference/customize). `test/forge` therefore runs under its own `pytest.ini`, and `log_cli` /
  `log_cli_level` are the documented live-logging options (how-to/logging). The root `--import-mode=importlib` does
  not apply to that run. The by-path load works under either import mode, which DL-005's rejection of `import
  ephemeral` (a second copy) already accounts for.
- By-path loading: `spec_from_file_location`, `module_from_spec`, `sys.modules[name] = module`, then
  `exec_module`, is the docs.python.org importlib "Importing a source file directly" recipe. The entry is popped on
  failure.
- `-X sff_test_marker`: the -X option "allows passing arbitrary values and retrieving them through the
  `sys._xoptions` dictionary" (docs.python.org using/cmdline).
- subprocess: every call passes a list argv with no shell, `stdin=DEVNULL`, `capture_output`, `encoding="utf-8"` and
  a `timeout`. `run` kills the child on `TimeoutExpired`, and `_invoke` / `_git_output` wrap that as
  `SubprocessError`. `HEAD^{tree}` goes through CreateProcess, not cmd.exe, so `^` is literal.
- git credential helper (git-scm.com gitcredentials):
  - "If the helper string begins with "!", it is considered a shell snippet". Git appends one operation argument,
    which the snippet tests as `$1`.
  - Non-`get` operations are ignored, as "it should silently ignore the request" requires. "For a `store` or `erase`
    operation, the helper's output is ignored."
  - An empty `credential.helper` "resets the helper list to empty", and command-line `-c` is read last. So the reset
    followed by `credential.https://github.com.helper` leaves only the snippet. That holds even with a URL-scoped
    global helper.
  - The path is single-quoted and in forward-slash form. A path holding `'` is refused.
- `git checkout -B <branch> --track origin/<branch>`: "-B … if the branch already exists it resets <branch> to the
  start point", and "--track … When creating a new branch, set up "upstream" configuration" (git-scm.com
  git-checkout). On the unborn branch `git init` leaves, it creates the branch.
- The push: `git push origin forge-pull-request` carries no `.github/workflows/` path, so the Workflows permission is
  not needed, as `docs/forge-suite.md` states.
- GitHub REST answers the modules assert (docs.github.com, apiVersion 2022-11-28):
  - Code scanning "List code scanning alerts for a repository": 403 "Response if GitHub Advanced Security is not
    enabled for this repository".
  - Secret scanning: 404 "Repository is public or secret scanning is disabled for the repository".
  - "Create an organization repository": `auto_init` "Pass true to create an initial commit with empty README", and
    `private` "Whether the repository is private".
  - "Delete a repository": 204, or 404 "Resource not found". This matches `delete_leftover`'s treatment of 404 as
    already deleted.
  - "List organization repositories": `type` defaults to `all`.
- GitHub Actions:
  - actions/checkout `persist-credentials`: "Whether to configure the token or SSH key with the local git config",
    default true. Setting it to false keeps `GITHUB_TOKEN` out of the checkout's config.
  - The secret is scoped to one step's `env:`, and the workflow uses `pull_request`, not `pull_request_target`.
  - `needs.<job_id>.result`: "Possible values are `success`, `failure`, `cancelled`, or `skipped`" (contexts). The
    `!= "success"` test therefore fails the report on a cancelled or skipped forge job too.
  - The report step sets no `shell:`, so it runs as `bash -e {0}` (workflow-syntax). `PIPESTATUS[0]` is read
    straight after the pipeline, before the added `echo | tee`, and without `pipefail` the `tee` pipeline cannot end
    the step early.
- `remove_tree`: docs.python.org shutil's rmtree example clears the read-only bit with `os.chmod(path, stat.S_IWRITE)`
  and retries. `remove_tree` does the same over the remaining tree, with whole-call retries, and `os.chmod` on
  Windows honours only that flag.
  - `shutil.rmtree(path=...)`, `Path.rglob(pattern=...)`, `Path.chmod(mode=...)` and `Path.touch(mode=...,
    exist_ok=False)` use the documented parameter names from 3.9 on.
  - `tempfile.mkdtemp` makes the workspace, not `tmp_path_factory`, whose directories pytest keeps.

CLEAN
