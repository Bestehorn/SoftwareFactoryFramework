# Standards review — issue #46 design, iteration 01

Scope: `requirements.md`, `design.md`, `decisions/decision-log.md` against `.claude/rules/`, `CLAUDE.md` and the
conventions of `src/payload/scripts/github_api/` (worktree at aafecbb; #27's modules read from origin/main f374b3d).

## Findings

### C1 — D4 leaves the second use of `RECORDED_IDS` in G unstated
Severity: C
Location: design.md § D4 "The tests that encode the deferral are restated"
Defect: G (origin/main) uses `RECORDED_IDS` in two tests, `test_only_the_upload_is_pending` and
`test_every_record_sends_the_default_version_and_media_type`, whose docstring reads "every `repos/` ID but the pending
one". "`RECORDED_IDS` becomes `REPOS_OPERATION_IDS`" combined with "Every other test of G and M passes unedited" can
mean either (a) the constant is deleted, so the second test is edited although D4 says it is not, or (b) the constant
stays, so the second test no longer covers the upload and keeps a stale docstring. `tests-must-not-fail.md` lets a
test change only when the spec documents it, so the edit should be named.
Material-because: ambiguous conformance with `tests-must-not-fail.md` (a test edit the spec does not name).
Proposed-edit: replace "`RECORDED_IDS` becomes `REPOS_OPERATION_IDS` and `PENDING` must be empty." with
"`RECORDED_IDS` is deleted. Its two uses, here and in `test_every_record_sends_the_default_version_and_media_type`,
read `REPOS_OPERATION_IDS`, and that test's docstring drops "but the pending one". `PENDING` must be empty." Then
replace "Every other test of G and M passes unedited" with "Apart from that substitution, every other test of G and
M passes unedited".

### C2 — `read_input`'s message duplicates argparse's option prefix
Severity: C
Location: design.md § D1 "`--input FILE`", the `OSError` bullet
Defect: the bullet says the `ArgumentTypeError` names "the option and the path". The module's existing convention
(`commands/call.py` docstring; `_split`, `json_member`) is that argparse names the option ("argument --input: …") and
the `type`'s message names only the caller's text, rendered with `json.dumps`. Following D1 as written gives
"argument --input: --input …".
Material-because: ambiguous conformance with the established pattern of `commands/call.py` (`design-principles.md`
§4, use established patterns).
Proposed-edit: replace "naming the option and the path rendered with `json.dumps`" with "naming the path rendered
with `json.dumps`. argparse names the option, as it does for `assignment` and `json_member`".

### D1 — `RestOperation.origin` holds a root URL
Severity: D
Location: design.md § D2 "`origin: str = API_ROOT`"
Defect: the field holds a root string and is passed as `request_raw(root=operation.origin)`, next to
`_api_url(root=...)` and `REST_ROOTS`. Meanwhile the requirements glossary defines "Origin" as what `transport.origin`
returns (scheme, host, port), and `cmd_call`'s `owner`/`repo` come from the git `origin`. The existing
`_send(allowed_origin=...)` and `UPLOAD_ORIGIN` do the same, so this is a preference.
Material-because: wording only.
Proposed-edit: name the field `root: str = API_ROOT`, and read `root=operation.root` in D2, D4 and Data flow.

### D2 — D7 names no constants for the metavar, the standard-input marker or the two methods
Severity: D
Location: design.md § D7, the `commands/call.py` and `transport.py` rows
Defect: `commands/call.py` names every option string (`METAVAR_VALUE`, `METAVAR_TEXT`, `ACTION_APPEND`), and
`transport.py` names its methods (`METHOD_GET`, `METHOD_POST`). The rows list `OPTION_INPUT`, `ARG_RAW_BODY` and
`RESENT_METHODS` but no constant for `FILE`, `-`, `PATCH` or `DELETE`.
Material-because: wording only; an implementer following the module would add them.
Proposed-edit: call.py row: after "`OPTION_INPUT`, `ARG_RAW_BODY`," insert "`METAVAR_FILE`, `STDIN_INPUT` (`-`),".
transport.py row: replace "`RESENT_METHODS`" with "`METHOD_PATCH`, `METHOD_DELETE`, `RESENT_METHODS`".

### D3 — "Order" carries a commit identifier
Severity: D
Location: design.md § Overview "Order."
Defect: "(f374b3d, PR #47)". A SHA is not a measurement, and `proportionality.md` "Specs state behaviour" does not
forbid it, but "PR #47" alone identifies the landing.
Material-because: wording only.
Proposed-edit: replace "(f374b3d, PR #47)" with "(PR #47)".

## Conformance confirmed (no finding)

- Product only: every D7 path is in `src/payload/`, `test/` (not toolchain) or `docs/`. None is in
  `config/toolchain.json` `files`. Nothing is promoted. Ledger rows go through `memory_compile.py ledger add`.
- Standard library, Python 3.9: new imports are `sys`, `pathlib`, and `urllib.request.Request` subclassed. Hypothesis
  stays in `test/` and is declared in `pyproject.toml` dev extras. No `argparse.FileType`, no `http_error_308`.
- Named parameters at every call site the design spells out (`request_raw(...)`, `ResentRequest(...)`,
  `origin(url=...)`, `read_input(text=...)`). `pathlib` is used for the file read. Refusals are `ValueError`, logged,
  `EXIT_REFUSED`, as in #28 D4. No new exception class, so no `details=None` is owed.
- No environment variable; no option string contains `token`.
- Breaking change flagged: the `PATCH`/`DELETE` `307` re-send on the compatibility subcommands (DL-002, UB-1.1
  exception, D3 "Every entry point"). No existing test pins a `307`, and no test pins `RestOperation`'s field list.
- The test restatements in G and M are documented as a spec change (D4, DL-005), as `tests-must-not-fail.md` requires.
- The `registry.py` change past #28 D8's slice-exceptions row is recorded and owned (DL-004).
- The D6 usage lines are within 120 columns. The User Prompts sections are present in both documents.

Verdict: CLEAN
