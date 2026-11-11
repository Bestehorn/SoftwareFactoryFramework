# spec-review-agent — design review, iteration 01 (issue #43, tier M)

Checked against #40's approved `design.md` and `origin/main` 25c91d3. Every #40 name #43 uses is one #40 defines:
`PLACEHOLDER`'s `sigil`/`name` groups, `required_placeholders`, `RestOperation.content_type` after `fixed`,
`send(data=)`, `Transport.request_raw`, `refuse_both_bodies`, `refuse_raw_body`, N's `[:*]` `PATH_PLACEHOLDER`,
`glob_names`, `documented_raw_body` and `RAW_BODY_ROW` (#40 D1, D3 to D5). The criteria it cites (#40 AC-1.4, AC-2.1,
AC-2.2, AC-2.4, AC-3.2) are also #40's. On main: `GROUP_NAME`, `takes_project`, `documented_names`,
`missing_path_parameters`, `CONTENT_TYPE_JSON` and `MAX_PER_PAGE`. The index rows match the design: only the Conan v1
entries and `upload-a-package-file-5` list two endpoints, with the kept one second; the 13 `page`/`per_page` sections
are D6's paged list, none of them a prefix record; `:module-name` is the only hyphenated name; the three
`<route-prefix>` lines match AC-2.1 in order. Git Bash, run here, passes `/groups/:id/-/packages/npm` unchanged and
rewrites `/packages/npm`, as Operability states.

### B1 — Both Residuals sections are over the 10-line limit, and the design's second bullet is stale
Severity: B
Location: requirements.md § Residuals; design.md § Residuals
Defect: Neither section fits the 10 lines the rule allows. The design's second bullet still says AC-1.4 and AC-4.2
send the Conan, Debian, Maven, npm and Ruby gems uploads multipart and asks the conductor to restate them, but DL-004
has already done that.
Material-because: unmaintainable-by-rule `.claude/rules/proportionality.md` ("recorded in `## Residuals` (≤ 10
lines)").
Proposed-edit: replace the body of requirements.md § Residuals with:

> - More than one key under one Reference (AC-1.2): the project endpoint of each Conan v1 entry and the `/v2` endpoint
>   of NuGet "Upload a package file" stay pending; a record needs `registry.lookup` to hold several records per ID and
>   a call to choose among them (#41 `design.md` Residuals).
> - Registry host (AC-1.3): both keys need the registry's own host in `config/gitlab.json`, a `/jwt/auth` bearer token
>   for a registry scope (https://docs.gitlab.com/api/container_registry/) and a second origin, against UB-2.
> - "Upload module" lists no `file` row and npm "Upload a package file" a multipart `file`; both follow Workhorse's
>   route as raw bodies (AC-4.2), as docs.gitlab.com's examples do; GitLab's own answer is #11's real-instance run.

and the body of design.md § Residuals with:

> - The `requirements.md` Residuals stand; its first two are one findings-ledger row each (D8).
> - Git Bash on Windows rewrites `--route-prefix /packages/npm` into a Windows path, so the npm instance prefix is
>   refused from it (Operability) → one findings-ledger row.
> - `package#upload-a-package` and the `avatar` of `package#change-the-visibility-of-the-container-registry` reach
>   GitLab through Workhorse's catch-all `proxy`; whether GitLab takes their part is #11's real-instance run to judge.
> - The project-edit attributes of `package#change-the-visibility-of-the-container-registry` and the Conan tokens that
>   `package#create-an-authentication-token` and `…-1` print are callable ungated (Security Considerations) → one
>   findings-ledger row each.

### C1 — AC-4.2's third bullet is traced to no test
Severity: C
Location: design.md § Correctness Properties AC-4.2
Defect: The entry names only F's two upload tests. Neither tests `--input` given beside `-f`/`-F`, or `--input` given
to a multipart record. Both refusals are #40's: K `test_a_raw_body_the_call_cannot_send_is_refused` holds them, and
F's `RAW_BODIES` fixes which records of this change take `--input`.
Proposed-edit: append to the AC-4.2 entry: "- The third bullet: #40's K `test_a_raw_body_the_call_cannot_send_is_refused`
holds both refusals unedited; F's `RAW_BODIES` fixes which records of this change take `--input`."

### C2 — The headers do not say what the branch rebases onto
Severity: C
Location: requirements.md header; design.md header
Defect: The headers say the branch "rebases onto #40", while DL-001 says "after #40 lands". #40 is not merged and its
wave-1 code is still in progress, so the text allows stacking on #40's unmerged branch.
Proposed-edit: in both headers, "the branch rebases onto #40 before its implementation waves" becomes "the branch
rebases onto `origin/main` once #40 has merged, before its implementation waves".

### D1 — The design header mislabels #40 D2 and D3
Severity: D
Location: design.md header
Defect: "#40 D1 to D3 (the glob, the optional group, the escaped parenthesis)": #40 D1 holds all three forms, #40 D2 is
`call`'s optional path parameter, and #40 D3 is N's path reading.
Proposed-edit: "#40 D1 (the glob, the optional group, the escaped parenthesis), D2 (`call`'s optional path parameter),
D3 (N's path reading) and D5 (the raw body)".

### D2 — `route` renders the caller's text differently from `call`
Severity: D
Location: design.md § D2 `route` table, second row
Defect: D2 renders the given prefix with `repr`. `commands/call.py`'s module docstring says every name the caller
supplied is rendered with `json.dumps` (`check_parameters`).
Proposed-edit: "the text given (`repr`, as `encode` renders a name)" becomes "the text given (`json.dumps`, as
`check_parameters` renders a caller's name)".

NOT-CLEAN (0 A, 1 B)

Verdict: NOT-READY
