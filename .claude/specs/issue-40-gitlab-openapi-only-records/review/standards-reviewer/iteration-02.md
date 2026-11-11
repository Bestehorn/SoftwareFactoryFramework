# Standards review — design iteration 02 (delta) — issue #40

Lane: standards-reviewer. Subject: the fix sites of iteration 01 and the new D5, against `.claude/rules/`, the
conventions of `src/payload/scripts/gitlab_api/` and #41 D8.

Iteration 01: B1 (§ Residuals is ten lines), B2 (D1, D7 rows D1 and D3 name the docstrings of `expand`,
`placeholders`, `expanded_path` and `route_problems`), B3 (`re.compile(pattern=…)`), C1 (D3's sentence) and C2 (the
refusal test is K's in D6, the mapping and Correctness Properties) are closed.

Not findings, on the conductor's question: D5 keeps `read_input`, `refuse_both_bodies`, `refuse_raw_body` and
`request_raw` per forge, which is correct. No module is shared between `gitlab_api` and `github_api`, no import of
`gitlab_api` names `github_api`, and UB-3 keeps `github_api/` untouched. `refuse_both_bodies(raw_body=, args=)` follows
GitLab `call.py`'s `args` convention (`undocumented`, `path_values`). `read_input(text)` follows its argparse types
(`assignment`, `file_member`). The families' import of `gitlab_api.transport` makes no cycle, because
`families/__init__.py` imports nothing, and GitHub's `families/repos.py` on origin/main imports
`CONTENT_TYPE_OCTET_STREAM` the same way. D5 names its yields to #41 D8's never row (`commands/call.py`,
`gitlab_wrapper.py`, N's `documented_raw_body`). `config/toolchain.json` lists none of D7's files.

### B1 — G's standard-input setup passes its arguments positionally
Severity: B
Location: design.md § Correctness Properties AC-3.2, G `test_the_upload_sends_the_bytes_as_its_body`
Defect: The oracle sets `sys.stdin` to `io.TextIOWrapper(io.BytesIO(<the bytes>))`. That is two call sites, and each
passes its argument positionally.
Material-because: unmaintainable-by-rule `.claude/rules/coding-standards.md` (rule 4, "Named parameters at all call
sites", NO EXCEPTIONS). The model D5 names writes this setup with named arguments: origin/main
`src/payload/test/test_github_api_call.py` has `io.TextIOWrapper(buffer=io.BytesIO(initial_bytes=RAW_MARKDOWN), …)`,
and the shipped `github_api/commands/ci.py` has `io.BytesIO(initial_bytes=blob)`.
Proposed-edit: replace "`io.TextIOWrapper(io.BytesIO(<the bytes>))`" with
"`io.TextIOWrapper(buffer=io.BytesIO(initial_bytes=<the bytes>))`, as #46's `test_github_api_call.py` builds it".

NOT-CLEAN (0 A, 1 B)

Verdict: NOT-READY
