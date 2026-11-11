# Standards review — design iteration 03 (delta) — issue #40

Lane: standards-reviewer. Subject: iteration 02's fix sites in `design.md` (consolidated B1 and B2, and the C and D
items applied in the same pass), plus the one `requirements.md` § Residuals line that pass added. Checked against
`.claude/rules/` and the conventions of `src/payload/scripts/gitlab_api/`.

Iteration 02's B1 is closed. Correctness Properties AC-3.2, G `test_the_upload_sends_the_bytes_as_its_body`, now
writes `io.TextIOWrapper(buffer=io.BytesIO(initial_bytes=<the bytes>))`. Both call sites name their argument, the
same way origin/main `src/payload/test/test_github_api_call.py` does
(`io.TextIOWrapper(buffer=io.BytesIO(initial_bytes=RAW_MARKDOWN), encoding=STDIN_ENCODING)`). The expression also
runs: in the venv it was built with `b'a\r\n\xff'`, and `.buffer.read()` returned `b'a\r\n\xff'`. So `read_input`'s
`sys.stdin.buffer.read()` gets the bytes unchanged.

Checked on the delta, and not findings:

- Named parameters: the edits add no call site. Every call the design writes still names its arguments
  (`refuse_both_bodies(raw_body=..., args=...)`, `refuse_raw_body(operation=..., raw_body=...)`,
  `request_raw(...)`, `_send(...)`). The keyword-only signature of `Transport._send` in `gitlab_api/transport.py`
  takes exactly the names D5 passes.
- The added redirect sentence (security C1) names `CredentialStrippingRedirectHandler`. That class exists in
  `gitlab_api/transport.py`, and the module's comment above its method constants says a redirect of any method other
  than GET or HEAD is not followed.
- Constants: the edits access no JSON field and add no literal for the implementation to hold.
  `CONTENT_TYPE_OCTET_STREAM` is the existing `transport.py` constant.
- Standard library only, and product paths: the edits add no dependency and no file. Every D7 file is under
  `src/payload/`, `test/` or `docs/`. The only GitLab entry in `config/toolchain.json` is `gitlab_wrapper.py`, under
  `not_installed` ("the repository is on GitHub"), so no D7 file is toolchain.
- Proportionality: design § Residuals and requirements § Residuals are ten lines each, which is within the cap.
  Practice C2 went into requirements § Residuals and adds no acceptance criterion. The new Sources lines give a read
  date and a status code, not a figure that a later commit would make wrong.

CLEAN

Verdict: READY
