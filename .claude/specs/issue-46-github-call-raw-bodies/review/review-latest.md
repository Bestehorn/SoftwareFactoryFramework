# Review latest — issue #46 design

## Iteration 01 (consolidated by the conductor)

Lanes:

- devops CLEAN (1 C);
- security CLEAN (3 C);
- standards CLEAN (2 C, 3 D);
- best-practice CLEAN (1 C, 1 D);
- spec-review READY (6 C, 1 D);
- test-architect NOT-CLEAN (0 A, 1 B, 2 C; 15/16 COVERED).

### Root cause (B): 1 finding → 1 cause

- **Z1: the standard-input form of `--input` is not proven byte-exact.** AC-4.3's markdown test uses unspecified
  bytes, so a text-mode read would pass. Fix: AC-4.3 monkeypatches `sys.stdin` to
  `io.TextIOWrapper(io.BytesIO(...))` over bytes holding a `\r\n` line ending and the byte `\xff`. [TA-B1]

### C/D: apply in the same pass, no new round

- TA-C1: the missing-file case requires `argument --input:` and the path as `json.dumps` renders it on standard
  error.
- TA-C2 and SR-C3: D4's restatement of #27's G and #33's M is re-checked at the rebase onto #33. Name the G comment and
  docstring that go stale. Remove `RECORDED_IDS` and point both of its uses at `REPOS_OPERATION_IDS`, dropping the
  stale docstring phrase (ST-C1).
- ST-C2: `read_input`'s message names only the path, since argparse names the option.
- ST-D1: rename `origin` to `root`.
- ST-D2: name constants for `FILE`, `-`, `PATCH` and `DELETE` in the files table.
- ST-D3: drop the hash from the Overview.
- SR-C1: #46's cases stay outside K's `CALL_CASES`.
- SR-C2: D1 step 4's message names `--input`.
- SR-C4: UB-2.2 states that `Transport.upload` already reaches `UPLOAD_ORIGIN`.
- SR-C5: correct the Out of scope list of redirects that still end in an error.
- SR-C6: log the three #28 D8 "never" edits. The conductor writes DL-006.
- SR-D1 and BP-D1: urllib calls `redirect_request` only for 301, 302, 303 and 307, plus 308 from 3.11, and only with a
  `Location`.
- BP-C1: one sentence saying `read_input` reads in the argparse `type` safely, because it converts `OSError` and
  `read_bytes` closes the file.
- SEC-C1: the credential exposure through upload or render.
- SEC-C2: `request_raw` builds its URL with `_api_url(root=...)`.
- SEC-C3: the body is read into memory even when the call is refused.
- DV-C1: an INFO log line on the `307` re-send, or a Residuals line.

Next: one author pass over Z1 and every C/D above, then a delta review in iteration 02 (cap 4).

## Iteration 02 (delta)

test-architect CLEAN (16/16 COVERED); the other five lanes were CLEAN or READY at iteration 01 and their C/D items are applied. Approved (DL-008).
