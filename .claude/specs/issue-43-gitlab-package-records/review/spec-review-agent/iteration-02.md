# spec-review-agent — design review, iteration 02 (issue #43, tier M, delta)

Delta against iteration 01 and DL-006. I checked the fix sites against the revised `requirements.md` and `design.md`,
`rest/package.md`, `operations-index.md`, `families/package.py` `PENDING`, and #40's branch (`.claude/worktrees/issue-40`,
8b489b0).

My iteration-01 findings are closed:
- B1: requirements.md § Residuals and design.md § Residuals have ten lines each. The stale multipart bullet is gone,
  and the design's first bullet now says "first three", which matches the four requirements residuals (the fourth is
  #11's).
- C1: the AC-4.2 entry traces the third bullet's refusals to K `test_a_raw_body_the_call_cannot_send_is_refused`, and
  F's `RAW_BODIES` fixes which records take `--input`. That test exists on #40's branch, as does
  `test_gitlab_api_deploy.py` `test_the_upload_sends_the_bytes_as_its_body`.
- C2: both headers say the branch rebases onto `origin/main` once #40's PR has merged.
- D1: the design header gives #40 D1, D2, D3 and D5 their contents correctly.
- D2: D2's `route` table renders the caller's text with `json.dumps`.

The other iteration-01 edits agree between requirements and design:
- A1 (npm dist-tag):
  - AC-4.2's lead sentence and raw-body list, D5's row and its `CONTENT_TYPE_JSON` bullet, and F's raw-upload row (prefix
    `/projects/:id/packages/npm`, `application/json`) all agree.
  - The entry's `version` row is `body`, `string`, Required `yes`. AC-1.4 and D6 make it a required `Location.QUERY`
    `Param`. #40's N `documented_raw_body` reads it as `query`, and the entry has no `file` row, which D4's "Raw bodies"
    bullet allows.
  - F's call passes no `--query version` and still expects exit 0. That holds because `commands/call.py` never reads
    `Param.required`: no `required` occurs in it.
- B1 (`PUT /projects/:id/`):
  - The key is held pending in AC-1.3, D6's kept keys, the Correctness Properties literals for AC-1.1 and AC-1.3, and
    the Security "Gates" bullet.
  - No `avatar` text remains in requirements, design or prompt.
  - The requirements residual is accurate: "Change the visibility of the container registry" and tenant-scale "Update
    a project" both carry `import_url`, `mirror` and `mirror_overwrites_diverged_branches`.
- B2 (NuGet v3):
  - D5 splits the NuGet row. AC-4.2's `--file` list ("the NuGet, PyPI and Helm uploads and the Maven virtual-registry
    upload") matches D5's five `--file` records.
  - The entry lists `/packages/nuget` before `/v2`, as AC-1.2's oracle states.
  - The design's third residual names `package#upload-a-package-file-5`.
- B3: D4's "reached past" bullet names the same four edits as D8's N row.
- Other lanes' C items: practice C1 and C2 (the Conan-token bullet and the authentication residual), security C1 ("The
  credential") and standards C1 (`st.sampled_from(elements=...)`) are applied. They add no AC id.
- Caps: `requirements.md` is 16,347 B (cap 20,000) and `design.md` is 49,104 B (cap 60,000).

No new defect.

CLEAN

Verdict: READY
