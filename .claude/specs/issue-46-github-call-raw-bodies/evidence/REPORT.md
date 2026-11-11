# Evidence report — issue #46: GitHub `call`: non-JSON request bodies, uploads and the 307 re-send

Tier M, four waves. Branch `issue-46-github-call-raw-bodies`, PR #57. It was rebased onto d30d022 (#33), where code-merge-reviewer kept both sides of the `commands/call.py` docstring. It was then rebased onto 52403f8 (#36), with no conflict.

| Criterion | Tests | Capture | Verdict |
|---|---|---|---|
| AC-1.1 `--input FILE`/`-` reads a raw body; refused beside `-f/-F` and on a JSON record | K | red/green wave-2 | green |
| AC-1.2 raw bytes sent unchanged with the record's media type | T, R, K (incl. the stdin `\r\n` and `\xff` case) | red/green waves 1, 2, 4 | green |
| AC-1.3 both bodies given → exit 2, no request | K | red/green wave-2 | green |
| AC-2.1, AC-2.2 the upload goes to `uploads.github.com`; the origin check holds | T, R, K, N | red/green waves 1, 2 | green |
| AC-3.1, AC-3.2 a same-origin 307 is re-sent with method and body; a cross-origin redirect drops the credential | T, K | red/green wave-1 | green |
| AC-4.1 `repos/upload-release-asset` and `markdown/render-raw` declared, both `PENDING` empty | G, M, N, V | red/green waves 2, 4 | green |
| AC-4.2, AC-4.3 records sent as their sections; a raw Markdown document rendered | N, K | green waves 2, 4 | green |
| AC-5.1, AC-5.2 usage and map name `call --input` and the upload | C, B | red/green wave-3 | green |
| UB the compatibility cases, credential, stdlib only, the trunk's gates | C, P, V, K; the PR diff | every wave | green |

Green captures:
- Wave 1: 943 passed. Wave 2: 951 passed. Wave 3: 562 passed. Wave 4: 1085 passed.
- After the rebase onto 52403f8: 1108 passed.
- Product `run_checks.py --group lint --group types --group security`: 5 passed.

**Verifier.** VERIFIED (`evidence/verify/refutation-report.md`):
- **Mutants:** all 41 were killed (19 in wave 1, 12 in wave 2, 6 in wave 3, 4 in wave 4). They include the two the tasks name: the 307 branch without its origin check, and N's reader keeping the default host.
- **Rebase merge in `commands/call.py`:** it keeps all 17 trunk gate entries and the three message forms.

**Whole suite.** CI run 42982400640 success on 10a2223.

E2E: not applicable. The real-forge check is #10's fixture. K and N run `call` through `main` up to the API boundary in CI job `verify`, leg `tests`.
