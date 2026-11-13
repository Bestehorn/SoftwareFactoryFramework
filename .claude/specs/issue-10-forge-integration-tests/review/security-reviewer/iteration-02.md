# Security review — design iteration 02, delta (lane: security-reviewer)

## Iteration-01 findings (all C, each applied as proposed)

- C1 resolved. D2's `shown` is `owner.rpartition("@")[2]`. With `GITHUB_REPOSITORY_PATTERN` as written
  (`src/payload/scripts/github_wrapper.py`), a match can reach userinfo only from a `github.com:` inside the authority.
  Then the owner group runs to the authority's first `/`, and the text after its last `@` is the host. That drops every
  userinfo byte under either `@` split rule, the same way `_without_userinfo` does. AC-4.1's W case covers
  `https://github.com:<sentinel>@example.com/repo` and asserts that no log record holds the sentinel. AC-4.1's "and no
  credential" holds.
- C2 resolved. D8 Writing states `0o600` and the Windows caveat. Both quotes match the docs: docs.python.org `os.chmod`
  ("you can only set the file's read-only flag with it") and `tempfile.mkdtemp` ("readable, writable, and searchable
  only by the creating user ID").
- C3 resolved. The CI-trust bullet now bounds a same-repository branch or a `workflow_dispatch` by the token's reach,
  not by D9's guards.
- C4 resolved. D3 first resets with the unscoped empty `credential.helper=` and then registers
  `credential.https://github.com.helper`. git `credential.c` `credential_apply_config` sets
  `config.select_fn = select_all`, so every matching entry is applied in order, and `credential_config_callback` runs
  `string_list_clear(&c->helpers, 0)` on an empty `helper`. `-c` is read after every config file, so the reset also
  clears a file-configured scoped helper. A URL other than `https://github.com` (an `insteadOf` rewrite) gets no helper
  at all (gitcredentials "CREDENTIAL CONTEXTS": "both protocols are the same and both hosts are the same"). S's
  `git credential fill` passes `protocol=https` and `host=github.com`.

## Delta checked for new risk

- Token exposure: no new path.
  - `log_cli` at `INFO` prints only records logged inside the pytest process. The wrapper runs in a separate process,
    and the in-process `_one_token` logs nothing; its refusal names no contents.
  - `scripts/run_tests.py` `REPORT_ARGS` is `-ra --tb=short` with no `--showlocals`, so a traceback never prints
    `provision`'s token local.
  - AC-6.3's `caplog` check at `DEBUG` and the `repr` check of `EphemeralRepository` pin this.
- Deletion reach: unchanged.
  - `swept_at` and the D9 reordering change no selector.
  - `EPHEMERAL_REPOSITORY_PREFIX` is now read from `product_wrapper()`. Its value stays pinned by W AC-4.1/AC-4.2 and
    by S AC-2.1's literal `sff-test-<run id>`.
  - AC-5.1's exact `on:` set keeps `pull_request_target` out of the job that holds the secret.
- AC-6.1's fallback to the main working tree reads only `github-sff-testing-pat.txt`.
- The backlog token reaches no request. The wrapper's `CREDENTIALS_FILE` is the relative path
  `credentials/github-pat.txt`, and the wrapper's working directory is the clone.

### C1 — The rollback keeps a live credential that nothing uses
Severity: C
Location: design.md § Operability (Rollback)
Defect: the delta's sentence "the secret and the token's grants can stay" keeps `SFF_TEST_TOKEN` (Administration
write on every repository of `bestehorn-sff-test`). After a permanent revert nothing needs that secret, but any branch
or dispatch whose `ci.yml` references it can still use it (§ Security Considerations, CI trust). OWASP Secrets
Management Cheat Sheet §2.7.3 "Revocation": "When secrets are no longer required or potentially compromised, you must
securely revoke them to restrict access."
Proposed-edit: replace "the secret and the token's grants can stay." with "the secret and the token stay only while
the suite is to return; otherwise the operator deletes the secret `SFF_TEST_TOKEN` and revokes the token."

## Residuals

None new. The protected environment for `SFF_TEST_TOKEN` and the `@`-in-owner parsing without the marker are already in
design.md § Residuals.

CLEAN
