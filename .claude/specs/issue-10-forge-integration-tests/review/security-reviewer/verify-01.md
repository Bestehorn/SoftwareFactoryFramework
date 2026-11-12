# Security review, VERIFY pass 01 (issue #10, `590e4a9..59d5928`, code only)

No A or B finding. These were checked against the code as built: the token's paths (argv, URL, log, pytest report,
`.git/config`, commit, pushed branch, CI log); both deletion paths; the origin guard's position in `main`; the
credential helper after the reset; `write_credential.py`'s file mode; `remove_tree`.

### C1: the CI step writes the test credential file with the process's default mode
Severity: C
Location: test/forge/ephemeral.py § `write_test_credential` (design D8 "CI")
Defect: `write_test_credential` writes `credentials/github-sff-testing-pat.txt` with `Path.write_bytes`, so the file
  is created `0o666` less the umask, while `_write_clone_credential` creates the clone's copy owner-only
  (`touch(mode=CLONE_CREDENTIAL_MODE, exist_ok=False)`). D8 "CI" names no mode. The forge job runs on `ubuntu-latest`,
  where "each GitHub-hosted runner is a new virtual machine" and "The Linux and macOS virtual machines both run using
  passwordless `sudo`" (docs.github.com "GitHub-hosted runners reference"). So the mode keeps the file from no step of
  that job, and no other job shares the machine.
Material-because: none. It is a hardening residual that matters only if the forge job moves to a shared self-hosted
  runner, which `ci.yml` does not use.
Proposed-edit: none in this change (adding a mode is beyond D8). It is listed under Residuals so the conductor can
  route it to the findings ledger.

## Residuals
- C1: an owner-only mode for the CI-written test credential file, if the forge job ever moves to a self-hosted
  runner.

CLEAN
