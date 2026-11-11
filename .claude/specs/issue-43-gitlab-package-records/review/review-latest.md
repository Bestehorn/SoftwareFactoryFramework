# Review — design iteration 01 (consolidated)

Six lanes. Overall: NOT-CLEAN (1 A, 4 distinct B). READY: devops-iac-reviewer, test-architect. NOT-READY:
best-practice-reviewer (A1, B1), security-reviewer (B1), standards-reviewer (B1, B2), spec-review-agent (B1 = standards
B2).

## A (gating)

- **A1 — npm "Create or update a dist-tag" can never tag the version** (best-practice A1; AC-4.2). GitLab reads the
  whole parsed request body as the version (`npm_endpoints.rb` `version = env['api.request.body']`); the npm CLI sends
  `"1.0.0"` as `application/json`. Edit: a raw-body record with a JSON body through #40's `--input`; AC-4.2's raw-body
  list restated as DL-004 restated it.

## B (gating)

- **B1 — `PUT /projects/:id/` can configure a pull mirror that overwrites the trunk** (security B1). Edit: keep
  `("PUT", "/projects/:id/")` pending as DL-002 keeps the registry-host keys; restate AC-1.3, drop the `avatar` clause
  from AC-4.2 and D5, add a residual handing it to tenant-scale's "Update a project" with the same mirror rows.
- **B2 — NuGet v3 "Upload a package file" (`PUT /projects/:id/packages/nuget`, no trailing slash) misses Workhorse's
  `/packages/nuget/` route** and goes to the catch-all proxy, where GitLab refuses an un-rewritten file part
  (best-practice B1; AC-4.2). Edit: split D5's row; this record moves to the residual named in best-practice C1.
- **B3 — N's edits beyond #41 D8's exceptions are not recorded** (standards B1; `design-principles.md` rule 4). Edit:
  one D4 bullet naming the four edits and why AC-4.3 needs them (lane text).
- **B4 — both Residuals sections exceed ten lines; the design's second bullet is stale** (standards B2 = spec B1;
  `proportionality.md`). Edit: the spec lane's replacement texts (7 and 8 lines), after A1/B1/B2's residual changes.

## C and D (same author pass)

- practice C1: the "#11 will judge" residual restated — the Maven virtual-registry upload is Workhorse-only
  (`require_gitlab_workhorse!`); `avatar` through the proxy is refused.
- practice C2: Conan, Debian, NuGet, Helm and Ruby gems read only HTTP Basic, their own tokens or a bare
  `Authorization` token, not `PRIVATE-TOKEN`/`JOB-TOKEN`/`Bearer`: restate Security Considerations (the Conan token
  endpoints answer 401, not a token) and add one residual (HTTP Basic is outside this change).
- security C1: "The credential" bullet points the virtual-registry upstream `password` rows at #41's "Secrets in
  arguments" residual.
- standards C1: the AC-2.4 strategy `st.sampled_from(elements=...)`.
- test C1 / spec C1: AC-4.2's refusals traced to #40's `test_a_raw_body_the_call_cannot_send_is_refused` with F's
  `RAW_BODIES` table (one sentence).
- devops C1 / spec C2: both headers say "rebases onto `origin/main` once #40's PR has merged, before its implementation
  waves (DL-001)".
- spec D1: #40's three forms are all its D1; D2 is `call`'s optional path parameter, D3 the contract test's reading.
- spec D2: `route` shows caller text with `json.dumps`, as `call.py`'s docstring says.

Lane files: `review/<lane>/iteration-01.md`.
