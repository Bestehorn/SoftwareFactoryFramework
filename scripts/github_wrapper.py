"""GitHub API wrapper for CI/CD and issue operations.

Usage:
    python scripts/github_wrapper.py list-workflows
    python scripts/github_wrapper.py list-runs --limit 5
    python scripts/github_wrapper.py get-run <run_id>
    python scripts/github_wrapper.py wait-run <run_id> --timeout-seconds 540 [--interval-seconds 30]
        # BLOCKS until the run completes; exit 0 success, 10 any other conclusion, 11 timeout
        # (distinct from the wrapper's own 1 API error, 2 usage error, 3 claim-check unclaimed).
        # Run it AFTER the unblocked work, in the FOREGROUND, re-issued on exit 11 (parallel-by-default.md);
        # never as a background task the turn ends to wait for, never `sleep`.
    python scripts/github_wrapper.py require-green-deploy --workflow deploy-dev.yml --head-sha <40-hex sha> \
        [--run-id <run_id>] [--by-run-name] [--token-stdin]
        # exit 0 only for a Green Deploy of the commit: the run --run-id names, or else one listed run, matches every
        # run field checked and its latest attempt lists the workflow's jobs, each once and concluded success
        # (GREEN_DEPLOY_JOBS: deploy-dev.yml's admission, deploy, openings-harness and sync-harness, or
        # deploy-stage.yml's deploy and sync-harness, any other --workflow refused; issues #1052, #1059, #1266);
        # otherwise exit 1. With --by-run-name the run's display_title must be the Run Name of the commit for
        # --workflow (RUN_NAME_TEMPLATES: the bare sha for deploy-dev.yml, the Stage Run Name for deploy-stage.yml),
        # in place of its head_sha, for the run --run-id names or a listed run (issues #1036, #1266). With
        # --token-stdin the token is the WHOLE of standard input, not credentials/github-pat.txt (issue #908).
    python scripts/github_wrapper.py require-newest-trunk-run --run-id <ci.yml run_id> --head-sha <40-hex sha> \
        --own-run-id <run_id> --run-attempt <n> --token-stdin
        # deploy-dev.yml's Admission Job (issue #1266): exit 0 for a re-run (--run-attempt above 1), or when the
        # --run-id run is a green push run of ci.yml on main at the commit and no listed one has a higher run_number;
        # a newer one cancels run --own-run-id, waits SELF_CANCEL_WAIT_SECONDS and exits 1; anything else exits 1.
    python scripts/github_wrapper.py get-jobs <run_id> --failed-only
    python scripts/github_wrapper.py get-jobs <run_id> --show-steps
    python scripts/github_wrapper.py get-jobs <run_id> --step-status   # each step's live status (issue #1277)
    python scripts/github_wrapper.py get-jobs <run_id> --timing
    python scripts/github_wrapper.py get-jobs <run_id> --all-attempts   # include re-run history
    python scripts/github_wrapper.py ci-liveness [--max-age-hours 72] [--scan-runs 20]
    python scripts/github_wrapper.py token-info
    python scripts/github_wrapper.py list-hooks   # id, active, receiving HOST (never the URL's token), events
    python scripts/github_wrapper.py hook-deliveries <hook_id> [--since 2026-10-25T09:00Z] [--limit N] [--failed-only]
    python scripts/github_wrapper.py hook-delivery <hook_id> <delivery_id>   # the job + the receiver's reply
    python scripts/github_wrapper.py get-logs <run_id> --failed-only
    python scripts/github_wrapper.py list-repo-artifacts   # every Actions artifact, then the unexpired bytes
    python scripts/github_wrapper.py delete-artifacts --older-than-days 3 [--dry-run]
        # deletes each unexpired artifact created before the cutoff, each CONFIRM-READ 404 (a full storage quota)
    python scripts/github_wrapper.py rerun <run_id> --failed-only
    python scripts/github_wrapper.py cancel <run_id>
    python scripts/github_wrapper.py dispatch-workflow ci-runner-pilot.yml [--ref main]
    python scripts/github_wrapper.py get-variable CI_RUNNER_MODE
    python scripts/github_wrapper.py security-alerts   # are Dependabot ALERTS enabled?
    python scripts/github_wrapper.py set-variable CI_RUNNER_MODE codebuild   # writes, then CONFIRM-READS
    python scripts/github_wrapper.py put-file --path README.md --file notes.md --message '...' \
        [--target-repo owner/repo] [--expected-blob-sha SHA]   # seeds an EMPTY repo, which a release needs a commit in
    python scripts/github_wrapper.py get-release --tag engine-assets-2026-09-19 [--target-repo owner/repo] \
        [--body-out FILE [--expected-body-sha256 H]]   # the body's exact bytes; exit 1 on a MISMATCH
    python scripts/github_wrapper.py repo-visibility [--target-repo owner/repo]   # PUBLIC or PRIVATE
    python scripts/github_wrapper.py upload-release-asset --tag engine-assets-2026-09-19 \
        --file tmp/engine-net/maia-2200.onnx --expected-sha256 <digest> \
        --target-repo MarkusBestehorn-Chess/chess-engine-assets --require-existing-release   # digest-gated
    python scripts/github_wrapper.py set-release-notes --tag engine-assets-2026-09-19 --notes-file notes.md \
        --target-repo owner/repo --expected-latest engine-assets-2026-09-19 --expected-body-sha256 <digest>
        # replaces the notes, then CONFIRM-READS them and the latest release; every option is REQUIRED
    python scripts/github_wrapper.py get-file --path README.md --out tmp/README.md --target-repo owner/repo \
        [--expected-sha256 H]   # read-only: writes the file's exact bytes; exit 1 on a MISMATCH
    python scripts/github_wrapper.py download-public-asset --target-repo owner/repo \
        --tag engine-assets-2026-09-19 --name maia-2200.onnx --out tmp/maia-2200.onnx --expected-sha256 <digest>
        # NO credential; keeps the file only if its sha256 matches, else exit 1
    python scripts/github_wrapper.py get-public-latest-release --target-repo owner/repo
        # NO credential: ONE read of the latest release, printed as one JSON object holding its tag_name and each
        # asset's name and digest (a null digest as null); exit 1 when GitHub answers 404 (issue #1248)
    python scripts/github_wrapper.py get-release --tag <tag> --target-repo owner/repo --include-drafts
        # a tag with no published release: its ONE draft, read through the authenticated release listing
    python scripts/github_wrapper.py upload-release-asset --tag <tag> --file <file> --expected-sha256 <digest> \
        --target-repo owner/repo --require-draft-release   # only into the tag's ONE draft; never creates one
    python scripts/github_wrapper.py create-draft-release --target-repo owner/repo --tag <tag> \
        --notes-file notes.md --target-commitish <40-hex sha> --expected-latest <latest tag>
        # ONE draft, no make_latest; then CONFIRM-READS its body and the latest release; every option is REQUIRED
    python scripts/github_wrapper.py publish-release --target-repo owner/repo --tag <tag> --expected-latest <latest tag>
        # PATCHes draft false and make_latest "false", then CONFIRM-READS the tag and the latest release
    python scripts/github_wrapper.py create-pr --head feature-branch --title "..." --body "..."
    python scripts/github_wrapper.py get-pr <pr_number>
    python scripts/github_wrapper.py get-pr-checks <pr_number>
    python scripts/github_wrapper.py approve-pr <pr_number>
    python scripts/github_wrapper.py merge-pr <pr_number> --method merge   # "merge": "direct" only
    python scripts/github_wrapper.py delete-remote-branch <branch>
    python scripts/github_wrapper.py enqueue-pr <pr_number>     # "merge": "steward": hand the PR to the queue
    python scripts/github_wrapper.py dequeue-pr <pr_number> --reason "..."
    python scripts/github_wrapper.py queue-status [--json]
        # The delivery verbs DELEGATE to scripts/merge_steward.py (enqueue / dequeue / status) with this
        # wrapper's token on its standard input and pass its exit status through (enqueue: 0 queued, 4 refused
        # with the reason printed); the queue's rules live in that one script (.claude/docs/delivery.md).
    python scripts/github_wrapper.py list-issues --state open --assignee '*'
    python scripts/github_wrapper.py list-issues --state all --limit 300   # paginates past 100/page
    python scripts/github_wrapper.py list-issues --state open --limit 100 --token-stdin   # the token on stdin
    python scripts/github_wrapper.py get-issue <issue_number>
    python scripts/github_wrapper.py get-issue-comments <issue_number>   # every page, one JSON list
    python scripts/github_wrapper.py comment-issue <issue_number> --body "..."
    python scripts/github_wrapper.py comment-issue <issue_number> --body-file notes.md
    python scripts/github_wrapper.py delete-issue-comment <comment_id>
    python scripts/github_wrapper.py update-issue <issue_number> --state closed
    python scripts/github_wrapper.py reopen-issue <issue_number>   # undo a premature close (verified)
    python scripts/github_wrapper.py checklist <issue_number>      # ticked/total + the unticked items
    python scripts/github_wrapper.py checklist <issue_number> --tick "wire the parser"   # or --untick
    python scripts/github_wrapper.py update-issue <issue_number> --body-file new-body.md
    python scripts/github_wrapper.py create-issue --title "..." --body-file body.md
    python scripts/github_wrapper.py create-issue --title "..." --body-file body.md --token-stdin   # token on stdin
    python scripts/github_wrapper.py create-pr --head branch --title "..." --body-file pr.md
    python scripts/github_wrapper.py link-issue <issue_number> --blocked-by <other_number>
    python scripts/github_wrapper.py add-sub-issue <parent_number> --sub-issue <child_number>
    python scripts/github_wrapper.py unlink-issue <issue_number> --blocked-by <other>
    python scripts/github_wrapper.py get-issue-dependencies <issue_number>
    python scripts/github_wrapper.py list-available            # OPEN + NOT in-progress (pick work here)
    python scripts/github_wrapper.py list-in-progress          # OPEN + in-progress (already claimed)
    python scripts/github_wrapper.py claim-issue <issue_number> [--strict]  # ADD 'in-progress' (before you start)
    python scripts/github_wrapper.py release-issue <issue_number>  # REMOVE 'in-progress' (if you stop)
    python scripts/github_wrapper.py claim-check <issue_number>    # READ-ONLY probe; exit 3 = OPEN + UNCLAIMED
    python scripts/github_wrapper.py issue claim-check <issue_number>  # identical; the argv the claim gate sends
    python scripts/github_wrapper.py start-issue <issue_number>    # THE claim: additive + assigns + VERIFIES
    python scripts/github_wrapper.py issue start <issue_number>    # identical; the nested claim-trio spelling
    python scripts/github_wrapper.py issue release <issue_number>  # alias of release-issue
    python scripts/github_wrapper.py label-add <issue_number> --labels a,b   # ADDITIVE (never a whole-set replace)
    python scripts/github_wrapper.py label-remove <issue_number> --label a   # removes exactly one label
    python scripts/github_wrapper.py assign <issue_number> --me | --user LOGIN | --unassign
    python scripts/github_wrapper.py issue label-add|label-remove|assign ...  # identical; nested spellings

Worker protocol (prevents two workers duplicating the same issue — READ THIS before starting work):
    A worker (agent or human) picks and claims work ONLY through these commands, so a claim made in
    one session is visible to every other session:
      1. `list-available`  — the pool of OPEN, unclaimed issues. Choose from here; never start an
         issue that is not listed as available.
      2. `claim-issue <n> --strict` — ATOMICALLY acquire it BEFORE creating a branch/worktree or
         writing code. `--strict` FAILS (exit 1) if another worker already claimed it, so a race
         (both workers saw it as available) is caught here instead of duplicating work — check the
         exit status and move on if it is nonzero. Omit `--strict` only to RE-assert a claim on your
         OWN issue (e.g. resuming an interrupted run), where an existing claim is a no-op success.
         Label-preserving either way.
      3. do the work, keeping the issue updated (see .claude/rules/issue-tracking.md).
      4. on finish: close the issue (`update-issue <n> --state closed`). If you STOP WITHOUT
         finishing (blocked / handing off / abandoning): `release-issue <n>` so it returns to the pool.
      5. `list-in-progress` — audit what is currently claimed (before adopting "stalled" work, etc.).
      6. `claim-check <n>` — the READ-ONLY probe (writes nothing) that mechanically ENFORCES step 2.
         Exit 3 = the issue is OPEN and UNCLAIMED; exit 0 = claimed, or not open.
    claim/release touch ONLY the 'in-progress' label and preserve all other labels, unlike
    `update-issue --labels`, which REPLACES the whole label set.

The DETERMINISTIC claim — `start-issue <n>` (equivalently `issue start <n>`):
    `claim-issue` above is this project's original label-only claim and is kept as-is. `start-issue`
    is the stronger claim the project's rules and agents actually prescribe
    (`.claude/rules/issue-tracking.md`, `.claude/agents/issue-work-orchestrator.md`,
    `.claude/commands/work-issue.md`, `.claude/commands/auto-work.md`): ONE command that is both
    IDEMPOTENT and FAIL-CLOSED. It refuses a non-open issue, refuses an issue another worker already
    holds, adds the in-progress label through GitHub's ADDITIVE label endpoint, assigns the working
    identity, and then RE-READS the issue to confirm BOTH landed — exiting non-zero if they did not,
    so a claim is never believed unless it actually took effect. `release-issue` is its inverse.
    All label changes go through the additive `label-add` / `label-remove` primitives; the plain
    `labels` field of the issue-update endpoint is a FULL REPLACE that silently drops sibling labels
    and has repeatedly made the in-progress label vanish, causing duplicate work.

Mechanical enforcement of step 2 — the claim-before-worktree gate, .claude/hooks/gate_claim.py (PreToolUse):
    The gate refuses `git worktree add ... issue-<N>` until issue N is claimed, catching a skipped
    claim at the moment work would start instead of after two workers have duplicated it. It shells
    out to `<wrapper> issue claim-check <N>` — the NESTED argv form — blocks on exit code 3 alone,
    and fails OPEN on every other status. This wrapper therefore accepts BOTH spellings: the flat
    project convention (`claim-check <n>`) and the nested claim trio (`issue claim-check|start|
    release <n>`). The hook is synced verbatim from the shared standard, so re-spelling its argv
    locally would be reverted by the next sync and would silently return the gate to a no-op; the
    wrapper is the artifact that adapts. Keep exit code 3 exactly as it is — the gate reads nothing
    else, and any other value degrades it to a permanent allow.

Credentials: credentials/github-pat.txt (one-line PAT, gitignored); `require-green-deploy`, `require-newest-trunk-run`,
`list-issues` and `create-issue` with `--token-stdin` read the job token from standard input instead, through the same
one-token validator; the commands of `CREDENTIAL_FREE_COMMANDS`, `download-public-asset` and
`get-public-latest-release`, read no token at all.
"""

from __future__ import annotations

import argparse
import base64
import configparser
import hashlib
import json
import logging
import math
import re
import subprocess  # nosec B404  # only the delivery verbs: this interpreter on scripts/merge_steward.py
import sys
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.message import Message
from io import BytesIO
from pathlib import Path
from typing import Any, NoReturn
from urllib.error import HTTPError
from urllib.parse import quote, urlparse
from urllib.request import HTTPRedirectHandler, OpenerDirector, Request, build_opener

# --- JSON / HTTP field constants (per coding-standards.md) ---
#: The one HTTP status this module compares against by name: `delete-issue-comment`'s confirm-read
#: treats it as proof of deletion, so it is a decision value rather than a number in a log line.
HTTP_NOT_FOUND = 404

FIELD_NAME = "name"
FIELD_ID = "id"
FIELD_STATE = "state"
FIELD_STATUS = "status"
FIELD_CONCLUSION = "conclusion"
FIELD_TITLE = "title"
FIELD_BODY = "body"
FIELD_HEAD = "head"
FIELD_BASE = "base"
FIELD_LABELS = "labels"
FIELD_NUMBER = "number"
FIELD_CREATED_AT = "created_at"
FIELD_UPDATED_AT = "updated_at"
FIELD_URL = "html_url"
FIELD_WORKFLOW_RUNS = "workflow_runs"
FIELD_WORKFLOWS = "workflows"
FIELD_RUN_NUMBER = "run_number"
FIELD_JOBS = "jobs"
FIELD_STEPS = "steps"
#: Per-job attempt number, returned by the workflow-jobs endpoints. Reported by `get-jobs` when a
#: listing spans more than one attempt, so two rows with the same job name are distinguishable (#254).
FIELD_RUN_ATTEMPT = "run_attempt"

#: Values for the workflow-jobs `filter` query parameter. Per the GitHub REST docs, `latest` "returns
#: jobs from the most recent execution of the workflow run" and `all` "returns all jobs for a workflow
#: run, including from old executions"; `latest` is the API DEFAULT. `get-jobs` passes one of these
#: explicitly so the lossy behaviour is never inherited by omission (#254).
JOBS_FILTER_LATEST = "latest"
JOBS_FILTER_ALL = "all"
FIELD_STARTED_AT = "started_at"
FIELD_COMPLETED_AT = "completed_at"
FIELD_SHA = "sha"
FIELD_REF = "ref"
FIELD_MERGED = "merged"
FIELD_MERGEABLE = "mergeable"
FIELD_MERGEABLE_STATE = "mergeable_state"
FIELD_EVENT = "event"
FIELD_MERGE_METHOD = "merge_method"
FIELD_COMMIT_MESSAGE = "commit_message"
FIELD_CHECK_RUNS = "check_runs"
FIELD_TOTAL_COUNT = "total_count"
FIELD_STATUSES = "statuses"
FIELD_CONTEXT = "context"
FIELD_DESCRIPTION = "description"
FIELD_ISSUE_ID = "issue_id"
FIELD_SUB_ISSUE_ID = "sub_issue_id"
FIELD_ASSIGNEES = "assignees"
FIELD_LOGIN = "login"
# Repository-variable and workflow-dispatch payload fields (issue #286). The capacity ladder in
# `.claude/rules/remote-ci-must-pass.md` requires READING a CI-mode repository variable (Rung 1's
# cheapest check) and DISPATCHING a workflow through THIS wrapper — `gh` is forbidden — and neither
# capability existed, so Rung 1 was unreachable for want of a subcommand rather than for want of
# infrastructure. That rule says so itself: "No variable subcommand exists in
# `scripts/github_wrapper.py` as of writing … so this check requires EXTENDING the wrapper first".
FIELD_VALUE = "value"
FIELD_WORKFLOW_RUN_ID = "workflow_run_id"
# The repository artifact listing (docs.github.com/en/rest/actions/artifacts), read by `list-repo-artifacts` and
# `delete-artifacts`.
FIELD_ARTIFACTS = "artifacts"
FIELD_SIZE_IN_BYTES = "size_in_bytes"
FIELD_EXPIRED = "expired"
FIELD_WORKFLOW_RUN = "workflow_run"
ARTIFACT_STATE_LIVE = "live"
ARTIFACT_STATE_EXPIRED = "expired"
#: WHERE a job ran. The workflow-jobs endpoint returns the assigned runner's name and the labels the
#: job requested; both are the capacity ladder's structural discriminators for a relocation, and
#: neither was previously surfaced by any subcommand.
FIELD_RUNNER_NAME = "runner_name"

# Release-asset fields (issue #432). Named, never literal at a call site.
FIELD_TAG_NAME = "tag_name"
FIELD_UPLOAD_URL = "upload_url"
FIELD_ASSETS = "assets"
FIELD_SIZE = "size"
FIELD_DRAFT = "draft"
FIELD_PRERELEASE = "prerelease"
FIELD_VISIBILITY = "visibility"
FIELD_PRIVATE = "private"
FIELD_CONTENT = "content"
FIELD_MESSAGE = "message"
FIELD_COMMIT = "commit"
FIELD_BROWSER_DOWNLOAD_URL = "browser_download_url"
#: The release field `immutable` (the release schema's "`immutable`: boolean") and the asset field `digest`, which
#: GitHub computes and the asset schema documents as "required, string or null"; `get-release` reports both (#509).
FIELD_IMMUTABLE = "immutable"
FIELD_DIGEST = "digest"
#: The release-update field `make_latest`, and the two values `set-release-notes` sends in it. The Update endpoint
#: documents it "Default: `true`", so a PATCH that left it out would make the release it rewrites the latest one: the
#: value is always sent, `true` if and only if the release is `--expected-latest` (E5.3 step 5; issue #509).
FIELD_MAKE_LATEST = "make_latest"
MAKE_LATEST_TRUE = "true"
MAKE_LATEST_FALSE = "false"
#: The release-create field `target_commitish`, which "determines where the Git tag is created from"; the one
#: create field `create-draft-release` sends beyond `set-release-notes`' and `_resolve_or_create_release`'s (#702).
FIELD_TARGET_COMMITISH = "target_commitish"
#: The Contents API file object's `encoding` and `type` fields, and the one value of each that a file object a Contents
#: read accepts carries (E5.12; issue #509).
FIELD_ENCODING = "encoding"
FIELD_TYPE = "type"
CONTENT_ENCODING_BASE64 = "base64"
CONTENT_KIND_FILE = "file"
#: The Contents API file object's `path`, which `get-file` prints with the object's `sha` and `size` (E5.6; issue #509).
FIELD_PATH = "path"
#: A read confirm's two verdict lines (issue #509): the match line, which one space and the digest follow, and the
#: mismatch line.
CONFIRM_READ_BODY_MATCH = "CONFIRM-READ BODY : match"
CONFIRM_READ_BODY_MISMATCH = "CONFIRM-READ BODY : MISMATCH"

#: Subject-issue and Entry payload fields read only by ``get-issue-dependencies``. ``state_reason`` is
#: documented "string or null" (enum: completed, reopened, not_planned, duplicate, null), so it is read
#: with ``.get`` rather than indexed like the required ``state`` above. Each Summary Object is read from
#: the subject issue's payload AND printed under the same name, so ONE constant per summary serves both
#: sites and the printed key can never drift from the key that was read. ``FIELD_SUB_ISSUES_SUMMARY``
#: names a COUNT OBJECT while ``KEY_SUB_ISSUES`` below names a LIST of Entries — names differing by a
#: suffix, things differing by kind; ``_dependency_entry``'s docstring carries both near-collisions.
FIELD_STATE_REASON = "state_reason"
FIELD_ISSUE_DEPENDENCIES_SUMMARY = "issue_dependencies_summary"
FIELD_SUB_ISSUES_SUMMARY = "sub_issues_summary"

#: This repository's default branch, named once (coding-standards rule 1). A `workflow_dispatch` is
#: only REGISTERED from the default branch, so it is also the ref a dispatch normally targets.
BRANCH_MAIN_DEFAULT = "main"

#: The only ``state`` value for which an issue can be claimed at all — a closed issue is nobody's
#: outstanding work, so ``claim-check`` reports it as "nothing to claim" rather than "unclaimed".
ISSUE_STATE_OPEN = "open"

#: Keys of the ``claim-check`` verdict object printed on stdout.
KEY_CLAIMED = "claimed"
KEY_EXIT_CODE = "exit_code"

#: Key of the ``start-issue`` verdict object. It is the load-bearing one: it is printed ``True``
#: ONLY when a FRESH re-read confirmed that both the label and the assignment actually landed, so a
#: caller reading it is reading observed remote state rather than the wrapper's own intent.
KEY_VERIFIED = "verified"
#: Key of the ``release-issue`` verdict object listing the assignee logins the release dropped.
KEY_UNASSIGNED = "unassigned"

#: Keys of the three Entry Lists ``get-issue-dependencies`` PRINTS. Output-only: those three endpoints
#: return bare arrays, so these names are never read from a payload — which is why they are ``KEY_``
#: while the two Summary Object names above are ``FIELD_``. They double as the ``list_key`` argument
#: ``_dependency_entry`` names in its diagnostics, which is still not a payload read. NOTE that
#: ``blocked_by`` and ``blocking`` each name TWO different things in that Command's output; see
#: ``_dependency_entry``'s docstring.
KEY_BLOCKED_BY = "blocked_by"
KEY_BLOCKING = "blocking"
KEY_SUB_ISSUES = "sub_issues"

# The canonical "someone is actively working this issue" marker. A worker CLAIMS an issue by
# ADDING this label (the claim-issue subcommand) before starting, and DROPS it (release-issue)
# if it stops without finishing. It is the project's cross-session mutual-exclusion signal — the
# work-discovery subcommands (list-in-progress / list-available) partition open issues by its
# presence — so its spelling MUST stay stable and match the label configured on the repo. See the
# "Worker protocol" section of the module docstring for the claim -> work -> release/close flow.
LABEL_IN_PROGRESS = "in-progress"

# --- Process exit statuses (a CONTRACT with .claude/hooks/gate_claim.py) ---
#: Normal success. Also the verdict "this issue is claimed, or is not open" from ``claim-check``.
EXIT_OK = 0
#: ``claim-check``'s ONE positive finding: the issue is OPEN and NOT claimed by anybody. The
#: claim-before-worktree PreToolUse gate blocks the worktree creation on EXACTLY this status and
#: fails OPEN on every other one, so the number is load-bearing and must not be changed.
EXIT_OPEN_AND_UNCLAIMED = 3

# --- wait-run (the framework's REQUIRED blocking wait; see its usage line above) ---
#: ``wait-run`` verdicts besides ``EXIT_OK`` (the run concluded ``success``): it concluded anything else;
#: the timeout elapsed before it completed. Deliberately NOT 1/2/3: 1 is this wrapper's API-error exit
#: (``main``), 2 is a usage or credential error, 3 is ``claim-check``'s "open and unclaimed", so a caller
#: that saw 1 could not tell "the run failed" from "the API call failed". The framework's template fixes
#: these numbers.
EXIT_WAIT_NOT_SUCCESS = 10
EXIT_WAIT_TIMEOUT = 11
RUN_STATUS_COMPLETED = "completed"
RUN_CONCLUSION_SUCCESS = "success"
WAIT_RUN_DEFAULT_TIMEOUT_SECONDS = 3600
WAIT_RUN_DEFAULT_INTERVAL_SECONDS = 30
KEY_RUN_ID = "run_id"
KEY_TIMEOUT_SECONDS = "timeout_seconds"
#: The clock ``wait-run`` uses, and the sleep ``wait-run`` and ``require-newest-trunk-run`` use (the latter once, after
#: it cancels its own run; issue #1266), as module seams so their tests never really wait.
_monotonic = time.monotonic
_sleep = time.sleep

# --- require-green-deploy (the stage and prod legs' admission proof; issue #908, design D6) ---
#: The workflow-run fields a Green Deploy is judged on besides `path`, `event`, `status` and `conclusion` (named
#: above): the commit, its branch, and the `head_repository` object whose `full_name` is the `owner/repo` it came from.
FIELD_HEAD_SHA = "head_sha"
FIELD_HEAD_BRANCH = "head_branch"
FIELD_HEAD_REPOSITORY = "head_repository"
FIELD_FULL_NAME = "full_name"
#: A run's Run Name, which `--by-run-name` judges in place of `head_sha` (issue #1036, design D3; issue #1266, design
#: D6): a `Deploy stage` or `Deploy dev` run, started by `workflow_run`, has as its `head_sha` its `github.sha`, the
#: default branch's last commit, not the commit it deployed.
FIELD_DISPLAY_TITLE = "display_title"
#: The Stage Run Name of a commit, formatted with its full sha as `sha`: a second spelling of `deploy-stage.yml`'s
#: `run-name:`, with `{sha}` in place of its `${{ github.event.workflow_run.display_title }}`, the dev run's title,
#: which names the commit dev deployed (issue #1266, design D6), pinned to it by test/ci/test_deploy_leg_workflows.py
#: (issue #1036, design D2). Spelled here, not imported, because the wrapper imports nothing from `scripts/`, `src/` or
#: `cdk/` and loads on the bare interpreter.
STAGE_RUN_NAME_TEMPLATE = "Deploy stage {sha}"
#: The Dev Run Name of a commit, formatted with its full sha as `sha`: a second spelling of `deploy-dev.yml`'s
#: `run-name:`, with `{sha}` in place of its `${{ github.event.workflow_run.head_sha }}`, the commit its jobs check out,
#: pinned to it by test/ci/test_deploy_dev_workflow.py (issue #1266, design D5), and spelled here for the reason
#: `STAGE_RUN_NAME_TEMPLATE` is.
DEV_RUN_NAME_TEMPLATE = "{sha}"
#: The `event` of a run a `workflow_run` trigger started: `Deploy dev`'s, which the Stage Leg admits on, and `Deploy
#: stage`'s, which the Prod Leg admits on.
EVENT_WORKFLOW_RUN = "workflow_run"
#: The directory a run's `path` names its workflow file under.
WORKFLOWS_DIRECTORY = ".github/workflows/"
#: A `--workflow` value: one workflow file name, ASCII letters, digits, `.`, `_` or `-`, ending `.yml` or `.yaml`.
#: Applied with `fullmatch` before any request, so a trailing newline or a `/` is refused; it is interpolated into the
#: listing's path and into the `path` a run must carry.
WORKFLOW_FILE_PATTERN = re.compile(r"[A-Za-z0-9._-]+\.ya?ml")
#: A `--run-id` value: ASCII digits only, applied with `fullmatch`. Never `\d` or `int()`, which admit other scripts'
#: digits, an underscore, a sign or surrounding whitespace.
RUN_ID_PATTERN = re.compile(r"[0-9]+")
#: The refusal of a `--head-sha` that does not fullmatch `COMMITISH_PATTERN`, shared by `require-green-deploy` and
#: `require-newest-trunk-run` (issue #1266, design D3 "Input checks"): it names the option and its shape, never the
#: value.
HEAD_SHA_REFUSAL = (
    "Refusing the --head-sha value: it must be a full commit sha, 40 lowercase hex characters. Nothing has been "
    "requested."
)
#: The job ids of the leg workflows: `deploy-dev.yml`'s Admission Job (issue #1266, design D2), Deploy Job, Openings
#: Job and Sync Job, and `deploy-stage.yml`'s Deploy Job and Sync Job (issue #1059, design D7). No job of either file
#: declares `name:`, so the Actions API lists each job by its id.
JOB_ADMISSION = "admission"
JOB_DEPLOY = "deploy"
JOB_OPENINGS_HARNESS = "openings-harness"
JOB_SYNC_HARNESS = "sync-harness"
#: Each workflow the legs' Guards name, mapped to the job ids its latest attempt must list, each once and concluded
#: `success` (issue #1052, design D8; DL-003): `deploy-dev.yml`'s `admission`, `deploy`, `openings-harness` and
#: `sync-harness` (issue #1266, design D5), and `deploy-stage.yml`'s `deploy` and `sync-harness` (issue #1059, design
#: D7). A second spelling of those files' `jobs:`, which test/ci/test_wrapper_require_green_deploy.py holds equal to
#: them: the wrapper runs in the Guard step before any install, on the bare interpreter, which has no YAML reader. A
#: `--workflow` that is no key is refused before any request (DL-004); the keys' order is the order that refusal lists
#: them in.
GREEN_DEPLOY_JOBS: dict[str, tuple[str, ...]] = {
    "deploy-dev.yml": (JOB_ADMISSION, JOB_DEPLOY, JOB_OPENINGS_HARNESS, JOB_SYNC_HARNESS),
    "deploy-stage.yml": (JOB_DEPLOY, JOB_SYNC_HARNESS),
}
#: Each workflow of `GREEN_DEPLOY_JOBS`, in its keys' order, mapped to the template of its Run Name, which
#: `--by-run-name` requires a run's `display_title` to equal, formatted with `--head-sha` (issue #1266, design D5, D6).
RUN_NAME_TEMPLATES: dict[str, str] = {
    "deploy-dev.yml": DEV_RUN_NAME_TEMPLATE,
    "deploy-stage.yml": STAGE_RUN_NAME_TEMPLATE,
}
#: The names a refusal gives the two checks that are not one run field: a listed run carries no integer `id`, and its
#: latest attempt does not list exactly the workflow's jobs in `GREEN_DEPLOY_JOBS`, each named once and concluded
#: `success`.
CHECK_RUN_ID = "id"
CHECK_GREEN_JOBS = "jobs"
#: The argparse `dest` of `--token-stdin`, read by `main` before its dispatch with a `False` default, because only
#: `require-green-deploy`, `require-newest-trunk-run`, `list-issues` and `create-issue` register the option.
DEST_STDIN_CREDENTIAL = "token_stdin"
#: The two subcommands that read a PUBLIC repository with no credential (issue #509; issue #1248, design C6), each named
#: once for its parser entry, its `DISPATCH` entry and `CREDENTIAL_FREE_COMMANDS`.
CMD_DOWNLOAD_PUBLIC_ASSET = "download-public-asset"
CMD_GET_PUBLIC_LATEST_RELEASE = "get-public-latest-release"
#: The commands `main` loads no token for (issue #1248, design C6): each sends its one request with no credential, so
#: the Release Check's `verify` job, which holds none, can run them. Every other command loads a token as before.
CREDENTIAL_FREE_COMMANDS: frozenset[str] = frozenset({CMD_DOWNLOAD_PUBLIC_ASSET, CMD_GET_PUBLIC_LATEST_RELEASE})
#: What `main` hands the handler of a command of `CREDENTIAL_FREE_COMMANDS` as its token: nothing, which the handler
#: deletes unread.
NO_CREDENTIAL = ""

# --- require-newest-trunk-run (the dev leg's Admission Job; issue #1266, design D3) ---
#: The trunk workflow, whose successful push runs on `BRANCH_MAIN_DEFAULT` are Trunk Runs, and a push run's `event`.
TRUNK_WORKFLOW = "ci.yml"
EVENT_PUSH = "push"
#: A run's `created_at` as the Actions API returns it, `YYYY-MM-DDTHH:MM:SSZ`, applied with `fullmatch` before the
#: value is quoted into the listing's `created` qualifier.
CREATED_AT_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
#: The names a refusal gives the Triggering Run's two checks that are not a comparison with one value: an integer
#: `run_number`, and a `created_at` of the shape `CREATED_AT_PATTERN` fullmatches.
CHECK_RUN_NUMBER = "run_number"
CHECK_CREATED_AT = "created_at"
#: The search syntax's "created on or after" qualifier, prefixed to the Triggering Run's `created_at` in the listing.
CREATED_ON_OR_AFTER = ">="
#: How long a Superseded run waits, once, after it requested its own cancellation: five minutes, below the Admission
#: Job's `timeout-minutes`, which test/ci/test_deploy_dev_workflow.py holds above it, so the wait ends before the job's
#: limit and the refusal that follows fails the job if the cancellation has not landed.
SELF_CANCEL_WAIT_SECONDS = 300

# --- checklist / reopen-issue (the task-item gate's two REQUIRED primitives) ---
#: One GitHub task-list item: a ``-`` or ``*`` bullet, ``[ ]`` or ``[x]``, then the item text.
CHECKLIST_ITEM_RE = re.compile(r"^(?P<lead>\s*[-*]\s+\[)(?P<mark>[ xX])(?P<tail>\]\s+)(?P<text>.*?)\s*$")
CHECK_MARK_TICKED = "x"
CHECK_MARK_UNTICKED = " "
KEY_TICKED = "ticked"
KEY_TOTAL = "total"
KEY_UNTICKED = "unticked"
KEY_CHANGED = "changed"
KEY_ISSUE = "issue"
KEY_ITEM = "item"

# --- Subcommand names used by BOTH the parser and the dispatch tables ---
#: The flat, project-convention probe name (this wrapper's own naming style).
CMD_CLAIM_CHECK = "claim-check"
#: The nested claim-trio group. The claim gate hook is synced verbatim from the upstream standard
#: and invokes ``<wrapper> issue claim-check <N>``, so this wrapper accepts that argv shape too
#: rather than the hook being forked locally (a local hook edit would be reverted by the next sync,
#: silently turning the gate back into a no-op).
CMD_ISSUE_GROUP = "issue"
CMD_ISSUE_GROUP_START = "start"
CMD_ISSUE_GROUP_RELEASE = "release"
#: The FLAT GitHub spelling of the deterministic claim. The standard mandates it for GitHub hosts
#: ("GitHub — the same as ``start-issue``/``release-issue``/``claim-check``", Part 5.3), and five
#: installed artifacts instruct agents to run exactly this argv: ``.claude/rules/issue-tracking.md``,
#: ``.claude/agents/issue-work-orchestrator.md`` (twice), ``.claude/commands/work-issue.md`` and
#: ``.claude/commands/auto-work.md``. It is an alias of ``issue start`` — the SAME handler — so a
#: rule that cites either spelling describes one behaviour.
CMD_START_ISSUE = "start-issue"
#: The delivery verbs (framework 5a18930, `.claude/docs/delivery.md`): the same spelling on every host, each
#: DELEGATING to the merge steward, where the queue's rules live, with this wrapper's token on its standard input.
CMD_ENQUEUE_PR = "enqueue-pr"
CMD_DEQUEUE_PR = "dequeue-pr"
CMD_QUEUE_STATUS = "queue-status"
MERGE_STEWARD_SCRIPT = Path(__file__).resolve().parent / "merge_steward.py"
STEWARD_STDIN_OPTION = "--token-stdin"
STEWARD_ENQUEUE = "enqueue"
STEWARD_DEQUEUE = "dequeue"
STEWARD_STATUS = "status"
STEWARD_REASON = "--reason"
STEWARD_JSON = "--json"
#: The additive label/assignee primitives. One constant serves BOTH the flat and the nested spelling
#: of each (as ``CMD_CLAIM_CHECK`` already does), so the two can never advertise different verbs.
CMD_LABEL_ADD = "label-add"
CMD_LABEL_REMOVE = "label-remove"
CMD_ASSIGN = "assign"
#: argparse ``dest`` holding the verb chosen inside the nested group.
DEST_ISSUE_SUBCOMMAND = "issue_subcommand"
#: Shared by the flat subcommand and its nested alias so the two can never advertise different
#: contracts. The exit statuses are spelled out because the gate keys on them numerically.
CLAIM_CHECK_HELP = (
    "READ-ONLY claim probe (writes nothing): exit 0 = claimed or not open, exit 3 = OPEN and "
    "UNCLAIMED, exit 1 = API error. The claim-before-worktree gate blocks ONLY on exit 3."
)
#: Shared by the flat ``start-issue`` and the nested ``issue start`` for the same reason.
START_ISSUE_HELP = (
    "THE claim: idempotent AND fail-closed. Refuses a non-open or foreign-held issue, ADDS the "
    "'in-progress' label additively, assigns you, then RE-READS to verify both landed (exit 1 if not)."
)
LABEL_ADD_HELP = (
    "ADD labels without touching the others (POST .../labels). Use this instead of "
    "'update-issue --labels', whose 'labels' field REPLACES the whole set and drops siblings."
)
LABEL_REMOVE_HELP = "REMOVE exactly one label, leaving every other label intact (DELETE .../labels/{name})"
ASSIGN_HELP = "Set or clear the assignee via the additive assignees endpoints (--me / --user LOGIN / --unassign)"

HEADER_ACCEPT = "Accept"
HEADER_AUTH = "Authorization"
HEADER_UA = "User-Agent"
HEADER_API_VERSION = "X-GitHub-Api-Version"
# The fifth request header, previously the module's ONE header attached by a string LITERAL (issue #469):
# measured by AST walk, 24 of the 25 add_header call sites pass a HEADER_* constant and exactly one did not.
HEADER_CONTENT_TYPE = "Content-Type"

ACCEPT_JSON = "application/vnd.github+json"
CONTENT_TYPE_JSON = "application/json"
API_VERSION = "2022-11-28"
# The issue-dependencies (blocked_by/blocking) and sub-issues endpoints are documented only
# under the newer dated version (https://docs.github.com/en/rest/issues/issue-dependencies,
# .../sub-issues). Pin those specific calls to it via a per-request override so the other
# commands keep their long-stable 2022-11-28 behavior unchanged.
API_VERSION_DEPENDENCIES = "2026-03-10"
USER_AGENT = "chess-github-wrapper/1.0"

API_BASE = "https://api.github.com"
#: The web host a public repository serves its release assets from, at `/{owner}/{repo}/releases/download/{tag}/{name}`
#: to an anonymous client, which is how `download-public-asset` reads one back (issue #509).
WEB_BASE = "https://github.com"

#: Release assets upload to a DIFFERENT host from the API, addressed through the release object's
#: hypermedia `upload_url` template. Asserted rather than assumed: that template is server-supplied
#: and the request built from it carries a Bearer PAT.
UPLOAD_HOST_PREFIX = "https://uploads.github.com/"

#: The PRODUCT release namespace `.github/workflows/release.yml` triggers on. A publish tag matching
#: this would fire all four release jobs, and a PAT-authenticated push is NOT suppressed the way a
#: `GITHUB_TOKEN` one is — so this is a refusal, not a warning.
SEMVER_TAG_PATTERN = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+")

#: The shape an engine-asset tag takes, quoted in the refusal so the remedy is in the message.
ASSET_TAG_NAMESPACE_EXAMPLE = "engine-assets-2026-09-19"

#: The body a created asset release carries. Says what the release is FOR, because a bare tag in a
#: repository's release list is indistinguishable from an abandoned experiment.
ASSET_RELEASE_BODY = (
    "Engine artefacts this project produces rather than fetches. NOT a product release: the tag is "
    "deliberately outside the `v*.*.*` namespace so it does not trigger the release pipeline. Each "
    "asset is pinned by sha256 in the engine manifest that declares it."
)

CONTENT_TYPE_OCTET_STREAM = "application/octet-stream"

#: An `owner/repo` slug, for the release subcommands that may address a DIFFERENT repository from the
#: one this wrapper is run in. Deliberately strict — the value is interpolated into an API path, so a
#: slug carrying a slash, a query or a traversal segment would address something else entirely.
#: Applied with `fullmatch`, so a trailing newline is refused; the two lookaheads refuse an owner or a
#: repository that is `.` or `..`, a dot segment that would make `/repos/<slug>/...` address another endpoint.
REPO_SLUG_PATTERN = re.compile(r"(?!\.{1,2}/)[A-Za-z0-9._-]+/(?!\.{1,2}\Z)[A-Za-z0-9._-]+")
#: ONE component of a release path, such as a `--tag`: a letter or digit, then letters, digits, `.`, `_` or `-`.
#: Applied with `fullmatch` before any request, because `quote()` keeps `/`, so an unchecked `../../x` would reach a
#: different, credential-carrying endpoint than `/repos/{owner}/{repo}/releases/tags/{quote(tag)}` names.
ASSET_PART_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
#: A `--target-commitish` `create-draft-release` accepts: a full commit sha, 40 lowercase hex characters, applied with
#: `fullmatch` so that a trailing newline is refused, and never a branch name, whose commit can move (issue #702).
COMMITISH_PATTERN = re.compile(r"[0-9a-f]{40}")
CREDENTIALS_FILE = Path("credentials") / "github-pat.txt"
PLACEHOLDER = "PASTE_YOUR_GITHUB_PAT_HERE"

# Shared --body-file help text. Long markdown bodies (evidence tables, fenced command output,
# backticks, '$', '!') are mangled by shell expansion when passed via --body on a command line;
# reading from a file posts exactly the bytes on disk. Mutually exclusive with --body.
BODY_FILE_HELP = "Path to a UTF-8 markdown file holding the body (avoids shell mangling; not with --body)"
TARGET_REPO_HELP = (
    "Address a DIFFERENT repository as owner/repo. Needed because a produced engine artefact cannot "
    "be served from a PRIVATE repository: its /releases/download/ path answers 404 to the "
    "unauthenticated fetch every consumer performs. Defaults to this checkout's origin"
)
#: The help of the `--target-repo` each of the three subcommands issue #509 adds REQUIRES. They are new, so nothing
#: depends on a default, and the shared help above ends by naming one.
TARGET_REPO_REQUIRED_HELP = (
    "REQUIRED, with no default: the repository to address, as owner/repo, shape-checked before any request"
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


#: What an operator can DO about the one redirect GitHub documents for these endpoints — a repository
#: rename or transfer. Named rather than inlined so the refusal tests assert against THIS value instead
#: of a second copy of the sentence, which could drift and still pass.
REDIRECT_REFUSAL_ADVICE = (
    "If this repository was renamed or transferred, update the remote with "
    "`git remote set-url origin <new-url>` and retry."
)

#: The `Location`/`URI` header names, per `.claude/rules/coding-standards.md` item 1 — no literal at a
#: call site. `email.message.Message.get` is case-insensitive, so the lowercase spelling is exact.
HEADER_LOCATION = "location"
HEADER_URI = "uri"

#: Bound on the RENDERED form of an upstream-controlled value — repr's OUTPUT, not its input (AC-2.8).
MAX_LOGGED_TARGET_CHARS = 200

#: Appended when the rendered form is clipped. Named so the arm asserts the exact bound
#: `MAX_LOGGED_TARGET_CHARS + len(ELISION_MARKER)` rather than a second copy of the number.
ELISION_MARKER = "...[truncated]"

#: The two `path` prefixes the Tier A helpers' root-relative guard is expressed on, per
#: `.claude/rules/coding-standards.md` item 1. The guard is on the INPUT `path` and never on the resolved
#: url: `url.startswith(API_BASE)` would admit `https://api.github.com.evil.test/x`.
PATH_ROOT = "/"
PATH_PROTOCOL_RELATIVE = "//"


def _render_untrusted(value: object) -> str:
    """Render an upstream-controlled value for a message: coerced to text, fully escaped, then bounded.

    `repr()` escapes every codepoint `str.isprintable()` rejects — all C0/C1 controls, DEL, and the Cf
    bidi-control class. That is not an observation about CPython's behaviour but the SPECIFIED contract,
    whose normative home is the library reference: `str.isprintable()` states it directly and carries no
    "Changed in version" note — "Nonprintable characters are those in group Separator or Other (Z or C),
    except the ASCII space." PEP 3138 is the RATIONALE and spells the same set as the categories Cc, Cf,
    Cs, Co, Cn, Zl, Zp and `Zs` OTHER THAN ASCII space (U+0020) — measured, of all Zs codepoints exactly
    ONE (U+0020) is emitted verbatim and 16 are escaped. Either spelling is exactly AC-2.8's predicate,
    which IS `str.isprintable()` and therefore carries the same carve-out. This is MANDATORY rather than
    belt-and-braces because refusing at the Refusal Entry Point means the RAW header value is what reaches
    the message: measured, it still carries `0x9 0xa 0xd` from an obs-folded header, `0x1b` from an ANSI CSI
    sequence, and `0x7 0x8 0x7f`, where the value reaching `redirect_request` had already been stripped and
    percent-encoded by the stdlib (`evidence/T3-choke-point-measurement.txt` LEG 4a vs 4b). The stream this
    lands on is configured with `errors="replace"`, which removes the `backslashreplace` escaping that would
    otherwise have rendered a control byte inert.

    ESCAPE FIRST, CLIP AFTER — the order is load-bearing and the reverse order is not a bound at all.
    Clipping first constrains repr's INPUT; repr then expands each escaped codepoint to `\\xNN` (4 chars),
    `\\uNNNN` (6) or `\\UNNNNNNNN` (10), so the emitted length measured 216 for plain ASCII, 802 for a C0
    control, 1202 for U+202E and 2002 for U+E0001 — 10.01x the named constant
    (`evidence/C3-cycle3-measurements.txt` LEG 1). In this order the emitted length is exactly
    `MAX_LOGGED_TARGET_CHARS + len(ELISION_MARKER)` for every one of those classes. A clip can land
    mid-escape. That is safe for a reason stronger than a sample: a clip can only ever leave a PREFIX of
    one of the SEVEN escape token shapes repr emits (``\\\\``, ``\\n``, ``\\r``, ``\\t``, ``\\xNN``,
    ``\\uNNNN``, ``\\UNNNNNNNN``), and every prefix of every one of them is drawn from
    ``0123456789U\\abcdefnrtux`` — all printable ASCII. Measured EXHAUSTIVELY over all 1,114,112
    codepoints: 154,809 are emitted verbatim, 959,303 are escaped, the escaped ones collapse to exactly
    those seven shapes, and every prefix of every one of the 959,303 distinct tokens — 9,552,858 prefix
    cells — yields ZERO offenders. So AC-2.8's first clause cannot be violated by a clip, for any input,
    on any interpreter: it is a decision procedure over all inputs, not a sample
    (``evidence/C4-renderer-exhaustive-proof.txt``, reproduced by ``evidence/probe_c4_repr_proof.py``).

    The lost closing delimiter on the clip branch is a FEATURE, not a defect to repair: absence of the
    closing quote is an unforgeable truncation signal, so an upstream can neither fake a truncation nor
    disguise one by ending its value with the marker text.

    NON-``str`` INPUTS ARE COERCED, and the ``str()`` call is not defensive clutter. ``repr()`` is total
    over every object, so escaping first turned what used to be a loud ``TypeError`` into a silent
    ``<email.header.Header object at 0x...>`` — a heap-address leak that ALSO defeats AC-2.3, since the
    message then names no target at all. Measured UNREACHABLE on the production path — ``http.client``
    decodes header bytes as iso-8859-1 before ``email.parser`` sees them, which is total over ``0x00``
    to ``0xFF`` and produces no surrogate — and coerced anyway because the failure is silent rather than
    loud.
    """
    rendered = repr(value if isinstance(value, str) else str(value))
    if len(rendered) <= MAX_LOGGED_TARGET_CHARS:
        return rendered
    return rendered[:MAX_LOGGED_TARGET_CHARS] + ELISION_MARKER


class GitHubAPIError(Exception):
    """Raised when the GitHub API returns a non-success response."""

    def __init__(self, message: str, status_code: int | None = None, details: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.details = details


class GitHubRedirectRefusedError(GitHubAPIError):
    """A credential-carrying API request received a redirect, and the wrapper refused to follow it.

    Deliberately a ``GitHubAPIError`` subclass, and deliberately NOT an ``HTTPError``:

    * as a ``GitHubAPIError`` it reaches ``main()``'s existing handler, which logs the message and returns
      1 — no new reporting path is needed;
    * as a NON-``HTTPError`` it passes untouched through the ``except HTTPError`` clauses in
      ``_api_request``, ``_api_status`` and ``_api_request_headers``. That matters most in ``_api_status``,
      which RETURNS ``exc.code`` for an ``HTTPError`` and would otherwise report a refused 301 as an alerts
      *status*.

    It adds no fields: ``GitHubAPIError`` already takes ``status_code`` and ``details=None``, which is the
    whole of what this refusal carries. ``details`` stays ``None`` on purpose — the redirect response body
    is upstream-controlled and ``main()`` logs ``details`` verbatim.
    """


class _NoRedirectHandler(HTTPRedirectHandler):
    """Tier B: follow ONE redirect with the Authorization header stripped — DELIBERATE, not an oversight.

    GitHub's ``/logs`` endpoint returns a 302 to Azure Blob Storage.
    Azure rejects requests that carry a GitHub Authorization header, so we
    must drop it before following the redirect.

    **Following is deliberate here, and it is scoped to the DOWNLOAD helpers** — ``_fetch_log_content``,
    ``_fetch_job_log_content``, ``_fetch_artifact_zip``, ``_fetch_release_asset`` and the credential-free
    ``_fetch_public_download``, which reach this handler only through ``_build_download_opener``. On each the hop
    IS the download: the bytes live on the storage host and nowhere else, so refusing the redirect would break
    ``get-logs``, ``get-job-logs``, ``download-artifact`` and the asset downloads outright. Stripping the header
    before following is what keeps the credential out of that request, and it is also what Azure requires.

    Every other helper carries the PAT to ``api.github.com`` and belongs to Tier A, whose
    ``_RefusingRedirectHandler`` (below) REFUSES every redirect instead. The two handlers are opposite
    policies for opposite tiers: read this one as a policy decision, never as a policy the refusing half
    forgot to apply (``AC-7.3``).
    """

    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> Request | None:
        new_req = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new_req is not None:
            new_req.headers.pop(HEADER_AUTH, None)
            new_req.unredirected_hdrs.pop(HEADER_AUTH, None)
        return new_req


class _RefusingRedirectHandler(HTTPRedirectHandler):
    """Tier A: refuse EVERY redirect on a request that carries the PAT.

    ``HTTPRedirectHandler`` copies every header except ``content-length``/``content-type`` onto the
    redirected request, so the default opener re-sends ``Authorization: Bearer <PAT>`` to whatever host the
    upstream ``Location`` names — measured on 301/302/303/307/308 and on ``http``, ``https`` and ``ftp``
    targets in
    ``.claude/specs/issue-469-wrapper-redirect-policy/evidence/T0-baseline-redirect-measurement.txt``.

    The refusal is installed at the **Refusal Entry Point** — ``http_error_302``, with the other four
    status codes aliased to the same function object — and raises before ANY decision the stdlib would
    otherwise make about the ``Location`` value: before ``urlparse``, before the stdlib's scheme
    allow-list, and before ``quote``/``urljoin``. It DOES read the header, on the line above the
    ``raise``, and only to render it: the raw value is the report, and reading it decides nothing.
    Overriding ``redirect_request`` alone is NOT sufficient and was measured so: a
    disallowed scheme raises ``HTTPError`` from inside ``http_error_302`` without reaching the refusal, and
    a malformed IPv6 literal or a non-latin-1 ``Location`` escapes as ``ValueError`` /
    ``UnicodeEncodeError`` — neither a ``GitHubAPIError`` nor an ``OSError``, so neither is caught anywhere
    in this module or in ``main()`` (``evidence/T3-choke-point-measurement.txt`` LEG 1).

    Contrast ``_NoRedirectHandler`` above, which DOES follow, keeps its override on
    ``redirect_request`` because strip-and-follow WANTS the stdlib's header read and normalisation, and
    must never acquire routing of its own (AC-4.4).
    """

    def http_error_302(self, req: Request, fp: Any, code: int, msg: str, headers: Message) -> Any:
        """Refuse, before any decision the stdlib would otherwise make about the ``Location`` value."""
        del msg  # the status, the original URL and the rendered target are the whole report
        # The stdlib delays closing ``fp`` only because it may become an ``HTTPError``'s body ("Don't close
        # the fp until we are sure that we won't use it with HTTPError"). This refusal never attaches it to
        # anything, so that condition is met. ``fp`` is ``None`` when the handler is driven directly, which
        # is one of the three drives the tests use.
        if fp is not None:
            try:
                fp.close()
            except OSError:
                pass
        raw_target = headers.get(HEADER_LOCATION) or headers.get(HEADER_URI)
        where = (
            f"to {_render_untrusted(value=raw_target)}"
            if raw_target is not None
            else "and the upstream named no location"
        )
        raise GitHubRedirectRefusedError(
            f"Refusing to follow an HTTP {code} redirect for {_render_untrusted(value=req.full_url)} "
            f"{where}: a request carrying the GitHub credential is never redirected. "
            f"{REDIRECT_REFUSAL_ADVICE}",
            status_code=code,
        )

    # ``OpenerDirector.add_handler`` scans ``dir(handler)`` for ``http_error_<n>`` names, so these four
    # aliases register four routes; an un-aliased 308 would inherit the stdlib's own ``http_error_302``.
    http_error_301 = http_error_303 = http_error_307 = http_error_308 = http_error_302

    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Message,
        newurl: str,
    ) -> Request | None:
        """Second layer: no call path on this class may ever produce a redirected ``Request``."""
        del fp, msg, headers
        raise GitHubRedirectRefusedError(
            f"Refusing to follow an HTTP {code} redirect for "
            f"{_render_untrusted(value=req.full_url)} to {_render_untrusted(value=newurl)}: a request "
            f"carrying the GitHub credential is never redirected. {REDIRECT_REFUSAL_ADVICE}",
            status_code=code,
        )


def _build_api_opener() -> OpenerDirector:
    """The opener for every credential-carrying API request: refuse every redirect (Tier A).

    One factory per tier, and the module's only ``build_opener`` call sites, so a helper's tier is a single
    greppable token in its body and a new helper cannot end up on the default opener by omission.
    """
    return build_opener(_RefusingRedirectHandler())


def _build_download_opener() -> OpenerDirector:
    """The opener for the log/artifact downloads: drop the credential, then follow (Tier B).

    The GitHub ``/logs`` and ``/artifacts`` endpoints answer 302 to Azure Blob Storage, and Azure REJECTS a
    request that carries a GitHub ``Authorization`` header, so this leg must keep dropping the header and
    following. Behaviour is identical to the three inline ``build_opener(_NoRedirectHandler())`` expressions
    this replaces.
    """
    return build_opener(_NoRedirectHandler())


def _one_token(*, data: bytes, refusal: str) -> str:
    """The token `data` holds, its outer whitespace stripped: the one validator of every token source `main` reads.

    `data` holds one token when it decodes as UTF-8 and, its outer whitespace stripped, holds no whitespace, no
    non-printable and no non-ASCII character, so that a second pasted line or a pair of smart quotes never reaches a
    request's `Authorization` header (E5.28; issue #509). Anything else raises `GitHubAPIError(refusal)`, a message the
    caller writes to name its source and none of `data`; the decode error is raised again `from None`, because its own
    message names a byte and its position. An empty `data` gives the empty string, which each caller refuses in its own
    words. Shared by `_load_token`'s file and `--token-stdin`'s standard input (issue #908, design D6 "Token").
    """
    try:
        token = data.decode("utf-8").strip()
    except UnicodeDecodeError:
        raise GitHubAPIError(refusal) from None
    if any(ch.isspace() or not ch.isprintable() or not ch.isascii() for ch in token):
        raise GitHubAPIError(refusal)
    return token


def _load_token() -> str:
    """The token in `CREDENTIALS_FILE`, refusing a file that is missing, holds the placeholder or is not one token.

    Whether the file is one token is `_one_token`'s judgment. Each refusal names the file and none of its contents.
    """
    if not CREDENTIALS_FILE.exists():
        raise GitHubAPIError(
            f"Missing credentials file: {CREDENTIALS_FILE}. Create it and paste your GitHub PAT (one line)."
        )
    not_one_token_message = (
        f"{CREDENTIALS_FILE} does not hold a single token. Paste only your GitHub PAT, on one line, into this file."
    )
    token = _one_token(data=CREDENTIALS_FILE.read_bytes(), refusal=not_one_token_message)
    if not token or token == PLACEHOLDER:
        raise GitHubAPIError(
            f"{CREDENTIALS_FILE} still contains the placeholder. Paste a real GitHub PAT into this file."
        )
    return token


def _load_stdin_token() -> str:
    """The token on the WHOLE of standard input, for `--token-stdin` (issue #908, design D6 "Token").

    A deploy leg pipes its job token in with `printf '%s'`, so no credential file exists on the runner and the token is
    never on a command line. Read as bytes, so no newline translation or locale decoding happens before `_one_token`
    judges it; an empty input is refused too. Each refusal names "standard input" and none of what it holds, and the
    token is never logged.
    """
    stream = getattr(sys.stdin, "buffer", None)
    if stream is None:
        raise GitHubAPIError("The standard input cannot be read as bytes, so --token-stdin has no token to read.")
    token = _one_token(
        data=stream.read(),
        refusal="The standard input does not hold a single token. Pipe only the job token, on one line, into it.",
    )
    if not token:
        raise GitHubAPIError("The standard input holds no token. Pipe the job token into it for --token-stdin.")
    return token


def _detect_repo() -> tuple[str, str]:
    """Parse .git/config to extract (owner, repo) from the origin URL."""
    cfg_path = Path(".git") / "config"
    if not cfg_path.exists():
        raise GitHubAPIError("Not a git repository (no .git/config found).")
    parser = configparser.ConfigParser()
    parser.read(cfg_path)
    section = 'remote "origin"'
    if section not in parser:
        raise GitHubAPIError("No 'origin' remote configured in .git/config.")
    url = parser[section]["url"]
    match = re.search(r"github\.com[:/]([^/]+)/([^/.]+)(?:\.git)?/?$", url)
    if not match:
        raise GitHubAPIError(f"Could not parse GitHub owner/repo from origin URL: {url}")
    return match.group(1), match.group(2)


def _http_error_details(*, exc: HTTPError) -> Any:
    """GitHub's error body of `exc`, parsed as JSON, or `None` when it cannot be read or parsed (E5.27; issue #509).

    The `details` of the `GitHubAPIError` that `_api_request` and `_fetch_release_asset` raise for an `HTTPError`, which
    `main()` logs, so that an upload's 422 carries GitHub's reason, such as an asset name the release already has. It
    is the one home of the parse both clauses share. The catch is `Exception`, as the inline parse it replaces had it:
    a body that is not JSON, one cut short, whose read raises `http.client.IncompleteRead`, and one whose read times
    out each give `None`, so that no failure to read the body replaces the error it belongs to.
    """
    try:
        return json.loads(exc.read().decode("utf-8"))
    except Exception:
        return None


def _api_request(
    *,
    method: str,
    path: str,
    token: str,
    body: dict[str, Any] | None = None,
    raw: bool = False,
    api_version: str = API_VERSION,
    response_headers: dict[str, str] | None = None,
) -> Any:
    """Send one API request and return its decoded body (``raw``: its bytes; an empty body: ``None``).

    ``response_headers``, when given, receives the response's headers with lower-cased names: the deliveries listing
    pages by a cursor only its ``Link`` header carries (issue #1257), and reading it here keeps this the one request
    builder rather than a copy of it.
    """
    if not path.startswith(PATH_ROOT) or path.startswith(PATH_PROTOCOL_RELATIVE):
        raise GitHubAPIError(f"Refusing a non-root-relative API path: {_render_untrusted(value=path)}")
    url = f"{API_BASE}{path}"
    if not url.startswith("https://"):
        raise GitHubAPIError(f"Refusing to call non-HTTPS URL: {url}")
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = Request(url=url, method=method, data=data)
    req.add_header(HEADER_ACCEPT, ACCEPT_JSON)
    req.add_header(HEADER_AUTH, f"Bearer {token}")
    req.add_header(HEADER_UA, USER_AGENT)
    req.add_header(HEADER_API_VERSION, api_version)
    if body is not None:
        req.add_header(HEADER_CONTENT_TYPE, CONTENT_TYPE_JSON)
    opener = _build_api_opener()
    try:
        with opener.open(req) as resp:
            content = resp.read()
            if response_headers is not None:
                response_headers.update({str(name).lower(): str(value) for name, value in resp.headers.items()})
            if raw:
                return content
            if not content:
                return None
            return json.loads(content.decode("utf-8"))
    except HTTPError as exc:
        raise GitHubAPIError(
            f"GitHub API {method} {url} failed: HTTP {exc.code}",
            status_code=exc.code,
            details=_http_error_details(exc=exc),
        ) from exc


def _fetch_log_content(*, token: str, owner: str, repo: str, run_id: int) -> bytes:
    """Fetch the log zip for a workflow run, handling the 302 to Azure Blob."""
    url = f"{API_BASE}/repos/{owner}/{repo}/actions/runs/{run_id}/logs"
    if not url.startswith("https://"):
        raise GitHubAPIError(f"Refusing to call non-HTTPS URL: {url}")
    req = Request(url=url)
    req.add_header(HEADER_ACCEPT, ACCEPT_JSON)
    req.add_header(HEADER_AUTH, f"Bearer {token}")
    req.add_header(HEADER_UA, USER_AGENT)
    req.add_header(HEADER_API_VERSION, API_VERSION)
    opener = _build_download_opener()
    try:
        with opener.open(req) as resp:
            return resp.read()
    except HTTPError as exc:
        raise GitHubAPIError(
            f"Failed to fetch logs for run {run_id}: HTTP {exc.code}",
            status_code=exc.code,
        ) from exc


# --- Subcommands ---


def cmd_list_workflows(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    del args
    data = _api_request(method="GET", path=f"/repos/{owner}/{repo}/actions/workflows", token=token)
    for wf in data.get(FIELD_WORKFLOWS, []):
        print(f"{wf[FIELD_ID]:<12} {wf[FIELD_STATE]:<10} {wf[FIELD_NAME]}")


def cmd_list_runs(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    params = [f"per_page={args.limit}"]
    if args.status:
        params.append(f"status={args.status}")
    path = f"/repos/{owner}/{repo}/actions/runs?" + "&".join(params)
    if args.workflow:
        path = f"/repos/{owner}/{repo}/actions/workflows/{args.workflow}/runs?" + "&".join(params)
    data = _api_request(method="GET", path=path, token=token)
    for run in data.get(FIELD_WORKFLOW_RUNS, []):
        print(f"{run[FIELD_ID]:<12} {run[FIELD_STATUS]:<12} {str(run.get(FIELD_CONCLUSION)):<12} {run[FIELD_NAME]}")


def cmd_get_run(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    data = _api_request(
        method="GET",
        path=f"/repos/{owner}/{repo}/actions/runs/{args.run_id}",
        token=token,
    )
    print(json.dumps(data, indent=2))


def cmd_wait_run(token: str, owner: str, repo: str, args: argparse.Namespace) -> int:
    """Block until a workflow run completes; the exit status IS the verdict (0 / 10 / 11).

    The one sanctioned way to wait on CI (``parallel-by-default.md``): after the unblocked work is done,
    run in the FOREGROUND with ``--timeout-seconds 540`` (under the tool's 10-minute ceiling) and re-issued
    while it exits 11. Not as a background task: that dies with the session's process and a stopped task
    never wakes the agent. The polling lives here, bounded by ``--timeout-seconds``, instead of as repeated
    ``sleep`` calls in an agent's turn.
    """
    deadline = _monotonic() + args.timeout_seconds
    status = ""
    while True:
        data = _api_request(method="GET", path=f"/repos/{owner}/{repo}/actions/runs/{args.run_id}", token=token)
        status = str(data.get(FIELD_STATUS) or "")
        conclusion = str(data.get(FIELD_CONCLUSION) or "")
        if status == RUN_STATUS_COMPLETED:
            print(
                json.dumps(
                    {
                        KEY_RUN_ID: args.run_id,
                        FIELD_STATUS: status,
                        FIELD_CONCLUSION: conclusion,
                        FIELD_URL: data.get(FIELD_URL, ""),
                    }
                )
            )
            return EXIT_OK if conclusion == RUN_CONCLUSION_SUCCESS else EXIT_WAIT_NOT_SUCCESS
        if _monotonic() >= deadline:
            break
        _sleep(args.interval_seconds)
    print(
        json.dumps(
            {KEY_RUN_ID: args.run_id, FIELD_STATUS: status or "unknown", KEY_TIMEOUT_SECONDS: args.timeout_seconds}
        )
    )
    return EXIT_WAIT_TIMEOUT


def _admission_inputs(*, args: argparse.Namespace) -> tuple[str, str, int | None]:
    """`require-green-deploy`'s `--workflow`, `--head-sha` and `--run-id`, each checked whole before any request.

    `--workflow` must `fullmatch` `WORKFLOW_FILE_PATTERN`, `--head-sha` `COMMITISH_PATTERN` (a full lowercase-hex commit
    sha) and `--run-id`, when given, `RUN_ID_PATTERN` (design D6 "Input checks"). They are checked here and not by an
    argparse `type=`, whose refusal exits 2, the wrapper's usage and credential status; a refusal here exits 1. A
    refusal names the option and the shape it needs and never the refused value, which may carry a control character.
    A `--workflow` that fullmatches its pattern but is no key of `GREEN_DEPLOY_JOBS` is refused too, naming the
    workflows the wrapper holds jobs for, in its keys' order (issue #1052, design D8 "Input check"; DL-004).
    `--by-run-name` is admitted beside `--run-id` as without it (issue #1266, design D6, withdrawing issue #1036's
    refusal of the pair), so it is no input this function checks.
    """
    workflow, head_sha, run_id = args.workflow, args.head_sha, args.run_id
    if WORKFLOW_FILE_PATTERN.fullmatch(workflow) is None:
        raise GitHubAPIError(
            "Refusing the --workflow value: it must be one workflow file name of ASCII letters, digits, '.', '_' or "
            "'-' ending in .yml or .yaml. Nothing has been requested."
        )
    if workflow not in GREEN_DEPLOY_JOBS:
        raise GitHubAPIError(
            "Refusing the --workflow value: it must be a workflow whose jobs the wrapper holds: "
            f"{', '.join(GREEN_DEPLOY_JOBS)}. Nothing has been requested."
        )
    if COMMITISH_PATTERN.fullmatch(head_sha) is None:
        raise GitHubAPIError(HEAD_SHA_REFUSAL)
    if run_id is None:
        return workflow, head_sha, None
    if RUN_ID_PATTERN.fullmatch(run_id) is None:
        raise GitHubAPIError("Refusing the --run-id value: it must be ASCII digits only. Nothing has been requested.")
    return workflow, head_sha, int(run_id)


def _listed_run_id(*, run: Any) -> int | None:
    """A listed run's `id` when it is an integer, which alone may enter a jobs path or a message; `None` otherwise."""
    value = run.get(FIELD_ID) if isinstance(run, dict) else None
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _failed_run_checks(
    *, run: Any, workflow: str, head_sha: str, repository: str, by_run_name: bool = False
) -> list[str]:
    """The names of the run fields in which `run` is not a Green Deploy of `head_sha` (design D6 "A Green Deploy").

    The subcommand checks every field itself, never trusting a listing's filters: `path` is `.github/workflows/FILE`,
    `head_sha` is the commit, `head_branch` is `BRANCH_MAIN_DEFAULT`, `event` is `workflow_run`, `status` is
    `RUN_STATUS_COMPLETED`, `conclusion` is `RUN_CONCLUSION_SUCCESS` and `head_repository.full_name` is `repository`,
    the `owner/repo` of this checkout. A missing or `null` field, or a record that is not an object, fails its check.
    With `by_run_name` (`--by-run-name`, issue #1036 design D3; issue #1266 design D6, on the `--run-id` path and the
    listing path alike), `display_title` must equal the Run Name of the commit for `workflow`,
    `RUN_NAME_TEMPLATES[workflow]` formatted with `head_sha`, exactly, in place of the `head_sha` check, which is then
    not made: the bare sha for `deploy-dev.yml`, the Stage Run Name for `deploy-stage.yml`. Every other check stands.
    The comparisons are `_failed_field_checks`', which `_failed_trunk_run_checks` shares.
    """
    commit_check = (FIELD_HEAD_SHA, head_sha)
    if by_run_name:
        commit_check = (FIELD_DISPLAY_TITLE, RUN_NAME_TEMPLATES[workflow].format(sha=head_sha))
    expected = (
        (FIELD_PATH, f"{WORKFLOWS_DIRECTORY}{workflow}"),
        commit_check,
        (FIELD_HEAD_BRANCH, BRANCH_MAIN_DEFAULT),
        (FIELD_EVENT, EVENT_WORKFLOW_RUN),
        (FIELD_STATUS, RUN_STATUS_COMPLETED),
        (FIELD_CONCLUSION, RUN_CONCLUSION_SUCCESS),
    )
    return _failed_field_checks(record=run, expected=expected, repository=repository)


def _failed_field_checks(*, record: Any, expected: tuple[tuple[str, str], ...], repository: str) -> list[str]:
    """The names of the fields in which `record` differs from `expected`, then `head_repository.full_name` if it is
    not `repository`, in that order (issue #1266, design D3).

    Each `(name, value)` pair of `expected` is compared by exact equality with `record.get(name)`; `head_repository`
    must be an object whose `full_name` is `repository`, the `owner/repo` of this checkout. A missing or `null` field,
    or a record that is not an object, fails its check. Shared by `_failed_run_checks` and `_failed_trunk_run_checks`,
    so a Green Deploy and a Trunk Run are compared one way. The names are the field names alone, so no API value
    reaches a refusal.
    """
    fields = record if isinstance(record, dict) else {}
    failed = [name for name, value in expected if fields.get(name) != value]
    head_repository = fields.get(FIELD_HEAD_REPOSITORY)
    full_name = head_repository.get(FIELD_FULL_NAME) if isinstance(head_repository, dict) else None
    if full_name != repository:
        failed.append(f"{FIELD_HEAD_REPOSITORY}.{FIELD_FULL_NAME}")
    return failed


def _failed_job_checks(*, token: str, owner: str, repo: str, run_id: int, workflow: str) -> list[str]:
    """`[]` when the run's latest attempt lists exactly `workflow`'s jobs, each concluded `success`; else
    `[CHECK_GREEN_JOBS]`.

    The jobs are read with `filter=latest` (`JOBS_FILTER_LATEST`), which returns "jobs from the most recent execution
    of the workflow run", so a job that failed in an earlier attempt and was re-run green counts as green, and one
    green in an earlier attempt and red in the latest does not. A job's conclusion shares the run's vocabulary. The
    listed jobs must be objects whose `name` strings are `GREEN_DEPLOY_JOBS[workflow]`, each once, in any order, and
    whose every `conclusion` is `RUN_CONCLUSION_SUCCESS` (issue #1052, design D8 "The jobs check"). The refusal is the
    check's name alone, so no job name, an API value, reaches it.
    """
    data = _api_request(
        method="GET",
        path=f"/repos/{owner}/{repo}/actions/runs/{run_id}/jobs?filter={JOBS_FILTER_LATEST}",
        token=token,
    )
    jobs = data.get(FIELD_JOBS) if isinstance(data, dict) else None
    if not isinstance(jobs, list) or not all(isinstance(job, dict) for job in jobs):
        return [CHECK_GREEN_JOBS]
    names = [job.get(FIELD_NAME) for job in jobs]
    every_job_green = all(job.get(FIELD_CONCLUSION) == RUN_CONCLUSION_SUCCESS for job in jobs)
    every_name_a_string = all(isinstance(name, str) for name in names)
    if every_job_green and every_name_a_string and sorted(names) == sorted(GREEN_DEPLOY_JOBS[workflow]):
        return []
    return [CHECK_GREEN_JOBS]


def _listing_query(*, head_sha: str, by_run_name: bool) -> str:
    """The query of `require-green-deploy`'s one listing page, but its `per_page`.

    Without `by_run_name` the runs of the commit, `head_sha={SHA}&status=success` (#908 design D6). With it the
    successful `workflow_run` runs on `BRANCH_MAIN_DEFAULT`, `status=success&event=workflow_run&branch=main`, with no
    `head_sha`, since a `Deploy stage` run's `head_sha` is not the commit it deployed (issue #1036, design D3).
    """
    if by_run_name:
        return f"status={RUN_CONCLUSION_SUCCESS}&event={EVENT_WORKFLOW_RUN}&branch={BRANCH_MAIN_DEFAULT}"
    return f"head_sha={head_sha}&status={RUN_CONCLUSION_SUCCESS}"


def cmd_require_green_deploy(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Return (exit 0) only when a run of `--workflow` is a Green Deploy of `--head-sha`; raise otherwise (exit 1).

    The half of the stage and prod legs' Guard that reads GitHub (issue #908, design D6). With `--run-id` the one
    candidate is `GET /repos/{o}/{r}/actions/runs/{ID}`; without it the candidates are one page of
    `GITHUB_MAX_PER_PAGE` runs of `GET /repos/{o}/{r}/actions/workflows/{FILE}/runs?head_sha={SHA}&status=success`.
    With `--by-run-name` (issue #1036, design D3) `_failed_run_checks` judges the candidate's `display_title`, the Run
    Name of `SHA` for `FILE` in `RUN_NAME_TEMPLATES`, in place of its `head_sha`: on the `--run-id` path the one
    candidate is still run `ID`, read once and never listed (issue #1266, design D6, the Stage Leg's spelling), and
    without `--run-id` the page is `.../runs?status=success&event=workflow_run&branch=main`, with no `head_sha` (the
    Prod Leg's). A candidate is admitted when `_failed_run_checks` and then `_failed_job_checks` find nothing, the
    second requiring the candidate's latest attempt to list `FILE`'s jobs in `GREEN_DEPLOY_JOBS`, each once and
    concluded `success` (issue #1052, design D8): `deploy-dev.yml`'s `admission`, `deploy`, `openings-harness` and
    `sync-harness` (issue #1266, design D5), and `deploy-stage.yml`'s `deploy` and `sync-harness` (issue #1059, design
    D7). Both paths judge the jobs of the `--workflow`'s set, so the Stage Leg's `--run-id` reads `deploy-dev.yml`'s
    four and the Prod Leg's `--by-run-name` reads `deploy-stage.yml`'s two (AC-6.2). `_admission_inputs` refuses a
    `FILE` that is no key of it before any request; the admission logs the run's id as an integer. A refusal's message
    names only `FILE`, `SHA`, run ids as integers and the names of the failed checks, all of which carry no control
    character, and no API value. An HTTP error is not caught here, so `main` reports it with its `Details:` line as for
    every subcommand.
    """
    workflow, head_sha, run_id = _admission_inputs(args=args)
    by_run_name = args.by_run_name
    repository = f"{owner}/{repo}"
    if run_id is not None:
        run = _api_request(method="GET", path=f"/repos/{owner}/{repo}/actions/runs/{run_id}", token=token)
        failed = _failed_run_checks(
            run=run, workflow=workflow, head_sha=head_sha, repository=repository, by_run_name=by_run_name
        )
        if not failed:
            failed = _failed_job_checks(token=token, owner=owner, repo=repo, run_id=run_id, workflow=workflow)
        if failed:
            raise GitHubAPIError(
                f"Refusing the admission: run {run_id} of {workflow} is not a Green Deploy of {head_sha}; it fails "
                f"{', '.join(failed)}."
            )
        logger.info("Admitted: run %d of %s is a Green Deploy of %s.", run_id, workflow, head_sha)
        return
    listing = _api_request(
        method="GET",
        path=(
            f"/repos/{owner}/{repo}/actions/workflows/{workflow}/runs?"
            f"{_listing_query(head_sha=head_sha, by_run_name=by_run_name)}&per_page={GITHUB_MAX_PER_PAGE}"
        ),
        token=token,
    )
    runs = listing.get(FIELD_WORKFLOW_RUNS) if isinstance(listing, dict) else None
    refusals: list[str] = []
    for run in runs if isinstance(runs, list) else []:
        candidate = _listed_run_id(run=run)
        if candidate is None:
            refusals.append(f"a listed run fails {CHECK_RUN_ID}")
            continue
        failed = _failed_run_checks(
            run=run, workflow=workflow, head_sha=head_sha, repository=repository, by_run_name=by_run_name
        )
        if not failed:
            failed = _failed_job_checks(token=token, owner=owner, repo=repo, run_id=candidate, workflow=workflow)
        if not failed:
            logger.info("Admitted: run %d of %s is a Green Deploy of %s.", candidate, workflow, head_sha)
            return
        refusals.append(f"run {candidate} fails {', '.join(failed)}")
    reasons = "; ".join(refusals) if refusals else "the listing holds no run"
    raise GitHubAPIError(
        f"Refusing the admission: no listed run of {workflow} is a Green Deploy of {head_sha}: {reasons}."
    )


def _trunk_admission_inputs(*, args: argparse.Namespace) -> tuple[int, str, int, int]:
    """`require-newest-trunk-run`'s `--run-id`, `--head-sha`, `--own-run-id` and `--run-attempt`, each checked whole
    before any request (issue #1266, design D3 "Input checks"), as `_admission_inputs` checks `require-green-deploy`'s.

    `--run-id`, `--own-run-id` and `--run-attempt` must `fullmatch` `RUN_ID_PATTERN`, `--run-attempt` must be at least
    1, and `--head-sha` must `fullmatch` `COMMITISH_PATTERN`. Every option is a plain argparse string, checked here and
    not by an argparse `type=`, so a refusal exits 1 and argparse never echoes the value. A refusal names the option
    and the shape it needs, never the value, and ends "Nothing has been requested." Every input is checked before the
    handler admits a re-run.
    """
    digit_options = (("--run-id", args.run_id), ("--own-run-id", args.own_run_id), ("--run-attempt", args.run_attempt))
    for option, value in digit_options:
        if RUN_ID_PATTERN.fullmatch(value) is None:
            raise GitHubAPIError(
                f"Refusing the {option} value: it must be ASCII digits only. Nothing has been requested."
            )
    if int(args.run_attempt) < 1:
        raise GitHubAPIError("Refusing the --run-attempt value: it must be at least 1. Nothing has been requested.")
    if COMMITISH_PATTERN.fullmatch(args.head_sha) is None:
        raise GitHubAPIError(HEAD_SHA_REFUSAL)
    return int(args.run_id), args.head_sha, int(args.own_run_id), int(args.run_attempt)


def _listed_run_number(*, run: Any) -> int | None:
    """A run's `run_number` when it is an `int` and not a `bool`, which alone may be compared or enter a message;
    `None` otherwise (issue #1266, design D3)."""
    value = run.get(FIELD_RUN_NUMBER) if isinstance(run, dict) else None
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _failed_trunk_run_checks(*, run: Any, repository: str, head_sha: str | None = None) -> list[str]:
    """The names of the checks in which `run` is not a green Trunk Run (issue #1266, design D3 "2. The Triggering
    Run", "4. The verdict").

    A green Trunk Run is a run of `.github/workflows/ci.yml` (`WORKFLOWS_DIRECTORY`, `TRUNK_WORKFLOW`) on
    `BRANCH_MAIN_DEFAULT`, its `event` `EVENT_PUSH`, its `status` `RUN_STATUS_COMPLETED` and its `conclusion`
    `RUN_CONCLUSION_SUCCESS`, whose `head_repository.full_name` is `repository`, the fields compared by
    `_failed_field_checks`, never trusting a listing's filters. With `head_sha`, the Triggering Run's checks: its
    `head_sha` is compared too, after `path`, and then its `run_number` must be an `int` and not a `bool`
    (`CHECK_RUN_NUMBER`) and its `created_at` a string `CREATED_AT_PATTERN` fullmatches (`CHECK_CREATED_AT`), since the
    listing's query and the verdict use both. Without it, a listed entry's checks, which judge no `head_sha`,
    `run_number` or `created_at`: a newer Trunk Run is of another commit and created later.
    """
    commit_checks: tuple[tuple[str, str], ...] = () if head_sha is None else ((FIELD_HEAD_SHA, head_sha),)
    expected: tuple[tuple[str, str], ...] = (
        (FIELD_PATH, f"{WORKFLOWS_DIRECTORY}{TRUNK_WORKFLOW}"),
        *commit_checks,
        (FIELD_HEAD_BRANCH, BRANCH_MAIN_DEFAULT),
        (FIELD_EVENT, EVENT_PUSH),
        (FIELD_STATUS, RUN_STATUS_COMPLETED),
        (FIELD_CONCLUSION, RUN_CONCLUSION_SUCCESS),
    )
    failed = _failed_field_checks(record=run, expected=expected, repository=repository)
    if head_sha is None:
        return failed
    if _listed_run_number(run=run) is None:
        failed.append(CHECK_RUN_NUMBER)
    created_at = run.get(FIELD_CREATED_AT) if isinstance(run, dict) else None
    if not isinstance(created_at, str) or CREATED_AT_PATTERN.fullmatch(created_at) is None:
        failed.append(CHECK_CREATED_AT)
    return failed


def _trunk_listing_path(*, owner: str, repo: str, created_at: str) -> str:
    """The root-relative path of the one listing page (issue #1266, design D3 "3. The listing"): the successful push
    runs of `ci.yml` on `BRANCH_MAIN_DEFAULT` created on or after `created_at`, its qualifier `CREATED_ON_OR_AFTER`
    and the value `quote`d with nothing safe, `GITHUB_MAX_PER_PAGE` to the page. `created_at` has fullmatched
    `CREATED_AT_PATTERN` before it reaches here."""
    created = quote(string=f"{CREATED_ON_OR_AFTER}{created_at}", safe="")
    return (
        f"/repos/{owner}/{repo}/actions/workflows/{TRUNK_WORKFLOW}/runs?event={EVENT_PUSH}&branch={BRANCH_MAIN_DEFAULT}"
        f"&status={RUN_CONCLUSION_SUCCESS}&created={created}&per_page={GITHUB_MAX_PER_PAGE}"
    )


def _green_listed_trunk_runs(*, listing: Any, repository: str) -> tuple[list[tuple[int, int]], int]:
    """The `(id, run_number)` of every listed entry that `_failed_trunk_run_checks` passes without its `head_sha`,
    `run_number` and `created_at` checks, and the number of entries on the page (issue #1266, design D3 "4. The
    verdict").

    `workflow_runs` must be a list of objects, and every entry that passes must carry an integer `id`
    (`_listed_run_id`) and a `run_number` that is an `int` and not a `bool` (`_listed_run_number`), or this raises,
    naming the failed checks alone; an entry that fails is no green Trunk Run and is passed over, whatever its `id`
    and `run_number`. The whole page is judged before the caller decides, so no cancel follows a page it cannot read.
    """
    runs = listing.get(FIELD_WORKFLOW_RUNS) if isinstance(listing, dict) else None
    if not isinstance(runs, list) or not all(isinstance(run, dict) for run in runs):
        raise GitHubAPIError(
            f"Refusing the admission: the listing of the successful push runs of {TRUNK_WORKFLOW} on "
            f"{BRANCH_MAIN_DEFAULT} is not a list of run objects."
        )
    green: list[tuple[int, int]] = []
    for run in runs:
        if _failed_trunk_run_checks(run=run, repository=repository):
            continue
        listed_id, run_number = _listed_run_id(run=run), _listed_run_number(run=run)
        if listed_id is None or run_number is None:
            checks = ((CHECK_RUN_ID, listed_id), (CHECK_RUN_NUMBER, run_number))
            failed = [name for name, value in checks if value is None]
            raise GitHubAPIError(
                f"Refusing the admission: a listed green push run of {TRUNK_WORKFLOW} on {BRANCH_MAIN_DEFAULT} fails "
                f"{', '.join(failed)}."
            )
        green.append((listed_id, run_number))
    return green, len(runs)


def _supersede_own_run(
    *, token: str, owner: str, repo: str, run_id: int, run_number: int, newer: list[tuple[int, int]], own_run_id: int
) -> NoReturn:
    """Cancel run `own_run_id`, wait once, and raise (issue #1266, design D3 "5. Superseded"; AC-2.2, AC-2.6).

    `newer` holds the `(id, run_number)` of each green Trunk Run listed with a `run_number` above `run_number`, the
    Triggering Run `run_id`'s; the log names the one with the highest. The one write is
    `POST /repos/{o}/{r}/actions/runs/{own_run_id}/cancel` with no body, the job's own `github.run_id`; an HTTP error is
    not caught, so `main` reports it with exit 1 and no wait follows. The wait is `SELF_CANCEL_WAIT_SECONDS` through
    the `_sleep` seam; once the cancellation lands GitHub stops the job and the run concludes `cancelled`, and if it
    has not landed by then the raise fails the job, so the jobs that need it are skipped either way.
    """
    newest_id, newest_number = max(newer, key=lambda entry: entry[1])
    logger.info(
        "Superseded: run %d of %s (number %d) has a newer successful push run on %s, run %d (number %d); cancelling "
        "run %d.",
        run_id,
        TRUNK_WORKFLOW,
        run_number,
        BRANCH_MAIN_DEFAULT,
        newest_id,
        newest_number,
        own_run_id,
    )
    _api_request(method="POST", path=f"/repos/{owner}/{repo}/actions/runs/{own_run_id}/cancel", token=token)
    _sleep(SELF_CANCEL_WAIT_SECONDS)
    raise GitHubAPIError(
        f"Refusing the admission: run {own_run_id} was not cancelled within the wait, so its deploy job must not start."
    )


def cmd_require_newest_trunk_run(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Return (exit 0) only for a re-run, or when the Triggering Run is the newest green Trunk Run; otherwise cancel
    the job's own run or raise (exit 1).

    The one step of `deploy-dev.yml`'s Admission Job that reads GitHub (issue #1266, design D2, D3). Its inputs are
    checked whole first (`_trunk_admission_inputs`). A re-run, `--run-attempt` above 1, is admitted with no request
    (UB-5): the check binds the first attempt alone. A first attempt reads the Triggering Run,
    `GET /repos/{o}/{r}/actions/runs/{ID}`, and requires `_failed_trunk_run_checks` to find nothing with `--head-sha`
    (AC-2.4); then it reads ONE page through `_api_get_page`, so the `link` header is read, of the successful push runs
    of `ci.yml` on `main` created on or after the Triggering Run (`_trunk_listing_path`). A listed green Trunk Run
    (`_green_listed_trunk_runs`) whose `run_number` is above the Triggering Run's is newer: the run is Superseded and
    `_supersede_own_run` cancels it (AC-2.2, AC-2.6). With none newer, a page that names a next page or holds
    `GITHUB_MAX_PER_PAGE` entries may hold more runs than it returned, so it is refused (AC-2.4); otherwise the
    Triggering Run is admitted (AC-2.1). Every message names only `ci.yml`, `SHA`, run ids, run numbers and attempts
    as integers, and check names; no API value reaches one (CWE-117), but for `next_page_path`'s own refusal of a
    next-page URL outside `API_BASE`, rendered through `_render_untrusted`. An HTTP error is not caught here, so
    `main` reports it as for every subcommand.
    """
    run_id, head_sha, own_run_id, run_attempt = _trunk_admission_inputs(args=args)
    if run_attempt > 1:
        logger.info(
            "Admitted: attempt %d of run %d is a re-run, which the newest check does not judge.",
            run_attempt,
            own_run_id,
        )
        return
    repository = f"{owner}/{repo}"
    run = _api_request(method="GET", path=f"/repos/{owner}/{repo}/actions/runs/{run_id}", token=token)
    failed = _failed_trunk_run_checks(run=run, repository=repository, head_sha=head_sha)
    if failed:
        raise GitHubAPIError(
            f"Refusing the admission: run {run_id} of {TRUNK_WORKFLOW} is not a green push run of {head_sha} on "
            f"{BRANCH_MAIN_DEFAULT}; it fails {', '.join(failed)}."
        )
    run_number: int = run[FIELD_RUN_NUMBER]
    listing, next_page = _api_get_page(
        path=_trunk_listing_path(owner=owner, repo=repo, created_at=run[FIELD_CREATED_AT]), token=token
    )
    green, listed = _green_listed_trunk_runs(listing=listing, repository=repository)
    newer = [entry for entry in green if entry[1] > run_number]
    if newer:
        _supersede_own_run(
            token=token,
            owner=owner,
            repo=repo,
            run_id=run_id,
            run_number=run_number,
            newer=newer,
            own_run_id=own_run_id,
        )
    if next_page is not None or listed >= GITHUB_MAX_PER_PAGE:
        incomplete = "names a next page" if next_page is not None else f"holds {GITHUB_MAX_PER_PAGE} runs, a full page"
        raise GitHubAPIError(
            f"Refusing the admission: the listing of the successful push runs of {TRUNK_WORKFLOW} on "
            f"{BRANCH_MAIN_DEFAULT} {incomplete}, so it may hold a run newer than run {run_id} that it did not return."
        )
    logger.info(
        "Admitted: run %d of %s (number %d) is the newest successful push run on %s.",
        run_id,
        TRUNK_WORKFLOW,
        run_number,
        BRANCH_MAIN_DEFAULT,
    )


def _parse_iso8601_utc(value: str) -> datetime | None:
    """Parse a GitHub ISO-8601 timestamp (e.g. ``2026-07-07T18:00:00Z``) to an aware UTC datetime.

    Returns ``None`` for a missing/blank/unparseable value so timing output degrades cleanly
    rather than raising (a still-running job has no ``completed_at``).
    """
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _job_billed_minutes(job: dict[str, Any]) -> tuple[float | None, int | None]:
    """Return ``(wall_seconds, billed_minutes)`` for a job from its start/complete timestamps.

    GitHub bills each job's duration ROUNDED UP to the next whole minute (per
    docs.github.com/en/billing/reference/actions-runner-pricing); a run is billed as the sum
    of its jobs. A job whose duration is 0 < d <= 60s bills 1 minute. Returns ``(None, None)``
    if either timestamp is missing (e.g. the job is still running).
    """
    started = _parse_iso8601_utc(str(job.get(FIELD_STARTED_AT, "")))
    completed = _parse_iso8601_utc(str(job.get(FIELD_COMPLETED_AT, "")))
    if started is None or completed is None:
        return None, None
    wall_seconds = (completed - started).total_seconds()
    if wall_seconds < 0:
        return wall_seconds, None
    billed = int(math.ceil(wall_seconds / 60.0))
    if wall_seconds > 0 and billed == 0:
        billed = 1
    return wall_seconds, billed


@dataclass(frozen=True)
class LivenessVerdict:
    """Whether the CI pipeline is EXECUTING, not merely whether the latest run is green (R4.3).

    A quota-blocked run reports `conclusion: failure` while having executed zero steps, so
    `conclusion` cannot answer the question. This verdict keys on `steps` instead (R4.2).
    """

    alive: bool
    threshold_hours: float
    scanned_runs: int
    newest_executed_run_number: int | None
    newest_executed_run_age_hours: float | None
    latest_run_number: int | None
    latest_run_conclusion: str | None
    latest_run_proven_executed: bool
    unavailable_job_lists: int


def _run_proven_executed(*, jobs: Any) -> bool:
    """A run is an EXECUTED RUN iff at least one job reports `steps` as a non-empty list (R4.2).

    The single authoritative classifier. The three corroborating signals from the blackout — ~3 s per
    job, empty `--failed-only` logs, a `skipped` dependent job — are deliberately NOT classifiers: each
    admits false positives (a fast genuine run, a genuinely-empty failure log, a legitimately-skipped
    job). Making one signal authoritative keeps the classifier falsifiable.

    This also settles R4.8 with no special-casing: a `skipped` job carries `steps=0`, which is evidence
    NEITHER for nor against execution, and the existential quantifier already handles it correctly.
    """
    if not isinstance(jobs, list):
        return False
    return any(job.get(FIELD_STEPS) for job in jobs if isinstance(job, dict))


def _run_liveness_verdict(
    *, runs_with_jobs: list[tuple[dict[str, Any], Any]], now: datetime, threshold_hours: float
) -> LivenessVerdict:
    """Fold runs (newest first) into a verdict. PURE — no network, no clock (R4.10).

    Absence of evidence is never evidence of execution (R4.8): a run whose job list could not be
    fetched is counted as degraded rather than assumed alive.
    """
    newest_number: int | None = None
    newest_age: float | None = None
    unavailable = 0
    latest_number: int | None = None
    latest_conclusion: str | None = None
    latest_executed = False

    for index, (run, jobs) in enumerate(runs_with_jobs):
        executed = _run_proven_executed(jobs=jobs)
        if jobs is None:
            unavailable += 1
        if index == 0:
            latest_number = run.get(FIELD_RUN_NUMBER)
            latest_conclusion = run.get(FIELD_CONCLUSION)
            latest_executed = executed
        if executed and newest_number is None:
            newest_number = run.get(FIELD_RUN_NUMBER)
            created = run.get(FIELD_CREATED_AT)
            if created:
                stamp = datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                newest_age = (now - stamp).total_seconds() / 3600.0

    alive = newest_age is not None and newest_age <= threshold_hours
    return LivenessVerdict(
        alive=alive,
        threshold_hours=threshold_hours,
        scanned_runs=len(runs_with_jobs),
        newest_executed_run_number=newest_number,
        newest_executed_run_age_hours=newest_age,
        latest_run_number=latest_number,
        latest_run_conclusion=latest_conclusion,
        latest_run_proven_executed=latest_executed,
        unavailable_job_lists=unavailable,
    )


def _format_liveness_report(*, verdict: LivenessVerdict) -> str:
    """Render the verdict. PURE (R4.10).

    The word "green" never appears next to a run that is not proven executed (R4.7).
    """
    lines: list[str] = []
    if verdict.alive:
        lines.append(
            f"LIVENESS: ALIVE  newest Executed Run #{verdict.newest_executed_run_number}, "
            f"age {verdict.newest_executed_run_age_hours:.1f} h "
            f"(threshold {verdict.threshold_hours:.1f} h)"
        )
    elif verdict.newest_executed_run_number is None:
        lines.append(
            f"LIVENESS: UNAVAILABLE  no Executed Run in the {verdict.scanned_runs} runs scanned — "
            "every run reported zero steps, so no check could have run"
        )
    else:
        lines.append(
            f"LIVENESS: UNAVAILABLE  newest Executed Run #{verdict.newest_executed_run_number} is "
            f"{verdict.newest_executed_run_age_hours:.1f} h old, past the "
            f"{verdict.threshold_hours:.1f} h threshold"
        )
    if verdict.latest_run_number is not None:
        suffix = (
            "-> conclusion IS a check result"
            if verdict.latest_run_proven_executed
            else "-> this conclusion is NOT a check result: zero steps ran, so no check could have failed"
        )
        lines.append(
            f"LATEST RUN: #{verdict.latest_run_number}  conclusion={verdict.latest_run_conclusion}  "
            f"executed={'yes' if verdict.latest_run_proven_executed else 'no'}  {suffix}"
        )
    if verdict.unavailable_job_lists:
        lines.append(
            f"DEGRADED: {verdict.unavailable_job_lists} run(s) had no retrievable job list; "
            "absence of evidence is not evidence of execution"
        )
    return "\n".join(lines)


#: The THIRD value of the ci-liveness vocabulary (issue #469). `ALIVE` and `UNAVAILABLE` are produced by
#: `_format_liveness_report` above and by the NOT-LIVE raise below; this one is produced only by the emitter
#: that follows. Named so the tests and the four documentation surfaces assert against THIS string rather
#: than against a second copy of it, which could drift and still pass.
#:
#: It is the VERDICT TOKEN ONLY, and that is load-bearing rather than tidy: the ` — ` separator lives in the
#: emitter's f-string below. `docs/ci-capacity-ladder.md`'s third-verdict branch spells the token twice
#: WITHOUT a separator (mid-sentence, inside an inline code span), so folding the em dash back in here would
#: make the documentation test RED against a correct implementation. One string therefore serves three
#: purposes at once: the token the ladder carries, the prefix the emitted line begins with, and the substring
#: every doc arm asserts. `INDETERMINATE` also shares no substring with either other verdict, so a
#: grep-shaped reader cannot mis-read it as one of them.
LIVENESS_INDETERMINATE_PREFIX = "LIVENESS: INDETERMINATE"


def _liveness_indeterminate(*, exc: GitHubRedirectRefusedError, what: str) -> None:
    """Emit the third ci-liveness verdict on stdout, then let the caller re-raise.

    ONE emitter shared by BOTH of `cmd_ci_liveness`'s refusable reads rather than a copy per clause, so the
    two refusal paths cannot drift apart and the tests assert a single format string. `what` names the read
    that was blocked and is the only variable part besides the status code.

    **Nothing from upstream is interpolated** — not the Location Target, not the refusal message, not `exc`
    stringified. `docs/ci-capacity-ladder.md` makes this command's stdout the Rung-0 Step-A evidence, and a
    `Location` value reaches the refusal with its raw bytes intact: measured, a target carrying an obs-folded
    CRLF followed by `LIVENESS: ALIVE` arrives with its 0x0d 0x0a still present, so putting it on this
    channel would let the upstream forge a second, line-anchored verdict into the very report an operator
    reads to decide where CI runs. The full refusal message, with its escaped-and-bounded rendered target,
    still reaches the operator on stderr through `main()`'s `logger.error(str(exc))`.
    """
    print(
        f"{LIVENESS_INDETERMINATE_PREFIX} — a redirect refusal (HTTP {exc.status_code}) blocked the "
        f"{what}, so liveness could not be determined"
    )


def cmd_ci_liveness(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Report whether CI is EXECUTING, and raise on NOT-LIVE. Fetch, print, raise — nothing else.

    Consumes no workflow execution, so it breaks the re-push loop that burns billed minutes: the
    blackout produced ~80 runs each spending 2 billed minutes to execute zero steps.

    Signals NOT-LIVE by raising ``GitHubAPIError`` -> exit 1, the ``cmd_claim_issue --strict``
    precedent: every ``cmd_*`` is ``-> None`` and ``main()`` discards return values, so raising is the
    only way a handler reaches a non-zero shell status.
    """
    try:
        listing = _api_request(
            method="GET",
            path=f"/repos/{owner}/{repo}/actions/workflows/ci.yml/runs?per_page={args.scan_runs}",
            token=token,
        )
    except GitHubRedirectRefusedError as exc:
        # This read had NO enclosing `try` at all, which made it the one refusal path the per-run clause
        # below cannot cover: a refusal here leaves the command before the loop is entered and before
        # `print(_format_liveness_report(...))`, so it emitted no `LIVENESS:` line whatsoever while still
        # exiting 1 — byte-for-byte the shape NOT-LIVE uses. A reader following the capacity ladder's Rung-0
        # Step A then had a non-zero exit with no verdict and no way to tell "CI is dead" from "the wrapper
        # refused a redirect", which are opposite actions.
        _liveness_indeterminate(exc=exc, what="workflow-runs listing")
        raise
    runs_with_jobs: list[tuple[dict[str, Any], Any]] = []
    for run in listing.get(FIELD_WORKFLOW_RUNS, []):
        try:
            jobs_payload = _api_request(
                method="GET",
                path=f"/repos/{owner}/{repo}/actions/runs/{run[FIELD_ID]}/jobs?per_page=100",
                token=token,
            )
            jobs = jobs_payload.get(FIELD_JOBS)
        except GitHubRedirectRefusedError as exc:
            # A refused redirect is NOT "this run has no jobs". The clause below reads every GitHubAPIError as
            # an unretrievable job list, and the refusal IS one, so the fold counted it as a degraded run and
            # the command reported NOT-LIVE from a credential decision — sending the capacity ladder down a
            # rung for the wrong reason. It must reach the operator instead.
            #
            # The discriminator is printed HERE, not at the end: the refusal propagates out of this loop,
            # which is before `print(_format_liveness_report(...))`, so the verdict line has to be emitted on
            # the way out or the path carries no verdict at all.
            _liveness_indeterminate(exc=exc, what="per-run jobs read")
            raise
        except GitHubAPIError:
            jobs = None  # unchanged: a non-refusal error still means "no jobs observed"
        runs_with_jobs.append((run, jobs))
        # Short-circuit: newest-first, stop at the first Executed Run, so ALIVE costs one job-list call.
        if _run_proven_executed(jobs=jobs):
            break

    verdict = _run_liveness_verdict(
        runs_with_jobs=runs_with_jobs,
        now=datetime.now(timezone.utc),
        threshold_hours=args.max_age_hours,
    )
    print(_format_liveness_report(verdict=verdict))
    if not verdict.alive:
        raise GitHubAPIError(
            "CI pipeline UNAVAILABLE: no Executed Run within the age threshold",
            details={
                "alive": verdict.alive,
                "newest_executed_run_number": verdict.newest_executed_run_number,
                "scanned_runs": verdict.scanned_runs,
                "threshold_hours": verdict.threshold_hours,
            },
        )


def cmd_get_jobs(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    # The `filter` parameter is passed EXPLICITLY rather than left to the API default, because that
    # default is LOSSY and choosing it by omission hid real evidence (issue #254). Per the GitHub REST
    # docs for workflow jobs, `latest` "returns jobs from the most recent execution of the workflow run"
    # and `all` "returns all jobs for a workflow run, including from old executions" — with `latest` as
    # the default. So on a re-run run the wrapper reported ONLY the newest attempt and the failed
    # original became unreachable, INCLUDING its log, which is where crash evidence lives.
    #
    # That matters because `remote-ci-must-pass.md` requires never abandoning a red pipeline, so
    # re-running IS the mandated remedial action — and it was silently erasing the failure from the
    # queryable record. Measured on run 31086878415 (`run_attempt = 2`):
    #     filter=latest  ->  1 UI job: (92572952687, attempt 2, success)
    #     filter=all     ->  2 UI jobs: (92568369585, attempt 1, FAILURE), (92572952687, attempt 2, success)
    # Attempt 1 carried the `SEGV_MAPERR` that issue #253 exists to characterise.
    #
    # `latest` remains the DEFAULT here on purpose. `remote-ci-must-pass.md` Step A reads
    # `get-jobs <id>` (and `--failed-only`) to judge the CURRENT attempt when classifying quota-vs-merit;
    # silently widening that to every historical attempt would make a re-run run's earlier failures
    # surface as though the pipeline were still red. History is opt-in via `--all-attempts`.
    jobs_filter = JOBS_FILTER_ALL if getattr(args, "all_attempts", False) else JOBS_FILTER_LATEST
    data = _api_request(
        method="GET",
        path=f"/repos/{owner}/{repo}/actions/runs/{args.run_id}/jobs?per_page=100&filter={jobs_filter}",
        token=token,
    )
    show_timing = getattr(args, "timing", False)
    # With more than one attempt listed, two rows otherwise carry the same job name and differ only by
    # id — so the attempt number is reported to make the listing self-explanatory.
    jobs_listed = data.get(FIELD_JOBS, [])
    show_attempt = len({job.get(FIELD_RUN_ATTEMPT) for job in jobs_listed}) > 1
    billed_total = 0
    for job in jobs_listed:
        if args.failed_only and job.get(FIELD_CONCLUSION) not in ("failure", "cancelled", "timed_out"):
            continue
        line = f"{job[FIELD_ID]:<14} {job[FIELD_STATUS]:<12} {str(job.get(FIELD_CONCLUSION)):<12} {job[FIELD_NAME]}"
        if show_attempt:
            line = f"{line}  [attempt={job.get(FIELD_RUN_ATTEMPT)}]"
        if getattr(args, "show_steps", False):
            # A job that never executed any step (steps == 0) indicates a startup/billing
            # failure (e.g. Actions minute-quota exhaustion) rather than a check failure —
            # see .claude/rules/remote-ci-must-pass.md Step A. Report the step count so the
            # quota-vs-real-failure distinction is evidenced, not assumed.
            step_count = len(job.get(FIELD_STEPS, []))
            line = f"{line}  [steps={step_count}]"
        if show_timing:
            # Per-job wall duration + billed minutes (rounded up), so the R6/CP-9
            # billed-minute comparison is evidenced from the timing API, not assumed.
            wall_seconds, billed = _job_billed_minutes(job)
            if billed is None:
                line = f"{line}  [wall=? billed=?]"
            else:
                billed_total += billed
                line = f"{line}  [wall={wall_seconds:.0f}s billed={billed}min]"
        if getattr(args, "show_runner", False):
            # WHERE the job actually ran (issue #286). The capacity ladder names runner name and
            # runner labels as its other structural discriminators and records that this wrapper did
            # not expose them — "cmd_get_jobs prints no runner column and no subcommand does" — while
            # also requiring, for a relocation, that "every job must show a fallback label WITH a
            # non-empty runner name". That verification was therefore unperformable through the
            # sanctioned tool. This column is what makes it performable.
            #
            # It is also what separates the ladder's shape (C) from shape (B): a job carrying a
            # FALLBACK label must never be read as evidence about the HOSTED quota, and the label is
            # the only thing that distinguishes them.
            runner_name = job.get(FIELD_RUNNER_NAME) or ""
            labels = job.get(FIELD_LABELS) or []
            rendered_labels = ",".join(str(label) for label in labels) if labels else "-"
            line = f"{line}  [runner={runner_name or '(none)'} labels={rendered_labels}]"
        print(line)
        if getattr(args, "step_status", False):
            # Each step's live status and conclusion, in the API's order (issue #1277, DL-034): the jobs API
            # reports them while the job runs, where a running job's log was measured to arrive only once the job
            # had ended (CI run 40463278025, attempt 2), so a waiter reads a step's completion from here.
            for step in job.get(FIELD_STEPS, []):
                print(
                    f"    step {step.get(FIELD_NUMBER)} {str(step.get(FIELD_STATUS)):<12} "
                    f"{str(step.get(FIELD_CONCLUSION)):<12} {step.get(FIELD_NAME)}"
                )
    if show_timing:
        print(f"{'':<14} {'':<12} {'':<12} TOTAL billed minutes (sum of per-job rounded-up): {billed_total}")


def _fetch_job_log_content(*, token: str, owner: str, repo: str, job_id: int) -> bytes:
    """Fetch the plain-text log for a SINGLE job, handling the 302 to Azure Blob.

    Unlike the run-level ``/logs`` endpoint (a zip archive that is only available once the
    whole run has finished), the per-job ``/actions/jobs/{job_id}/logs`` endpoint returns a
    single job's plain-text log and is available as soon as that job completes — so a failed
    job can be inspected while sibling jobs are still running.
    """
    url = f"{API_BASE}/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"
    if not url.startswith("https://"):
        raise GitHubAPIError(f"Refusing to call non-HTTPS URL: {url}")
    req = Request(url=url)
    req.add_header(HEADER_ACCEPT, ACCEPT_JSON)
    req.add_header(HEADER_AUTH, f"Bearer {token}")
    req.add_header(HEADER_UA, USER_AGENT)
    req.add_header(HEADER_API_VERSION, API_VERSION)
    opener = _build_download_opener()
    try:
        with opener.open(req) as resp:
            return resp.read()
    except HTTPError as exc:
        raise GitHubAPIError(
            f"Failed to fetch logs for job {job_id}: HTTP {exc.code}",
            status_code=exc.code,
        ) from exc


#: Emit CI log text as UTF-8 regardless of the console codepage (issue #314).
#:
#: Both log commands already decoded GitHub's bytes with ``errors="replace"``, and then handed the
#: result to ``print()`` — which ENCODES with ``sys.stdout.encoding``, ``cp1252`` on a default Windows
#: console. GitHub's log blobs open with a BOM (U+FEFF) and carry the tools' own UTF-8 glyphs, none of
#: which cp1252 can map: the decode was guarded, the encode was not. Same defect class as issue #241,
#: in a second tool.
LOG_TEXT_ENCODING = "utf-8"

#: Substitute U+FFFD for a codepoint the stream cannot map, rather than raising. A log is evidence to
#: RELAY, not something whose exact bytes this command must validate, and one unmappable character must
#: never cost the surrounding diagnostic text. The substitution stays visible in the output, so a
#: genuinely mis-encoded log remains observable instead of being silently hidden.
LOG_TEXT_ERRORS = "replace"


def _configure_log_stream() -> None:
    """Make stdout AND stderr accept UTF-8 BEFORE any log-derived text is printed (issue #314).

    Separated from ``_emit_log_text`` because a log BODY is not the only log-derived text a command
    prints. ``cmd_get_logs`` prints a ``==== <name> ====`` header for each archive entry, before the
    body and OUTSIDE its ``try`` — and GitHub names those entries after the JOB and STEP, so the name
    comes from ``.github/workflows/ci.yml`` (``name: UI (Svelte/TypeScript)``), which any contributor
    edits. Configuring the stream only inside the body helper therefore left the original crash alive
    on the FIRST entry: measured, ``'charmap' codec can't encode character '\\u2713' in position 15``.
    The ``except Exception`` handler is no refuge either — it prints the same name and would raise
    while reporting the raise.

    Guarded by ``getattr`` because a replaced stdout (a test double, a capture object) need not
    implement ``reconfigure``, and a missing method must not turn log relay into a crash — the failure
    mode this exists to remove. Idempotent, so calling it per command and again per body is harmless.

    DISCLOSED RESIDUAL, deliberately not "fixed": widening the stream from cp1252 to UTF-8 admits
    codepoints a cp1252 console previously REFUSED, including the bidirectional overrides and
    zero-width characters behind CWE-451 / Trojan-Source. That is accepted rather than sanitized. A CI
    log is EVIDENCE TO RELAY, and its bytes are already fully controlled by whatever the code under
    test printed; stripping characters would corrupt the artifact a reader is trying to audit, which is
    the same reasoning `scripts/local_ci/report.py` applies to its relay zone (`relay_block`). The prior
    behaviour was not safety but denial of evidence — the log was destroyed rather than shown.
    """
    # BOTH streams — for CONSISTENT RENDERING, not to prevent a crash on stderr. `logging.basicConfig`
    # above creates a `StreamHandler` with no explicit stream, which the stdlib binds to `sys.stderr`, and
    # `main()` reports every refusal through that logger — messages that interpolate API-derived label
    # names and assignee logins. Configuring stderr too means a refusal renders the same way on both
    # channels: an emoji in a label arrives as itself rather than as the escape `\U0001f41b`. In production
    # the handler's bound stream IS this object (constructed at import, before any swap), so reconfiguring
    # `sys.stderr` reaches the handler.
    #
    # An earlier revision of this comment claimed stderr was exposed to the SAME crash as stdout. That was
    # FALSE and is retracted: measured, `sys.stderr.errors` is `backslashreplace`, which cannot raise,
    # while `sys.stdout.errors` is `surrogateescape`, which re-encodes lone surrogates only and so DOES
    # raise on an ordinary unmappable character. Only stdout ever had the exposure; the crash attributed to
    # stderr existed solely because a probe forced `errors="strict"` onto a fake stream
    # (`docs/lessons-learned.md`, `failure-conditioned-evidence-is-not-evidence`). The full measurement and
    # the per-handler table are in `test/ci/test_wrapper_log_encoding.py`'s stderr test.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding=LOG_TEXT_ENCODING, errors=LOG_TEXT_ERRORS)


def _emit_log_text(*, text: str) -> None:
    """Print captured log text without letting the console codepage destroy it (issue #314).

    MEASURED, both sites, against a strict cp1252 stream:

    - ``cmd_get_job_logs`` raised ``UnicodeEncodeError: 'charmap' codec can't encode character
      '\\ufeff' in position 0`` and the traceback replaced the log entirely.
    - ``cmd_get_logs`` wraps its print in ``except Exception``, so it SWALLOWED the same error and
      printed ``(error reading 0_Quality.txt: 'charmap' codec can't encode …)`` instead of the log —
      attributing a console problem to the archive, which is the more dangerous of the two because it
      is plausible and therefore believed.

    ``.claude/rules/remote-ci-must-pass.md`` makes these commands the only sanctioned way to read a
    failing job's log, so on a default Windows console the mandated debugging path was destroying the
    evidence it exists to deliver.

    Reconfiguring the TEXT layer is deliberate, rather than writing bytes to ``sys.stdout.buffer``:
    ``cmd_get_logs`` interleaves a ``==== <name> ====`` header on the text layer with each body, and
    mixing layers would risk reordering the two unless every site also flushed. ``reconfigure`` keeps
    ``print`` and therefore keeps ordering. The configuration itself lives in
    ``_configure_log_stream``, which a command also calls BEFORE printing any header derived from the
    archive — see that function for why the split is load-bearing rather than cosmetic.
    """
    _configure_log_stream()
    print(text)


def cmd_get_job_logs(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    blob = _fetch_job_log_content(token=token, owner=owner, repo=repo, job_id=args.job_id)
    _emit_log_text(text=blob.decode(LOG_TEXT_ENCODING, errors=LOG_TEXT_ERRORS))


def _fetch_artifact_zip(*, token: str, owner: str, repo: str, artifact_id: int) -> bytes:
    """Download a workflow-run artifact zip, handling the 302 to Azure Blob (auth-stripped)."""
    url = f"{API_BASE}/repos/{owner}/{repo}/actions/artifacts/{artifact_id}/zip"
    if not url.startswith("https://"):
        raise GitHubAPIError(f"Refusing to call non-HTTPS URL: {url}")
    req = Request(url=url)
    req.add_header(HEADER_ACCEPT, ACCEPT_JSON)
    req.add_header(HEADER_AUTH, f"Bearer {token}")
    req.add_header(HEADER_UA, USER_AGENT)
    req.add_header(HEADER_API_VERSION, API_VERSION)
    opener = _build_download_opener()
    try:
        with opener.open(req) as resp:
            return resp.read()
    except HTTPError as exc:
        raise GitHubAPIError(
            f"Failed to download artifact {artifact_id}: HTTP {exc.code}",
            status_code=exc.code,
        ) from exc


def cmd_list_artifacts(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    data = _api_request(
        method="GET",
        path=f"/repos/{owner}/{repo}/actions/runs/{args.run_id}/artifacts",
        token=token,
    )
    # Artifact names come from `.github/workflows/ci.yml` (`name: playwright-ui-artifacts`), so they
    # carry the same crash class as the log paths above (issue #314).
    _configure_log_stream()
    for art in data.get("artifacts", []):
        print(f"{art['id']:<14} {art.get('size_in_bytes', 0):>12}  {art['name']}")


def cmd_download_artifact(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    blob = _fetch_artifact_zip(token=token, owner=owner, repo=repo, artifact_id=args.artifact_id)
    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(BytesIO(blob)) as zf:
        # The trust basis is the EXTRACTION, not the source, and the previous justification named the source
        # (issue #469). `_fetch_artifact_zip` is Tier B: it follows GitHub's 302 to the storage host and
        # fetches the archive there anonymously, with the credential stripped, so these bytes are supplied by
        # whatever host the upstream `Location` named and are not a first-party artifact by the time they
        # arrive. What makes the call acceptable is narrower: CPython's `extractall` sanitises every member
        # path — a `..` component, a leading separator and a drive letter are all removed, measured in
        # `.claude/specs/issue-469-wrapper-redirect-policy/review/security-reviewer/probe_extractall.py`, with
        # nothing escaping `dest` — and `dest` is an explicit directory this command's caller named.
        # Deliberately NOT claimed: no expansion bound, no provenance check and no error contract for hostile
        # bytes. Those three are pre-existing, orthogonal to redirect policy, and recorded in
        # `docs/findings-ledger.md` rather than fixed here (design §4 `T8`).
        zf.extractall(dest)  # nosec B202  # member paths sanitised by CPython into an explicit dest dir
        names = zf.namelist()
    # Same reason as `cmd_list_artifacts` above: these names are archive-derived (issue #314).
    _configure_log_stream()
    print(f"Extracted {len(names)} entries into {dest}")
    for name in names:
        print(f"  {name}")


def _repository_artifacts(*, token: str, owner: str, repo: str) -> list[dict[str, Any]]:
    """Every Actions artifact of the repository, page by page.

    `GET /repos/{owner}/{repo}/actions/artifacts` answers `total_count` and an `artifacts` page of at most 100
    ("The number of results per page (max 100)", docs.github.com/en/rest/actions/artifacts); a short page is the last.
    """
    artifacts: list[dict[str, Any]] = []
    page = 1
    while True:
        data = _api_request(
            method="GET",
            path=f"/repos/{owner}/{repo}/actions/artifacts?per_page={GITHUB_MAX_PER_PAGE}&page={page}",
            token=token,
        )
        batch = data.get(FIELD_ARTIFACTS, []) if isinstance(data, dict) else []
        artifacts.extend(batch)
        if len(batch) < GITHUB_MAX_PER_PAGE:
            return artifacts
        page += 1


def _created_before(*, artifact: dict[str, Any], cutoff: datetime) -> bool:
    """Whether the artifact's `created_at` lies before `cutoff`; an artifact with no creation time never does."""
    created = artifact.get(FIELD_CREATED_AT)
    if not isinstance(created, str):
        return False
    return datetime.fromisoformat(created) < cutoff


def cmd_list_repo_artifacts(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """List every Actions artifact of the repository, then the bytes its unexpired ones hold.

    Added when the account's Actions storage quota was full ("Failed to CreateArtifact: Artifact storage quota has
    been hit", 2026-10-21): the unexpired artifacts are what that quota counts, and `list-artifacts` reads one run.
    """
    del args
    artifacts = _repository_artifacts(token=token, owner=owner, repo=repo)
    # Artifact names come from the workflows, the crash class of `cmd_list_artifacts` (issue #314).
    _configure_log_stream()
    live_bytes = 0
    for art in artifacts:
        run = art.get(FIELD_WORKFLOW_RUN) or {}
        expired = bool(art.get(FIELD_EXPIRED))
        size = int(art.get(FIELD_SIZE_IN_BYTES, 0))
        if not expired:
            live_bytes += size
        state = ARTIFACT_STATE_EXPIRED if expired else ARTIFACT_STATE_LIVE
        print(
            f"{art[FIELD_ID]:<14} {size:>12}  {art.get(FIELD_CREATED_AT)}  {state:<7}  "
            f"{run.get(FIELD_ID, '-')}  {art.get(FIELD_NAME)}"
        )
    print(f"{len(artifacts)} artifacts; {live_bytes} bytes in the unexpired ones")


def cmd_delete_artifacts(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Delete every unexpired Actions artifact created more than `--older-than-days` days ago, each verified.

    The owner's answer to a full Actions storage quota (2026-10-21, issue #755's question): delete the old artifacts.
    `--dry-run` lists what would go and deletes nothing. FAIL-CLOSED as `delete-issue-comment` is: each
    `DELETE /repos/{owner}/{repo}/actions/artifacts/{id}` ("204 - No Content") is followed by a confirm-read of the same
    resource that must answer 404, and any other answer stops the command before the next artifact.
    """
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=args.older_than_days)
    chosen = [
        art
        for art in _repository_artifacts(token=token, owner=owner, repo=repo)
        if not art.get(FIELD_EXPIRED) and _created_before(artifact=art, cutoff=cutoff)
    ]
    for art in chosen if not args.dry_run else []:
        path = f"/repos/{owner}/{repo}/actions/artifacts/{art[FIELD_ID]}"
        _api_request(method="DELETE", path=path, token=token)
        try:
            _api_request(method="GET", path=path, token=token)
        except GitHubAPIError as exc:
            if exc.status_code == HTTP_NOT_FOUND:
                continue
            raise
        raise GitHubAPIError(f"Artifact {art[FIELD_ID]} still resolves after its DELETE; not reporting it deleted")
    summary = {
        "dry_run": args.dry_run,
        "cutoff": cutoff.isoformat(),
        "count": len(chosen),
        "bytes": sum(int(art.get(FIELD_SIZE_IN_BYTES, 0)) for art in chosen),
        "ids": [art[FIELD_ID] for art in chosen],
    }
    print(json.dumps(summary, indent=2))


def cmd_get_logs(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    blob = _fetch_log_content(token=token, owner=owner, repo=repo, run_id=args.run_id)
    # BEFORE the loop (issue #314): the per-entry header below is itself log-derived — GitHub names
    # archive entries after the job and step — so configuring the stream only inside the body helper
    # left the crash alive on the first entry's header, which is printed outside the `try`.
    _configure_log_stream()
    with zipfile.ZipFile(BytesIO(blob)) as zf:
        for name in zf.namelist():
            if args.failed_only and "failed" not in name.lower():
                continue
            print(f"==== {name} ====")
            try:
                # `_emit_log_text` rather than `print` (issue #314): the encode to the console codepage
                # is what used to fail here, and this `except` then reported it as a READ error — so the
                # guard below no longer masks a console problem as an archive problem.
                _emit_log_text(text=zf.read(name).decode(LOG_TEXT_ENCODING, errors=LOG_TEXT_ERRORS))
            except Exception as exc:  # pragma: no cover - defensive
                print(f"(error reading {name}: {exc})")


def cmd_rerun(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    suffix = "/rerun-failed-jobs" if args.failed_only else "/rerun"
    _api_request(
        method="POST",
        path=f"/repos/{owner}/{repo}/actions/runs/{args.run_id}{suffix}",
        token=token,
    )
    print(f"Rerun requested for run {args.run_id}{suffix}")


def cmd_cancel(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    _api_request(
        method="POST",
        path=f"/repos/{owner}/{repo}/actions/runs/{args.run_id}/cancel",
        token=token,
    )
    print(f"Cancel requested for run {args.run_id}")


def cmd_dispatch_workflow(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Fire a ``workflow_dispatch`` event for one workflow (issue #286).

    Needed because the CodeBuild-fallback pilot and the hosted recovery probe are BOTH
    dispatch-triggered — deliberately, so that a push starts no billable runner build — and this
    wrapper had no way to trigger one. `gh workflow run` is forbidden
    (`.claude/rules/use-git-wrapper-scripts.md`), so the capability belongs here.

    The workflow is addressed by FILE NAME, which GitHub documents as accepted in place of the numeric
    id: "The ID of the workflow. You can also pass the workflow file name as a string"
    (https://docs.github.com/en/rest/actions/workflows). A file name is the stable identifier a spec or
    a rule can cite; a numeric id is not.

    Two constraints, both from that same page and both properties of GitHub rather than of this
    subcommand:

    * the target workflow "must be set up to respond to the ``workflow_dispatch`` webhook event", and
      the event "will only trigger a workflow run if the workflow file exists on the default branch" —
      so dispatching a file that lives only on a feature branch cannot work;
    * ``ref`` is required and "can be a branch or tag name". It selects the code that RUNS;
      registration still comes from the default branch.

    Prints the run id and URL when GitHub reports them (the documented 200 response carries
    ``workflow_run_id`` and ``html_url``), so the caller can monitor the run it just started instead of
    guessing which of several recent runs is theirs.
    """
    response = _api_request(
        method="POST",
        path=f"/repos/{owner}/{repo}/actions/workflows/{args.workflow}/dispatches",
        token=token,
        body={FIELD_REF: args.ref},
    )
    print(f"Dispatched {args.workflow} on ref {args.ref}")
    if isinstance(response, dict):
        run_id = response.get(FIELD_WORKFLOW_RUN_ID)
        if run_id is not None:
            print(f"RUN ID  : {run_id}")
        url = response.get(FIELD_URL)
        if url:
            print(f"RUN URL : {url}")
    else:
        # An empty 204 is also valid API behaviour. The run exists but its id was not reported, so say
        # so rather than leaving the caller to infer that nothing started.
        print("NOTE: GitHub reported no run id for this dispatch; locate the run with `list-runs`.")


def cmd_get_variable(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Read one repository variable, printing its value and ``updated_at``.

    ``GET /repos/{owner}/{repo}/actions/variables/{name}`` returns ``name``, ``value``, ``created_at``
    and ``updated_at`` (https://docs.github.com/en/rest/actions/variables). The capacity ladder's Rung 1
    names "the variable's presence, and its ``updated_at``" as the evidence, so both are printed.
    """
    data = _api_request(
        method="GET",
        path=f"/repos/{owner}/{repo}/actions/variables/{args.name}",
        token=token,
    )
    print(f"NAME       : {data.get(FIELD_NAME)}")
    print(f"VALUE      : {data.get(FIELD_VALUE)}")
    print(f"UPDATED_AT : {data.get(FIELD_UPDATED_AT)}")


def cmd_set_variable(token: str, owner: str, repo: str, args: argparse.Namespace) -> int:
    """Create-or-update a repository variable, then CONFIRM-READ it. Returns a process exit status.

    Idempotent by construction: ``PATCH`` the variable, and only if that fails create it with ``POST``.
    Per the REST docs, update is ``PATCH /repos/{owner}/{repo}/actions/variables/{name}`` (204) and
    create is ``POST /repos/{owner}/{repo}/actions/variables`` with ``{name, value}`` (201)
    (https://docs.github.com/en/rest/actions/variables).

    **The confirm-read is the point, not a courtesy.** The capacity ladder says of exactly this
    operation that "a write helper that probes-then-creates can fail partially, so an exit code
    establishes nothing". So this re-reads the variable and compares what is STORED against what was
    REQUESTED, returning non-zero when they differ — a flip is never believed unless it landed. The
    mode variable governs where the whole pipeline runs, so a silently-unwritten value would relocate
    nothing while the operator believed it had.
    """
    path = f"/repos/{owner}/{repo}/actions/variables/{args.name}"
    try:
        _api_request(method="PATCH", path=path, token=token, body={FIELD_VALUE: args.value})
        action = "updated"
    except GitHubRedirectRefusedError:
        # A refused PATCH must NEVER be read as "the variable is absent, so create it" — that turns a refused
        # READ into an attempted WRITE, and the variable this command exists to set is the one that decides
        # where the whole pipeline runs. No discriminator line here, unlike `cmd_ci_liveness`: this command's
        # stdout is not a capacity-ladder input, and `main()` already reports the refusal on stderr.
        raise
    except GitHubAPIError:
        # Absent, so create it. A failing create PROPAGATES — this is not a silent fallback.
        _api_request(
            method="POST",
            path=f"/repos/{owner}/{repo}/actions/variables",
            token=token,
            body={FIELD_NAME: args.name, FIELD_VALUE: args.value},
        )
        action = "created"

    confirmed = _api_request(method="GET", path=path, token=token)
    stored = confirmed.get(FIELD_VALUE)
    print(f"{action} {args.name}")
    print(f"CONFIRM-READ VALUE : {stored}")
    print(f"CONFIRM-READ AT    : {confirmed.get(FIELD_UPDATED_AT)}")
    if stored != args.value:
        logger.error(
            "confirm-read MISMATCH for %s: requested %r but the variable holds %r. The write did NOT "
            "land; treat the flip as NOT performed.",
            args.name,
            args.value,
            stored,
        )
        return 1
    return EXIT_OK


# --- Release assets (issue #432) ---------------------------------------------------------------------
#
# The wrapper had no release, asset or upload verb, and `use-git-wrapper-scripts.md` says to EXTEND it
# rather than reach for `gh` or `curl`. Four constraints shape this block, each from a measured review
# finding, and each of them is a way to get the one outward-facing step in this pipeline wrong.


def _target_repo(*, owner: str, repo: str, args: argparse.Namespace) -> tuple[str, str]:
    """Resolve which repository a release subcommand addresses: `--target-repo`, else this checkout's.

    NEEDED because a produced engine artefact cannot be served from THIS repository at all. Measured:
    this repository is private, and a private repository answers `/releases/download/<tag>/<name>` with
    404 to an unauthenticated client — which is every consumer of a declared engine url, since
    `fetch-engine.mjs` performs a bare `fetch(url)` and reading a runner's `GITHUB_TOKEN` is forbidden
    by `no-environment-vars.md`. So produced artefacts live in a separate PUBLIC repository and the
    publish has to be able to name it.

    The slug is SHAPE-CHECKED before it reaches an API path. It is an operator-supplied value that is
    interpolated into `/repos/<slug>/...`, so a value carrying an extra slash or a `..` would address a
    different endpoint than the one it appears to name.
    """
    slug = getattr(args, "target_repo", None)
    if slug is None:
        return owner, repo
    if REPO_SLUG_PATTERN.fullmatch(slug) is None:
        raise GitHubAPIError(
            f"Refusing the target repository {slug!r}: it must be a bare 'owner/repo' slug. This value is "
            f"interpolated into an API path."
        )
    target_owner, target_repo = slug.split("/", 1)
    return target_owner, target_repo


def _sha256_of_file(*, path: Path) -> str:
    """The sha256 of a local file, read whole.

    READ WHOLE rather than streamed, for two independent reasons. The immediate caller loads the SAME file
    entirely into memory two statements later as the POST body, so streaming the digest would save nothing it
    does not immediately spend; and `_fetch_log_content` and `_fetch_artifact_zip` beside it already
    `resp.read()` whole archives, so a whole-file read is this module's existing shape.

    It also keeps this function out of the `.open(` population the redirect policy's timeout invariant scans
    (`test_no_helper_passes_an_explicit_timeout`). MEASURED: a `Path.open` here was reported as a SEVENTH
    helper reaching the network, because that scanner matches any `.open(` call and a path's `open` is not an
    opener's. A function that does not call `.open(` at all cannot be confused for one.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_non_product_tag(*, tag: str) -> None:
    """Refuse a tag in the PRODUCT release namespace.

    CONSTRAINT 1. `.github/workflows/release.yml` triggers on `push: tags: "v*.*.*"`, and
    `test/ci/test_release_workflow.py`'s `test_release_triggers_on_semver_tags_only` pins that. A tag in
    that shape would create a public PRODUCT release and fire all four release jobs — and because this
    wrapper authenticates with a PAT rather than the workflow's `GITHUB_TOKEN`, GitHub's usual
    suppression of workflow-triggered-by-workflow does NOT apply, so the cascade would actually run.

    Engine assets therefore live in a DISTINCT, non-semver namespace. Refused here rather than merely
    documented, because the failure mode is a published product release that nobody asked for.
    """
    if SEMVER_TAG_PATTERN.match(tag):
        raise GitHubAPIError(
            f"Refusing the release tag {tag!r}: it matches the product-release shape 'v*.*.*' that "
            f".github/workflows/release.yml triggers on, so publishing under it would fire the whole "
            f"product release pipeline. Use a non-semver namespace such as "
            f"'{ASSET_TAG_NAMESPACE_EXAMPLE}'."
        )


def _assert_asset_part(*, value: str, option: str) -> None:
    """Refuse a value that is not, WHOLE, one component of a release path (`ASSET_PART_PATTERN`; issue #509).

    The value is interpolated into a credential-carrying API path, and `quote()` keeps `/`, so a `--tag` such as
    `../../x` would address a different endpoint than the one it appears to name. `_assert_non_product_tag` checks
    only the `v*.*.*` prefix, so it is no substitute. Called by each command before its first request, which is what
    makes the refusal cover every release resolver the command can reach.
    """
    if ASSET_PART_PATTERN.fullmatch(value) is None:
        raise GitHubAPIError(
            f"Refusing the {option} value {value!r}: it must be one path component, a letter or digit followed "
            f"only by letters, digits, '.', '_' or '-'. This value is interpolated into an API path."
        )


def _assert_contents_path(*, value: str) -> None:
    """Refuse a `--path` that is not a plain path inside the repository (E5.20; issue #509).

    The value is interpolated into the credential-carrying `/repos/{owner}/{repo}/contents/{quote(path)}`, and `quote()`
    keeps `/`, so an empty, `.` or `..` segment of `value.split("/")`, which also catches a leading or a trailing `/`,
    would address a different endpoint than the one it appears to name. A backslash and a NUL are refused as well.
    Called before the command's first request and before anything prints the value.
    """
    if any(segment in ("", ".", "..") for segment in value.split("/")) or "\\" in value or "\x00" in value:
        raise GitHubAPIError(
            f"Refusing the --path value {value!r}: it must be a plain path inside the repository, with no empty, '.' "
            f"or '..' segment, no leading '/', no backslash and no NUL. This value is interpolated into an API path."
        )


def _fetch_release_asset(
    *,
    url: str,
    token: str,
    method: str,
    accept: str,
    data: bytes | None = None,
    content_type: str | None = None,
    opener: OpenerDirector | None = None,
) -> bytes:
    """Perform ONE release-asset request and return its body — a Tier B helper (issue #432).

    ONE function that builds the request AND opens it, which is the shape every other helper in this module
    has, and the shape its redirect policy's source-scanning invariants require. An earlier revision split
    these into a request BUILDER and a transport so that a test could observe the built request; measured,
    that split violated four of those invariants at once — a function attaching `HEADER_AUTH` without calling
    an opener factory, a third `build_opener` site outside the two factories, a seventh `Request`
    construction site, and a `# nosec B310` the policy had removed. The seam moved to the OPENER instead,
    which observes strictly more: a fake opener still receives the fully-built `Request`.

    THREE THINGS THIS DOES THAT `_api_request` CANNOT, which is why it exists at all:

    * **An explicitly ABSOLUTE url.** Release assets upload to `uploads.github.com`, addressed through the
      hypermedia `upload_url` template the release object returns — a different host. `_api_request` prefixes
      `API_BASE` to any relative path and would mis-address it.
    * **A BINARY content type and body.** `_api_request` JSON-encodes its body unconditionally; this one
      carries 3.4 MB of ONNX.
    * **Tier B rather than Tier A.** The asset endpoints are documented as possibly answering 302 to a
      storage host, and that host rejects a request carrying a GitHub `Authorization` header — the same
      condition the log and artifact downloads are on Tier B for. `_build_download_opener()` follows the
      redirect with the credential STRIPPED; the Tier A opener would refuse it outright.

    An `HTTPError` becomes a `GitHubAPIError` carrying its status and, as `details`, GitHub's error body through
    `_http_error_details`, as `_api_request`'s does, so `main()` logs GitHub's reason for an upload's 422 (E5.27).
    """
    if not url.startswith("https://"):
        raise GitHubAPIError(f"Refusing to call non-HTTPS URL: {url}")
    req = Request(url=url, method=method, data=data)
    req.add_header(HEADER_ACCEPT, accept)
    req.add_header(HEADER_AUTH, f"Bearer {token}")
    req.add_header(HEADER_UA, USER_AGENT)
    req.add_header(HEADER_API_VERSION, API_VERSION)
    if content_type is not None:
        req.add_header("Content-Type", content_type)
    # REASSIGNED rather than bound to a second name, so the receiver of `.open(` is spelled `opener` exactly
    # as it is in the other six helpers. That spelling is load-bearing: the redirect policy's timeout
    # invariant asserts the receiver by NAME, so a helper opening on a differently-named local reports itself
    # instead of silently sitting outside the scan.
    opener = opener if opener is not None else _build_download_opener()
    try:
        with opener.open(req) as resp:
            return resp.read()
    except HTTPError as exc:
        raise GitHubAPIError(
            f"Release-asset request {method} failed: HTTP {exc.code}",
            status_code=exc.code,
            details=_http_error_details(exc=exc),
        ) from exc


def _expand_upload_url(*, template: str, asset_name: str) -> str:
    """Turn the release object's `upload_url` hypermedia template into a concrete URL.

    The template GitHub returns looks like
    `https://uploads.github.com/repos/o/r/releases/1/assets{?name,label}`. The RFC 6570 expansion
    suffix is cut and `name` supplied explicitly. Validated to be on the upload host rather than
    assumed: the template is server-supplied, and this url receives a Bearer PAT.
    """
    base = template.split("{", 1)[0]
    if not base.startswith(UPLOAD_HOST_PREFIX):
        raise GitHubAPIError(
            f"Refusing an upload_url that is not on {UPLOAD_HOST_PREFIX}: {base!r}. The release object's "
            f"template is server-supplied and this request carries a credential."
        )
    return f"{base}?name={quote(asset_name, safe='')}"


def _resolve_or_create_release(
    *, token: str, owner: str, repo: str, tag: str, notes: str | None = None
) -> dict[str, Any]:
    """Return the release for `tag`, creating it if absent. Idempotent, like `set-variable`.

    A failing create PROPAGATES — this is a resolve-or-create, not a silent fallback.

    `notes` replaces the generic body when a caller supplies one. That matters for a COPYLEFT artefact:
    the release page is the one piece of text served publicly beside the bytes, so it is where a
    conversion's upstream, its converter version and its GPL-3.0 section 5(a) modification notice can be
    read by whoever downloads the file — the served directory's own `SOURCE.json` reaches only someone
    who already has a build.
    """
    try:
        return _api_request(method="GET", path=f"/repos/{owner}/{repo}/releases/tags/{quote(tag)}", token=token)
    except GitHubAPIError as exc:
        if exc.status_code != HTTP_NOT_FOUND:
            raise
    created = _api_request(
        method="POST",
        path=f"/repos/{owner}/{repo}/releases",
        token=token,
        body={
            FIELD_TAG_NAME: tag,
            FIELD_NAME: tag,
            FIELD_BODY: notes if notes else ASSET_RELEASE_BODY,
            FIELD_DRAFT: False,
        },
    )
    print(f"created release {tag}")
    return created


def _resolve_existing_release(*, token: str, owner: str, repo: str, tag: str) -> dict[str, Any]:
    """Return the release for `tag`, which must already exist: `upload-release-asset --require-existing-release`.

    The GET by tag of `_resolve_or_create_release` and nothing after it (E5.9; issue #509). A 404 becomes a
    `GitHubAPIError` that names the tag and says nothing was created, and no POST is ever sent, so an upload into a
    release that is missing stops rather than creating it. Any other error propagates, as it does there.
    """
    try:
        return _api_request(method="GET", path=f"/repos/{owner}/{repo}/releases/tags/{quote(tag)}", token=token)
    except GitHubAPIError as exc:
        if exc.status_code != HTTP_NOT_FOUND:
            raise
        raise GitHubAPIError(
            f"Refusing to upload to release {tag!r} of {owner}/{repo}: it does not exist, and "
            f"--require-existing-release never creates one, so nothing was created.",
            status_code=exc.status_code,
        ) from exc


def _releases_of_tag(*, token: str, owner: str, repo: str, tag: str) -> list[dict[str, Any]]:
    """Every release of `tag`, drafts included, read through the authenticated release listing (issue #702, C3).

    The listing is the one documented way to find a draft: "Get a release by tag name" is "Get a published release
    with the specified tag", "Get a release" by id "Gets a public release", and of "List releases", "Only users with
    push access will receive listings for draft releases" (https://docs.github.com/en/rest/releases/releases). Pages
    are read with `per_page` pinned to the cap, constant across pages as `cmd_get_issue_comments` keeps it, until a
    short page ends the list. A page that is not a JSON list, and an entry that is not a JSON object, are each a
    `GitHubAPIError`. Every request is a GET.
    """
    path = f"/repos/{owner}/{repo}/releases"
    found: list[dict[str, Any]] = []
    page = 1
    while True:
        answer = _api_request(method="GET", path=f"{path}?per_page={GITHUB_MAX_PER_PAGE}&page={page}", token=token)
        if not isinstance(answer, list):
            raise GitHubAPIError(f"GET {path} answered {type(answer).__name__}, not a JSON list")
        for release in answer:
            if not isinstance(release, dict):
                raise GitHubAPIError(f"GET {path} answered a release that is {type(release).__name__}, not an object")
            if release.get(FIELD_TAG_NAME) == tag:
                found.append(release)
        if len(answer) < GITHUB_MAX_PER_PAGE:
            return found
        page += 1


def _draft_of_tag(*, releases: list[dict[str, Any]], owner: str, repo: str, tag: str) -> dict[str, Any]:
    """The one draft among `releases`, `_releases_of_tag`'s answer for `tag`, refusing any other count (issue #702).

    A release is a draft when its `draft` is `true`. Unless exactly one is, the refusal names the count; a draft whose
    `id` is not an `int` is refused as `_release_to_rewrite` refuses one, so no path is built from it.
    """
    drafts = [release for release in releases if release.get(FIELD_DRAFT) is True]
    if len(drafts) != 1:
        raise GitHubAPIError(
            f"Refusing release {tag!r} of {owner}/{repo}: its authenticated release listing holds {len(drafts)} "
            f"drafts of that tag, and exactly one is required."
        )
    release_id = drafts[0].get(FIELD_ID)
    if not isinstance(release_id, int):
        raise GitHubAPIError(
            f"The release listing of {owner}/{repo} answered a draft of {tag!r} whose {FIELD_ID} is "
            f"{type(release_id).__name__}, not an integer"
        )
    return drafts[0]


def _assert_no_published_release(*, token: str, owner: str, repo: str, tag: str) -> None:
    """Refuse a `tag` that has a published release: the GET by tag must answer 404 (issue #702).

    Any other error propagates, as it does in `_resolve_existing_release`, and any answer is the refusal, so a command
    that acts only on a draft never acts beside a published release of the same tag.
    """
    try:
        _api_request(method="GET", path=f"/repos/{owner}/{repo}/releases/tags/{quote(tag)}", token=token)
    except GitHubAPIError as exc:
        if exc.status_code == HTTP_NOT_FOUND:
            return
        raise
    raise GitHubAPIError(
        f"Refusing release {tag!r} of {owner}/{repo}: a published release of that tag exists, and this command acts "
        f"only on a draft. Nothing has been written."
    )


def _resolve_draft_release(*, token: str, owner: str, repo: str, tag: str) -> dict[str, Any]:
    """The one draft of `tag`: `upload-release-asset --require-draft-release` (issue #702, AC-3.3).

    A published release of the tag is refused, then the draft is read through the listing by `_draft_of_tag`, so no
    draft, more than one, or a draft whose `id` is not an `int` is refused before any upload, and nothing is created.
    """
    _assert_no_published_release(token=token, owner=owner, repo=repo, tag=tag)
    releases = _releases_of_tag(token=token, owner=owner, repo=repo, tag=tag)
    return _draft_of_tag(releases=releases, owner=owner, repo=repo, tag=tag)


def _existing_asset(*, release: dict[str, Any], asset_name: str) -> dict[str, Any] | None:
    """The already-published asset of that name on this release, or `None`.

    An array `next`, never a dict lookup: the asset list is server-supplied data, and this repository's
    lookup discipline is an iteration over a list rather than indexing a plain object.
    """
    assets = release.get(FIELD_ASSETS)
    if not isinstance(assets, list):
        return None
    return next((item for item in assets if isinstance(item, dict) and item.get(FIELD_NAME) == asset_name), None)


def _read_back_digest(*, token: str, owner: str, repo: str, asset_id: int, opener: OpenerDirector | None) -> str:
    """RE-DOWNLOAD the published asset and return the sha256 of the bytes actually served.

    CONSTRAINT 2, half two. A confirm-read on the API RESPONSE cannot substitute for this: a GitHub
    asset object carries `name`, `size`, `state` and a server-computed `digest`, which may be null, and the
    re-download stays because it verifies the bytes actually served. So the only way to know the
    published bytes are the bytes intended is to fetch them back and hash them.

    `Accept: application/octet-stream` is what makes the asset endpoint serve bytes rather than JSON; it
    answers 302 to a storage host, which is why this goes through the no-redirect transport.
    """
    body = _fetch_release_asset(
        url=f"{API_BASE}/repos/{owner}/{repo}/releases/assets/{asset_id}",
        token=token,
        method="GET",
        accept=CONTENT_TYPE_OCTET_STREAM,
        opener=opener,
    )
    return hashlib.sha256(body).hexdigest()


def cmd_upload_release_asset(
    token: str, owner: str, repo: str, args: argparse.Namespace, opener: OpenerDirector | None = None
) -> int:
    """Create-or-reuse a release by tag, upload a local file as an asset, then CONFIRM-READ the bytes.

    DIGEST-GATED IN BOTH DIRECTIONS (CONSTRAINT 2), and that is the point rather than belt-and-braces.
    Every other byte promotion in this chain verifies before committing — the HTTP adapter's `.tmp` then
    `os.replace`, the Producer's own post-conversion check, `fetch-engine.mjs`'s temp-then-verify-then-
    rename, the browser's verify-before-cache. An unverified publish would be the only one, and the
    hazard is concrete: the maintainer host legitimately holds TWO outputs of the same conversion
    differing by sixteen bytes of 3.4 MB, plus whatever earlier runs left behind.

    So `--expected-sha256` is REQUIRED. There is no un-gated upload path through this subcommand at all,
    which is stronger than checking a flag: a caller cannot forget the gate, only supply a wrong digest,
    and a wrong digest fails before any byte leaves the host.

    A release asset is immutable only by CONVENTION — it can be replaced under a fixed tag, unlike a
    content-addressed revision URL. `--replace` exists for a partially-completed publish and says so
    loudly, because without it a half-finished publish would be unrecoverable through the wrapper and
    the alternative is a forbidden `curl`.

    `--require-existing-release` (E5.9; issue #509) is read with `getattr`, so a `Namespace` without it keeps the
    behaviour above. With it, the release is resolved through `_resolve_existing_release` instead: the GET by tag
    alone, so a release that does not exist is refused and never created. `--notes-file` matters only when a release
    is created, which is why argparse refuses the two options together (E5.10).

    `--require-draft-release` (issue #702, AC-3.3), read with `getattr` in the same way, resolves the release through
    `_resolve_draft_release` instead: the tag's one draft, found through the authenticated release listing, and never a
    published release or a created one. argparse makes it exclusive with both options above. The digest gate before
    any request and the read-back after the upload are the same on every path.
    """
    owner, repo = _target_repo(owner=owner, repo=repo, args=args)
    path = Path(args.file)
    if not path.is_file():
        raise GitHubAPIError(f"No such file to upload: {path}")
    _assert_asset_part(value=args.tag, option="--tag")
    _assert_non_product_tag(tag=args.tag)

    local = _sha256_of_file(path=path)
    if local != args.expected_sha256:
        raise GitHubAPIError(
            f"Refusing to upload {path.name}: its sha256 is {local} but {args.expected_sha256} was "
            f"expected. Nothing has been published. On a host that has run the producer more than once "
            f"the likeliest cause is the wrong file — the raw conversion rather than the normalised one."
        )
    asset_name = args.name or path.name
    if getattr(args, "require_draft_release", False):
        release = _resolve_draft_release(token=token, owner=owner, repo=repo, tag=args.tag)
    elif getattr(args, "require_existing_release", False):
        release = _resolve_existing_release(token=token, owner=owner, repo=repo, tag=args.tag)
    else:
        notes = Path(args.notes_file).read_text(encoding="utf-8") if args.notes_file else None
        release = _resolve_or_create_release(token=token, owner=owner, repo=repo, tag=args.tag, notes=notes)

    existing = _existing_asset(release=release, asset_name=asset_name)
    if existing is not None:
        if not args.replace:
            raise GitHubAPIError(
                f"Release {args.tag} already carries an asset named {asset_name!r} (id "
                f"{existing.get(FIELD_ID)}). A published asset is not overwritten silently: re-run with "
                f"--replace if you intend to replace those bytes."
            )
        _api_request(
            method="DELETE",
            path=f"/repos/{owner}/{repo}/releases/assets/{existing.get(FIELD_ID)}",
            token=token,
        )
        print(f"deleted the existing asset {asset_name} (id {existing.get(FIELD_ID)})")

    upload_url = _expand_upload_url(template=str(release.get(FIELD_UPLOAD_URL, "")), asset_name=asset_name)
    uploaded_body = _fetch_release_asset(
        url=upload_url,
        token=token,
        method="POST",
        accept=ACCEPT_JSON,
        data=path.read_bytes(),
        content_type=CONTENT_TYPE_OCTET_STREAM,
        opener=opener,
    )
    uploaded = json.loads(uploaded_body.decode("utf-8")) if uploaded_body else {}
    asset_id = uploaded.get(FIELD_ID)
    if not isinstance(asset_id, int):
        raise GitHubAPIError(f"The upload response carried no asset id: {uploaded!r}")
    print(f"uploaded {asset_name} (id {asset_id}, size {uploaded.get(FIELD_SIZE)})")
    print(f"DOWNLOAD URL       : {uploaded.get(FIELD_BROWSER_DOWNLOAD_URL)}")

    served = _read_back_digest(token=token, owner=owner, repo=repo, asset_id=asset_id, opener=opener)
    print(f"CONFIRM-READ SHA256: {served}")
    if served != args.expected_sha256:
        logger.error(
            "confirm-read MISMATCH for %s: the published asset serves %s but %s was expected. Treat the "
            "publish as NOT performed and do not resolve any manifest pin against it.",
            asset_name,
            served,
            args.expected_sha256,
        )
        return 1
    return EXIT_OK


def _latest_release_tag(*, token: str, owner: str, repo: str) -> str | None:
    """The `tag_name` of the repository's latest release, from `GET /repos/{owner}/{repo}/releases/latest` (#509).

    `None` when that endpoint answers 404, which `get-release` prints as `LATEST     : None`. Any other HTTP error
    propagates, and an answer that is not a JSON object is a `GitHubAPIError` rather than a printed tag.
    """
    path = f"/repos/{owner}/{repo}/releases/latest"
    try:
        latest = _api_request(method="GET", path=path, token=token)
    except GitHubAPIError as exc:
        if exc.status_code != HTTP_NOT_FOUND:
            raise
        return None
    if not isinstance(latest, dict):
        raise GitHubAPIError(f"GET {path} answered {type(latest).__name__}, not a JSON object")
    return latest.get(FIELD_TAG_NAME)


def _confirm_read_body(*, written: bytes, expected: str) -> int:
    """Compare the sha256 of bytes a read just wrote with `expected`, print the verdict, and return the exit status.

    A match prints `CONFIRM-READ BODY : match <expected>` and returns 0. A mismatch prints
    `CONFIRM-READ BODY : MISMATCH`, `EXPECTED : <expected>` and `SERVED : <length> <sha256>` and returns 1. The
    caller writes its file before calling this, so the file is written either way (issue #509).
    """
    served = hashlib.sha256(written).hexdigest()
    if served == expected:
        print(f"{CONFIRM_READ_BODY_MATCH} {expected}")
        return EXIT_OK
    print(CONFIRM_READ_BODY_MISMATCH)
    print(f"EXPECTED : {expected}")
    print(f"SERVED : {len(written)} {served}")
    return 1


def _confirm_written_body(*, local: bytes, served: bytes) -> int:
    """Compare a write's confirm-read with the local bytes it sent, print the verdict, and return the exit status.

    The write side of `_confirm_read_body`, which compares with an expected digest instead (issue #509). A match prints
    `CONFIRM-READ BODY : match <sha256 of the local bytes>`, the line the Pin Commit's evidence coupling reads, and
    returns 0. A mismatch prints `CONFIRM-READ BODY : MISMATCH`, `LOCAL  : <length> <sha256>`,
    `SERVED : <length> <sha256>` and `FIRST DIFFERENCE AT : <offset>`, and returns 1. The offset is that of the first
    byte the two differ at, or the shorter length when one extends the other.
    """
    local_sha256 = hashlib.sha256(local).hexdigest()
    if served == local:
        print(f"{CONFIRM_READ_BODY_MATCH} {local_sha256}")
        return EXIT_OK
    first_difference = next(
        (offset for offset, (sent, got) in enumerate(zip(local, served)) if sent != got), min(len(local), len(served))
    )
    print(CONFIRM_READ_BODY_MISMATCH)
    print(f"LOCAL  : {len(local)} {local_sha256}")
    print(f"SERVED : {len(served)} {hashlib.sha256(served).hexdigest()}")
    print(f"FIRST DIFFERENCE AT : {first_difference}")
    return 1


def _release_or_draft_of_tag(*, token: str, owner: str, repo: str, tag: str, include_drafts: bool) -> Any:
    """`get-release`'s release: the published release of `tag`, or with `include_drafts` its one draft (issue #702).

    The GET by tag is today's read, and without `include_drafts` its answer and its errors are returned and raised as
    they always were. With it, a 404 is followed by the authenticated release listing: when that holds no draft of the
    tag the 404 is raised again, so it stands, and otherwise `_draft_of_tag` answers the one draft or refuses.
    """
    try:
        return _api_request(method="GET", path=f"/repos/{owner}/{repo}/releases/tags/{quote(tag)}", token=token)
    except GitHubAPIError as exc:
        if exc.status_code != HTTP_NOT_FOUND or not include_drafts:
            raise
        releases = _releases_of_tag(token=token, owner=owner, repo=repo, tag=tag)
        if not any(release.get(FIELD_DRAFT) is True for release in releases):
            raise
        return _draft_of_tag(releases=releases, owner=owner, repo=repo, tag=tag)


def cmd_get_release(token: str, owner: str, repo: str, args: argparse.Namespace) -> int:
    """Read one release by tag: its draft/prerelease state, its tag, and every asset it carries.

    The READ half of `upload-release-asset`, and it exists because the write half's confirm-read cannot
    see the two facts that decide whether a published asset is actually SERVABLE: a DRAFT release has no
    public `/releases/download/<tag>/` path at all, and a PRIVATE repository answers that path with 404 to
    an unauthenticated client. Both look identical from the API — the asset object is present and its
    bytes read back correctly — so diagnosing a 404 at `fetch:engine` without this is guesswork.

    Issue #509 adds what a publisher reads back: `IMMUTABLE`, the `LATEST` release's tag, and each asset's
    `digest`. `--body-out` writes the body's exact UTF-8 bytes with `write_bytes`, because `write_text`
    translates newlines on Windows; `--expected-body-sha256` then confirms those bytes, and without
    `--body-out` it is refused before any request. Both are read with `getattr`, so an older `Namespace` that
    lacks them keeps its behaviour.

    `--include-drafts` (issue #702, AC-3.5), read with `getattr` too, reports the tag's one draft when the GET by tag
    answers 404, through `_release_or_draft_of_tag`, in the same lines; with no draft of the tag the 404 stands.
    """
    owner, repo = _target_repo(owner=owner, repo=repo, args=args)
    _assert_asset_part(value=args.tag, option="--tag")
    body_out = getattr(args, "body_out", None)
    expected_body_sha256 = getattr(args, "expected_body_sha256", None)
    if expected_body_sha256 is not None and body_out is None:
        raise GitHubAPIError(
            "Refusing --expected-body-sha256 without --body-out: the read confirm hashes the body this command "
            "writes to --body-out. Nothing has been requested."
        )
    data = _release_or_draft_of_tag(
        token=token, owner=owner, repo=repo, tag=args.tag, include_drafts=bool(getattr(args, "include_drafts", False))
    )
    latest = _latest_release_tag(token=token, owner=owner, repo=repo)
    print(f"REPOSITORY : {owner}/{repo}")
    print(f"TAG        : {data.get(FIELD_TAG_NAME)}")
    print(f"DRAFT      : {data.get(FIELD_DRAFT)}")
    print(f"PRERELEASE : {data.get(FIELD_PRERELEASE)}")
    print(f"IMMUTABLE  : {data.get(FIELD_IMMUTABLE)}")
    print(f"LATEST     : {latest}")
    print(f"URL        : {data.get(FIELD_URL)}")
    assets = data.get(FIELD_ASSETS)
    for asset in assets if isinstance(assets, list) else []:
        print(
            f"  asset {asset.get(FIELD_NAME)} id={asset.get(FIELD_ID)} state={asset.get(FIELD_STATE)} "
            f"size={asset.get(FIELD_SIZE)}"
        )
        print(f"    download {asset.get(FIELD_BROWSER_DOWNLOAD_URL)}")
        print(f"    digest {asset.get(FIELD_DIGEST)}")
    if body_out is None:
        return EXIT_OK
    written = (data.get(FIELD_BODY) or "").encode("utf-8")
    Path(body_out).write_bytes(written)
    if expected_body_sha256 is None:
        return EXIT_OK
    return _confirm_read_body(written=written, expected=expected_body_sha256)


def cmd_repo_visibility(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Report whether this repository is PUBLIC or PRIVATE.

    Load-bearing for any artefact served from a release asset of THIS repository: a private repository
    answers `/releases/download/<tag>/<name>` with 404 to an unauthenticated client, and every consumer of
    a declared engine URL — `fetch:engine` on a developer machine, on a CI runner, in a release job — is
    unauthenticated by design. So the visibility is a precondition of the hosted-artefact model, not a
    detail, and it is READ rather than assumed.
    """
    owner, repo = _target_repo(owner=owner, repo=repo, args=args)
    data = _api_request(method="GET", path=f"/repos/{owner}/{repo}", token=token)
    print(f"REPOSITORY : {owner}/{repo}")
    print(f"VISIBILITY : {data.get(FIELD_VISIBILITY)}")
    print(f"PRIVATE    : {data.get(FIELD_PRIVATE)}")


def _contents_file_bytes(*, answer: Any, path: str) -> bytes:
    """The bytes of the file object a Contents API `GET {path}` answered, refusing an answer that is not one (E5.12).

    A file object is a JSON object whose `content` is a string, whose `encoding` is `base64` and whose `type` is
    `file`, and its bytes are `base64.b64decode(content, validate=False)`. An answer that is not a JSON object, a
    `content` that is absent or not a string, another `encoding`, another `type`, and a `content` whose decode raises
    `ValueError` (`binascii.Error`, or the plain one a non-ASCII `str` raises) are each a `GitHubAPIError`, which
    `main()` logs as one message with exit 1 (issue #509).
    """
    if not isinstance(answer, dict):
        raise GitHubAPIError(f"GET {path} answered {type(answer).__name__}, not a JSON object")
    content = answer.get(FIELD_CONTENT)
    if not isinstance(content, str):
        raise GitHubAPIError(
            f"GET {path} answered an object whose {FIELD_CONTENT} is {type(content).__name__}, not a string"
        )
    if answer.get(FIELD_ENCODING) != CONTENT_ENCODING_BASE64:
        raise GitHubAPIError(f"GET {path} answered an object whose {FIELD_ENCODING} is not {CONTENT_ENCODING_BASE64!r}")
    if answer.get(FIELD_TYPE) != CONTENT_KIND_FILE:
        raise GitHubAPIError(f"GET {path} answered an object whose {FIELD_TYPE} is not {CONTENT_KIND_FILE!r}")
    try:
        return base64.b64decode(content, validate=False)
    except ValueError as exc:  # binascii.Error is a ValueError, and a non-ASCII str raises a plain one
        raise GitHubAPIError(f"GET {path} answered a {FIELD_CONTENT} that base64 cannot decode: {exc}") from exc


def cmd_put_file(token: str, owner: str, repo: str, args: argparse.Namespace) -> int:
    """Create or update one file in a repository through the Contents API, producing a commit, then CONFIRM-READ it.

    EXISTS FOR A MEASURED REASON. `POST /releases` answers HTTP 422 `"Repository is empty."` on a repository
    with no commits, because a release needs a target commitish. The public assets repository this project
    publishes produced engine artefacts to was created empty, so it had to be given a first commit before
    any asset could be published to it — and an artefact repository wants a README and the licence text of
    what it serves anyway.

    `PUT /repos/{owner}/{repo}/contents/{path}` creates the file when no `sha` is supplied and updates it
    when one is, so the existing content is READ FIRST and its `sha` carried through. Without that, a second
    run answers 422 rather than updating, which would make this subcommand single-use.

    The bytes are base64-encoded, which is what that endpoint requires; `Path.read_bytes` keeps it honest
    for a non-UTF-8 file even though every current use is text.

    Issue #509 makes the write provable. A `--path` with an empty, `.` or `..` segment, a leading `/`, a backslash or a
    NUL is refused before any request and before anything prints it. `--expected-blob-sha S`, read with `getattr` so an
    older `Namespace` that lacks it keeps its behaviour, makes the write a compare-and-swap: unless the path holds blob
    `S` the command refuses before the PUT, and the PUT carries `S`, so a change in between is answered 409, whose
    GitHub error body `main()` logs as the `details`. After the PUT the path is read again, a malformed answer is a
    `GitHubAPIError`, and `_confirm_written_body` prints the verdict and returns the exit status.
    """
    owner, repo = _target_repo(owner=owner, repo=repo, args=args)
    _assert_contents_path(value=args.path)
    source = Path(args.file)
    if not source.is_file():
        raise GitHubAPIError(f"No such file to upload: {source}")
    expected_blob_sha = getattr(args, "expected_blob_sha", None)
    path = f"/repos/{owner}/{repo}/contents/{quote(args.path)}"
    existing_sha: str | None = None
    try:
        current = _api_request(method="GET", path=path, token=token)
        if isinstance(current, dict) and isinstance(current.get(FIELD_SHA), str):
            existing_sha = current[FIELD_SHA]
    except GitHubAPIError as exc:
        # A 404 is the CREATE case and is the expected answer on an empty repository. Anything else — a
        # permission failure, a rate limit — must propagate rather than be read as "absent".
        if exc.status_code != HTTP_NOT_FOUND:
            raise
    if expected_blob_sha is not None and existing_sha != expected_blob_sha:
        found = "no file" if existing_sha is None else f"the blob {_render_untrusted(value=existing_sha)}"
        raise GitHubAPIError(
            f"Refusing to write {args.path!r} in {owner}/{repo}: --expected-blob-sha is {expected_blob_sha!r}, but "
            f"the path holds {found}. Nothing has been written."
        )
    local = source.read_bytes()
    body: dict[str, Any] = {
        FIELD_MESSAGE: args.message,
        FIELD_CONTENT: base64.b64encode(local).decode("ascii"),
    }
    # With --expected-blob-sha the check above has made `existing_sha` equal to S, so the PUT carries S (E5.11).
    if existing_sha is not None:
        body[FIELD_SHA] = existing_sha
    result = _api_request(method="PUT", path=path, token=token, body=body)
    commit = result.get(FIELD_COMMIT) if isinstance(result, dict) else None
    print(f"{'updated' if existing_sha else 'created'} {owner}/{repo}:{args.path}")
    if isinstance(commit, dict):
        print(f"COMMIT     : {commit.get(FIELD_SHA)}")
    served = _contents_file_bytes(answer=_api_request(method="GET", path=path, token=token), path=path)
    return _confirm_written_body(local=local, served=served)


def _fetch_public_api(*, path: str, opener: OpenerDirector | None = None) -> Any:
    """Perform ONE anonymous GET of a public GitHub API path and return the decoded JSON (issue #509).

    The verifier's only API read: `_api_request`'s shape without the credential, on the Tier A opener, which
    refuses a redirect, because one would read a repository other than the one named. It takes no token. A `path`
    that is not root-relative is refused before any request, as `_api_request` refuses one, and the request carries
    only the `Accept`, `User-Agent` and API-version headers, each added with `add_header`, so neither header mapping
    of the request holds the credential's header. An `HTTPError` becomes a `GitHubAPIError` carrying its status,
    raised from that `HTTPError`, so the verifier reads the answer's `retry-after` and `x-ratelimit-reset` headers
    from its `__cause__` (E5.26, E10.4, E10.8).
    """
    if not path.startswith(PATH_ROOT) or path.startswith(PATH_PROTOCOL_RELATIVE):
        raise GitHubAPIError(f"Refusing a non-root-relative API path: {_render_untrusted(value=path)}")
    req = Request(url=f"{API_BASE}{path}", method="GET")
    req.add_header(HEADER_ACCEPT, ACCEPT_JSON)
    req.add_header(HEADER_UA, USER_AGENT)
    req.add_header(HEADER_API_VERSION, API_VERSION)
    opener = opener if opener is not None else _build_api_opener()
    try:
        with opener.open(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        raise GitHubAPIError(f"Public API GET failed: HTTP {exc.code}", status_code=exc.code) from exc


def _fetch_public_download(*, url: str, opener: OpenerDirector | None = None) -> bytes:
    """Perform ONE anonymous download from a public repository's release path and return its body (issue #509).

    `_fetch_release_asset`'s shape without the credential, on the Tier B download opener, which follows the redirect a
    release download may answer with to the host that stores its bytes. It takes no token, and it adds only the
    `Accept` and `User-Agent` headers, each with `add_header`, so neither header mapping of the request holds the
    credential's header. An `HTTPError` becomes a `GitHubAPIError` carrying its status, raised from that `HTTPError`,
    so `main()` logs one message and a caller reads the answer's `retry-after` and `x-ratelimit-reset` headers from its
    `__cause__` (E5.7, E5.12, E10.4).
    """
    if not url.startswith("https://"):
        raise GitHubAPIError(f"Refusing to call non-HTTPS URL: {url}")
    req = Request(url=url, method="GET")
    req.add_header(HEADER_ACCEPT, CONTENT_TYPE_OCTET_STREAM)
    req.add_header(HEADER_UA, USER_AGENT)
    opener = opener if opener is not None else _build_download_opener()
    try:
        with opener.open(req) as resp:
            return resp.read()
    except HTTPError as exc:
        raise GitHubAPIError(f"Public download failed: HTTP {exc.code}", status_code=exc.code) from exc


def _read_notes_file(*, notes_file: str) -> tuple[bytes, str]:
    """A notes file's bytes and their text, refusing bytes that are not UTF-8 or that hold a CR (E5.3 step 2).

    The bytes are decoded with `errors="strict"`, and a decode that fails is a `GitHubAPIError`, which `main()` logs as
    one message, rather than a `UnicodeDecodeError`. A Materialised Public Text is LF by construction, so a carriage
    return in the file is a defect. Both refusals come before any request (issue #509).
    """
    path = Path(notes_file)
    if not path.is_file():
        raise GitHubAPIError(f"No such notes file: {path}")
    local = path.read_bytes()
    try:
        text = local.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise GitHubAPIError(
            f"Refusing the notes file {path}: its bytes are not UTF-8 ({exc}). Nothing has been requested."
        ) from exc
    if "\r" in text:
        offset = local.index(b"\r")
        raise GitHubAPIError(
            f"Refusing the notes file {path}: it holds a carriage return at byte {offset}, and a public text is LF "
            f"only. Nothing has been requested."
        )
    return local, text


def _release_and_body(*, answer: Any, path: str) -> tuple[dict[str, Any], bytes]:
    """The release object a releases API `GET {path}` answered, and the UTF-8 bytes of its body (issue #509).

    A null body is `b""`, as `get-release --body-out` writes it. An answer that is not a JSON object, and a body that is
    neither a string nor null, are each a `GitHubAPIError`, which `main()` logs as one message (E5.12).
    """
    if not isinstance(answer, dict):
        raise GitHubAPIError(f"GET {path} answered {type(answer).__name__}, not a JSON object")
    body = answer.get(FIELD_BODY)
    if body is not None and not isinstance(body, str):
        raise GitHubAPIError(f"GET {path} answered a release whose {FIELD_BODY} is {type(body).__name__}, not a string")
    return answer, (body or "").encode("utf-8")


def _release_to_rewrite(
    *, token: str, owner: str, repo: str, tag: str, expected_latest: str, expected_body_sha256: str
) -> int:
    """The `id` of the release of `tag` whose notes `set-release-notes` rewrites, after its checks before the write.

    E5.3 steps 3-4 and E5.4, and every request here is a GET. The release is resolved by tag and never created, so a
    404 is the `GitHubAPIError` that `_api_request` raises and nothing is POSTed. A draft, a prerelease and an `id`
    that is not an `int` are refused, then a current body whose sha256 is not `expected_body_sha256` and a latest
    release other than `expected_latest`, each of those two refusals naming both values (issue #509).
    """
    path = f"/repos/{owner}/{repo}/releases/tags/{quote(tag)}"
    release, body = _release_and_body(answer=_api_request(method="GET", path=path, token=token), path=path)
    for field, kind in ((FIELD_DRAFT, "a draft"), (FIELD_PRERELEASE, "a prerelease")):
        if release.get(field):
            raise GitHubAPIError(
                f"Refusing to rewrite the notes of release {tag!r} in {owner}/{repo}: it is {kind}. Nothing has been "
                f"written."
            )
    release_id = release.get(FIELD_ID)
    if not isinstance(release_id, int):
        raise GitHubAPIError(
            f"GET {path} answered a release whose {FIELD_ID} is {type(release_id).__name__}, not an integer"
        )
    current = hashlib.sha256(body).hexdigest()
    if current != expected_body_sha256:
        raise GitHubAPIError(
            f"Refusing to rewrite the notes of release {tag!r} in {owner}/{repo}: its current body has sha256 "
            f"{current}, but --expected-body-sha256 is {expected_body_sha256!r}. Nothing has been written."
        )
    latest = _latest_release_tag(token=token, owner=owner, repo=repo)
    if latest != expected_latest:
        found = "no release is the latest" if latest is None else f"the latest is {_render_untrusted(value=latest)}"
        raise GitHubAPIError(
            f"Refusing to rewrite the notes of release {tag!r} in {owner}/{repo}: --expected-latest is "
            f"{expected_latest!r}, but {found}. Nothing has been written."
        )
    return release_id


def cmd_set_release_notes(token: str, owner: str, repo: str, args: argparse.Namespace) -> int:
    """Replace one release's notes with a local file's text, then CONFIRM-READ the stored body (issue #509).

    E5.3, E5.4 and E5.14, in order. All five options are REQUIRED, `--target-repo` among them, and each is read with
    `getattr`: the command is new, so nothing depends on a default, and an absent one is refused before any request.
    Before its one write the command shape-checks the target, refuses a `--tag` or an `--expected-latest` that is not
    one asset part and a `--tag` in the product namespace `v*.*.*`, and reads the notes file, refusing bytes that are
    not UTF-8 or that hold a CR. `_release_to_rewrite` then refuses a release that does not exist, is a draft or a
    prerelease, or has an `id` that is not an `int`, a current body whose sha256 is not `--expected-body-sha256`, and a
    latest release other than `--expected-latest`.

    The write is a PATCH of exactly `body` and `make_latest`, sent explicitly because the Update endpoint defaults it
    to `true`. The release and the latest release are then read again: `_confirm_written_body` prints the body's
    verdict, `LATEST : <tag> (expected <L>)` follows, and the exit status is 1 when the stored body's bytes are not the
    file's or the latest release is not `--expected-latest`. A latest release that moved is reported and never moved
    back: there is no restore path.
    """
    tag = getattr(args, "tag", None)
    notes_file = getattr(args, "notes_file", None)
    expected_latest = getattr(args, "expected_latest", None)
    expected_body_sha256 = getattr(args, "expected_body_sha256", None)
    if None in (tag, notes_file, getattr(args, "target_repo", None), expected_latest, expected_body_sha256):
        raise GitHubAPIError(
            "Refusing set-release-notes: --tag, --notes-file, --target-repo, --expected-latest and "
            "--expected-body-sha256 are all required. Nothing has been requested."
        )
    owner, repo = _target_repo(owner=owner, repo=repo, args=args)
    _assert_asset_part(value=tag, option="--tag")
    _assert_asset_part(value=expected_latest, option="--expected-latest")
    _assert_non_product_tag(tag=tag)
    local, text = _read_notes_file(notes_file=notes_file)
    release_id = _release_to_rewrite(
        token=token,
        owner=owner,
        repo=repo,
        tag=tag,
        expected_latest=expected_latest,
        expected_body_sha256=expected_body_sha256,
    )
    path = f"/repos/{owner}/{repo}/releases/{release_id}"
    make_latest = MAKE_LATEST_TRUE if tag == expected_latest else MAKE_LATEST_FALSE
    _api_request(method="PATCH", path=path, token=token, body={FIELD_BODY: text, FIELD_MAKE_LATEST: make_latest})
    _, served = _release_and_body(answer=_api_request(method="GET", path=path, token=token), path=path)
    latest = _latest_release_tag(token=token, owner=owner, repo=repo)
    status = _confirm_written_body(local=local, served=served)
    print(f"LATEST : {latest} (expected {expected_latest})")
    return status if latest == expected_latest else 1


def _assert_draft_verb_values(*, tag: str, expected_latest: str) -> None:
    """The shape checks `create-draft-release` and `publish-release` share before any request (issue #702).

    `--tag` and `--expected-latest` must each be one asset part, and `--tag` outside the product namespace `v*.*.*`, as
    `set-release-notes` checks them; `_target_repo` checks the slug at each command's own first line.
    """
    _assert_asset_part(value=tag, option="--tag")
    _assert_asset_part(value=expected_latest, option="--expected-latest")
    _assert_non_product_tag(tag=tag)


def _assert_expected_latest(*, token: str, owner: str, repo: str, expected_latest: str, action: str) -> None:
    """Refuse, before a write, a latest release other than `expected_latest`, naming both, as `_release_to_rewrite`
    does; `action` says what was not done (issue #702)."""
    latest = _latest_release_tag(token=token, owner=owner, repo=repo)
    if latest != expected_latest:
        found = "no release is the latest" if latest is None else f"the latest is {_render_untrusted(value=latest)}"
        raise GitHubAPIError(
            f"Refusing to {action} in {owner}/{repo}: --expected-latest is {expected_latest!r}, but {found}. Nothing "
            f"has been written."
        )


def cmd_create_draft_release(token: str, owner: str, repo: str, args: argparse.Namespace) -> int:
    """Create one DRAFT release of `--tag` with a notes file's text as its body, then CONFIRM-READ it (issue #702).

    AC-3.1 and AC-3.2. Before its one write the command shape-checks the slug, `--tag` and `--expected-latest`,
    refuses a `--tag` in the product namespace and a `--target-commitish` that is not 40 lowercase hex characters, and
    reads the notes file, refusing bytes that are not UTF-8 or that hold a CR. It then refuses a published release of
    the tag (the GET by tag must answer 404), any release of the tag in the authenticated listing, which is where a
    draft is, and a latest release other than `--expected-latest`.

    The write is one POST of `tag_name`, `name` (the tag), `body`, `draft` true and `target_commitish`, and no
    `make_latest`, because "Drafts and prereleases cannot be set as latest". The listing is then read again: its one
    draft of the tag must be the created id, `RELEASE ID : <id>` and `_confirm_written_body`'s verdict over its body are
    printed, the latest release is read and `LATEST : <tag> (expected <L>)` follows, and the exit status is 1 when the
    stored body's bytes are not the file's or the latest release is not `--expected-latest`.
    """
    tag, expected_latest, commitish = args.tag, args.expected_latest, args.target_commitish
    owner, repo = _target_repo(owner=owner, repo=repo, args=args)
    _assert_draft_verb_values(tag=tag, expected_latest=expected_latest)
    if COMMITISH_PATTERN.fullmatch(commitish) is None:
        raise GitHubAPIError(
            f"Refusing the --target-commitish value {commitish!r}: it must be a full commit sha, 40 lowercase hex "
            f"characters. Nothing has been requested."
        )
    local, text = _read_notes_file(notes_file=args.notes_file)
    _assert_no_published_release(token=token, owner=owner, repo=repo, tag=tag)
    existing = _releases_of_tag(token=token, owner=owner, repo=repo, tag=tag)
    if existing:
        raise GitHubAPIError(
            f"Refusing to create a draft of {tag!r} in {owner}/{repo}: its release listing already holds "
            f"{len(existing)} release(s) of that tag. Nothing has been written."
        )
    _assert_expected_latest(
        token=token, owner=owner, repo=repo, expected_latest=expected_latest, action=f"create a draft of {tag!r}"
    )
    path = f"/repos/{owner}/{repo}/releases"
    body: dict[str, Any] = {
        FIELD_TAG_NAME: tag,
        FIELD_NAME: tag,
        FIELD_BODY: text,
        FIELD_DRAFT: True,
        FIELD_TARGET_COMMITISH: commitish,
    }
    created = _api_request(method="POST", path=path, token=token, body=body)
    created_id = created.get(FIELD_ID) if isinstance(created, dict) else None
    if not isinstance(created_id, int):
        raise GitHubAPIError(f"POST {path} answered no integer {FIELD_ID}: {type(created_id).__name__}")
    draft = _draft_of_tag(
        releases=_releases_of_tag(token=token, owner=owner, repo=repo, tag=tag), owner=owner, repo=repo, tag=tag
    )
    if draft[FIELD_ID] != created_id:
        raise GitHubAPIError(
            f"The release listing's one draft of {tag!r} in {owner}/{repo} is id {draft[FIELD_ID]}, but the create "
            f"answered id {created_id}."
        )
    print(f"RELEASE ID : {created_id}")
    _, served = _release_and_body(answer=draft, path=path)
    status = _confirm_written_body(local=local, served=served)
    latest = _latest_release_tag(token=token, owner=owner, repo=repo)
    print(f"LATEST : {latest} (expected {expected_latest})")
    return status if latest == expected_latest else 1


def _confirm_published(*, answer: Any, release_id: int, tag: str, path: str) -> int:
    """`publish-release`'s confirm of the GET by tag after its PATCH: the same id, neither a draft nor a prerelease.

    A match prints `PUBLISHED : <tag> id=<id>` and returns 0; a mismatch logs what the tag resolved to, each served
    value through `_render_untrusted`, and returns 1. An answer that is not a JSON object is a `GitHubAPIError`.
    """
    if not isinstance(answer, dict):
        raise GitHubAPIError(f"GET {path} answered {type(answer).__name__}, not a JSON object")
    served_id, draft, prerelease = answer.get(FIELD_ID), answer.get(FIELD_DRAFT), answer.get(FIELD_PRERELEASE)
    if isinstance(served_id, int) and served_id == release_id and draft is False and prerelease is False:
        print(f"PUBLISHED : {tag} id={release_id}")
        return EXIT_OK
    logger.error(
        "confirm-read MISMATCH for release %r: GET %s answered id=%s draft=%s prerelease=%s, but id=%s, neither a "
        "draft nor a prerelease, was expected. Nothing is restored.",
        tag,
        path,
        _render_untrusted(value=served_id),
        _render_untrusted(value=draft),
        _render_untrusted(value=prerelease),
        release_id,
    )
    return 1


def cmd_publish_release(token: str, owner: str, repo: str, args: argparse.Namespace) -> int:
    """Publish the one draft of `--tag`, never as the latest release, then CONFIRM-READ it (issue #702, AC-3.4).

    Before its one write the command makes `create-draft-release`'s shape checks of the slug, `--tag` and
    `--expected-latest`, refuses a published release of the tag, reads the one draft through the authenticated listing
    with `_draft_of_tag`, which refuses no draft, more than one, or an `id` that is not an `int`, and refuses a latest
    release other than `--expected-latest`.

    The write is one PATCH of exactly `draft` false and `make_latest` `"false"` (`MAKE_LATEST_FALSE`), sent because the
    Update endpoint "Defaults to true for newly published releases". The GET by tag must then answer the same id,
    neither a draft nor a prerelease, through `_confirm_published`; the latest release is read and
    `LATEST : <tag> (expected <L>)` follows; the exit status is 1 on any mismatch, and nothing is restored, as
    `set-release-notes` restores nothing.
    """
    tag, expected_latest = args.tag, args.expected_latest
    owner, repo = _target_repo(owner=owner, repo=repo, args=args)
    _assert_draft_verb_values(tag=tag, expected_latest=expected_latest)
    _assert_no_published_release(token=token, owner=owner, repo=repo, tag=tag)
    draft = _draft_of_tag(
        releases=_releases_of_tag(token=token, owner=owner, repo=repo, tag=tag), owner=owner, repo=repo, tag=tag
    )
    release_id: int = draft[FIELD_ID]
    _assert_expected_latest(
        token=token, owner=owner, repo=repo, expected_latest=expected_latest, action=f"publish release {tag!r}"
    )
    _api_request(
        method="PATCH",
        path=f"/repos/{owner}/{repo}/releases/{release_id}",
        token=token,
        body={FIELD_DRAFT: False, FIELD_MAKE_LATEST: MAKE_LATEST_FALSE},
    )
    by_tag = f"/repos/{owner}/{repo}/releases/tags/{quote(tag)}"
    answer = _api_request(method="GET", path=by_tag, token=token)
    status = _confirm_published(answer=answer, release_id=release_id, tag=tag, path=by_tag)
    latest = _latest_release_tag(token=token, owner=owner, repo=repo)
    print(f"LATEST : {latest} (expected {expected_latest})")
    return status if latest == expected_latest else 1


def cmd_get_file(token: str, owner: str, repo: str, args: argparse.Namespace) -> int:
    """Read one file of a repository through the Contents API and write its exact bytes (issue #509).

    The independent read-back of what `put-file` writes, and read-only: ONE `GET /repos/{owner}/{repo}/contents/{path}`
    and no write. The `--path` is refused before that request, as `put-file` refuses it, and an answer that is not a
    file object whose `encoding` is `base64` and whose `content` decodes is a `GitHubAPIError` from
    `_contents_file_bytes` (E5.12). The decoded bytes are written to `--out` with `write_bytes`, because `write_text`
    translates newlines on Windows, and then the file object's `path`, blob `sha` and `size` are printed.

    `--expected-sha256`, read with `getattr` as `get-release` reads `--expected-body-sha256`, is the same read confirm:
    `_confirm_read_body` prints the match line, or `MISMATCH` with `EXPECTED` and `SERVED`, and returns the exit
    status. The file is written either way.
    """
    owner, repo = _target_repo(owner=owner, repo=repo, args=args)
    _assert_contents_path(value=args.path)
    expected_sha256 = getattr(args, "expected_sha256", None)
    path = f"/repos/{owner}/{repo}/contents/{quote(args.path)}"
    answer = _api_request(method="GET", path=path, token=token)
    content = _contents_file_bytes(answer=answer, path=path)
    Path(args.out).write_bytes(content)
    print(f"PATH       : {answer.get(FIELD_PATH)}")
    print(f"SHA        : {answer.get(FIELD_SHA)}")
    print(f"SIZE       : {answer.get(FIELD_SIZE)}")
    if expected_sha256 is None:
        return EXIT_OK
    return _confirm_read_body(written=content, expected=expected_sha256)


def cmd_download_public_asset(
    token: str, owner: str, repo: str, args: argparse.Namespace, opener: OpenerDirector | None = None
) -> int:
    """Download one release asset of a public repository anonymously, gated on its sha256 (issue #509).

    E5.7, E5.16 and E5.17. The handler begins `del token`, so the credential `main()` loads is never used: the one
    request goes through `_fetch_public_download`, which carries none. All five options are REQUIRED and each is read
    with `getattr`, so an absent one is refused before any request; `--target-repo` among them, because this checkout
    is private and answers the download path 404 to an anonymous client. `--target-repo`, `--tag` and `--name` are each
    checked whole, and the URL is built from the three checked parts rather than accepted whole.

    The bytes are written to `<F>.tmp` with `write_bytes`, never through `.open(`, and the sha256 of that file is
    compared with `--expected-sha256`. A match moves it to `F` and prints `SHA256 : <hex> (matches)`; a mismatch
    removes it, writes no file at `F`, logs both digests and returns 1. `opener` reaches the helper as the tests' seam;
    `main()` never passes it, so production always takes the download opener factory.
    """
    del token
    tag = getattr(args, "tag", None)
    name = getattr(args, "name", None)
    out = getattr(args, "out", None)
    expected_sha256 = getattr(args, "expected_sha256", None)
    if None in (getattr(args, "target_repo", None), tag, name, out, expected_sha256):
        raise GitHubAPIError(
            "Refusing download-public-asset: --target-repo, --tag, --name, --out and --expected-sha256 are all "
            "required. Nothing has been requested."
        )
    owner, repo = _target_repo(owner=owner, repo=repo, args=args)
    _assert_asset_part(value=tag, option="--tag")
    _assert_asset_part(value=name, option="--name")
    url = f"{WEB_BASE}/{owner}/{repo}/releases/download/{quote(tag)}/{quote(name)}"
    destination = Path(out)
    partial = destination.with_name(f"{destination.name}.tmp")
    partial.write_bytes(_fetch_public_download(url=url, opener=opener))
    served = _sha256_of_file(path=partial)
    if served != expected_sha256:
        partial.unlink()
        logger.error(
            "download MISMATCH for %s: the served bytes have sha256 %s but %s was expected. Nothing has been "
            "written at %s.",
            url,
            served,
            expected_sha256,
            destination,
        )
        return 1
    partial.replace(destination)
    print(f"SHA256 : {served} (matches)")
    return EXIT_OK


def _latest_release_summary(*, release: Any, slug: str) -> dict[str, Any]:
    """The `tag_name` of `release`, GitHub's answer to the latest-release read of `slug`, and each asset's `name` and
    `digest` in the answer's order, a null digest kept as `None` (issue #1248, design C6).

    An answer that is not a JSON object, or whose `assets` is not a list of JSON objects, is a `GitHubAPIError`, which
    `main()` logs as one message with exit 1, rather than a summary that reads as a release with no asset.
    """
    assets = release.get(FIELD_ASSETS) if isinstance(release, dict) else None
    if not isinstance(assets, list) or not all(isinstance(asset, dict) for asset in assets):
        raise GitHubAPIError(f"The latest release of {slug} answered no release object with a list of {FIELD_ASSETS}")
    return {
        FIELD_TAG_NAME: release.get(FIELD_TAG_NAME),
        FIELD_ASSETS: [{FIELD_NAME: asset.get(FIELD_NAME), FIELD_DIGEST: asset.get(FIELD_DIGEST)} for asset in assets],
    }


def cmd_get_public_latest_release(
    token: str, owner: str, repo: str, args: argparse.Namespace, opener: OpenerDirector | None = None
) -> int:
    """Print the latest release of a public repository, read with no credential, as one JSON object (issue #1248, C6).

    ONE `GET /repos/{owner}/{repo}/releases/latest`, which answers "the most recent non-prerelease, non-draft release",
    whose every asset carries a `digest` that is "required, string or null"
    (https://docs.github.com/en/rest/releases/releases#get-the-latest-release). The handler begins `del token`, as
    `cmd_download_public_asset` does, and `main()` loads none for it (`CREDENTIAL_FREE_COMMANDS`): the request goes
    through `_fetch_public_api`, which carries no credential. `--target-repo` is required and checked by `_target_repo`
    before any request, because this checkout is private and an anonymous read of it addresses no upstream. The one
    line printed holds `tag_name` and, under `assets`, each asset's `name` and `digest` (`_latest_release_summary`).
    GitHub's 404, a repository with no published release or none at all, is a `GitHubAPIError` naming the repository,
    which `main()` logs with exit 1. `opener` reaches the helper as the tests' seam; `main()` never passes it.
    """
    del token
    if getattr(args, "target_repo", None) is None:
        raise GitHubAPIError(
            f"Refusing {CMD_GET_PUBLIC_LATEST_RELEASE}: --target-repo is required. Nothing has been requested."
        )
    owner, repo = _target_repo(owner=owner, repo=repo, args=args)
    path = f"/repos/{owner}/{repo}/releases/latest"
    try:
        release = _fetch_public_api(path=path, opener=opener)
    except GitHubAPIError as exc:
        if exc.status_code != HTTP_NOT_FOUND:
            raise
        raise GitHubAPIError(
            f"{owner}/{repo} has no latest release to read: GET {path} answered HTTP {HTTP_NOT_FOUND}, so the "
            f"repository has no published release or does not exist.",
            status_code=HTTP_NOT_FOUND,
        ) from exc
    print(json.dumps(_latest_release_summary(release=release, slug=f"{owner}/{repo}")))
    return EXIT_OK


def cmd_create_pr(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    body = {
        FIELD_TITLE: args.title or args.head,
        FIELD_HEAD: args.head,
        FIELD_BASE: args.base,
    }
    resolved_body = _resolve_body(args=args)
    if resolved_body:
        body[FIELD_BODY] = resolved_body
    data = _api_request(
        method="POST",
        path=f"/repos/{owner}/{repo}/pulls",
        token=token,
        body=body,
    )
    print(json.dumps(data, indent=2))


def cmd_get_pr(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    data = _api_request(
        method="GET",
        path=f"/repos/{owner}/{repo}/pulls/{args.pr_number}",
        token=token,
    )
    print(json.dumps(data, indent=2))


def cmd_get_pr_checks(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Report the combined CI state for a PR's head commit.

    Combines the modern Checks API (``check-runs``) with the legacy commit-status
    API (``statuses``); the orchestrator polls this to decide when CI is green.
    """
    pr = _api_request(
        method="GET",
        path=f"/repos/{owner}/{repo}/pulls/{args.pr_number}",
        token=token,
    )
    head_sha = pr[FIELD_HEAD][FIELD_SHA]
    check_runs = _api_request(
        method="GET",
        path=f"/repos/{owner}/{repo}/commits/{head_sha}/check-runs?per_page=100",
        token=token,
    )
    combined = _api_request(
        method="GET",
        path=f"/repos/{owner}/{repo}/commits/{head_sha}/status",
        token=token,
    )
    summary = {
        FIELD_HEAD: head_sha,
        FIELD_MERGEABLE: pr.get(FIELD_MERGEABLE),
        FIELD_MERGEABLE_STATE: pr.get(FIELD_MERGEABLE_STATE),
        "combined_status": combined.get(FIELD_STATE),
        FIELD_CHECK_RUNS: [
            {
                FIELD_NAME: run[FIELD_NAME],
                FIELD_STATUS: run[FIELD_STATUS],
                FIELD_CONCLUSION: run.get(FIELD_CONCLUSION),
            }
            for run in check_runs.get(FIELD_CHECK_RUNS, [])
        ],
        FIELD_STATUSES: [
            {
                FIELD_CONTEXT: status[FIELD_CONTEXT],
                FIELD_STATE: status[FIELD_STATE],
                FIELD_DESCRIPTION: status.get(FIELD_DESCRIPTION),
            }
            for status in combined.get(FIELD_STATUSES, [])
        ],
    }
    print(json.dumps(summary, indent=2))


def cmd_approve_pr(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Submit an APPROVE review on a PR.

    GitHub forbids approving your own PR; on that 422 the orchestrator falls back to
    polling for an external approval (see issue-work-orchestrator).
    """
    body: dict[str, Any] = {FIELD_EVENT: "APPROVE"}
    if args.body:
        body[FIELD_BODY] = args.body
    data = _api_request(
        method="POST",
        path=f"/repos/{owner}/{repo}/pulls/{args.pr_number}/reviews",
        token=token,
        body=body,
    )
    print(json.dumps(data, indent=2))


def cmd_merge_pr(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    body: dict[str, Any] = {FIELD_MERGE_METHOD: args.method}
    if args.commit_message:
        body[FIELD_COMMIT_MESSAGE] = args.commit_message
    data = _api_request(
        method="PUT",
        path=f"/repos/{owner}/{repo}/pulls/{args.pr_number}/merge",
        token=token,
        body=body,
    )
    print(json.dumps(data, indent=2))


def cmd_delete_remote_branch(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    _api_request(
        method="DELETE",
        path=f"/repos/{owner}/{repo}/git/refs/heads/{args.branch}",
        token=token,
    )
    print(f"Deleted remote branch: {args.branch}")


GITHUB_MAX_PER_PAGE = 100  # GitHub REST caps per_page at 100; larger values are silently clamped


def cmd_list_issues(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """List up to ``--limit`` issues, paginating past GitHub's 100-per-page cap.

    The previous implementation sent ``per_page=<limit>`` with no ``page`` parameter, so a
    ``--limit`` above one page silently returned page 1 only — duplicate checks against older
    issues never saw them (observed by four intake runs, 2026-09-05/06). The endpoint also
    interleaves pull requests with issues; PRs are filtered locally and do NOT count toward the
    limit, so pagination continues until ``--limit`` issues are printed or the last page is
    exhausted. ``per_page`` stays constant across pages — GitHub page boundaries are only
    coherent for a fixed page size.
    """
    printed = 0
    page = 1
    while printed < args.limit:
        params = [f"state={args.state}", f"per_page={GITHUB_MAX_PER_PAGE}", f"page={page}"]
        if args.labels:
            params.append(f"labels={args.labels}")
        if args.assignee:
            params.append(f"assignee={args.assignee}")
        data = _api_request(
            method="GET",
            path=f"/repos/{owner}/{repo}/issues?" + "&".join(params),
            token=token,
        )
        for issue in data:
            if "pull_request" in issue:
                continue
            print(f"#{issue[FIELD_NUMBER]:<6} {issue[FIELD_STATE]:<8} {issue[FIELD_TITLE]}")
            printed += 1
            if printed >= args.limit:
                break
        if len(data) < GITHUB_MAX_PER_PAGE:
            break
        page += 1


def cmd_get_issue(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    data = _api_request(
        method="GET",
        path=f"/repos/{owner}/{repo}/issues/{args.issue_number}",
        token=token,
    )
    print(json.dumps(data, indent=2))


def cmd_get_issue_comments(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Print EVERY comment of an issue as one JSON list, paginating past GitHub's per-page cap.

    The previous implementation sent no ``per_page`` and no ``page`` parameter, so GitHub served
    its default first page of 30 and the rest of the list was silently missing: issue #515 carried
    52 comments while ``get-issue-comments 515`` printed 30 (measured 2026-10-03). Pages are read
    with ``per_page`` pinned to the cap, constant across pages as ``cmd_list_issues`` keeps it,
    until a short page ends the list.
    """
    comments: list[Any] = []
    page = 1
    while True:
        data = _api_request(
            method="GET",
            path=f"/repos/{owner}/{repo}/issues/{args.issue_number}/comments?per_page={GITHUB_MAX_PER_PAGE}&page={page}",
            token=token,
        )
        comments.extend(data)
        if len(data) < GITHUB_MAX_PER_PAGE:
            break
        page += 1
    print(json.dumps(comments, indent=2))


def _resolve_body(args: argparse.Namespace) -> str | None:
    """Return the markdown body from ``--body`` or ``--body-file``, whichever was supplied.

    ``--body-file`` exists because long, structured markdown (evidence tables, fenced command
    output, backticks, ``$``, ``!``) passed through ``--body`` on a shell command line is subject
    to the shell's own expansion and quoting rules, which has silently MANGLED posted comments in
    practice. Reading the text from a file bypasses shell interpretation entirely, so what is on
    disk is exactly what is posted. The file is read as UTF-8 with ``pathlib.Path``
    (``.claude/rules/coding-standards.md`` item 10).

    Returns ``None`` when neither option was supplied, so callers that treat the body as optional
    (``update-issue``, ``create-issue``, ``approve-pr``) keep their existing semantics; supplying
    both is a usage error rather than a silent precedence rule.
    """
    body_file = getattr(args, "body_file", None)
    body = getattr(args, "body", None)
    if body_file is not None and body is not None:
        raise GitHubAPIError("pass either --body or --body-file, not both")
    if body_file is not None:
        return Path(body_file).read_text(encoding="utf-8")
    return body


def cmd_comment_issue(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    body = _resolve_body(args=args)
    if body is None:
        raise GitHubAPIError("comment-issue requires --body or --body-file")
    data = _api_request(
        method="POST",
        path=f"/repos/{owner}/{repo}/issues/{args.issue_number}/comments",
        token=token,
        body={FIELD_BODY: body},
    )
    print(json.dumps(data, indent=2))


def cmd_delete_issue_comment(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Delete ONE issue comment by its comment id, then verify it is gone.

    Added because `comment-issue` has no undo and a duplicate is easy to create: a caller that
    re-runs the command to capture the returned URL posts the body twice, and on an issue several
    sibling runs read as the live record, a duplicated contract comment is noise that misleads.

    The comment id is NOT the issue number — take it from `get-issue-comments`, whose entries carry
    `"id"`. Deleting by issue number is impossible by construction here, because the API path this
    calls is the comment resource itself.

    FAIL-CLOSED, in the shape `start-issue` established: the DELETE is followed by a confirm-read
    that must return 404. A 204 alone is GitHub reporting that it accepted the request; only the
    re-read establishes the resulting state, and this command is destructive, so it is the one place
    a wrong answer cannot be walked back.
    """
    path = f"/repos/{owner}/{repo}/issues/comments/{args.comment_id}"
    _api_request(method="DELETE", path=path, token=token)
    try:
        _api_request(method="GET", path=path, token=token)
    except GitHubAPIError as exc:
        if exc.status_code == HTTP_NOT_FOUND:
            print(json.dumps({FIELD_ID: args.comment_id, "deleted": True}, indent=2))
            return
        raise
    raise GitHubAPIError(
        f"comment {args.comment_id} still resolves after DELETE — it was NOT deleted",
    )


def cmd_update_issue(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    body: dict[str, Any] = {}
    resolved_body = _resolve_body(args=args)
    if args.title is not None:
        body[FIELD_TITLE] = args.title
    if resolved_body is not None:
        body[FIELD_BODY] = resolved_body
    if args.state is not None:
        body[FIELD_STATE] = args.state
    if args.labels is not None:
        body[FIELD_LABELS] = [s.strip() for s in args.labels.split(",") if s.strip()]
    if not body:
        raise GitHubAPIError("update-issue requires at least one of --title, --body/--body-file, --state, --labels")
    data = _api_request(
        method="PATCH",
        path=f"/repos/{owner}/{repo}/issues/{args.issue_number}",
        token=token,
        body=body,
    )
    print(json.dumps(data, indent=2))


def _issue_path(*, owner: str, repo: str, issue_number: int) -> str:
    return f"/repos/{owner}/{repo}/issues/{issue_number}"


def cmd_reopen_issue(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Reopen an issue, then RE-READ it and fail closed unless it now reads ``open``.

    How a close made over unfinished checklist items is undone (``issue-tracking.md`` Closing,
    ``/close-session`` step 2). Idempotent: an issue that is already open is reported and not written.
    Re-claiming it afterwards is ``start-issue``'s job, not this one's.
    """
    path = _issue_path(owner=owner, repo=repo, issue_number=args.issue_number)
    before = _api_request(method="GET", path=path, token=token)
    if before.get(FIELD_STATE) == ISSUE_STATE_OPEN:
        print(json.dumps({KEY_ISSUE: args.issue_number, FIELD_STATE: ISSUE_STATE_OPEN, KEY_CHANGED: False}))
        return
    _api_request(method="PATCH", path=path, token=token, body={FIELD_STATE: ISSUE_STATE_OPEN})
    after = _api_request(method="GET", path=path, token=token)
    if after.get(FIELD_STATE) != ISSUE_STATE_OPEN:
        raise GitHubAPIError(
            f"issue #{args.issue_number} still reads state={after.get(FIELD_STATE)!r} after the reopen PATCH",
        )
    print(json.dumps({KEY_ISSUE: args.issue_number, FIELD_STATE: ISSUE_STATE_OPEN, KEY_CHANGED: True}))


def _checklist_items(*, body: str) -> list[tuple[int, re.Match[str]]]:
    """Every task-list line of ``body`` as ``(line index, match)``; line endings are not part of a match."""
    items: list[tuple[int, re.Match[str]]] = []
    for index, line in enumerate(body.split("\n")):
        match = CHECKLIST_ITEM_RE.match(line.rstrip("\r"))
        if match is not None:
            items.append((index, match))
    return items


def _checklist_counts(*, body: str) -> dict[str, Any]:
    items = _checklist_items(body=body)
    unticked = [m.group("text") for _, m in items if m.group("mark") == CHECK_MARK_UNTICKED]
    return {KEY_TICKED: len(items) - len(unticked), KEY_TOTAL: len(items), KEY_UNTICKED: unticked}


def _flip_checklist_item(*, body: str, needle: str, to_mark: str) -> str:
    """Return ``body`` with exactly ONE item containing ``needle`` flipped to ``to_mark``.

    Only items currently in the OTHER state are candidates, so ticking a ticked item is not a match.
    Zero or several candidates raise, naming them: a checklist write must never guess which line.
    """
    from_ticked = to_mark == CHECK_MARK_UNTICKED
    candidates = [
        (index, match)
        for index, match in _checklist_items(body=body)
        if needle in match.group("text") and (match.group("mark") != CHECK_MARK_UNTICKED) == from_ticked
    ]
    if len(candidates) != 1:
        names = [m.group("text") for _, m in candidates]
        raise GitHubAPIError(f"--tick/--untick {needle!r} must match exactly one item; matched {names}")
    index, match = candidates[0]
    lines = body.split("\n")
    ending = "\r" if lines[index].endswith("\r") else ""
    lines[index] = f"{match.group('lead')}{to_mark}{match.group('tail')}{match.group('text')}{ending}"
    return "\n".join(lines)


def cmd_checklist(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Count an issue's task list, or tick/untick ONE item by substring and RE-READ to verify it.

    The task-item gate's arithmetic (``issue-tracking.md`` Closing, ``/close-session`` step 2): without
    an action it prints ``ticked``/``total`` and the unticked items from a fresh read of the body.
    """
    path = _issue_path(owner=owner, repo=repo, issue_number=args.issue_number)
    body = str(_api_request(method="GET", path=path, token=token).get(FIELD_BODY) or "")
    needle = args.tick if args.tick is not None else args.untick
    if needle is None:
        print(json.dumps({KEY_ISSUE: args.issue_number, **_checklist_counts(body=body)}))
        return
    to_mark = CHECK_MARK_TICKED if args.tick is not None else CHECK_MARK_UNTICKED
    new_body = _flip_checklist_item(body=body, needle=needle, to_mark=to_mark)
    _api_request(method="PATCH", path=path, token=token, body={FIELD_BODY: new_body})
    reread = str(_api_request(method="GET", path=path, token=token).get(FIELD_BODY) or "")
    if reread != new_body:
        raise GitHubAPIError(f"issue #{args.issue_number}: the checklist write did not land (body differs on re-read)")
    print(json.dumps({KEY_ISSUE: args.issue_number, KEY_ITEM: needle, **_checklist_counts(body=reread)}))


def cmd_create_issue(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    body: dict[str, Any] = {FIELD_TITLE: args.title}
    resolved_body = _resolve_body(args=args)
    if resolved_body:
        body[FIELD_BODY] = resolved_body
    if args.labels:
        body[FIELD_LABELS] = [s.strip() for s in args.labels.split(",") if s.strip()]
    data = _api_request(
        method="POST",
        path=f"/repos/{owner}/{repo}/issues",
        token=token,
        body=body,
    )
    print(json.dumps(data, indent=2))


def _extract_issue_id(issue: dict[str, Any]) -> int:
    """Return the internal numeric ``id`` from a GitHub issue object.

    The issue-dependencies and sub-issues write endpoints identify the *other* issue by its
    internal database ``id`` (the ``issue_id`` / ``sub_issue_id`` body field), NOT by the
    human-facing ``number`` in the URL — see
    https://docs.github.com/en/rest/issues/issue-dependencies and
    https://docs.github.com/en/rest/issues/sub-issues. Callers therefore resolve a number to
    an id via ``GET /issues/{number}`` first; this pure helper isolates that extraction so it
    can be unit-tested without a live API.
    """
    raw = issue.get(FIELD_ID)
    if not isinstance(raw, int):
        raise GitHubAPIError(f"Issue object has no integer '{FIELD_ID}' field to resolve to an internal id.")
    return raw


def _resolve_issue_id(*, token: str, owner: str, repo: str, number: int) -> int:
    """Resolve a human issue ``number`` to its internal numeric ``id`` via the issues API."""
    issue = _api_request(method="GET", path=f"/repos/{owner}/{repo}/issues/{number}", token=token)
    return _extract_issue_id(issue)


def _dependency_entry(*, entry: Any, list_key: str) -> dict[str, Any]:
    """Project one dependency or sub-issue Entry to the four keys the output carries (PURE — no network).

    THE single producer for all three lists (``blocked_by``, ``blocking``, ``sub_issues``). Three inline
    comprehensions is how this defect came to exist in three places at once, so the next field added
    here must not be addable to only two of them; ``test_the_state_projection_has_one_producer`` asserts
    on the SOURCE that the state projection lives nowhere else.

    The three REQUIRED keys raise ``GitHubAPIError``, never ``KeyError``: ``main``'s only handler around
    the dispatch is ``except GitHubAPIError``, so a bare ``KeyError`` escapes it and reaches the operator
    as a traceback naming neither the issue, the list, nor the entry — from a read-only diagnostic.
    ``number`` is validated FIRST and its message names the LIST, because without a usable ``number``
    there is nothing else to identify the entry by; ``title`` and ``state`` then name the number.

    ``number``'s TYPE is checked, not only its presence, and that is load-bearing rather than tidy.
    ``main`` makes TWO stderr writes per raise and only the second is serialized: ``logger.error(str(exc))``
    runs unconditionally with no serializer, and the ``Details:`` write that follows goes through
    ``json.dumps``. Since the message below interpolates ``number``, a string ``number`` would put raw
    ESC/NUL/BEL, a bidirectional override and a forged ``ERROR:`` line on the operator's terminal;
    measured, only ``str`` does this, because ``format()`` falls back to ``repr()`` for containers.
    Requiring an ``int`` makes the message provably non-hostile by construction and leaves ``details=``
    as the place the offending value is shown, escaped. ``bool`` is excluded because it is an ``int``
    subclass, and a JSON ``true`` would otherwise be emitted as a ``number`` that the downstream
    verifier's ``int()`` silently resolves to 1.

    ``state`` is INDEXED and ``state_reason`` uses ``.get`` on purpose. ``state`` is documented
    "required, string", and a null one has no legitimate meaning — a consumer testing
    ``state == "closed"`` would read it as live, which is the very ambiguity this command was fixed to
    remove. ``state_reason`` is documented "string or null" (enum: completed, reopened, not_planned,
    duplicate, null) and IS null on every open issue, so an absent key and a null value mean the same
    thing to a reader.

    Do not confuse the output's top-level ``blocked_by`` and ``blocking`` (LISTS of these Entries) with
    ``issue_dependencies_summary.blocked_by`` and ``.blocking`` (INTEGER counts of OPEN relationships).
    """
    number = entry.get(FIELD_NUMBER) if isinstance(entry, dict) else None
    if not isinstance(number, int) or isinstance(number, bool):
        raise GitHubAPIError(
            f"An entry of '{list_key}' is not a JSON object carrying an integer '{FIELD_NUMBER}'.",
            details=entry,
        )
    for field in (FIELD_TITLE, FIELD_STATE):
        if field not in entry:
            raise GitHubAPIError(f"Entry #{number} of '{list_key}' has no '{field}'.", details=entry)
    return {
        FIELD_NUMBER: number,
        FIELD_TITLE: entry[FIELD_TITLE],
        FIELD_STATE: entry[FIELD_STATE],
        FIELD_STATE_REASON: entry.get(FIELD_STATE_REASON),
    }


def _read_entry_list(*, token: str, path: str) -> list[Any]:
    """GET one Entry List Endpoint and return its array, or raise naming that endpoint.

    THE single producer for all three Entry List reads. Two things live here exactly once: the
    ``2026-03-10`` pin those three endpoints are documented under (see the comment above
    ``API_VERSION_DEPENDENCIES``), and the check that what came back IS a JSON array.

    MEASURED reason for the check — a projection over a non-array payload does not fail loudly.
    ``{}`` and ``""`` both iterate zero times and project to ``[]``, which renders as "no blockers":
    the same false negative this command was fixed to remove, reached by a different route and
    invisible because it also exits 0. ``None`` and an API error body raise ``TypeError``, which
    ``main``'s only handler around the dispatch (``except GitHubAPIError``) does not catch. An empty
    array is NOT an error and must stay one: an all-empty subject is a normal, live case.

    This RAISES; it never warns and continues. The only downstream consumer of this command's output
    parses ``stdout + stderr`` as one JSON document, so a diagnostic written on a zero-exit run breaks
    its parse outright — a non-zero exit is what makes a diagnostic safe.

    The element type is deliberately NOT asserted here — ``list[Any]``, not ``list[dict[str, Any]]``.
    Per-entry validation belongs to ``_dependency_entry``, which names the offending entry; claiming
    the stronger type here would assert a guarantee this function does not check.
    """
    payload = _api_request(method="GET", path=path, token=token, api_version=API_VERSION_DEPENDENCIES)
    if not isinstance(payload, list):
        raise GitHubAPIError(f"Unexpected payload from GET {path}: expected a JSON array of issues.", details=payload)
    return payload


def cmd_link_issue(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Add a native ``blocked_by`` dependency: ``issue_number`` is blocked by ``blocked_by``.

    Uses the issue-dependencies API
    (https://docs.github.com/en/rest/issues/issue-dependencies). The blocking issue is
    identified by its internal ``id`` in the body, so its number is resolved first. The
    reciprocal ``blocking`` view is maintained by GitHub automatically.
    """
    blocking_id = _resolve_issue_id(token=token, owner=owner, repo=repo, number=args.blocked_by)
    data = _api_request(
        method="POST",
        path=f"/repos/{owner}/{repo}/issues/{args.issue_number}/dependencies/blocked_by",
        token=token,
        body={FIELD_ISSUE_ID: blocking_id},
        api_version=API_VERSION_DEPENDENCIES,
    )
    print(json.dumps(data, indent=2))


def cmd_unlink_issue(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Remove a native ``blocked_by`` dependency: ``issue_number`` is no longer blocked by ``blocked_by``.

    The inverse of :func:`cmd_link_issue`, and it exists because a wrong dependency edge is worse
    than a missing one: the graph is what a later reader trusts to decide what is actionable, and
    while the blocking issue is OPEN the edge is counted live — `link-issue 257 --blocked-by 253`,
    issued in error, is the case this command was commissioned for. Once that blocker CLOSES GitHub
    discounts it from the live ``blocked_by`` count (measured on #388: ``blocked_by: 0`` against
    ``total_blocked_by: 3``), so what survives is not an inflated live count but an assertion that no
    longer holds — one that still counts in ``total_blocked_by``, and that epic #410's decision-14
    convention forbids against merged work. Without a removal path the only options were to leave the
    wrong edge in place or to reach for `curl`, which `use-git-wrapper-scripts.md` forbids ("extend
    the wrapper rather than bypassing it").

    Uses ``DELETE /repos/{owner}/{repo}/issues/{issue_number}/dependencies/blocked_by/{issue_id}``
    (https://docs.github.com/en/rest/issues/issue-dependencies). Note the asymmetry with the POST
    form: the blocking issue is identified by its internal ``id`` in the URL PATH here, not in a
    body — so its number is resolved first, exactly as ``link-issue`` does. The reciprocal
    ``blocking`` view is maintained by GitHub automatically.
    """
    blocking_id = _resolve_issue_id(token=token, owner=owner, repo=repo, number=args.blocked_by)
    data = _api_request(
        method="DELETE",
        path=f"/repos/{owner}/{repo}/issues/{args.issue_number}/dependencies/blocked_by/{blocking_id}",
        token=token,
        api_version=API_VERSION_DEPENDENCIES,
    )
    print(json.dumps(data, indent=2))


def cmd_add_sub_issue(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Attach ``sub_issue`` as a sub-issue of the parent ``issue_number``.

    Uses the sub-issues API (https://docs.github.com/en/rest/issues/sub-issues). The child is
    identified by its internal ``id`` in the body, so its number is resolved first.
    """
    sub_id = _resolve_issue_id(token=token, owner=owner, repo=repo, number=args.sub_issue)
    data = _api_request(
        method="POST",
        path=f"/repos/{owner}/{repo}/issues/{args.issue_number}/sub_issues",
        token=token,
        body={FIELD_SUB_ISSUE_ID: sub_id},
        api_version=API_VERSION_DEPENDENCIES,
    )
    print(json.dumps(data, indent=2))


def cmd_get_issue_dependencies(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Print the ``blocked_by`` list, ``blocking`` list, and sub-issues for an issue.

    Read-only verification companion to ``link-issue`` / ``add-sub-issue`` so the native graph
    can be confirmed from the wrapper (per no-guessing) rather than assumed.

    Every Entry carries its live ``state`` and ``state_reason``, and the subject issue's own two summary
    objects are passed through verbatim, so the output also answers "how much of this epic is left?"
    from GitHub's own counts rather than from a count derived here.

    The four reads deliberately use TWO api versions: the three list endpoints are pinned to
    ``2026-03-10`` because they are documented only there, while the subject read goes out under the
    module default, because both summary objects are measurably identical across the two versions.
    """
    base = f"/repos/{owner}/{repo}/issues/{args.issue_number}"
    blocked_by = _read_entry_list(token=token, path=f"{base}/dependencies/blocked_by?per_page=100")
    blocking = _read_entry_list(token=token, path=f"{base}/dependencies/blocking?per_page=100")
    sub_issues = _read_entry_list(token=token, path=f"{base}/sub_issues?per_page=100")
    subject = _fetch_issue(token=token, owner=owner, repo=repo, number=args.issue_number)
    summary = {
        FIELD_NUMBER: args.issue_number,
        FIELD_ISSUE_DEPENDENCIES_SUMMARY: subject.get(FIELD_ISSUE_DEPENDENCIES_SUMMARY),
        FIELD_SUB_ISSUES_SUMMARY: subject.get(FIELD_SUB_ISSUES_SUMMARY),
        KEY_BLOCKED_BY: [_dependency_entry(entry=entry, list_key=KEY_BLOCKED_BY) for entry in blocked_by],
        KEY_BLOCKING: [_dependency_entry(entry=entry, list_key=KEY_BLOCKING) for entry in blocking],
        KEY_SUB_ISSUES: [_dependency_entry(entry=entry, list_key=KEY_SUB_ISSUES) for entry in sub_issues],
    }
    print(json.dumps(summary, indent=2))


# ============================================================================================
# In-progress lifecycle + work discovery (mutual exclusion across concurrent workers)
# --------------------------------------------------------------------------------------------
# WHY THIS EXISTS: multiple workers (agents and humans) share one repo. Without a claim signal,
# two of them can independently start the SAME issue and duplicate the work. These commands make
# the ``in-progress`` label (LABEL_IN_PROGRESS) the single, shared claim mechanism and give
# workers a first-class way to (a) claim an issue, (b) release it, and (c) DISCOVER what is free
# to work on vs. already taken.
#
# WORKER PROTOCOL — every worker MUST follow this before touching any issue's code:
#   1. Run ``list-available`` to see OPEN, NOT-in-progress issues (the pool of free work).
#      Never start an issue that is not in this list.
#   2. ``claim-issue <n>`` to add the in-progress label BEFORE creating a branch/worktree or
#      writing code. This publishes your claim so sibling workers skip it.
#   3. Do the work; keep the issue updated (see issue-tracking rule).
#   4. On finishing: close the issue (``update-issue <n> --state closed``); the label is moot
#      once closed. If you STOP WITHOUT FINISHING (blocked, handing off, abandoning): run
#      ``release-issue <n>`` so the issue returns to the ``list-available`` pool for others.
#   5. Use ``list-in-progress`` to audit what is currently claimed (and by the checklist/comments,
#      by whom) — e.g. before picking up "stalled" work, confirm no one else is live on it.
#
# These operations are label-PRESERVING: they add/remove ONLY the in-progress label and leave
# every other label on the issue intact (unlike ``update-issue --labels``, which REPLACES the
# whole label set and would silently drop ``enhancement``/``bug``/etc.).
# ============================================================================================


def _current_label_names(*, token: str, owner: str, repo: str, number: int) -> list[str]:
    """Return the issue's current label names (a fresh GET, so we never clobber siblings' labels).

    The GitHub "set labels" endpoint REPLACES the full set, so claim/release must first read the
    live labels and then write back the union/difference — never a blind overwrite.
    """
    issue = _api_request(method="GET", path=f"/repos/{owner}/{repo}/issues/{number}", token=token)
    return [label[FIELD_NAME] for label in issue.get(FIELD_LABELS, [])]


def _replace_labels(*, token: str, owner: str, repo: str, number: int, labels: list[str]) -> Any:
    """PATCH the issue's label set to exactly ``labels`` (caller has already computed the union/diff)."""
    return _api_request(
        method="PATCH",
        path=f"/repos/{owner}/{repo}/issues/{number}",
        token=token,
        body={FIELD_LABELS: labels},
    )


# --------------------------------------------------------------------------------------------
# ADDITIVE label / assignee primitives — the non-destructive path
# --------------------------------------------------------------------------------------------
# GitHub exposes endpoints that mutate ONE label or ONE assignee without restating the rest, and
# these wrap exactly those. They exist because the alternative — read the whole set, then write the
# whole set back — has a race window between the read and the write in which a concurrent worker's
# change is silently overwritten. `.claude/rules/issue-tracking.md` names that hazard directly: the
# plain `labels` field is "a **full replace** that silently drops other labels and has repeatedly
# caused the in-progress label to vanish and duplicate work".
#
# Endpoint shapes verified against the GitHub REST documentation (not assumed):
#   - https://docs.github.com/en/rest/issues/labels
#       POST   /repos/{owner}/{repo}/issues/{issue_number}/labels  {"labels": [...]}
#              -> the `labels` body field holds "The labels to add to the issue's existing labels",
#                 i.e. it is ADDITIVE. (The whole-set replace is the PUT on the same path, which
#                 this wrapper deliberately does NOT use for claim changes.)
#       DELETE /repos/{owner}/{repo}/issues/{issue_number}/labels/{name}
#              -> removes ONE label, "returns the remaining labels on the issue", 404 if absent.
#   - https://docs.github.com/en/rest/issues/assignees
#       POST   /repos/{owner}/{repo}/issues/{issue_number}/assignees  {"assignees": [...]}
#              -> "Usernames of people to assign this issue to"; existing assignees are KEPT.
#       DELETE /repos/{owner}/{repo}/issues/{issue_number}/assignees  {"assignees": [...]}
#              -> "Usernames of assignees to remove from an issue"; leaves the others in place.
#   - https://docs.github.com/en/rest/users/users
#       GET    /user  -> the authenticated account, whose handle is the `login` field.
# --------------------------------------------------------------------------------------------


def _fetch_issue(*, token: str, owner: str, repo: str, number: int) -> dict[str, Any]:
    """GET one issue object.

    The claim path calls this TWICE on purpose — once to decide, once to VERIFY — so it is a named
    helper rather than an inlined request: the second call has to be a genuinely fresh read of
    remote state, and a reader can see here that it is one.
    """
    issue = _api_request(method="GET", path=f"/repos/{owner}/{repo}/issues/{number}", token=token)
    if not isinstance(issue, dict):
        raise GitHubAPIError(f"Unexpected issue payload for #{number}: not a JSON object.", details=issue)
    return issue


def _label_names(*, issue: dict[str, Any]) -> list[str]:
    """Extract the label names from an issue object (PURE — no network)."""
    return [label[FIELD_NAME] for label in issue.get(FIELD_LABELS) or []]


def _assignee_logins(*, issue: dict[str, Any]) -> list[str]:
    """Extract the assignee logins from an issue object (PURE — no network)."""
    return [user[FIELD_LOGIN] for user in issue.get(FIELD_ASSIGNEES) or []]


def _add_labels(*, token: str, owner: str, repo: str, number: int, labels: list[str]) -> Any:
    """ADD labels, leaving every other label untouched (``POST .../labels``)."""
    return _api_request(
        method="POST",
        path=f"/repos/{owner}/{repo}/issues/{number}/labels",
        token=token,
        body={FIELD_LABELS: labels},
    )


def _remove_label(*, token: str, owner: str, repo: str, number: int, label: str) -> Any:
    """REMOVE exactly one label (``DELETE .../labels/{name}``).

    The name is percent-encoded with ``safe=""`` because it is interpolated into the URL PATH and a
    label may legitimately contain a space or a ``/`` (``help wanted``, ``area/ui``) — either of
    which would otherwise change which resource is addressed.
    """
    return _api_request(
        method="DELETE",
        path=f"/repos/{owner}/{repo}/issues/{number}/labels/{quote(label, safe='')}",
        token=token,
    )


def _add_assignees(*, token: str, owner: str, repo: str, number: int, assignees: list[str]) -> Any:
    """ADD assignees, keeping any already present (``POST .../assignees``)."""
    return _api_request(
        method="POST",
        path=f"/repos/{owner}/{repo}/issues/{number}/assignees",
        token=token,
        body={FIELD_ASSIGNEES: assignees},
    )


def _remove_assignees(*, token: str, owner: str, repo: str, number: int, assignees: list[str]) -> Any:
    """REMOVE the named assignees, leaving any others in place (``DELETE .../assignees``)."""
    return _api_request(
        method="DELETE",
        path=f"/repos/{owner}/{repo}/issues/{number}/assignees",
        token=token,
        body={FIELD_ASSIGNEES: assignees},
    )


def _resolve_authenticated_login(*, token: str) -> str:
    """Return the login of the account the PAT belongs to (``GET /user``) — the "working identity".

    Resolved from the token rather than configured anywhere, so the identity a claim records is
    necessarily the identity that made it, and no environment variable or config key can make the
    two disagree (``.claude/rules/no-environment-vars.md``).
    """
    user = _api_request(method="GET", path="/user", token=token)
    login = user.get(FIELD_LOGIN) if isinstance(user, dict) else None
    if not isinstance(login, str) or not login:
        raise GitHubAPIError("GET /user returned no 'login' — cannot determine the working identity.")
    return login


def cmd_label_add(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """ADD one or more labels additively (``label-add`` / ``issue label-add``).

    The primitive `.claude/rules/issue-tracking.md` mandates for "any label change", in place of a
    whole-set replace. Unlike ``update-issue --labels`` this never reads the current set at all, so
    there is no read-then-write window a concurrent worker's label change can be lost in.
    """
    labels = [name.strip() for name in args.labels.split(",") if name.strip()]
    if not labels:
        raise GitHubAPIError(f"{CMD_LABEL_ADD} requires at least one label name in --labels")
    data = _add_labels(token=token, owner=owner, repo=repo, number=args.issue_number, labels=labels)
    logger.info("Added label(s) %s to issue #%s.", labels, args.issue_number)
    print(json.dumps(data, indent=2))


def cmd_label_remove(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """REMOVE exactly one label, preserving all others (``label-remove`` / ``issue label-remove``).

    The endpoint takes ONE label per call by design, which is what makes it non-destructive: there
    is no set to restate and therefore nothing to drop by omission.
    """
    data = _remove_label(token=token, owner=owner, repo=repo, number=args.issue_number, label=args.label)
    logger.info("Removed label '%s' from issue #%s.", args.label, args.issue_number)
    print(json.dumps(data, indent=2))


def cmd_assign(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Set or clear an issue's assignee (``assign`` / ``issue assign``).

    Exactly one mode is required (argparse enforces it):

    * ``--me`` — assign the account the PAT belongs to, resolved via ``GET /user``. This is the
      "working identity" the claim records, so it is never spelled out by the caller.
    * ``--user LOGIN`` — assign a named account (no ``GET /user`` call is made).
    * ``--unassign`` — clear the current assignees. The logins to remove come from a fresh read of
      the issue, because the DELETE endpoint names whom to remove rather than accepting an empty set.

    Additive/subtractive throughout: assigning does not displace an existing assignee, and removing
    names only the logins being dropped.
    """
    number = args.issue_number
    if getattr(args, "unassign", False):
        current = _assignee_logins(issue=_fetch_issue(token=token, owner=owner, repo=repo, number=number))
        if not current:
            logger.info("Issue #%s has no assignees (no change).", number)
            print(json.dumps({FIELD_NUMBER: number, FIELD_ASSIGNEES: [], KEY_UNASSIGNED: []}, indent=2))
            return
        _remove_assignees(token=token, owner=owner, repo=repo, number=number, assignees=current)
        logger.info("Unassigned %s from issue #%s.", current, number)
        print(json.dumps({FIELD_NUMBER: number, FIELD_ASSIGNEES: [], KEY_UNASSIGNED: current}, indent=2))
        return
    login = _resolve_authenticated_login(token=token) if getattr(args, "me", False) else args.user
    data = _add_assignees(token=token, owner=owner, repo=repo, number=number, assignees=[login])
    logger.info("Assigned issue #%s to '%s'.", number, login)
    print(json.dumps({FIELD_NUMBER: number, FIELD_ASSIGNEES: _assignee_logins(issue=data)}, indent=2))


def _claim_is_held_by_another(*, labels: list[str], assignees: list[str], me: str) -> bool:
    """Would starting work here TAKE OVER somebody else's claim? (PURE — no network.)

    Fail-closed by construction, which is why the ambiguous case counts as held:

    * another login is assigned -> theirs, unambiguously;
    * the in-progress label is present but NOBODY is assigned -> the label carries no owner, so the
      holder cannot be established. Refusing costs one wasted candidate selection; proceeding costs
      the duplicated work this whole mechanism exists to prevent;
    * the label is present AND I am assigned -> MINE, so a re-run is the idempotent no-op that
      ``.claude/rules/issue-tracking.md`` requires of the claim.
    """
    if any(login != me for login in assignees):
        return True
    return LABEL_IN_PROGRESS in labels and me not in assignees


def cmd_claim_issue(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Claim an issue for work by ADDING the ``in-progress`` label (worker protocol step 2).

    Call this BEFORE creating a branch/worktree or writing any code, so concurrent workers see
    the claim (via ``list-in-progress`` / its absence from ``list-available``) and do not start
    the same issue. Label-preserving: keeps all existing labels.

    Two modes, chosen by ``--strict``:

    * Default (``strict`` False): idempotent — a no-op success if the issue is ALREADY claimed.
      Use this to (re)assert a claim on YOUR OWN issue, e.g. when resuming an interrupted run.
    * ``--strict``: an atomic ACQUIRE — if the ``in-progress`` label is already present, FAIL
      (raise ``GitHubAPIError`` → exit 1) and write nothing, so a concurrent worker gets an
      unambiguous "already taken, do not start" signal instead of a silent success. This is the
      guard against DUPLICATED work: a second worker that races to the same issue is rejected
      rather than proceeding in parallel. Re-fetches the live labels immediately before deciding,
      so the check reflects current tracker state, not a stale ``list-available`` snapshot.
    """
    strict = getattr(args, "strict", False)
    before = _current_label_names(token=token, owner=owner, repo=repo, number=args.issue_number)
    if LABEL_IN_PROGRESS in before:
        if strict:
            raise GitHubAPIError(
                f"Issue #{args.issue_number} is already marked '{LABEL_IN_PROGRESS}' — "
                f"another worker has claimed it; not starting (strict claim rejected).",
                details={FIELD_NUMBER: args.issue_number, FIELD_LABELS: before, "claimed_by_other": True},
            )
        logger.info("Issue #%s is already marked '%s' (no change).", args.issue_number, LABEL_IN_PROGRESS)
        print(json.dumps({FIELD_NUMBER: args.issue_number, FIELD_LABELS: before, "claimed": True}, indent=2))
        return
    updated = _replace_labels(
        token=token, owner=owner, repo=repo, number=args.issue_number, labels=[*before, LABEL_IN_PROGRESS]
    )
    logger.info("Claimed issue #%s (added '%s').", args.issue_number, LABEL_IN_PROGRESS)
    after = [label[FIELD_NAME] for label in updated.get(FIELD_LABELS, [])]
    print(json.dumps({FIELD_NUMBER: args.issue_number, FIELD_LABELS: after, "claimed": True}, indent=2))


def cmd_release_issue(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Release a claim: REMOVE the ``in-progress`` label AND drop your OWN assignment (step 4).

    Call this when you STOP working an issue WITHOUT closing it (blocked, handing off, abandoning),
    so it returns to the free-work pool. Do NOT call this on an issue you finished — just close it.

    It drops the assignment as well as the label because it has to INVERT ``start-issue``, which sets
    both. Removing only the label would leave the assignee behind, and an assignee is itself a claim
    signal (``_issue_is_claimed``) — so ``claim-check`` would keep reporting the issue as claimed and
    the ``claim-before-worktree`` gate would never ask the next worker to claim it. That also matches
    the contract the installed artifacts state for this command: ``issue release <X>`` "removes the
    in-progress label and unassigns" (``.claude/agents/issue-work-orchestrator.md``).

    Only YOUR OWN login is unassigned, never a third party's: releasing your claim is not authority
    to displace a human who assigned themselves. ``GET /user`` is called only when the issue actually
    has assignees, so the common no-assignee release costs no extra request.

    Label-preserving and idempotent: removes only ``in-progress``, and is a no-op when there is
    neither that label nor an assignment of yours to drop.
    """
    number = args.issue_number
    issue = _fetch_issue(token=token, owner=owner, repo=repo, number=number)
    before = _label_names(issue=issue)
    assignees = _assignee_logins(issue=issue)
    mine: list[str] = []
    if assignees:
        me = _resolve_authenticated_login(token=token)
        mine = [login for login in assignees if login == me]
    if LABEL_IN_PROGRESS not in before and not mine:
        logger.info("Issue #%s is not claimed by you (no change).", number)
        verdict = {FIELD_NUMBER: number, FIELD_LABELS: before, KEY_CLAIMED: False, KEY_UNASSIGNED: []}
        print(json.dumps(verdict, indent=2))
        return
    after = before
    if LABEL_IN_PROGRESS in before:
        updated = _replace_labels(
            token=token,
            owner=owner,
            repo=repo,
            number=number,
            labels=[name for name in before if name != LABEL_IN_PROGRESS],
        )
        after = _label_names(issue=updated)
    if mine:
        _remove_assignees(token=token, owner=owner, repo=repo, number=number, assignees=mine)
    logger.info("Released issue #%s (label '%s' dropped, unassigned %s).", number, LABEL_IN_PROGRESS, mine)
    print(json.dumps({FIELD_NUMBER: number, FIELD_LABELS: after, KEY_CLAIMED: False, KEY_UNASSIGNED: mine}, indent=2))


def cmd_start_issue(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """THE deterministic in-progress claim: idempotent AND fail-closed (``start-issue``/``issue start``).

    This is the ONE command every installed artifact tells an agent to claim work with, and its
    contract is theirs verbatim: it "adds the in-progress label *additively*, assigns the working
    identity, then re-reads and verifies BOTH took effect, exiting non-zero if not — so a claim is
    never believed unless it actually landed" (``.claude/rules/issue-tracking.md``). It is a SEPARATE
    handler from ``claim-issue``, which keeps this project's original label-only semantics untouched.

    Five steps, in this order, matching the standard's wrapper contract:

    1. GET the issue and ABORT unless ``state == "open"``. Claiming a closed issue records a claim on
       work that no longer exists.
    2. Resolve the working identity from the token (``GET /user``).
    3. ABORT if the claim is held by ANOTHER worker (see :func:`_claim_is_held_by_another`) — the
       lost-race branch the orchestrator keys on. ``--force`` overrides this deliberately.
    4. Write ADDITIVELY: ``POST .../labels`` for the in-progress label and ``POST .../assignees`` for
       the identity. Neither restates an existing set, so no sibling label or assignee is dropped.
       A write already satisfied is skipped, which is what makes a re-run a cheap no-op.
    5. RE-READ the issue with a FRESH GET and raise unless the label AND the assignment are both
       present. The response bodies of step 4 are deliberately NOT trusted for this: a write that
       reports success while the state does not change is exactly the failure this guards, so the
       verification has to be an independent observation or it proves nothing.

    Any failure raises ``GitHubAPIError``, which ``main`` turns into exit 1 — the non-zero status the
    orchestrator branches on to release its local lock and pick a different issue.

    ``--strict`` additionally rejects a claim that is ALREADY YOURS, mirroring the meaning the flag
    has on ``claim-issue`` (fail rather than no-op when the claim is present). Use it to demand a
    fresh acquisition; omit it to re-assert a claim while resuming your own interrupted run.
    """
    number = args.issue_number
    issue = _fetch_issue(token=token, owner=owner, repo=repo, number=number)
    state = issue.get(FIELD_STATE)
    if state != ISSUE_STATE_OPEN:
        raise GitHubAPIError(
            f"Issue #{number} is not open (state={state}) — refusing to claim work that is not outstanding.",
            details={FIELD_NUMBER: number, FIELD_STATE: state},
        )
    me = _resolve_authenticated_login(token=token)
    labels_before = _label_names(issue=issue)
    assignees_before = _assignee_logins(issue=issue)
    if getattr(args, "strict", False) and (LABEL_IN_PROGRESS in labels_before or assignees_before):
        raise GitHubAPIError(
            f"Issue #{number} already carries a claim ('{LABEL_IN_PROGRESS}' label and/or an assignee) — "
            f"strict claim rejected; nothing was written.",
            details={FIELD_NUMBER: number, FIELD_LABELS: labels_before, FIELD_ASSIGNEES: assignees_before},
        )
    if _claim_is_held_by_another(labels=labels_before, assignees=assignees_before, me=me) and not getattr(
        args, "force", False
    ):
        raise GitHubAPIError(
            f"Issue #{number} is already claimed by another worker "
            f"(labels={labels_before}, assignees={assignees_before}; you are '{me}') — not starting. "
            f"Pass --force only to deliberately take it over.",
            details={FIELD_NUMBER: number, FIELD_LABELS: labels_before, FIELD_ASSIGNEES: assignees_before},
        )
    if LABEL_IN_PROGRESS not in labels_before:
        _add_labels(token=token, owner=owner, repo=repo, number=number, labels=[LABEL_IN_PROGRESS])
    if me not in assignees_before:
        _add_assignees(token=token, owner=owner, repo=repo, number=number, assignees=[me])
    verified = _fetch_issue(token=token, owner=owner, repo=repo, number=number)
    labels_after = _label_names(issue=verified)
    assignees_after = _assignee_logins(issue=verified)
    if LABEL_IN_PROGRESS not in labels_after or me not in assignees_after:
        raise GitHubAPIError(
            f"Claim on issue #{number} did NOT land: re-read shows labels={labels_after}, "
            f"assignees={assignees_after} (expected '{LABEL_IN_PROGRESS}' and '{me}'). "
            f"Do NOT start work on an unverified claim.",
            details={
                FIELD_NUMBER: number,
                FIELD_LABELS: labels_after,
                FIELD_ASSIGNEES: assignees_after,
                KEY_VERIFIED: False,
            },
        )
    logger.info("Claimed issue #%s for '%s' (label + assignee verified by re-read).", number, me)
    print(
        json.dumps(
            {
                FIELD_NUMBER: number,
                FIELD_STATE: state,
                FIELD_LABELS: labels_after,
                FIELD_ASSIGNEES: assignees_after,
                KEY_CLAIMED: True,
                KEY_VERIFIED: True,
            },
            indent=2,
        )
    )


def _list_open_issues(*, token: str, owner: str, repo: str, labels: str | None = None) -> list[dict[str, Any]]:
    """Return OPEN issues (PRs filtered out), optionally narrowed to a label, most-recent page first.

    Shared by the two discovery commands. ``labels`` (comma-separated) is passed to the GitHub
    issues list endpoint, which returns issues carrying ALL of the given labels.
    """
    params = ["state=open", "per_page=100"]
    if labels:
        params.append(f"labels={labels}")
    data = _api_request(method="GET", path=f"/repos/{owner}/{repo}/issues?" + "&".join(params), token=token)
    # The issues endpoint returns PRs too; a PR object carries a "pull_request" key. Exclude them.
    return [issue for issue in data if "pull_request" not in issue]


def _print_issue_rows(issues: list[dict[str, Any]]) -> None:
    """Print one ``#<num> <title> [labels]`` row per issue (stable, greppable worker output)."""
    for issue in issues:
        names = ",".join(label[FIELD_NAME] for label in issue.get(FIELD_LABELS, []))
        print(f"#{issue[FIELD_NUMBER]:<6} {issue[FIELD_TITLE]}  [{names}]")
    print(f"({len(issues)} issue(s))")


def _issue_is_claimed(*, issue: dict[str, Any]) -> bool:
    """THE single "is somebody already working this?" test. In-progress label OR any assignee.

    Both readers of this question — ``list-available`` ("may I pick this up?") and ``claim-check``
    ("must I be stopped?") — go through THIS predicate, and that is load-bearing rather than tidiness.
    They were once two implementations: ``claim-check`` tested label-OR-assignee while
    ``list-available`` tested the label alone, and the disagreement opened a path with ZERO
    enforcement. An OPEN issue with an assignee and no label was simultaneously offered as free work
    by ``list-available`` AND reported already-claimed (exit 0) by ``claim-check`` — so an agent could
    take that issue, skip the claim entirely, and ``gate_claim.py``, which blocks on exit 3
    alone, would wave the worktree through.

    Label-OR-assignee is the half that conforms to the standard's stated convention: "an issue is in
    progress if it has ANY assignee OR a label matching ``in-progress``/``in progress``/``wip``/
    ``doing``" (``ClaudeCodeSetupPrompt.txt``, Part 5.3). Unifying on it makes ``list-available``
    STRICTER — it offers strictly fewer issues than before — which cannot create duplicate work, only
    prevent it. Any future divergence must add a signal HERE, not fork a second predicate.
    """
    return LABEL_IN_PROGRESS in _label_names(issue=issue) or bool(_assignee_logins(issue=issue))


def cmd_list_in_progress(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """List OPEN issues currently CLAIMED (carrying the ``in-progress`` label) — worker protocol step 5.

    Use this to audit active work: what is already taken, so you don't duplicate it, and (via each
    issue's comments/checklist) who is on it. An issue here is being worked by someone — do NOT
    start it. Server-side filtered by the in-progress label.
    """
    issues = _list_open_issues(token=token, owner=owner, repo=repo, labels=LABEL_IN_PROGRESS)
    _print_issue_rows(issues)


def cmd_list_available(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """List OPEN issues that NOBODY has claimed — the free-work pool (worker protocol step 1).

    This is where a worker PICKS NEW WORK: every issue here is open and unclaimed. GitHub's issues
    endpoint has no "missing claim" filter, so this lists all open issues and subtracts the claimed
    ones locally, through the SAME :func:`_issue_is_claimed` predicate ``claim-check`` uses — so an
    issue this command offers is exactly an issue the claim gate will require you to claim. Claim one
    with ``start-issue <n>`` BEFORE starting.
    """
    all_open = _list_open_issues(token=token, owner=owner, repo=repo)
    available = [issue for issue in all_open if not _issue_is_claimed(issue=issue)]
    _print_issue_rows(available)


# Response headers GitHub uses to report the authenticated token's own properties. Read by
# `token-info`, which exists because an expired credential presents as a HANG rather than an error on
# the CodeBuild runner-dispatch path (issue #286), so the expiry has to be diarised BEFORE it bites.
HEADER_TOKEN_EXPIRY = "github-authentication-token-expiration"  # nosec B105  # an HTTP header NAME, not a secret
HEADER_OAUTH_SCOPES = "x-oauth-scopes"
HEADER_ACCEPTED_SCOPES = "x-accepted-oauth-scopes"

#: Reported as "not reported" rather than guessed at. A fine-grained PAT carries no OAuth scopes at
#: all, so an ABSENT scope header means "fine-grained" — never "no permissions".
_NOT_REPORTED = "(not reported by GitHub for this token type)"


#: Dependabot ALERTS are reported by STATUS ONLY, with no response body:
#: `GET /repos/{owner}/{repo}/vulnerability-alerts` answers 204 when enabled and 404 when not.
STATUS_ALERTS_ENABLED = 204
STATUS_ALERTS_ABSENT = 404


def _api_status(*, path: str, token: str) -> int:
    """Return the HTTP STATUS of a GET, treating 4xx as a status rather than an error.

    Needed because the vulnerability-alerts endpoint carries NO body and signals its answer entirely in the
    status line, so `_api_request` — which raises on a 404 — cannot express "not enabled".
    """
    if not path.startswith(PATH_ROOT) or path.startswith(PATH_PROTOCOL_RELATIVE):
        raise GitHubAPIError(f"Refusing a non-root-relative API path: {_render_untrusted(value=path)}")
    url = f"{API_BASE}{path}"
    if not url.startswith("https://"):
        raise GitHubAPIError(f"Refusing to call non-HTTPS URL: {url}")
    req = Request(url=url, method="GET")
    req.add_header(HEADER_ACCEPT, ACCEPT_JSON)
    req.add_header(HEADER_AUTH, f"Bearer {token}")
    req.add_header(HEADER_UA, USER_AGENT)
    req.add_header(HEADER_API_VERSION, API_VERSION)
    opener = _build_api_opener()
    try:
        with opener.open(req) as resp:
            return int(resp.status)
    except HTTPError as exc:
        return int(exc.code)


def classify_alerts_status(*, status: int) -> tuple[str, str]:
    """Map a vulnerability-alerts status to (verdict, explanation). Pure, so it is testable hermetically.

    The 404 mapping is deliberately NOT a bare "disabled". GitHub documents 404 as "Not Found if repository
    is not enabled with vulnerability alerts", AND answers 404 when the caller lacks the required admin read
    access — the two are indistinguishable from the status alone. Reporting it as "disabled" would publish an
    unverified claim, which `no-guessing.md` forbids.
    """
    if status == STATUS_ALERTS_ENABLED:
        return ("ENABLED", "the repository has Dependabot alerts enabled")
    if status == STATUS_ALERTS_ABSENT:
        return (
            "DISABLED-OR-UNAUTHORIZED",
            "GitHub answers 404 both when alerts are OFF and when the token lacks admin read access, so this "
            "status alone cannot distinguish them",
        )
    return ("CANNOT-DETERMINE", f"unexpected status {status}")


def cmd_security_alerts(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Report whether Dependabot ALERTS are enabled for this repository (issue #338).

    Reads `GET /repos/{owner}/{repo}/vulnerability-alerts`, titled "Check if vulnerability alerts are enabled
    for a repository", which answers by STATUS ONLY: 204 enabled, 404 not-enabled-or-unauthorized.

    NOT `security_and_analysis` on the repository object, which was the first thing tried and is WRONG: that
    block has no alerts key at all. Its documented sub-keys are `advanced_security`, `code_security`,
    `dependabot_security_updates` and the `secret_scanning*` family — and `dependabot_security_updates` is a
    DIFFERENT feature (automatic fix pull requests), with its own `automated-security-fixes` endpoint. A
    subcommand reading that block would either report the wrong feature's state or find nothing at all.

    The advisory gate deliberately does NOT consult this: a gate that depended on a repository setting no
    tracked file can establish would be unreproducible from the repository alone.
    """
    del args
    status = _api_status(path=f"/repos/{owner}/{repo}/vulnerability-alerts", token=token)
    verdict, explanation = classify_alerts_status(status=status)
    print(f"DEPENDABOT ALERTS : {verdict}")
    print(f"HTTP STATUS       : {status}")
    print(f"MEANING           : {explanation}")


def _api_request_headers(*, path: str, token: str) -> dict[str, str]:
    """Return the RESPONSE HEADERS of a GET, lower-cased. The token is never returned or logged."""
    if not path.startswith(PATH_ROOT) or path.startswith(PATH_PROTOCOL_RELATIVE):
        raise GitHubAPIError(f"Refusing a non-root-relative API path: {_render_untrusted(value=path)}")
    url = f"{API_BASE}{path}"
    if not url.startswith("https://"):
        raise GitHubAPIError(f"Refusing to call non-HTTPS URL: {url}")
    req = Request(url=url, method="GET")
    req.add_header(HEADER_ACCEPT, ACCEPT_JSON)
    req.add_header(HEADER_AUTH, f"Bearer {token}")
    req.add_header(HEADER_UA, USER_AGENT)
    req.add_header(HEADER_API_VERSION, API_VERSION)
    opener = _build_api_opener()
    try:
        with opener.open(req) as resp:
            return {str(key).lower(): str(value) for key, value in resp.headers.items()}
    except HTTPError as exc:
        raise GitHubAPIError(f"GitHub API GET {url} failed: HTTP {exc.code}") from exc
    except OSError as exc:
        # URLError derives from OSError; catching the base avoids an import this module does not
        # otherwise need, and still reports the transport failure by exception CLASS only.
        raise GitHubAPIError(f"GitHub API GET {url} failed: {type(exc).__name__}") from exc


def cmd_token_info(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Report the authenticated token's EXPIRY and SCOPES, without ever printing the token.

    Two independent needs, one call:

    * **Expiry** — an expired credential presents as a HANG on the CodeBuild runner-dispatch path,
      and a credential listing returns no expiry, no validity and no last-used. So the expiry must be
      diarised from the token itself rather than inferred after a hang.
    * **Scopes** — the CodeBuild source credential needs webhook-administration permission. Without
      it the repository webhook is never created and every relocated job hangs with no artifact.

    A fine-grained PAT reports no OAuth scopes, so an absent scope header is reported as
    "not reported", never as "no permissions".
    """
    del owner, repo, args  # this reports on the TOKEN, not on a repository
    headers = _api_request_headers(path="/user", token=token)
    expiry = headers.get(HEADER_TOKEN_EXPIRY, "")
    scopes = headers.get(HEADER_OAUTH_SCOPES, "")

    print(f"TOKEN EXPIRY : {expiry or _NOT_REPORTED}")
    print(f"TOKEN SCOPES : {scopes or _NOT_REPORTED}")
    accepted = headers.get(HEADER_ACCEPTED_SCOPES, "")
    if accepted:
        print(f"ACCEPTED     : {accepted}")
    if not expiry:
        print("NOTE: no expiry header means the token does not expire, or GitHub does not report it.")


# --- Repository webhooks and their deliveries (issue #1257) ---------------------------------------------------------
# A relocated job that never gets a CodeBuild runner leaves no build to inspect; CodeBuild's reply to the job's
# `workflow_job.queued` delivery is the one record of why ("Review the Response tab, as this contains the response or
# error message returned from CodeBuild",
# https://docs.aws.amazon.com/codebuild/latest/userguide/action-runner-troubleshoot-webhook.html). The endpoints are
# https://docs.github.com/en/rest/repos/webhooks: a hook's `config.url` is never printed beyond its host, because
# CodeBuild's webhook URL carries a token in its query string.
FIELD_ACTIVE = "active"
FIELD_EVENTS = "events"
FIELD_CONFIG = "config"
FIELD_CONFIG_URL = "url"
FIELD_ACTION = "action"
FIELD_DELIVERED_AT = "delivered_at"
FIELD_STATUS_CODE = "status_code"
FIELD_REDELIVERY = "redelivery"
FIELD_REQUEST = "request"
FIELD_RESPONSE = "response"
FIELD_PAYLOAD = "payload"
FIELD_WORKFLOW_JOB = "workflow_job"
FIELD_RUN_ID = "run_id"
HEADER_LINK = "link"
#: The `rel` of the Link-header entry that names the next page of a cursor-paginated listing.
LINK_REL_NEXT = 'rel="next"'


def _api_get_page(*, path: str, token: str) -> "tuple[Any, str | None]":
    """GET one page of a Link-paginated listing: the decoded body and the root-relative path of the next page, if any.

    The deliveries listing pages by an opaque ``cursor`` that only the ``Link`` header carries, so the page is read
    through :func:`_api_request` with ``response_headers``. A next-page URL outside :data:`API_BASE` is refused rather
    than followed.
    """
    headers: dict[str, str] = {}
    body = _api_request(method="GET", path=path, token=token, response_headers=headers)
    return body, next_page_path(link=headers.get(HEADER_LINK, ""))


def next_page_path(*, link: str) -> "str | None":
    """The root-relative path of a ``Link`` header's ``rel="next"`` entry, or ``None`` when there is none.

    Raises:
        GitHubAPIError: If the next-page URL is not under :data:`API_BASE`.
    """
    for entry in link.split(","):
        if LINK_REL_NEXT not in entry:
            continue
        url = entry.split(";", 1)[0].strip().lstrip("<").rstrip(">")
        if not url.startswith(f"{API_BASE}{PATH_ROOT}"):
            raise GitHubAPIError(f"Refusing a next-page URL outside the API: {_render_untrusted(value=url)}")
        return url[len(API_BASE) :]
    return None


def parse_since(value: str) -> datetime:
    """``hook-deliveries --since``: an ISO 8601 time carrying ``Z`` or a UTC offset, as an aware ``datetime``.

    A time without an offset, or no time at all, is refused rather than compared: a text comparison against
    ``delivered_at`` would end the listing early or print nothing, which reads as "no refused delivery".

    Raises:
        argparse.ArgumentTypeError: If ``value`` is not an ISO 8601 time or carries no offset.
    """
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"not an ISO 8601 time: {_render_untrusted(value=value)}") from exc
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError(f"needs Z or a UTC offset: {_render_untrusted(value=value)}")
    return parsed


def _render_field(*, value: object) -> str:
    """A delivery value for a line of output: an integer as it is, anything else escaped by ``_render_untrusted``."""
    return str(value) if isinstance(value, int) and not isinstance(value, bool) else _render_untrusted(value=value)


def _delivered_at(*, delivery: dict[str, Any]) -> datetime:
    """A delivery's ``delivered_at`` as an aware ``datetime``.

    Raises:
        GitHubAPIError: If GitHub's value is not an ISO 8601 time with an offset.
    """
    value = str(delivery.get(FIELD_DELIVERED_AT, ""))
    try:
        delivered = datetime.fromisoformat(value)
    except ValueError as exc:
        raise GitHubAPIError(f"a delivery's delivered_at is not a time: {_render_untrusted(value=value)}") from exc
    if delivered.tzinfo is None:
        raise GitHubAPIError(f"a delivery's delivered_at carries no offset: {_render_untrusted(value=value)}")
    return delivered


def format_delivery_row(*, delivery: dict[str, Any]) -> str:
    """One listing line of a delivery: time, id, event.action, the receiver's HTTP status, GitHub's status text."""
    event = f"{delivery.get(FIELD_EVENT)}.{delivery.get(FIELD_ACTION)}"
    redelivery = " redelivery" if delivery.get(FIELD_REDELIVERY) else ""
    return (
        f"{_render_field(value=delivery.get(FIELD_DELIVERED_AT))}  {_render_field(value=delivery.get(FIELD_ID)):<12} "
        f"{_render_untrusted(value=event):<26} {_render_field(value=delivery.get(FIELD_STATUS_CODE)):<4} "
        f"{_render_untrusted(value=delivery.get(FIELD_STATUS))}{redelivery}"
    )


def cmd_list_hooks(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """List the repository's webhooks: id, active, events and the receiving HOST only (never the URL's query)."""
    del args
    hooks = _api_request(method="GET", path=f"/repos/{owner}/{repo}/hooks?per_page={GITHUB_MAX_PER_PAGE}", token=token)
    for hook in hooks:
        host = urlparse(str(hook.get(FIELD_CONFIG, {}).get(FIELD_CONFIG_URL, ""))).hostname
        events = ",".join(str(event) for event in hook.get(FIELD_EVENTS, []))
        print(
            f"{_render_field(value=hook.get(FIELD_ID)):<12} active={_render_field(value=hook.get(FIELD_ACTIVE)):<6} "
            f"{_render_untrusted(value=host)} {_render_untrusted(value=events)}"
        )


def cmd_hook_deliveries(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """List a webhook's deliveries in the listing's order (newest first, as observed), at most ``--limit`` rows.

    GitHub documents no order for this listing, so each page is read whole: no delivery older than ``--since`` is
    printed, and no page after one holding such a delivery is requested. ``--failed-only`` keeps the deliveries whose
    receiver did not answer 2xx, which is where a refused build start shows up.
    """
    path: "str | None" = f"/repos/{owner}/{repo}/hooks/{args.hook_id}/deliveries?per_page={GITHUB_MAX_PER_PAGE}"
    printed = 0
    while path is not None:
        page, path = _api_get_page(path=path, token=token)
        older_seen = False
        for delivery in page:
            if args.since is not None and _delivered_at(delivery=delivery) < args.since:
                older_seen = True
                continue
            code = delivery.get(FIELD_STATUS_CODE)
            if args.failed_only and isinstance(code, int) and 200 <= code < 300:
                continue
            print(format_delivery_row(delivery=delivery))
            printed += 1
            if printed >= args.limit:
                return
        if older_seen:
            return


def cmd_hook_delivery(token: str, owner: str, repo: str, args: argparse.Namespace) -> None:
    """Show one delivery: its workflow job (name, run, attempt, labels) and the receiver's response, status and body.

    Never the delivery's ``url``, the hook's target, which for CodeBuild's hook carries a token in its query.
    """
    data = _api_request(
        method="GET", path=f"/repos/{owner}/{repo}/hooks/{args.hook_id}/deliveries/{args.delivery_id}", token=token
    )
    payload = (data.get(FIELD_REQUEST) or {}).get(FIELD_PAYLOAD) or {}
    job = payload.get(FIELD_WORKFLOW_JOB) or {}
    response = data.get(FIELD_RESPONSE) or {}
    print(format_delivery_row(delivery=data))
    print(f"JOB        : {_render_field(value=job.get(FIELD_ID))} {_render_field(value=job.get(FIELD_NAME))}")
    print(
        f"RUN        : {_render_field(value=job.get(FIELD_RUN_ID))} "
        f"attempt {_render_field(value=job.get(FIELD_RUN_ATTEMPT))}"
    )
    print(f"LABELS     : {_render_field(value=job.get(FIELD_LABELS))}")
    print(
        f"JOB STATUS : {_render_field(value=job.get(FIELD_STATUS))} "
        f"runner={_render_field(value=job.get(FIELD_RUNNER_NAME))}"
    )
    # Unclipped, unlike the lines above, because the reply is the evidence; ``json.dumps`` escapes every control
    # character and non-ASCII codepoint, so it cannot drive the terminal.
    print(f"RESPONSE   : {json.dumps(response.get(FIELD_PAYLOAD))}")


def cmd_claim_check(token: str, owner: str, repo: str, args: argparse.Namespace) -> int:
    """READ-ONLY claim probe. Writes NOTHING. Consumed by the claim-before-worktree PreToolUse gate.

    The gate refuses ``git worktree add ... issue-<N>`` until issue N is verifiably claimed, so that
    a skipped claim is caught at the exact moment work would start instead of after two workers have
    duplicated it. The gate keys on the numeric exit status alone, which makes these codes a
    CONTRACT — do not renumber them:

    * ``EXIT_OK`` (0) — the issue is CLAIMED (``in-progress`` label OR any assignee) **or** is not
      ``open``. Nothing to enforce: the gate ALLOWS the worktree creation.
    * ``EXIT_OPEN_AND_UNCLAIMED`` (3) — the issue is OPEN and NOBODY has claimed it. The gate
      BLOCKS (its own exit 2) and tells the agent to claim it first.
    * ``1`` — an API/auth/network error (``GitHubAPIError`` out of ``main``). The gate fails OPEN on
      any status other than 3, so infrastructure trouble can never wedge a session.

    Claim it with ``start-issue <n>`` (equivalently ``issue start <n>``) before retrying — that is the
    verified claim, so a success from it is a claim this probe will agree with on the next call.
    """
    issue = _fetch_issue(token=token, owner=owner, repo=repo, number=args.issue_number)
    state = issue.get(FIELD_STATE)
    labels = _label_names(issue=issue)
    assignees = _assignee_logins(issue=issue)
    claimed = _issue_is_claimed(issue=issue)
    unclaimed_and_open = state == ISSUE_STATE_OPEN and not claimed
    exit_code = EXIT_OPEN_AND_UNCLAIMED if unclaimed_and_open else EXIT_OK
    if unclaimed_and_open:
        logger.info(
            "Issue #%s is OPEN and UNCLAIMED (no '%s' label, no assignee) — claim it before starting work.",
            args.issue_number,
            LABEL_IN_PROGRESS,
        )
    else:
        logger.info("Issue #%s needs no claim (state=%s, claimed=%s).", args.issue_number, state, claimed)
    print(
        json.dumps(
            {
                FIELD_NUMBER: args.issue_number,
                FIELD_STATE: state,
                FIELD_LABELS: labels,
                FIELD_ASSIGNEES: assignees,
                KEY_CLAIMED: claimed,
                KEY_EXIT_CODE: exit_code,
            },
            indent=2,
        )
    )
    return exit_code


def _exit_code_of(result: Any) -> int:
    """Map a subcommand handler's return value to a process exit status (``None`` -> success).

    Most handlers report only through exceptions and return ``None``; ``claim-check`` additionally
    returns a verdict status that must survive to the shell, because the gate reads nothing else.
    """
    return EXIT_OK if result is None else int(result)


def _run_merge_steward(*, token: str, steward_args: list[str]) -> int:
    """Run ``scripts/merge_steward.py <steward_args>`` with this wrapper's token on its standard input; its exit
    status IS this command's (enqueue: 0 queued, 4 refused with the reason printed; 1 a host error; 2 usage).

    The steward reads ``--token-stdin`` before its subcommand, so the one credential this wrapper loaded is the one
    it uses: no second read of the credential file, no shell variable (``no-environment-vars.md``). Its output is
    not captured, so its refusal reason reaches the caller unchanged."""
    completed = subprocess.run(  # nosec B603  # this interpreter, the steward's own file, a fixed argv, no shell
        [sys.executable, str(MERGE_STEWARD_SCRIPT), STEWARD_STDIN_OPTION, *steward_args],
        input=token,
        text=True,
        check=False,
    )
    return completed.returncode


def cmd_enqueue_pr(token: str, owner: str, repo: str, args: argparse.Namespace) -> int:
    """Hand a PR whose own CI is green to the merge queue (``merge_steward.py enqueue``)."""
    del owner, repo  # the steward detects the repository itself, from config/delivery.json and git
    return _run_merge_steward(token=token, steward_args=[STEWARD_ENQUEUE, str(args.pr_number)])


def cmd_dequeue_pr(token: str, owner: str, repo: str, args: argparse.Namespace) -> int:
    """Take a PR out of the merge queue with a stated reason (``merge_steward.py dequeue``)."""
    del owner, repo
    return _run_merge_steward(
        token=token, steward_args=[STEWARD_DEQUEUE, str(args.pr_number), STEWARD_REASON, args.reason]
    )


def cmd_queue_status(token: str, owner: str, repo: str, args: argparse.Namespace) -> int:
    """Print the merge queue (``merge_steward.py status``), as JSON with ``--json``."""
    del owner, repo
    return _run_merge_steward(token=token, steward_args=[STEWARD_STATUS, *([STEWARD_JSON] if args.json else [])])


def cmd_issue_group(token: str, owner: str, repo: str, args: argparse.Namespace) -> int:
    """Route the nested ``issue <verb>`` claim trio onto this wrapper's flat handlers.

    Pure routing — it adds no behaviour of its own and every verb resolves to the same handler the
    flat subcommand uses, so the two spellings can never drift apart in semantics.
    """
    verb = getattr(args, DEST_ISSUE_SUBCOMMAND)
    handler = ISSUE_GROUP_DISPATCH[verb]
    return _exit_code_of(result=handler(token=token, owner=owner, repo=repo, args=args))


def _register_actions_subcommands(sub: Any) -> None:
    """Workflow-run / CI subcommands."""
    sub.add_parser("list-workflows", help="List all GitHub Actions workflows")
    sub.add_parser(
        "token-info",
        help="Report the authenticated token's expiry and scopes (never prints the token)",
    )

    p = sub.add_parser(
        "ci-liveness",
        help="Report whether CI is EXECUTING (steps ran), not merely whether the latest run is green",
    )
    p.add_argument(
        "--max-age-hours",
        type=float,
        default=72.0,
        help=(
            "Age of the newest Executed Run past which the pipeline is UNAVAILABLE (default: 72.0). "
            "Measured from the last Executed Run of the observed blackout, a 72 h threshold turns red "
            "~31 h BEFORE the UI-hanging defect merged into it. No environment-variable fallback."
        ),
    )
    p.add_argument(
        "--scan-runs",
        type=int,
        default=20,
        help=(
            "How many recent runs to scan, newest first (default: 20 ~ 3 days at the observed "
            "~6.6 runs/day). Scanning short-circuits at the first Executed Run, so ALIVE costs one "
            "job-list call. No environment-variable fallback."
        ),
    )

    p = sub.add_parser("list-runs", help="List recent workflow runs")
    p.add_argument("--workflow", help="Filter by workflow file name or ID")
    p.add_argument("--status", help="Filter by status (queued, in_progress, completed, ...)")
    p.add_argument("--limit", type=int, default=10)

    p = sub.add_parser("get-run", help="Show a single run")
    p.add_argument("run_id", type=int)

    p = sub.add_parser("get-jobs", help="List jobs for a run")
    p.add_argument("run_id", type=int)
    p.add_argument("--failed-only", action="store_true")
    p.add_argument(
        "--all-attempts",
        action="store_true",
        help=(
            "Include jobs from EARLIER attempts of a re-run run (API filter=all). Without this, only "
            "the newest attempt is listed, so a failure that was re-run to green is unreachable — "
            "including its log. Use when investigating a flake that a re-run has already hidden."
        ),
    )
    p.add_argument(
        "--show-steps",
        action="store_true",
        help="Append [steps=N] per job; steps=0 evidences a startup/billing (quota) failure",
    )
    p.add_argument(
        "--show-runner",
        action="store_true",
        help=(
            "Append [runner=NAME labels=...] per job — WHERE it ran. Required to verify a relocation "
            "(every job must show a fallback label with a NON-EMPTY runner name) and to tell a "
            "fallback job that never started from a refused hosted job"
        ),
    )
    p.add_argument(
        "--timing",
        action="store_true",
        help="Append [wall=Ns billed=Mmin] per job (billed = wall rounded UP to a whole minute) "
        "and print the run's TOTAL billed minutes (sum of per-job rounded durations)",
    )
    p.add_argument(
        "--step-status",
        action="store_true",
        help="Print, under each job, one line per step: `step <number> <status> <conclusion> <name>`, live while "
        "the job runs (issue #1277)",
    )

    p = sub.add_parser(
        "get-job-logs",
        help="Fetch the plain-text log for a single job (a running job's log can arrive only once it ends: #1277)",
    )
    p.add_argument("job_id", type=int)

    p = sub.add_parser("list-artifacts", help="List artifacts uploaded by a run")
    p.add_argument("run_id", type=int)

    p = sub.add_parser("download-artifact", help="Download + extract a run artifact zip into a directory")
    p.add_argument("artifact_id", type=int)
    p.add_argument("--dest", default="tmp/artifact", help="Directory to extract into (default: tmp/artifact)")

    sub.add_parser("list-repo-artifacts", help="List every Actions artifact of the repository and the bytes held")

    p = sub.add_parser(
        "delete-artifacts",
        help="Delete every unexpired Actions artifact older than --older-than-days, each confirm-read 404",
    )
    p.add_argument("--older-than-days", type=_at_least_one_day, required=True)
    p.add_argument("--dry-run", action="store_true", help="list what would be deleted; delete nothing")

    p = sub.add_parser("get-logs", help="Fetch logs for a run (zip archive, extracted)")
    p.add_argument("run_id", type=int)
    p.add_argument("--failed-only", action="store_true")

    p = sub.add_parser("rerun", help="Rerun a workflow run")
    p.add_argument("run_id", type=int)
    p.add_argument("--failed-only", action="store_true")

    p = sub.add_parser("cancel", help="Cancel an in-progress run")
    p.add_argument("run_id", type=int)

    p = sub.add_parser(
        "dispatch-workflow",
        help="Fire a workflow_dispatch event (the workflow must exist on the DEFAULT branch)",
    )
    p.add_argument("workflow", help="Workflow FILE NAME (e.g. ci-runner-pilot.yml) or numeric id")
    p.add_argument(
        "--ref",
        default=BRANCH_MAIN_DEFAULT,
        help=f"Branch or tag whose code the run executes (default: {BRANCH_MAIN_DEFAULT})",
    )

    sub.add_parser(
        "security-alerts",
        help="Report whether Dependabot ALERTS are enabled (204 enabled / 404 disabled-or-unauthorized)",
    )
    p = sub.add_parser("get-variable", help="Read one repository variable (value + updated_at)")
    p.add_argument("name", help="Variable name, e.g. CI_RUNNER_MODE")

    p = sub.add_parser(
        "set-variable",
        help="Create-or-update a repository variable, then CONFIRM-READ it (non-zero on mismatch)",
    )
    p.add_argument("name", help="Variable name, e.g. CI_RUNNER_MODE")
    p.add_argument("value", help="Value to store")


def _register_webhook_subcommands(sub: Any) -> None:
    """Repository-webhook subcommands (issue #1257): the hooks and CodeBuild's reply to each delivery."""
    sub.add_parser("list-hooks", help="List the repository's webhooks: id, active, receiving host, events")
    p = sub.add_parser("hook-deliveries", help="List a webhook's deliveries, newest first (receiver status per row)")
    p.add_argument("hook_id", type=int)
    p.add_argument(
        "--since",
        type=parse_since,
        default=None,
        help="Print no delivery older than this ISO 8601 time, which carries Z or an offset",
    )
    p.add_argument("--limit", type=int, default=GITHUB_MAX_PER_PAGE, help="Print at most this many rows")
    p.add_argument("--failed-only", action="store_true", help="Only deliveries whose receiver did not answer 2xx")
    p = sub.add_parser("hook-delivery", help="Show one delivery: its workflow job and the receiver's response body")
    p.add_argument("hook_id", type=int)
    p.add_argument("delivery_id", type=int)


def _register_release_asset_subcommands(sub: Any) -> None:
    """Register the seven release-asset subcommands: the publish, its seeder, its notes rewrite and four reads.

    Separate from `_register_actions_subcommands` for the same TWO reasons `_register_claim_subcommands` is
    separate from `_register_issue_subcommands`: it keeps that function under the complexity limit this
    project's targeted pylint run enforces (MEASURED — the first four of these registrations took it to
    R0915 61/50), and it lets the release-asset lifecycle read as one unit.

    They belong together because each exists to make the publish work, or to show what it served or why it
    did not: `put-file` seeds a repository that has no commit for a release to target; the two read-only
    diagnostics, `get-release` and `repo-visibility`, report the draft flag and the visibility that the
    publish's own confirm-read cannot see; `set-release-notes` replaces a release's notes and confirm-reads
    them; and `get-file` and `download-public-asset` read back one repository file and, with no credential,
    one release asset (issue #509).
    """
    p = sub.add_parser(
        "put-file",
        help="Create or update one file in a repository via the Contents API (needed to seed an EMPTY repo)",
    )
    p.add_argument("--path", required=True, help="Path inside the repository, e.g. README.md")
    p.add_argument("--file", required=True, help="Local file whose bytes to store there")
    p.add_argument("--message", required=True, help="Commit message")
    p.add_argument("--target-repo", help=TARGET_REPO_HELP)
    p.add_argument(
        "--expected-blob-sha",
        help=(
            "Compare-and-swap: refuse before the PUT unless the path's current blob sha is this one, then send it as "
            "the PUT's sha, so a change in between is answered 409"
        ),
    )

    p = sub.add_parser("get-release", help="Read one release by tag: draft state, prerelease state, assets")
    p.add_argument("--tag", required=True, help="The release tag to read")
    p.add_argument("--target-repo", help=TARGET_REPO_HELP)
    p.add_argument(
        "--body-out",
        help="Write the release's body to this file as its exact UTF-8 bytes, with no newline translation",
    )
    p.add_argument(
        "--expected-body-sha256",
        help=(
            "With --body-out: the sha256 the written body must have. Prints 'CONFIRM-READ BODY : match <H>', or "
            "MISMATCH and exits 1; the file is written either way. Refused without --body-out"
        ),
    )
    p.add_argument(
        "--include-drafts",
        action="store_true",
        help=(
            "When the tag has no published release, report its one DRAFT instead, read through the authenticated "
            "release listing; with no draft of the tag the 404 stands"
        ),
    )

    p = sub.add_parser("repo-visibility", help="Report whether a repository is PUBLIC or PRIVATE")
    p.add_argument("--target-repo", help=TARGET_REPO_HELP)

    p = sub.add_parser(
        "upload-release-asset",
        help="Create-or-reuse a release by tag and upload a DIGEST-GATED local file as an asset",
    )
    p.add_argument("--tag", required=True, help="The release tag. MUST NOT match v*.*.* (the product namespace)")
    p.add_argument("--file", required=True, help="Path to the local file to upload")
    p.add_argument(
        "--expected-sha256",
        required=True,
        help="The digest the file MUST have. REQUIRED: there is no un-gated upload path",
    )
    p.add_argument("--name", help="Asset name on the release (default: the file name)")
    p.add_argument("--target-repo", help=TARGET_REPO_HELP)
    # `--notes-file` is the body of a release this command CREATES, and `--require-existing-release` never creates
    # one, so argparse refuses the two together (E5.10; issue #509).
    release_options = p.add_mutually_exclusive_group()
    release_options.add_argument(
        "--notes-file",
        help=(
            "Path to a UTF-8 markdown file used as the release body when the release is CREATED. "
            "For a copyleft artefact this is where its upstream, its converter and its "
            "modification notice are served publicly"
        ),
    )
    release_options.add_argument(
        "--require-existing-release",
        action="store_true",
        help=(
            "Upload only into a release that already exists: a --tag with no release is refused and "
            "nothing is created. Not combinable with --notes-file"
        ),
    )
    # `--require-draft-release` never creates a release and never uploads into a published one, so it joins the same
    # group and argparse refuses it beside either option above (issue #702, design C3).
    release_options.add_argument(
        "--require-draft-release",
        action="store_true",
        help=(
            "Upload only into the ONE existing draft of --tag, read through the authenticated release listing: no "
            "draft, more than one, or a published release of the tag is refused before any upload, and nothing is "
            "created. Not combinable with --notes-file or --require-existing-release"
        ),
    )
    p.add_argument(
        "--replace",
        action="store_true",
        help="Delete an existing asset of the same name first. For a partially-completed publish",
    )

    p = sub.add_parser(
        "set-release-notes",
        help="Replace one release's notes with a local file's text, then CONFIRM-READ them and the latest release",
    )
    p.add_argument("--tag", required=True, help="The release tag whose notes to replace. MUST NOT match v*.*.*")
    p.add_argument("--notes-file", required=True, help="Path to a UTF-8 file, LF only, whose text becomes the notes")
    p.add_argument("--target-repo", required=True, help=TARGET_REPO_REQUIRED_HELP)
    p.add_argument(
        "--expected-latest",
        required=True,
        help=(
            "The tag that must be the latest release before the write, or nothing is written, and after it, or the "
            "exit is 1. make_latest is sent true only when --tag is this tag"
        ),
    )
    p.add_argument(
        "--expected-body-sha256",
        required=True,
        help="The sha256 the release's CURRENT body must have, or nothing is written",
    )

    p = sub.add_parser("get-file", help="Read one file of a repository via the Contents API and write its exact bytes")
    p.add_argument("--path", required=True, help="Path inside the repository, e.g. README.md")
    p.add_argument("--out", required=True, help="Local file to write the file's exact bytes to")
    p.add_argument("--target-repo", required=True, help=TARGET_REPO_REQUIRED_HELP)
    p.add_argument(
        "--expected-sha256",
        help=(
            "The sha256 the written file must have. Prints 'CONFIRM-READ BODY : match <H>', or MISMATCH and exits 1; "
            "the file is written either way"
        ),
    )

    p = sub.add_parser(
        CMD_DOWNLOAD_PUBLIC_ASSET,
        help="Download one release asset of a PUBLIC repository with NO credential, kept only if its sha256 matches",
    )
    p.add_argument("--target-repo", required=True, help=TARGET_REPO_REQUIRED_HELP)
    p.add_argument("--tag", required=True, help="The release tag the asset is published under")
    p.add_argument("--name", required=True, help="The asset's name on the release")
    p.add_argument("--out", required=True, help="Local file the asset is written to, only if its sha256 matches")
    p.add_argument(
        "--expected-sha256",
        required=True,
        help="The digest the served bytes MUST have. On a mismatch no file is written at --out and the exit is 1",
    )


def _register_draft_release_subcommands(sub: Any) -> None:
    """Register the two draft-first, never-latest release subcommands: a draft's creation and its publication.

    Separate from `_register_release_asset_subcommands`, whose docstring counts the seven it registers, and kept as
    one unit because the two are the ends of one publication (issue #702, design C3): `create-draft-release` makes the
    one draft the uploads go into, and `publish-release` publishes it without making it the latest release. Every
    option of both is REQUIRED, `--target-repo` among them, so nothing depends on a default.
    """
    expected_latest_help = (
        "The tag that must be the latest release before the write, or nothing is written, and after it, or the exit "
        "is 1. make_latest is never sent true"
    )
    p = sub.add_parser(
        "create-draft-release",
        help="Create one DRAFT release of a tag from a notes file, then CONFIRM-READ its body and the latest release",
    )
    p.add_argument("--target-repo", required=True, help=TARGET_REPO_REQUIRED_HELP)
    p.add_argument("--tag", required=True, help="The release tag. MUST NOT match v*.*.* and must have no release yet")
    p.add_argument("--notes-file", required=True, help="Path to a UTF-8 file, LF only, whose text becomes the body")
    p.add_argument(
        "--target-commitish",
        required=True,
        help="The commit the tag is created from: a full sha, 40 lowercase hex characters",
    )
    p.add_argument("--expected-latest", required=True, help=expected_latest_help)

    p = sub.add_parser(
        "publish-release",
        help='Publish the ONE draft of a tag with make_latest "false", then CONFIRM-READ it and the latest release',
    )
    p.add_argument("--target-repo", required=True, help=TARGET_REPO_REQUIRED_HELP)
    p.add_argument("--tag", required=True, help="The tag whose one draft to publish. MUST NOT match v*.*.*")
    p.add_argument("--expected-latest", required=True, help=expected_latest_help)


def _register_public_release_subcommands(sub: Any) -> None:
    """Register `get-public-latest-release`, the read of a public repository's latest release with no credential
    (issue #1248, design C6).

    Separate from `_register_release_asset_subcommands`, whose docstring counts the seven it registers, as
    `_register_draft_release_subcommands` is. `--target-repo` is REQUIRED, as it is for `download-public-asset`,
    because this checkout is private, so a read of it with no credential addresses no upstream.
    """
    p = sub.add_parser(
        CMD_GET_PUBLIC_LATEST_RELEASE,
        help=(
            "Read the latest release of a PUBLIC repository with NO credential, printed as one JSON object: its "
            "tag_name and each asset's name and digest"
        ),
    )
    p.add_argument("--target-repo", required=True, help=TARGET_REPO_REQUIRED_HELP)


def _register_pr_subcommands(sub: Any) -> None:
    """Pull-request lifecycle subcommands (create/get/checks/approve/merge/delete-branch)."""
    p = sub.add_parser("create-pr", help="Create a pull request")
    p.add_argument("--head", required=True)
    p.add_argument("--base", default="main")
    p.add_argument("--title")
    p.add_argument("--body")
    p.add_argument("--body-file", help=BODY_FILE_HELP)

    p = sub.add_parser("get-pr", help="Show a single pull request")
    p.add_argument("pr_number", type=int)

    p = sub.add_parser("get-pr-checks", help="Show combined CI check state for a PR's head commit")
    p.add_argument("pr_number", type=int)

    p = sub.add_parser("approve-pr", help="Submit an APPROVE review on a PR")
    p.add_argument("pr_number", type=int)
    p.add_argument("--body", help="Optional review comment")

    p = sub.add_parser("merge-pr", help="Merge a pull request")
    p.add_argument("pr_number", type=int)
    p.add_argument("--method", default="merge", choices=["merge", "squash", "rebase"])
    p.add_argument("--commit-message", help="Optional merge commit message")

    p = sub.add_parser("delete-remote-branch", help="Delete a remote branch")
    p.add_argument("branch", help="Branch name (without refs/heads/)")


def _register_delivery_subcommands(sub: Any) -> None:
    """The delivery verbs (``.claude/docs/delivery.md``), each delegating to ``scripts/merge_steward.py``."""
    p = sub.add_parser(CMD_ENQUEUE_PR, help="Hand a PR whose own CI is green to the merge queue (exit 4: refused)")
    p.add_argument("pr_number", type=int)
    p = sub.add_parser(CMD_DEQUEUE_PR, help="Take a PR out of the merge queue")
    p.add_argument("pr_number", type=int)
    p.add_argument("--reason", required=True, help="Why it leaves the queue; posted on the PR")
    p = sub.add_parser(CMD_QUEUE_STATUS, help="Print the merge queue")
    p.add_argument("--json", action="store_true", help="The machine-readable form")


def _register_issue_subcommands(sub: Any) -> None:
    """Issue subcommands."""
    p = sub.add_parser("list-issues", help="List issues")
    p.add_argument("--state", default="open", choices=["open", "closed", "all"])
    p.add_argument("--labels", help="Comma-separated label names")
    p.add_argument("--assignee", help="Filter by assignee login, or '*' (any) / 'none'")
    p.add_argument("--limit", type=int, default=30)
    _add_stdin_credential_option(parser=p)

    p = sub.add_parser("get-issue", help="Show a single issue")
    p.add_argument("issue_number", type=int)

    p = sub.add_parser("get-issue-comments", help="List comments on an issue")
    p.add_argument("issue_number", type=int)

    p = sub.add_parser("comment-issue", help="Add a comment to an issue")
    p.add_argument("issue_number", type=int)
    p.add_argument("--body")
    p.add_argument("--body-file", help=BODY_FILE_HELP)

    p = sub.add_parser(
        "delete-issue-comment",
        help="Delete ONE issue comment by its comment id (from get-issue-comments), verified",
    )
    p.add_argument("comment_id", type=int, help="the comment's `id`, NOT the issue number")

    p = sub.add_parser("update-issue", help="Update an issue")
    p.add_argument("issue_number", type=int)
    p.add_argument("--title")
    p.add_argument("--body")
    p.add_argument("--body-file", help=BODY_FILE_HELP)
    p.add_argument("--state", choices=["open", "closed"])
    p.add_argument("--labels", help="Comma-separated label names (replaces existing)")

    p = sub.add_parser("create-issue", help="Create a new issue")
    p.add_argument("--title", required=True)
    p.add_argument("--body")
    p.add_argument("--body-file", help=BODY_FILE_HELP)
    p.add_argument("--labels", help="Comma-separated label names")
    _add_stdin_credential_option(parser=p)

    p = sub.add_parser("link-issue", help="Add a native blocked_by dependency between two issues")
    p.add_argument("issue_number", type=int, help="The blocked issue (depends on the other)")
    p.add_argument("--blocked-by", type=int, required=True, help="Issue number that blocks issue_number")

    p = sub.add_parser("unlink-issue", help="Remove a native blocked_by dependency between two issues")
    p.add_argument("issue_number", type=int, help="The blocked issue (the dependency is removed FROM this one)")
    p.add_argument(
        "--blocked-by",
        type=int,
        required=True,
        help="Issue number to remove as a blocker of issue_number (e.g. after it is closed)",
    )

    p = sub.add_parser("add-sub-issue", help="Attach a sub-issue to a parent issue")
    p.add_argument("issue_number", type=int, help="The parent issue")
    p.add_argument("--sub-issue", type=int, required=True, help="Issue number to attach as a child")

    p = sub.add_parser("get-issue-dependencies", help="Show blocked_by / blocking / sub-issues for an issue")
    p.add_argument("issue_number", type=int)

    # --- in-progress lifecycle + work discovery (see the "Worker protocol" block above) ---
    p = sub.add_parser(
        "claim-issue",
        help="Claim an issue for work: ADD the 'in-progress' label (do this BEFORE branching/coding)",
    )
    p.add_argument("issue_number", type=int)
    p.add_argument(
        "--strict",
        action="store_true",
        help="Atomic acquire: FAIL (exit 1) if the issue is already 'in-progress' instead of a "
        "no-op success — use this to claim work and detect a concurrent worker's claim.",
    )

    p = sub.add_parser(
        "release-issue",
        help="Release a claim: REMOVE the 'in-progress' label AND your own assignment (inverts start-issue)",
    )
    p.add_argument("issue_number", type=int)

    sub.add_parser(
        "list-in-progress",
        help="List OPEN issues currently claimed ('in-progress') — active work, do NOT duplicate",
    )
    sub.add_parser(
        "list-available",
        help="List OPEN issues NOT claimed (no 'in-progress') — the free-work pool; pick new work here",
    )

    p = sub.add_parser(CMD_CLAIM_CHECK, help=CLAIM_CHECK_HELP)
    p.add_argument("issue_number", type=int)


def _add_start_issue_arguments(*, parser: Any) -> None:
    """Register the claim's options ONCE for both the flat and the nested spelling.

    Shared deliberately: two hand-maintained copies would let ``start-issue`` and ``issue start``
    drift into accepting different flags, and an agent following a rule that cites the other
    spelling would hit an argparse error instead of the claim.
    """
    parser.add_argument("issue_number", type=int)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Claim even when another worker holds it (deliberate take-over; refused without this)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also refuse a claim that is ALREADY YOURS, demanding a fresh acquisition (as on claim-issue)",
    )


def _add_label_add_arguments(*, parser: Any) -> None:
    """Register ``label-add`` options for both spellings."""
    parser.add_argument("issue_number", type=int)
    parser.add_argument("--labels", required=True, help="Comma-separated label names to ADD (existing ones kept)")


def _add_label_remove_arguments(*, parser: Any) -> None:
    """Register ``label-remove`` options for both spellings."""
    parser.add_argument("issue_number", type=int)
    parser.add_argument("--label", required=True, help="The ONE label name to remove (all others kept)")


def _add_assign_arguments(*, parser: Any) -> None:
    """Register ``assign`` options for both spellings.

    The three modes are a REQUIRED mutually-exclusive group, so an assign call that names no mode is
    rejected by argparse rather than silently doing nothing.
    """
    parser.add_argument("issue_number", type=int)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--me", action="store_true", help="Assign the account the PAT belongs to (GET /user)")
    mode.add_argument("--user", help="Assign this login")
    mode.add_argument("--unassign", action="store_true", help="Clear the issue's current assignees")


def _register_claim_subcommands(sub: Any) -> None:
    """Register the FLAT spellings of the deterministic claim and its additive primitives.

    Separate from ``_register_issue_subcommands`` so that function stays under the complexity limits
    the project's targeted pylint run enforces (R0915), and so the claim lifecycle reads as one unit.
    """
    _add_start_issue_arguments(parser=sub.add_parser(CMD_START_ISSUE, help=START_ISSUE_HELP))
    _add_label_add_arguments(parser=sub.add_parser(CMD_LABEL_ADD, help=LABEL_ADD_HELP))
    _add_label_remove_arguments(parser=sub.add_parser(CMD_LABEL_REMOVE, help=LABEL_REMOVE_HELP))
    _add_assign_arguments(parser=sub.add_parser(CMD_ASSIGN, help=ASSIGN_HELP))


def _register_issue_group_subcommands(sub: Any) -> None:
    """Register the nested ``issue <verb>`` claim trio (start / release / claim-check).

    This group exists so the argv the upstream ``gate_claim.py`` gate sends —
    ``<wrapper> issue claim-check <N>`` — RESOLVES on this host. That hook is synced verbatim from
    the shared standard, so editing its argv locally would be silently reverted by the next sync and
    the gate would go back to a no-op; teaching the wrapper both spellings is the durable direction.
    ``start`` / ``release`` are aliases of ``claim-issue`` / ``release-issue`` — the gate's block
    message instructs the agent to run ``issue start <N>``, and a gate whose prescribed remedy does
    not resolve is a dead end rather than a gate.
    """
    group = sub.add_parser(
        CMD_ISSUE_GROUP,
        help="Nested claim verbs: 'issue claim-check|start|release|label-add|label-remove|assign <n>'",
    )
    group_sub = group.add_subparsers(dest=DEST_ISSUE_SUBCOMMAND, required=True)

    p = group_sub.add_parser(CMD_CLAIM_CHECK, help=CLAIM_CHECK_HELP)
    p.add_argument("issue_number", type=int)

    _add_start_issue_arguments(parser=group_sub.add_parser(CMD_ISSUE_GROUP_START, help=START_ISSUE_HELP))

    p = group_sub.add_parser(CMD_ISSUE_GROUP_RELEASE, help="Alias of release-issue: drop the label + your assignment")
    p.add_argument("issue_number", type=int)

    # The additive primitives, in the nested spelling the always-loaded issue-tracking rule cites
    # ("Use the additive `issue label-add` / `issue label-remove` ... primitives for any label change").
    _add_label_add_arguments(parser=group_sub.add_parser(CMD_LABEL_ADD, help=LABEL_ADD_HELP))
    _add_label_remove_arguments(parser=group_sub.add_parser(CMD_LABEL_REMOVE, help=LABEL_REMOVE_HELP))
    _add_assign_arguments(parser=group_sub.add_parser(CMD_ASSIGN, help=ASSIGN_HELP))


def _register_wait_and_task_item_subcommands(sub: Any) -> None:
    """The three verbs the framework makes REQUIRED: the blocking CI wait and the task-item gate's pair.

    Separate from the other registration functions for the reason they are separate from each other —
    each stays under the targeted pylint statement limit — and because these three share one purpose:
    they are what lets an agent wait without ``sleep`` and close an issue only over a complete checklist.
    """
    p = sub.add_parser("wait-run", help="BLOCK until a run completes: exit 0 success, 10 other conclusion, 11 timeout")
    p.add_argument("run_id", type=int)
    p.add_argument("--timeout-seconds", type=int, default=WAIT_RUN_DEFAULT_TIMEOUT_SECONDS)
    p.add_argument("--interval-seconds", type=int, default=WAIT_RUN_DEFAULT_INTERVAL_SECONDS)

    p = sub.add_parser("reopen-issue", help="Reopen an issue, then re-read and verify it is open (idempotent)")
    p.add_argument("issue_number", type=int)

    p = sub.add_parser(
        "checklist",
        help="Count an issue's task list (ticked/total + unticked items), or tick/untick ONE item, verified",
    )
    p.add_argument("issue_number", type=int)
    action = p.add_mutually_exclusive_group()
    action.add_argument("--tick", help="Tick the ONE unticked item whose text contains this substring")
    action.add_argument("--untick", help="Untick the ONE ticked item whose text contains this substring")


def _add_stdin_credential_option(*, parser: argparse.ArgumentParser) -> None:
    """Register `--token-stdin` on `parser`, under `DEST_STDIN_CREDENTIAL`, the one spelling both deploy admission
    subcommands, `list-issues` and `create-issue` share, so `main` reads their token through `_load_stdin_token`
    (issue #908, design D6; issue #1266, design D3; issue #1248, design C6)."""
    parser.add_argument(
        "--token-stdin",
        action="store_true",
        dest=DEST_STDIN_CREDENTIAL,
        help="Read the token from the WHOLE of standard input instead of credentials/github-pat.txt",
    )


def _register_deploy_admission_subcommands(sub: Any) -> None:
    """Register `require-green-deploy`, the stage and prod legs' admission proof (issue #908, design D6), and
    `require-newest-trunk-run`, the dev leg's Admission Job check (issue #1266, design D3).

    Separate from `_register_actions_subcommands` for the reason the other registration functions are separate, the
    targeted pylint statement limit, and because these two take their token from standard input, each with its own
    `--token-stdin` (`_add_stdin_credential_option`). Every value is a plain string, checked by the handler
    (`_admission_inputs`, `_trunk_admission_inputs`) rather than by an argparse `type=`, so that a refused value exits
    1 and is never echoed in argparse's usage error. `--by-run-name` (issue #1036, design D3) is a `store_true` flag
    outside any mutually exclusive group, admitted beside `--run-id` and without it (issue #1266, design D6).
    """
    p = sub.add_parser(
        "require-green-deploy",
        help=(
            "Exit 0 only when a run of a workflow at a commit is a Green Deploy (every run field, and the workflow's "
            "jobs, each green)"
        ),
    )
    p.add_argument("--workflow", required=True, help="The workflow FILE NAME, e.g. deploy-dev.yml")
    p.add_argument("--head-sha", required=True, help="The commit: a full sha, 40 lowercase hex characters")
    p.add_argument(
        "--run-id",
        help="The one run to judge, in ASCII digits; without it, one page of the workflow's runs of the commit",
    )
    p.add_argument(
        "--by-run-name",
        action="store_true",
        help=(
            "Match the run by its display_title, the Run Name of --head-sha for --workflow (RUN_NAME_TEMPLATES), "
            "instead of its head_sha"
        ),
    )
    _add_stdin_credential_option(parser=p)

    p = sub.add_parser(
        "require-newest-trunk-run",
        help=(
            "Exit 0 only for a re-run, or when a green push run of ci.yml on main at a commit is the newest one; a "
            "newer one cancels this job's own run"
        ),
    )
    p.add_argument("--run-id", required=True, help="The Triggering Run of ci.yml, in ASCII digits")
    p.add_argument("--head-sha", required=True, help="The commit it tested: a full sha, 40 lowercase hex characters")
    p.add_argument(
        "--own-run-id",
        required=True,
        help="This job's own run, github.run_id, in ASCII digits: the one run it may cancel",
    )
    p.add_argument(
        "--run-attempt",
        required=True,
        help="This job's run attempt, github.run_attempt, in ASCII digits, at least 1; above 1 makes no request",
    )
    _add_stdin_credential_option(parser=p)


def _at_least_one_day(text: str) -> int:
    """`--older-than-days`: a whole number of days, at least one, so `delete-artifacts` never takes today's runs."""
    days = int(text)
    if days < 1:
        raise argparse.ArgumentTypeError(f"must be at least 1 day, got {days}")
    return days


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GitHub API wrapper")
    sub = parser.add_subparsers(dest="command", required=True)
    _register_actions_subcommands(sub)
    _register_webhook_subcommands(sub)
    _register_wait_and_task_item_subcommands(sub)
    _register_deploy_admission_subcommands(sub)
    _register_release_asset_subcommands(sub)
    _register_draft_release_subcommands(sub)
    _register_public_release_subcommands(sub)
    _register_pr_subcommands(sub)
    _register_delivery_subcommands(sub)
    _register_issue_subcommands(sub)
    _register_claim_subcommands(sub)
    _register_issue_group_subcommands(sub)
    return parser


#: Verb -> handler for the nested ``issue <verb>`` group. Every entry points at the SAME handler as
#: the corresponding flat subcommand, so the nested spelling is an alias and never a second
#: implementation. Read by ``cmd_issue_group``; declared before DISPATCH, which references it.
ISSUE_GROUP_DISPATCH: dict[str, Any] = {
    CMD_CLAIM_CHECK: cmd_claim_check,
    # `start` routes to the VERIFIED claim, not to `claim-issue`. It used to alias the latter, which
    # reads only labels — no state check, no assignee, and no post-write re-read — so the command every
    # rule and agent calls "idempotent and fail-closed" could not fail closed. `claim-issue` keeps its
    # own label-only semantics for this project's original worker protocol; the two are now distinct
    # commands rather than one command wearing two names.
    CMD_ISSUE_GROUP_START: cmd_start_issue,
    CMD_ISSUE_GROUP_RELEASE: cmd_release_issue,
    CMD_LABEL_ADD: cmd_label_add,
    CMD_LABEL_REMOVE: cmd_label_remove,
    CMD_ASSIGN: cmd_assign,
}

#: Annotated ``Any`` because handlers are heterogeneous in return type: most report only through
#: exceptions and return ``None``, while ``claim-check`` returns the exit status the gate reads.
DISPATCH: dict[str, Any] = {
    "list-workflows": cmd_list_workflows,
    "list-runs": cmd_list_runs,
    "get-run": cmd_get_run,
    "wait-run": cmd_wait_run,
    "require-green-deploy": cmd_require_green_deploy,
    "require-newest-trunk-run": cmd_require_newest_trunk_run,
    "reopen-issue": cmd_reopen_issue,
    "checklist": cmd_checklist,
    "get-jobs": cmd_get_jobs,
    "ci-liveness": cmd_ci_liveness,
    "token-info": cmd_token_info,
    "list-hooks": cmd_list_hooks,
    "hook-deliveries": cmd_hook_deliveries,
    "hook-delivery": cmd_hook_delivery,
    "get-job-logs": cmd_get_job_logs,
    "list-artifacts": cmd_list_artifacts,
    "download-artifact": cmd_download_artifact,
    "list-repo-artifacts": cmd_list_repo_artifacts,
    "delete-artifacts": cmd_delete_artifacts,
    "get-logs": cmd_get_logs,
    "rerun": cmd_rerun,
    "cancel": cmd_cancel,
    "dispatch-workflow": cmd_dispatch_workflow,
    "security-alerts": cmd_security_alerts,
    "get-variable": cmd_get_variable,
    "set-variable": cmd_set_variable,
    "upload-release-asset": cmd_upload_release_asset,
    "get-release": cmd_get_release,
    "put-file": cmd_put_file,
    "repo-visibility": cmd_repo_visibility,
    "set-release-notes": cmd_set_release_notes,
    "get-file": cmd_get_file,
    CMD_DOWNLOAD_PUBLIC_ASSET: cmd_download_public_asset,
    "create-draft-release": cmd_create_draft_release,
    "publish-release": cmd_publish_release,
    CMD_GET_PUBLIC_LATEST_RELEASE: cmd_get_public_latest_release,
    "create-pr": cmd_create_pr,
    "get-pr": cmd_get_pr,
    "get-pr-checks": cmd_get_pr_checks,
    "approve-pr": cmd_approve_pr,
    "merge-pr": cmd_merge_pr,
    "delete-remote-branch": cmd_delete_remote_branch,
    CMD_ENQUEUE_PR: cmd_enqueue_pr,
    CMD_DEQUEUE_PR: cmd_dequeue_pr,
    CMD_QUEUE_STATUS: cmd_queue_status,
    "list-issues": cmd_list_issues,
    "get-issue": cmd_get_issue,
    "get-issue-comments": cmd_get_issue_comments,
    "comment-issue": cmd_comment_issue,
    "delete-issue-comment": cmd_delete_issue_comment,
    "update-issue": cmd_update_issue,
    "create-issue": cmd_create_issue,
    "link-issue": cmd_link_issue,
    "unlink-issue": cmd_unlink_issue,
    "add-sub-issue": cmd_add_sub_issue,
    "get-issue-dependencies": cmd_get_issue_dependencies,
    "claim-issue": cmd_claim_issue,
    "release-issue": cmd_release_issue,
    "list-in-progress": cmd_list_in_progress,
    "list-available": cmd_list_available,
    CMD_CLAIM_CHECK: cmd_claim_check,
    # Each flat claim spelling maps to the SAME object as its nested counterpart in
    # ISSUE_GROUP_DISPATCH above, so `start-issue` and `issue start` are one implementation.
    CMD_START_ISSUE: cmd_start_issue,
    CMD_LABEL_ADD: cmd_label_add,
    CMD_LABEL_REMOVE: cmd_label_remove,
    CMD_ASSIGN: cmd_assign,
    CMD_ISSUE_GROUP: cmd_issue_group,
}


def _force_utf8_output() -> None:
    """Reconfigure stdout/stderr to UTF-8 so non-cp1252 output never aborts a command.

    On Windows, redirected/piped output defaults to cp1252, and an issue title containing a
    character outside it (e.g. U+25A1 in issue #299's title) crashed every listing command with
    ``UnicodeEncodeError`` unless the caller remembered ``-X utf8``. ``errors="replace"`` keeps
    output total — an unencodable character must never abort a read-only listing. A stream
    without ``reconfigure`` (a test double, an exotic redirection) is left untouched.

    DELEGATES to ``_configure_log_stream`` rather than reconfiguring the streams itself, and the
    reason is a MEASURED near-miss rather than tidiness. This function and that one were written
    independently — this one for issue #299's crash on a listing command, that one for issue #314's
    crash on a CI log — and they reconfigure the SAME two streams to the SAME encoding with the SAME
    error handler (``LOG_TEXT_ENCODING`` / ``LOG_TEXT_ERRORS`` are exactly ``"utf-8"`` / ``"replace"``).
    Rebasing #314 onto trunk auto-merged both, with no conflict marker, leaving two bodies for one
    behaviour and ``main()`` calling each once.

    Two copies of one fix is not a harmless redundancy: it is the defect
    ``test_both_log_commands_emit_through_one_shared_helper`` exists to prevent one function away
    (a behavioural test "passes just as happily against two copies of the same fix, and then only one
    of them gets maintained"). Neither NAME could simply be deleted — ``test_wrapper_list_issues.py``
    calls this one directly and ``test_wrapper_log_encoding.py`` calls that one, and a passing test is
    never removed to tidy a signature — so both names are kept and the BODY is collapsed to one.

    ``_configure_log_stream`` is the surviving producer because it spells the pair through named
    constants instead of inline literals, and because it carries the disclosed Trojan-Source
    reasoning that this widening depends on.
    """
    _configure_log_stream()


def main() -> int:
    # ONCE, for every command (issues #299 and #314). Fixing this class per-command took four rounds —
    # the log bodies, the archive-entry header, then the two artifact commands — and a full
    # classification of all 57 print sites in this file still found SIX exposed, two of them on the
    # CI-debugging path `.claude/rules/remote-ci-must-pass.md` mandates (`get-jobs --show-steps`,
    # `list-runs`). Enumerating the exposed sites is what kept failing; configuring the streams once
    # retires the class.
    #
    # BEFORE `parse_args()`, deliberately: argparse prints its own usage and error text to these
    # streams, so a later call would leave a `--help` render or a bad-argument message on the one path
    # that cannot route through any command. This ordering arrived with #299 and is why THIS call site
    # is the one kept — #314's was after the parse.
    #
    # This is safe for the commands that were never at risk rather than merely harmless to them: the 26
    # `json.dumps` renders are ASCII by construction (`ensure_ascii` defaults True), so their bytes do not
    # change, and the literal/int prints have nothing to encode. The only behaviour that changes is that a
    # command carrying a non-cp1252 character now PRINTS instead of raising.
    #
    # It does extend the disclosed Trojan-Source widening in `_configure_log_stream` from CI logs to
    # user-authored text such as issue titles. Accepted on the same reasoning and for the same reason it
    # was accepted there: that text is already fully attacker-influenceable, stripping it would corrupt
    # the artifact a reader is auditing, and the prior behaviour was not safety but a crash.
    _force_utf8_output()
    args = _build_parser().parse_args()
    try:
        # A command of `CREDENTIAL_FREE_COMMANDS` loads no token (issue #1248, design C6). `--token-stdin`, registered
        # by `require-green-deploy`, `require-newest-trunk-run`, `list-issues` and `create-issue`, takes the token from
        # standard input instead of the credential file; both go through `_one_token`, and either refusal exits 2
        # (issue #908, design D6; issue #1266, design D3).
        if args.command in CREDENTIAL_FREE_COMMANDS:
            token = NO_CREDENTIAL
        elif getattr(args, DEST_STDIN_CREDENTIAL, False):
            token = _load_stdin_token()
        else:
            token = _load_token()
        owner, repo = _detect_repo()
    except GitHubAPIError as exc:
        logger.error(str(exc))
        return 2

    handler = DISPATCH[args.command]
    try:
        result = handler(token=token, owner=owner, repo=repo, args=args)
    except GitHubAPIError as exc:
        logger.error(str(exc))
        if exc.details is not None:
            logger.error("Details: %s", json.dumps(exc.details, indent=2))
        return 1
    # A handler's return value, when it has one, IS the process exit status: `claim-check` reports
    # its verdict that way and the claim gate reads nothing but the number.
    return _exit_code_of(result=result)


if __name__ == "__main__":
    sys.exit(main())
