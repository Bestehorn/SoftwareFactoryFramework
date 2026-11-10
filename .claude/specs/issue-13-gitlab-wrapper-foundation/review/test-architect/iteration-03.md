# Test architect — design review, iteration 03 (delta, issue #13, tier M)

Fix sites: C1, C3, C4, C5 and D1 are applied as proposed. C2 is superseded by `discover_families(*, package=…)`, and
the AC-1.2 test fails on an implementation that ignores `package` or lists families; C1 below restores what the
supersession dropped.

Delta: the five tests moved T→R check `expand`, `encode`, `lookup` and `call` and fail on a wrong encoding or a
missing refusal. AC-3.1 now compares names case-insensitively, so a `CREDENTIAL_HEADERS` spelling that
`remove_header` misses leaves `Private-token` on the hop and the test fails; the `https://<HOST>:443/` case fails on a
`req.host` comparison. The design has one opener factory and one `_send` (multipart, job trace, GraphQL and paging go
through it); there is no separate download path. `st.characters(exclude_categories=…)` exists in the installed
Hypothesis (`hypothesis/strategies/_internal/core.py` `characters`).

No A or B finding.

### C1 — A synthetic families package can be served from an earlier test
Severity: C
Location: design.md § D8 last bullet; § Correctness Properties AC-1.2
Defect: `MonkeyPatch.undo` restores `sys.path` only (`_pytest/monkeypatch.py`), so a second V test importing a
synthetic package of the same name in one worker gets the first test's module from `sys.modules`, and a second
`discover_families` call on one package returns the cached first set; both fail on a correct implementation.
Proposed-edit: after "passed as `package=`)" add "under a package name unique to the test, with one
`discover_families` call per package after its files are written".

### C2 — "Both shipped suites" predates the third shipped test module
Severity: C
Location: design.md § Testing Strategy "Fake host"
Defect: R is a third shipped module, and its AC-1.1 "nothing is recorded" oracle needs the fake host.
Proposed-edit: replace "Both shipped suites also install a `socket.socket.connect` guard as an autouse fixture." with
"T, R and C each install `FakeGitLab` and a `socket.socket.connect` guard as autouse fixtures."

### C3 — The redirect tests must use the default opener
Severity: C
Location: design.md § Testing Strategy "Transport and registry"
Defect: a test passing its own `build_opener(CredentialStrippingRedirectHandler())` passes against a default opener
that lacks the handler, the opener `from_config` builds.
Proposed-edit: after "a recording `sleep` and a fixed `clock`" add "and keeps `opener` at its default".

## Coverage

| Criterion | Test(s) | Status |
|---|---|---|
| AC-1.1 | review D1; R undeclared value, unknown and duplicate id | COVERED |
| AC-1.2 | V discovered alone (C1) | COVERED |
| AC-1.3 | review D2 table | COVERED |
| AC-2.1 | T one header per token type | COVERED |
| AC-2.2 | P one segment; R encoded path, empty and dot refusals | COVERED |
| AC-2.3 | P array and hash pairs; R array of hashes; T JSON body | COVERED |
| AC-2.4 | T multipart | COVERED |
| AC-2.5 | T offset paging | COVERED |
| AC-2.6 | T keyset paging, foreign next URL | COVERED |
| AC-3.1 | T hostile targets per token type, same-origin keep, return hop (C3) | COVERED |
| AC-3.2 | T `Retry-After` | COVERED |
| AC-3.3 | T header-less back-off | COVERED |
| AC-3.4 | T retries spent | COVERED |
| AC-3.5 | T body shapes | COVERED |
| AC-4.1 | T GraphQL POST | COVERED |
| AC-4.2 | T end-cursor paging | COVERED |
| AC-4.3 | T errors at 200; empty and field `errors` | COVERED |
| AC-5.1 | V unlisted rows | COVERED |
| AC-5.2 | V discovered alone | COVERED |
| AC-5.3 | V real index | COVERED |
| AC-5.4 | V socket guard | COVERED |
| UB-1 | C per-form cases and seven named tests; S; D unchanged | COVERED |
| UB-2 | C config and environment tests; P import scan | COVERED |
| UB-3 | verifier `git diff --name-only` | COVERED |

Verdict: TEST-READY — CLEAN (0 A, 0 B); 24 COVERED, 0 GAP.
