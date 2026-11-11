# devops-iac-reviewer — design iteration 01 — issue #41

### C1 — The GitLab.com premise of the Offering arm is unsettled on #11
Severity: C
Location: design.md § D5 "The rule" (the bullet "The rule takes #11's test project …"); § Residuals "The Offering arm"
Defect: The bullet can be read as `docs/reports/self-hosting-proposal-2026-11-07.md` §5 putting #11's project on
GitLab.com. But §5 names only `POST /projects` and the `api` scope, and #11 still has the question open. Its body asks
"Which GitLab instance and token do real-forge tests use, given #10 covers GitHub only?", and its 2026-11-10 comment
says "The real-GitLab integration tests item and the GitLab test-target question stay on this issue." With a
self-managed instance and an administrator token, both arms would call operations unreachable that #11 can in fact
exercise. Nothing in this change filters on `is_unreachable`: N proves every declared record either way. So no
behaviour here is wrong.
Proposed-edit: in D5, replace "on GitLab.com by a token that does not administer the instance (Residuals)" with "on
GitLab.com, by a token that does not administer the instance. The instance is this design's assumption, because #11
keeps the GitLab test-target question open (Residuals)". In Residuals "The Offering arm", append: "If #11 chooses a
self-managed instance, #11 restates both arms."

### C2 — H does not carry P's `deadline=None`
Severity: C
Location: design.md § Testing Strategy "Property test"; § Correctness Properties AC-1.3
Defect: P's two properties in `test/test_gitlab_api_properties.py` carry `@settings(deadline=None)  # the first
example also pays for importing the package`, and P imports at test time (`load_registry`). H puts
`src/payload/scripts` on `sys.path` "as P does", but its sketch names no settings. Its first example can then pay for
importing `gitlab_api.commands.call` against Hypothesis's default deadline, in CI's `tests` leg, which runs with
coverage instrumentation and `--workers auto`.
Proposed-edit: append to the "Property test" bullet: "It carries P's `@settings(deadline=None)` for P's reason: its
first example also imports the package."

### C3 — N's anchor rule must not import `verify.py`
Severity: C
Location: design.md § D5 "Reference half", "The anchor"
Defect: "as `scripts/api_reference/verify.py` `anchors` computes it" can be read as reusing that function. But
`verify.py` imports `yaml` at module level. PyYAML is not declared in `pyproject.toml`'s `dev` extra: in the venv it is
present only as a requirement of `bandit`, `detect-secrets` and `pre_commit` (`pip show PyYAML`). No `test/` module
imports `scripts/api_reference` today. Reusing it would give CI's `tests` leg an undeclared dependency
(`dependencies.md` rule 3). `anchors` also returns a `set[str]` per page, with no mapping from a heading to its section.
Proposed-edit: replace "**The anchor**, as `scripts/api_reference/verify.py` `anchors` computes it (`check_links` uses
it to check that every generated link resolves):" with "**The anchor**, computed in N by the rule that
`scripts/api_reference/verify.py` `anchors` applies (N does not import `verify.py`, which needs PyYAML):".

Verdict: CLEAN
