# Best-practice review — issue #17 design — iteration 01

No MCP documentation server covers GitHub or the Python standard library; official pages fetched 2026-11-10.
Checked and in line with the guidance (no finding): API versions `2022-11-28` / `2026-03-10` (both supported,
[API versions](https://docs.github.com/en/rest/about-the-rest-api/api-versions)); rate-limit order `retry-after`,
then `x-ratelimit-remaining: 0` until `x-ratelimit-reset`
([Rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)); `link` pagination
and the `upload_url` hypermedia relation ([Best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api),
[Release assets](https://docs.github.com/en/rest/releases/assets)); `Request.remove_header` clearing both header
maps and `build_opener` replacing the default `HTTPRedirectHandler` with a subclass instance
([urllib.request 3.9](https://docs.python.org/3.9/library/urllib.request.html)).

### C1 — A non-GET request to a renamed repository gets a 307 urllib does not follow; D5 says redirected API requests are followed
Severity: C
Location: design.md § D5 "Deviations from the fork, flagged"; requirements.md § Residuals (the `307` line)
Defect: GitHub answers every `POST`, `PATCH`, `PUT` and `DELETE` under a renamed or transferred repository with
`307` (`GET`/`HEAD` get `301`), and `HTTPRedirectHandler.redirect_request` follows `307` only for `GET`/`HEAD`, so
every mutating part-1 record (`issues/create`, `issues/add-labels`, `issues/remove-label`, `pulls/merge`,
`git/delete-ref`, …) raises `HTTPError` 307 there; D5's "a redirected API request (… AC-3.1 follows it)" holds for
`GET` only, and the residual names only `PATCH`/`DELETE /repos/{owner}/{repo}`.
Material-because: a clarification — the outcome there is exit 1, as the fork's, so no criterion breaks; the text
misstates which redirects are followed.
Source: [Preview Repository Redirects in the GitHub API](https://gist.github.com/jasonrudolph/56388a4ff51b4f721cac)
(the GitHub API changes post of 2015-04-17: "`POST`, `PATCH`, `PUT`, and `DELETE` requests receive a `307`
redirect"); observed 2024 in [git-machete #1211](https://github.com/VirtusLab/git-machete/issues/1211) ("every
POST/PATCH to `https://api.github.com/repos/...` results in a 307 redirect"); CPython 3.9
`Lib/urllib/request.py` `HTTPRedirectHandler.redirect_request` (`code in (301, 302, 303, 307) and m in ("GET",
"HEAD") or code in (301, 302, 303) and m == "POST"`, else `raise HTTPError`).
Proposed-edit: in D5 replace "a redirected API request (the fork's `_RefusingRedirectHandler` refuses every
redirect; AC-3.1 follows it)" with "a redirected `GET` (the fork's `_RefusingRedirectHandler` refuses every
redirect; AC-3.1 follows it) — a `POST`, `PATCH`, `PUT` or `DELETE` on a renamed repository gets `307`, which
urllib does not follow for those methods, so it exits 1 as the fork does"; in the requirements residual replace
"the `307` that `PATCH`/`DELETE /repos/{owner}/{repo}` declare" with "the `307` GitHub sends to every `POST`,
`PATCH`, `PUT` and `DELETE` on a renamed or transferred repository (and that `PATCH`/`DELETE
/repos/{owner}/{repo}` declare)".

### C2 — A malformed `Location` escapes the transport as `ValueError`, not `GitHubAPIError`
Severity: C
Location: design.md § D3 "Failures, in `_send`"
Defect: `HTTPRedirectHandler.http_error_302` runs `urlparse(newurl)` and `quote(newurl, encoding="iso-8859-1",
…)` before it calls `redirect_request`, so a `Location` with a malformed IPv6 literal or a non-Latin-1 character
raises `ValueError` / `UnicodeEncodeError` (a `ValueError`) out of `opener.open`; D3 converts only `HTTPError` and
`URLError`, so such a response reaches `main` as an uncaught traceback instead of the Glossary's "a return value or
a `GitHubAPIError`" — the fork measured exactly this and overrides `http_error_302` for it (`scripts/github_wrapper.py`
`_RefusingRedirectHandler` docstring, "Overriding `redirect_request` alone is NOT sufficient").
Material-because: a risk worth one sentence — nothing is sent with the credential and the process still exits
non-zero, so no criterion breaks.
Source: CPython 3.9 `Lib/urllib/request.py` `HTTPRedirectHandler.http_error_302`; [urllib.request 3.9](https://docs.python.org/3.9/library/urllib.request.html)
`redirect_request` ("called by the default implementations of the `http_error_30*()` methods").
Proposed-edit: append to D3 "Failures, in `_send`": "- A `ValueError` raised while urllib resolves a redirect's
`Location` raises `GitHubAPIError` naming the request URL, with `status_code` `None`."

Verdict: CLEAN
