# Design review — devops-iac-reviewer — iteration 01

### B1 — The promotion residual says to carry the new product tests into the toolchain, and routes it past the promotion where it applies
Severity: B
Location: design.md § Residuals (first bullet); requirements.md § Residuals ("A layout of more than one file …"); design.md § Overview ("Nothing is installed or promoted")
Defect: The first promotion of ANY release that contains this change, not only the new wrapper's promotion, puts `scripts/github_api/**`, `test/github_wrapper_fixtures.py`, `test/test_github_api_transport.py` and `test/test_github_wrapper_compat.py` into `files`. The promotion's manifest step (`prompts/update.txt` step 7, `scripts/toolchain_manifest.py` on origin/main) maps every `src/payload/` source through the LAYOUT row `("src/payload/", "")` unless `not_installed` names it. After that, `test/test_toolchain_integrity.py` `test_an_installed_file_equals_its_source_at_the_release` fails on each file that is not copied. A compat test that is copied runs beside the fork, and the fork defines neither `steward_delegate` nor `EXIT_DELIVERY_ELSEWHERE` (neither name appears in `scripts/github_wrapper.py`), both of which the UB-3.2 test asserts. The residual says to carry these files, which is the opposite of what that promotion needs.
Material-because: regression — the first routine promotion after the merge either goes red in CI (the integrity test) or installs tests that run against the wrong wrapper. `not_installed` already handles this case for `src/payload/test/test_wrapper_delivery.py`.
Proposed-edit: in design.md § Residuals, replace the first bullet with: "The first promotion of a release that contains this change, whatever it promotes, adds four entries to `config/toolchain.json` `not_installed` before its manifest step: `src/payload/scripts/github_api/*`, `src/payload/test/github_wrapper_fixtures.py`, `src/payload/test/test_github_api_*.py` and `src/payload/test/test_github_wrapper_compat.py`. Each gets the reason 'the product wrapper rewrite is not promoted (deviation `scripts/github_wrapper.py`)'. The patterns also cover part 2's `test_github_api_<family>.py` modules, so no family edits the manifest. Without these entries, `scripts/toolchain_manifest.py` installs the files beside the fork. This change cannot add the entries itself: `test/test_toolchain_manifest.py` `test_check_on_the_committed_manifest_exits_zero_and_writes_nothing` regenerates the manifest at the pinned release, and that drops any entry naming no release source. The promotion of the new wrapper removes the entries, carries `github_api/` in the setup prompts' copy step, and settles which of the installed and product `github_api` copies a single test process uses, since today it is whichever was imported first. Routed as an item on #12." In requirements.md § Residuals, replace "routed to the promotion of the new wrapper (out of scope, `prompt.md`)" with "routed per `design.md` § Residuals: the first promotion after the merge leaves them out, and the new wrapper's promotion installs them (out of scope, `prompt.md`)".

### C1 — Projects set up from a later release get the entry script without its package
Severity: C
Location: design.md § Testing Strategy ("E2E: not applicable …")
Defect: `prompts/setup-claude.txt` Part 5.3 and `prompts/setup-kiro.txt` copy only `src/payload/scripts/github_wrapper.py`. From the first release tag after the merge, a newly set-up project therefore gets an entry script whose `import github_api` fails, where it used to get the skeleton. "runs in no session or deployed system until its promotion" is true only of this repository.
Proposed-edit: append to the E2E line: "; a project set up from a later release copies the entry script without `github_api/` until the promotion edits the copy step (Residuals)".

### C2 — The new rate-limit wait is silent
Severity: C
Location: design.md § D3 "Failures, in `_send`" (first bullet)
Defect: Where the fork exits 1 at once, the transport now sleeps until `x-ratelimit-reset`, once per retry. D3 does not say that this wait is logged, so a promoted caller would see a long wait it cannot tell apart from a hang.
Proposed-edit: after "and resends, up to `RATE_LIMIT_MAX_RETRIES` times", insert "and logs a WARNING naming the bucket or kind of limit and the seconds before each wait".

NOT-CLEAN (0 A, 1 B)
