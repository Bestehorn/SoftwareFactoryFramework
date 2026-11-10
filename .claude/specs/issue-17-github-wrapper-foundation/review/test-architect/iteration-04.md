# Test architect - design review, iteration 04 (delta)

## Fix sites

| Id | Site | Status |
|---|---|---|
| A1 | Correctness Properties UB-1.1: the userinfo example asserts that the `caplog` records hold the refusal naming `.git/config` and `github.com/o/socket.io.git`, and that neither the records nor stderr hold `ghp_T` or `secret` | APPLIED. The positive half fails if the refusal is never logged, and the negative half fails if the fork's verbatim message is kept |
| B1 | AC-3.1: the cross-host `302` is followed "from `request` and from `download`" with no `Authorization` | APPLIED. The fake host records the headers `do_open` sends, so a `download` on a default opener that copies `req.headers` fails. AC-2.1's hand-off ("the storage hop is AC-3.1's") and D5's `get-logs` case now have a test |
| C9 | AC-3.1: `https://user:pw@api.github.com/x` raises `GitHubAPIError` with no request recorded, and `https://api.github.com:/x` keeps `Authorization` | APPLIED. This matches D3 Origin (the port after the last `:` is not an integer; an empty port counts as absent) and D3 Failures (`InvalidURL` becomes `GitHubAPIError`). An origin built from `urlsplit().hostname` records a request to the userinfo URL and fails | <!-- pragma: allowlist secret -->

The other iteration-03 edits leave every oracle intact:
- D3 Failures (BP-C1) and the D5 closing sentence describe behaviour that no example contradicts.
- `origin(url=req.full_url)` (ST-D1) keeps the "further hop back to the API host carries none" oracle.
- The D8 wording changes (SR-C2 and the conductor's #13 restatement) leave S's oracle unchanged. S still checks the package path in the Part 5.3 and Part 6.2 copy steps and in both shipped-Python lists.
- The rewraps (ST-D2) change no words. The mapping table is unchanged.

## Findings

None.

## Coverage (tests per § Acceptance Criteria Mapping)

| Criterion | Test | Status |
|---|---|---|
| AC-1.1 | inspection D1; R | COVERED |
| AC-1.2 | inspection D2; V | COVERED |
| AC-1.3 | V | COVERED |
| AC-2.1 | T | COVERED |
| AC-2.2 | T | COVERED |
| AC-2.3 | T | COVERED |
| AC-2.4 | T | COVERED |
| AC-3.1 | T | COVERED |
| AC-3.2 | T | COVERED |
| AC-3.3 | T | COVERED |
| AC-3.4 | T | COVERED |
| AC-4.1 | T | COVERED |
| AC-4.2 | T | COVERED |
| AC-4.3 | T | COVERED |
| AC-5.1 | V | COVERED |
| AC-5.2 | V | COVERED |
| AC-5.3 | V | COVERED |
| UB-1.1 | C; P | COVERED |
| UB-1.2 | `test_wrapper_delivery.py`; C | COVERED |
| UB-1.3 | C; S | COVERED |
| UB-2.1 | C | COVERED |
| UB-2.2 | V | COVERED |
| UB-3.1 | `test_wrapper_delivery.py`; PR diff | COVERED |
| UB-3.2 | C | COVERED |

Verdict: CLEAN - TEST-READY (24 COVERED, 0 GAP)
