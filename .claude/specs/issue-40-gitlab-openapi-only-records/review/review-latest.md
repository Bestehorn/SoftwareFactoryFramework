# Review — design iteration 02 (consolidated, delta)

Five delta lanes. Overall: NOT-CLEAN (0 A, 2 distinct B). Iteration 01's A1, B1-B3 and C/D are closed (every lane).
- READY: security-reviewer, best-practice-reviewer.
- NOT-READY: test-architect (B1), spec-review-agent (B1, the same finding), standards-reviewer (B1).

## B (gating)

- **B1 — F's `REQUIRED` oracle still counts a raw-body record's `file` row** (test-architect B1 = spec B1; criterion
  AC-1.3/AC-3.2). Edit in § Correctness Properties, AC-1.3, F `test_every_param_is_typed_as_its_row`: "the `yes`
  rows that name no path parameter, a raw-body record's `file` row excepted;", matching the `KINDS` bullet.
- **B2 — a test sketch calls `io.TextIOWrapper(io.BytesIO(...))` positionally** (standards B1; `coding-standards.md`
  rule 4). Edit in § Correctness Properties AC-3.2, G: `io.TextIOWrapper(buffer=io.BytesIO(initial_bytes=<the bytes>))`.

## C and D (applied in the same author pass)

- **security C1:** "The raw body": the configured origin also holds across a redirect, because
  `CredentialStrippingRedirectHandler` raises instead of following a redirect for a method other than GET or HEAD, and
  a 3xx exits 1 (#13 D4 "Redirects").
- **security C2:** "Gates", the Git-URL import line. GitLab's `POST ':id/import/git'` handler (`lib/api/project_import.rb`)
  answers 409 when the project already has a repository. Confirm that line against the raw source before you state
  it, and add a Sources line.
- **security D1:** Sources adds GitLab's Group access tokens API page.
- **practice C1:** AC-3.2 and D4 name only `file` as the job-artifacts upload's file part. Workhorse refuses any other
  file part and writes `metadata` itself.
- **practice C2:** one Residuals line. A job token given with `-f token=` never authenticates the upload: Workhorse's
  authorize request has no body, so only the configured job token works.
- **spec C1:** the refusal of `--input` beside `-f`/`-F` also says that a raw-body record's attributes are given with
  `--query`.
- **spec D1:** AC-1.3's raw-body clause follows the per-row rules it overrides, restated as the lane proposes.

Lane files: `review/<lane>/iteration-02.md`.
