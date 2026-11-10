# Design review — spec-review-agent — iteration 04 (delta; spec-review, standards, best-practice, security, devops)

Fix sites hold. D3 "Failures" converts `http.client.InvalidURL`, and D3 "Origin (X5)" still raises `GitHubAPIError`
first for a non-integer port. D5's closing sentence agrees with its "exited 1" heading and with the fork's `main`
(`except GitHubAPIError` only, `logger.error`). The `caplog` oracle can fail: it asserts the refusal is present, and
the fork's `_detect_repo` regex refuses `socket.io.git`. AC-3.1's `user:pw@` and `:/x` examples follow from D3's port
rule. The `user:pw@` URL raises inside `redirect_request`, before `parent.open`. SE-D1 and SR-C2 are applied, and
§ Residuals is ten lines. No new positional call, credential path or deploy surface.

### C1 — D8 leaves the GitLab half's wording open when #17 lands before #13
Severity: C
Location: design.md § D8, third bullet (the "skeletons" sentence)
Defect: "keeps its GitLab half as #13 D2 restates it" reads as an instruction to write #13 D2's text, which says the
GitLab wrapper serves the minimum set. On a tree where #13 has not merged, that text is false in a shipped prompt
(#13's Overview is what replaces the skeleton `src/payload/scripts/gitlab_wrapper.py`). #13 D2 only hands back "The
GitHub half of the sentence is #17's", so neither spec states the GitLab wording before #13.
Proposed-edit: replace "keeps its GitLab half as #13 D2 restates it" with "leaves its GitLab half as the tree holds
it — the GitLab template a skeleton, or #13 D2's restatement where #13 merged first".

### D1 — Two fix-site paragraphs are not rewrapped at 120 columns
Severity: D
Location: design.md § D8, third bullet; § D3 "Redirects"
Defect: the conductor's D8 insertion pushes the bullet's second line ("… that `get-jobs`, `rerun` and") past 120
columns. D3 "Redirects" breaks after "— the decision the" even though the next words fit on that line.
Proposed-edit: rewrap both paragraphs at 120 columns, with no word changes.

CLEAN
