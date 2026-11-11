# spec-review-agent — design review, iteration 02, delta (issue #40, tier M)

Scope: the changes since iteration 01, which are AC-3.2 and AC-1.3, the Introduction and Residuals of
`requirements.md`, and in `design.md` D4 "The uploads", the new D5, D6/D7 (renumbered), Correctness Properties AC-1.3
and AC-3.2, Security "The raw body" and "Gates", Residuals, the mapping, and DL-007/DL-008.

How the iteration-01 items stand:
- **A1 is closed.** AC-3.2 sends the four `requestBodyUploader` routes their raw bytes, and D5 builds that body.
  - `--input`, `registry.send`'s `data` and `Transport.request_raw` match the code they build on:
    `transport._send(*, method, url, credential, data=None, content_type=None)`; `_build_request` sets `Content-Type`
    only when `data is not None`; `CONTENT_TYPE_OCTET_STREAM` already exists.
  - `families/*` can import from `transport` without an import cycle, because `discover_families` imports lazily and
    `families/__init__.py` is empty.
  - `documented_raw_body` is right for N:
    - `table_rows` reads `form` as `body`;
    - `Section.attributes` is derived from `rows`;
    - N's `typed_argument` gives a QUERY scalar with `--query` and gives no `--input`, so `body_members` sees no body.
  - The precedent (#57, `github_api/commands/call.py` `read_input`, `refuse_both_bodies`, `refuse_raw_body`) is on
    `origin/main`. It is not yet in this branch's base.
- **C1, C2, D1 and D2 are closed.**
- **Renumbering:** no stale `D5`/`D6`/`D7` reference in `requirements.md` or `design.md` (D2 below is the one in the
  decision log).
- C's `USAGE_CALL_TEXTS` is a substring check, so the `--input` usage line keeps UB-1 with no edit to C.

### B1 — F's `REQUIRED` oracle still expects the raw-body records' `file` row as a required `Param`
Severity: B
Location: design.md § Correctness Properties AC-1.3 (F `test_every_param_is_typed_as_its_row`, the `REQUIRED` bullet)
Defect: `REQUIRED` is "the `yes` rows that name no path parameter". The `file` row (`form`, Required `yes`) of
`openapi-only#upload-package-file`, `openapi-only#upload-terraform-module-package-file` and
`openapi-only#create-or-update-a-terraform-state` is such a row (`rest/openapi-only.md` "Upload package file", "Upload
Terraform Module package file", "Create or update a Terraform state"). Since this revision, those records declare no
`file` `Param`.
- A `REQUIRED` written to this oracle maps each of the three to `{"file"}`.
- The records give no required name, so F fails on the implementation AC-3.2 asks for.
- The `KINDS` bullet just above already excludes "a raw-body record's `file` row". This bullet does not.
Material-because: AC-3.2 says "A raw-body record's `file` row is that body and no `Param`". The oracle contradicts it:
making F pass needs a required `file` `Param`, and N's `documented_raw_body` and AC-3.2 both refuse that `Param`.
Proposed-edit: replace "the `yes` rows that name no path parameter;" with "the `yes` rows that name no path parameter,
a raw-body record's `file` row excepted;".

### C1 — The `--input` beside `-f/-F` refusal does not say where a raw-body record's attributes go
Severity: C
Location: design.md § D5 "`call --input FILE`", `prepare_call` step 1
Defect: On GitLab, `-f`/`-F` give "an attribute of either location" (`commands/call.py` module docstring;
`documented_names` gives `ARG_FIELDS` every `Param`).
- So `-f select=package_file` on a raw-body record is a query value. It is refused only when it is given beside
  `--input`.
- In GitHub's `call`, `-f`/`-F` are body members. There, the message naming `--input`, `-f/--raw-field` and
  `-F/--field` is the whole answer. Here it does not tell the caller what to use instead.
Proposed-edit: step 1's sentence "The message names `--input`, `-f/--raw-field` and `-F/--field`" becomes "The
message names `--input`, `-f/--raw-field` and `-F/--field`, and says a raw-body record's attributes are given with
`--query`."

### D1 — AC-1.3's raw-body clause comes before the rule list it overrides
Severity: D
Location: requirements.md § AC-1.3
Defect: The colon after "a raw-body record's rows read as AC-3.2 reads them" applies "its `location` the row's `In`"
and "`file` `FILE`" to every record. AC-3.2 makes a raw-body record's rows `Location.QUERY` and its `file` row no
`Param`. D4's table settles which rule wins, but the criterion's own order reads the other way.
Proposed-edit: "Each record SHALL declare one `Param` per `query`, `body` or `form` row of its entry that does not name
a path parameter and is not a raw-body record's `file` row (AC-3.2): its `location` the row's `In`, `form` read as
`Location.BODY`, every `Param` of a raw-body record `Location.QUERY` (AC-3.2); its `kind` …" The rest stays as written.

### D2 — DL-006's Evidence names the old D5
Severity: D
Location: decisions/decision-log.md § DL-006 Evidence
Defect: "design.md D2, D3, D5" meant the Tests section: the deploy test module and the two Hypothesis properties.
That section is now D6, and D5 is the raw body.
Proposed-edit: none to DL-006, which is append-only (`agent-state-convention.md` §2 rule 1). The next entry that cites
the tests names D6.

NOT-CLEAN (0 A, 1 B).

Verdict: NOT-READY
