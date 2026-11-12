# Security review — design iteration 01 (lane: security-reviewer)

### C1 — The origin guard's refusal can print part of an origin URL's userinfo
Severity: C
Location: design.md § D2 (`_refuse_unless_ephemeral`); requirements.md AC-4.1
Defect: D2 says `_detect_repo`'s groups "never hold a URL's userinfo", but `GITHUB_REPOSITORY_PATTERN.search` on
`https://github.com:<secret>@example.com/repo` returns the owner `<secret>@example.com` (traced with the pattern as
written: `('SECRETVALUE@example.com', 'repo')`), so the message AC-4.1 requires would write `<secret>` to standard error.
The guard itself is not fooled: it judges exactly the `(owner, repo)` the requests would use, and extra path segments
(`.../Bestehorn/SoftwareFactoryFramework/github.com/x/sff-test-y` gives `x/sff-test-y`) change the target the wrapper
acts on, not the guard's verdict on it.
Proposed-edit: in D2 replace "`owner` and `repo` are `_detect_repo`'s groups of `GITHUB_REPOSITORY_PATTERN`, which
never hold a URL's userinfo." with "`owner` and `repo` are `_detect_repo`'s groups of `GITHUB_REPOSITORY_PATTERN`; the
message names the owner after its last `@` (`owner.rpartition("@")[2]`), because the owner group of an origin whose
userinfo ends in `github.com:` holds the rest of that userinfo." and add the origin
`https://github.com:<sentinel>@example.com/repo` to W `test_the_marker_refuses_an_origin_without_the_prefix`, asserting
the sentinel is absent from the log.

### C2 — "Owner-only file mode" is not a property on Windows
Severity: C
Location: design.md § D8 (Writing)
Defect: on Windows `os.chmod` "can only set the file's read-only flag ... All other bits are ignored"
(docs.python.org `os.chmod`), so the clone's credential file there is protected by the `tempfile.mkdtemp` workspace's
owner-only DACL (gh-118486, the CVE-2024-4030 fix; the local venv is 3.14.2), not by its mode. No new reader results:
the source test credential file sits in the checkout under the same inherited ACL.
Proposed-edit: in D8 Writing replace "owner-only file mode" with "file mode `0o600` (owner-only on POSIX; on Windows,
where `os.chmod` sets only the read-only flag, the owner-only protection is the `tempfile.mkdtemp` workspace's, D9)".

### C3 — The blast-radius text overstates what binds a same-repository run
Severity: C
Location: design.md § Security Considerations (Blast radius; CI trust)
Defect: D9's guards bind the suite as merged; a same-repository pull request, or a `workflow_dispatch` on any branch,
runs that branch's own `test/forge/` and `ci.yml` with `SFF_TEST_TOKEN`, so for its author the bound is the token's
reach (Administration write on every repository of `bestehorn-sff-test`), not D9's selection.
Proposed-edit: append to the CI trust bullet: "Such a run executes the branch's own suite, so its bound is the token's
reach, every repository of `bestehorn-sff-test`, and not D9's guards; that is why the token's resource owner is a
dedicated organization."

### C4 — The git credential helper answers for any host git authenticates to
Severity: C
Location: design.md § D3 (The helper)
Defect: the snippet answers every `get` whatever `protocol` and `host` git passes, and git authenticates to the URL
after the operator's global `url.<base>.insteadOf` rewrite (git-scm.com/docs/git-config `url.<base>.insteadOf`), so a
rewrite of `https://github.com/` to a mirror hands that mirror the test token.
Proposed-edit: in D3 replace the second option `-c credential.helper=!f() { ... }; f` with
`-c credential.https://github.com.helper=!f() { ... }; f` (gitcredentials "CREDENTIAL CONTEXTS": a context matches
only the same protocol and the exact host), keep the unscoped empty `-c credential.helper=` first, and have S's
`git credential fill` pass `protocol=https` and `host=github.com`.

## Residuals

- A protected deployment environment with required reviewers for `SFF_TEST_TOKEN` (C3's trust model): outside the
  ask; a findings-ledger row.
- Without the marker `_detect_repo` accepts an owner group holding `@` (C1's origin) and the request path carries it;
  pre-existing, kept by UB-3; a findings-ledger row, not this change.

CLEAN
