# Spec review — issue #46, design iteration 01 (SPEC lane)

### C1 — K's new cases can collide with #28's `rows_of` criterion keys
Severity: C
Location: design.md § Testing Strategy "CLI cases"; § Correctness Properties (K)
Defect: #46's criterion ids AC-1.1 to AC-2.3 repeat #28's, and K `rows_of(criterion=...)` selects every `CALL_CASES`
row whose name starts with that id, so a new row named `AC-1.3/…` (the both-bodies refusal) would also run under
`test_a_body_member_holds_the_given_json_value` and fail its one-`PATCH` assertion.
Proposed-edit: append to "CLI cases": "They are constants outside `CALL_CASES`, named `issue-46/<criterion>/…`,
because `rows_of` keys `CALL_CASES` by #28's criterion ids, which #46's repeat."

### C2 — D1 step 4's message omits `--input`, which AC-1.1's oracle requires
Severity: C
Location: design.md § D1 "`cmd_call`'s steps" step 4; § Correctness Properties AC-1.1
Defect: Step 4's message "names the ID and says that its body is given with `-f`/`-F`"; K
`test_a_raw_body_the_call_cannot_send_is_refused` expects a log record naming `issues/update` and `--input`.
Proposed-edit: step 4: "The message names the ID and `--input`, and says that its body is given with `-f`/`-F`."

### C3 — G's restatement is ambiguous and leaves two stale texts
Severity: C
Location: design.md § D4 "The tests that encode the deferral are restated"
Defect: "`RECORDED_IDS` becomes `REPOS_OPERATION_IDS`" reads as a value change or a rename. Under either,
`RECORDED_IDS`'s comment ("every `repos/` ID but the one left pending") and the docstring of
`test_every_record_sends_the_default_version_and_media_type` ("every `repos/` ID but the pending one") go stale; under
the rename that test's body is edited, which contradicts "Every other test of G and M passes unedited".
Proposed-edit: "`RECORDED_IDS` is removed; its uses in `test_no_repos_id_is_pending` and
`test_every_record_sends_the_default_version_and_media_type` read `REPOS_OPERATION_IDS`, and the latter's docstring
drops 'but the pending one'. No assertion of G or M is relaxed; every other test of G and M passes unedited."

### C4 — UB-2.2 misstates where the credential goes today
Severity: C
Location: requirements.md § UB-2.2
Defect: "Apart from AC-2.2's upload, the credential SHALL CONTINUE TO be sent only on requests to the origin of
`https://api.github.com`", yet `Transport.upload` already sends it to `UPLOAD_ORIGIN`
(`_send(..., allowed_origin=UPLOAD_ORIGIN)`; T `test_an_asset_is_uploaded_to_the_upload_url`), and D2 keeps
`Transport.upload` unchanged.
Proposed-edit: "Apart from requests to the origin of `https://uploads.github.com` (AC-2.2's upload, and
`Transport.upload`, unchanged), the credential SHALL CONTINUE TO …"

### C5 — Out of scope and D3 misstate urllib's handling of the other redirects
Severity: C
Location: requirements.md § Out of scope (first bullet); design.md § D3 "Every other redirect is unchanged"
Defect: CPython `HTTPRedirectHandler.redirect_request` follows a `301`/`302`/`303` of a `POST` as a `GET`
(`code in (301, 302, 303) and m == "POST"`) and any of the five codes of a `GET`/`HEAD`, so "a `308`, a redirect of a
`POST` … still end as #28 AC-1.7" is wrong for those; D3's list omits the `303` of `PATCH`/`DELETE` and the
`301`/`302`/`303` of `PUT`, which raise.
Proposed-edit: requirements: "a `307` or `308` of a `POST`, any redirect of a `PUT`, and a `301`, `302`, `303` or
`308` of a `PATCH` or `DELETE` still end as #28 AC-1.7." D3: the same list replaces its second sentence.

### C6 — No decision-log entry for the files #28 D8 marks "never" for a slice
Severity: C
Location: decisions/decision-log.md
Defect: D5 and D6 edit `github_wrapper_fixtures.py` (`NonGetRequest.of`), `test/test_github_wrapper_contract.py` and
the entry script's docstring, three files #28 D8's slice table marks "never"; DL-004 records only the `registry.py`
exception, while #33 recorded its own N edit (#33 DL-005).
Proposed-edit: append DL-006: "Edit, outside #28 D8's slice table: `github_wrapper_fixtures.py` `NonGetRequest.of` (a
body that is not UTF-8 raises in `RecordedRequest.json` inside `assert_outcome`), N `ReferenceSection.host` and
`_plan_call` (the upload's call is unrouted on the API host), the entry script's docstring (AC-5.1)."

### D1 — D3 says urllib calls `redirect_request` "for every `30x`"
Severity: D
Location: design.md § D3 "Where."
Defect: `HTTPRedirectHandler` aliases only `http_error_301`, `303`, `307` (and `308` from 3.11) to `http_error_302`,
which returns without calling `redirect_request` when the answer carries neither `location` nor `uri`.
Proposed-edit: "urllib calls it for a `301`, `302`, `303`, `307` or (3.11+) `308` that carries a `Location`, with
`newurl` already resolved: …"

Verdict: READY
