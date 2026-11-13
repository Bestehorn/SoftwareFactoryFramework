# DevOps / IaC review — issue #10 VERIFY, pass 01 (implemented diff 590e4a9..59d5928)

## Checked, no defect found

- `.github/workflows/ci.yml` `forge` matches D5 as designed: no `needs:` on `verify`, `persist-credentials: false`,
  the secret only in the credential step's `env:`, and one check command. `report` has `needs: [verify, forge]` and
  `if: always()`, and it fails unless `needs.forge.result` is `success`. Run 43295116103 shows this happening: `forge`
  failure, `report` failure, every `verify` leg success (evidence/regress/ci-43295116103-12d8df7.txt).
- Logs: `log_cli` puts "Created this run's repository bestehorn-sff-test/sff-test-20261112195559-…" and "Deleted this
  run's repository …" into the job log as the run happens, and the teardown ran even though 7 tests failed. The sweep
  logs each deletion by full name (`delete_leftover`), and a failed creation or teardown names its target
  (`_failure`). No infrastructure is changed outside version control, and nothing deploys.
- Operator messages: a missing permission shows as GitHub's 403 "Resource not accessible by personal access token"
  with the request URL and `documentation_url`, which matches `docs/forge-suite.md`. An empty secret shows as "the
  secret SFF_TEST_TOKEN is unavailable to this run", logged at ERROR by `write_credential.py` with `basicConfig`,
  and the step exits 1 (AC-5.3).
- Leftovers and rollback: the sweep runs before creation and treats a 404 as already deleted. A cancelled run's
  repository is removed by the first run more than a day later, as the note's opening paragraph says. A revert drops
  the job, the suite and the marker guard together. Nothing outside the forge suite sets `-X sff_test_marker`.
- The end-to-end check is the forge job on every pull request, every push to `main` and every dispatch. It needs no
  human step. Granting the token permissions is a setup step (DL-006), not part of the test.

### D1 — A set but malformed secret is reported as a bad file, and the note covers only the unset case
Severity: D
Location: docs/forge-suite.md § The Actions secret; test/forge/ephemeral.py `write_test_credential`, `read_test_token`
Defect: `write_test_credential` refuses only an empty token. A secret that holds two pasted lines or the placeholder
is therefore written to the runner's `credentials/github-sff-testing-pat.txt`, and `read_test_token` then refuses it
with "Paste only the test organization's token, on one line, into this file". In CI the fix is to replace the
secret, but the note's Actions-secret section names only the unset case.
Proposed-edit: in docs/forge-suite.md § The Actions secret, replace "An unset secret fails the job before the suite
runs;" with "An unset secret fails the job before the suite runs, and a secret that is not one token fails the run as
such a file does, naming the job's copy of the file: replace the secret;".

CLEAN
