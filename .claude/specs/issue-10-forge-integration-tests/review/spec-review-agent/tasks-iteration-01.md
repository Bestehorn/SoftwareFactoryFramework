# Tasks review, iteration 01 — spec-review-agent

### B1 — S cannot be collected in the red runs of waves 1 and 2
Severity: B
Location: tasks.md § Wave 1, 1.3 (and 2.1, 3.1, 4.2, which extend S)
Defect: 1.3 builds S on "the by-path loader of `test/forge/ephemeral.py`". That is the loader of P
(`test/test_github_wrapper_fork_parity.py` `_load_fixtures`, called at import as `fx = _load_fixtures()`), and it
breaks two red runs. In wave 1, 1.7 has not yet created the file when the red run imports S. In wave 2, S defines
`RecordingWrapperRunner(WrapperRunner)` at module level, and 2.3 has not yet created that base. Both runs report
"ERROR collecting test/test_forge_support.py". The TEST author cannot work around it: `spec-implementer.md` (Scope
boundary) allows a stub "in `src/`" only, and `test/forge/ephemeral.py` is not in `src/`.
Material-because: unmaintainable-by-rule `.claude/specs/_workflow/phases/spec-phase-implement.md`. Its RED step
refuses a red caused by "import, collection, syntax or fixture errors", and `.claude/hooks/red_for_right_reason.py`
`judge` returns 1 for any capture containing "ERROR collecting", whatever W and L assert. As written, waves 1 and 2
cannot pass RED.
Proposed-edit: in 1.3 replace "S, created with the by-path loader of `test/forge/ephemeral.py`:" with "S, created.
It loads `test/forge/ephemeral.py` by path from inside each test body, through a cached helper, never at import and
never in a fixture. Nothing at S's module level names a symbol of `ephemeral.py`. Its doubles (2.1
`RecordingWrapperRunner(WrapperRunner)`, 3.1 `ScriptedGitRunner(GitRunner)`) are built from the loaded module the
same way, and so is 4.2's load of `write_credential.py`. S therefore collects in every wave, and a test whose symbol
does not exist yet fails in its own body:".

### B2 — Wave 5, and 4.3, have no red run that the RED step accepts
Severity: B
Location: tasks.md § Runs; § Wave 5 (its paragraph, 5.1 to 5.4); § 4.3 ("Red: ...")
Defect: This defect has three parts.
1. Wave 5 writes no W, S or L file. By the Runs paragraph, its red run is therefore either 1.4's guards alone,
   which are green, or the forge run. While the operator prerequisite stands, the forge run fails every test at the
   setup of `ephemeral_repository` with `ForgeSetupError`: a fixture error.
2. Wave 5's stated red ("for want of a permission D6 marks 'to grant'") is false for 5.2. Its `repos/get`,
   `git/get-commit` and `git/get-tree` need only Metadata ("in place") and Contents ("granted") in D6's
   permission table, so 5.2 is green as soon as the credential exists.
3. 4.3's red run ("collects no forge test before 4.4") collects nothing at all, so `judge` sees no failure. L's
   structural tests over the forge modules (AC-7.2, AC-7.3, AC-8.1, AC-8.6) never run in wave 5, so they never
   check 5.1 to 5.4 before CI does.
Material-because: unmaintainable-by-rule `.claude/specs/_workflow/phases/spec-phase-implement.md`. Its RED step
says "Wrong-red or green → re-dispatch only the offending tasks", and no TEST author can make 4.3 or 5.2 red, so
the wave loops until escalation.
Proposed-edit:
1. Move 5.1 to 5.4 into Wave 4 as 4.7 to 4.10. Their files are disjoint from those of 4.1 to 4.6, and they need
   only 4.5's fixture. Each keeps "with its module docstring (D10)".
2. Delete the Wave 5 heading and its paragraph, and append "and the real-forge tests of the deferred slices
   (D6)" to the Wave 4 heading.
3. In Runs, replace "The forge modules (4.3, 5.1 to 5.4) run only as `python scripts/run_tests.py --workers 1
   test/forge`, and their green run is F.1." with "The forge modules (4.3, 4.7 to 4.10) are declared on wave 4's
   red and green captures, whose L tests read them. Against github.com they run only as `python
   scripts/run_tests.py --workers 1 test/forge`, which is F.1."
4. In 4.3, delete the sentence that begins "Red:".
5. In F.1, replace "5.1 to 5.4" with "4.7 to 4.10".

### C1 — No task creates `CHECKOUT`
Severity: C
Location: tasks.md § 3.3, 4.5
Defect: D8 names `CHECKOUT`, the working tree that holds the suite, and D10 places D8's constants in `ephemeral.py`.
4.5's fixture passes it to `provision`, but no task's symbol list includes it. 1.7's "the constants they use" does
not cover it, because `find_test_credential` takes `checkout` as a parameter.
Proposed-edit: in 3.3 replace "`EphemeralRepository`, `CLONE_CREDENTIAL_FILE`" with "`EphemeralRepository`,
`CHECKOUT`, `CLONE_CREDENTIAL_FILE`".

### C2 — 4.6 does not say how `write_credential.py` reaches `write_test_credential`
Severity: C
Location: tasks.md § 4.6
Defect: The module has to work two ways. CI runs it as a script, `python test/forge/write_credential.py` (D5). S
loads it by path (4.2), under `--import-mode=importlib` (`pyproject.toml` `addopts`), and in that mode a sibling
`import ephemeral` resolves nothing (design D1 quotes `explanation/pythonpath.html`). 4.6 does not say which
mechanism works in both cases.
Proposed-edit: in 4.6 replace "the CI step's command (D8 "CI")" with "the CI step's command (D8 "CI"): it loads
`ephemeral.py` by path, as `conftest.py` does (D10), and calls `write_test_credential`".

NOT-CLEAN (0 A, 2 B)
