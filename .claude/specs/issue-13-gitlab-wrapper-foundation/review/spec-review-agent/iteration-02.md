# Design review, iteration 02 (delta), lane spec-review-agent (issue #13, tier M)

### C1 — The setup prompts' pointers to the wrapper's notes dangle after D7
Severity: C
Location: design.md § D2 "Install path"; § D7 "Removed", "The usage docstring lists UB-1's whole set"
Defect: `prompts/setup-claude.txt` Part 5.3 sends the reader to "the expanded docstrings in ... `src/payload/scripts/gitlab_wrapper.py` for the exact REST endpoints and the "can't approve your own PR/MR" caveat", and `prompts/setup-kiro.txt` Part 6.2 says of the blocking wait and the delivery verbs "the template docstrings specify them". D7 removes the comment block holding the endpoints and the caveat and does not say the docstring keeps the `pipeline wait` 0/10/11 and delivery 0/4 notes. #17 D8 points the same sentence at its package and keeps the caveat in `commands/pulls.py`.
Proposed-edit: Append to "Install path": "Part 5.3's parenthetical names `src/payload/scripts/gitlab_api/` instead of the entry script for the endpoints (its records); `commands/mr.py`'s docstring carries the own-MR approval caveat of the removed comment block (#17 D8)." In D7: "The usage docstring lists UB-1's whole set and keeps the skeleton's exit-code notes for `pipeline wait` and the delivery verbs."

### C2 — Five remaining differences from #17 are not rows, though the header says every one is
Severity: C
Location: design.md header; § D2; § D4; § Differences from the GitHub sibling #17
Defect: Unrecorded: (1) registry tests sit in `test_gitlab_api_transport.py`, #17 has `test_github_api_registry.py`; (2) `Transport.pages` returns a list and takes `limit`, #17's is a generator; (3) family modules hold no `FAMILY`, #17's hold `FAMILY, OPERATIONS, PENDING`; (4) `commands/*` and `errors.py` are never edited by a family, #17's table allows `commands/<group>.py`, `_common.py` and `errors.py` when a family needs one; (5) `request(..., json=, form=, files=)`, #17 `body=`.
Proposed-edit: Adopt #17's form for (1)–(3), or add one row each with its forge reason; add rows for (4) "a family never edits an existing command module (#15 AC-4) | edited when a family needs a group, helper or error type" and (5) "JSON, form and multipart keywords | one `body` | GitLab bodies are form or multipart as well (AC-2.3, AC-2.4)".

### C3 — `request`'s `json` keyword shadows the `json` module
Severity: C
Location: design.md § D4, `request(...)`
Defect: Inside `request`, the `json.dumps` the same bullet names resolves to the `json=` argument (a `dict`), which has no `dumps`, so `AttributeError` is raised.
Proposed-edit: Rename the keyword `json_body` in the signature and in "`json_body` is sent with `json.dumps`".

### C4 — `discover_families()` is cached and takes no package, yet D8 tests it over a synthetic package
Severity: C
Location: design.md § D2 "Discovery, not a list"; § D8 last bullet; § Correctness Properties AC-1.2
Defect: No stated seam lets a `tmp_path` package reach the argument-less function, and a cache filled by the real coverage test returns the real families to the synthetic test; `hooks.discover_gates`, the cited pattern, takes its directory as a parameter.
Proposed-edit: "`registry.discover_families(*, package=gitlab_api.families)` walks `pkgutil.iter_modules(package.__path__)` in sorted name order, imports each as `package.__name__ + "." + name`, and caches per package."

### C5 — Origin parsing and redirect resolution omit two rules #17 D3 states
Severity: C
Location: design.md § D4 "URLs and origin"; § D4 "Errors (AC-3.5)"
Defect: "the port split off" leaves a bracketed IPv6 host (`[2001:db8::1]`) to a naive split; a `ValueError` urllib raises while resolving a malformed `Location` (`urlsplit`: "Invalid IPv6 URL") is outside the caught `HTTPError`, `OSError`, `HTTPException`, so it ends in a traceback rather than `GitLabAPIError`.
Proposed-edit: "…its `host` lower-cased, the port split after the last `:` outside `[...]` as `http.client.HTTPConnection` does…"; in Errors, add "or a `ValueError` raised while urllib resolves a redirect's `Location`" to the failures that raise `GitLabAPIError` with `status_code` 0.

### C6 — The no-config subprocess assertion uses a POSIX path
Severity: C
Location: design.md § Correctness Properties, UB-1 ("standard error names `config/gitlab.json`")
Defect: `_load_config` formats `CONFIG_FILE` (`Path("config") / "gitlab.json"`), printed `config\gitlab.json` on Windows, so a literal assertion passes on CI's `ubuntu-latest` and fails in a local affected-tests run on the project's platform; #17 UB-1.3 asserts `str(Path(...))`.
Proposed-edit: "standard error contains `str(Path("config") / "gitlab.json")` and no `Traceback`".

### C7 — The shared-file table omits the transport suite
Severity: C
Location: design.md § D2 "What a family's change edits", rows `transport.py`, `registry.py`
Defect: A family's `transport.py` or `registry.py` commit brings its tests into `src/payload/test/test_gitlab_api_transport.py`, a file more than one family can edit, which the table does not name.
Proposed-edit: Append to both rows' "Edited when" cell: "with its tests in `test_gitlab_api_transport.py`, in the same commit".

### D1 — Data flow passes `registry.call` arguments positionally
Severity: D
Location: design.md § Data flow
Proposed-edit: `registry.call(transport=transport, operation_id="plan#retrieve-a-project-issue", values=…)` (`coding-standards.md` item 4).

### D2 — The redirect handler is shown with constructor arguments it does not take
Severity: D
Location: design.md § D4, `Transport(...)`
Proposed-edit: `CredentialStrippingRedirectHandler()` (it compares against `req.full_url`).

### D3 — Elided record id
Severity: D
Location: design.md § D6, row `issue assign`
Proposed-edit: Replace `…#as-a-regular-user-1` with `software-supply-chain-security#as-a-regular-user-1`.

CLEAN
