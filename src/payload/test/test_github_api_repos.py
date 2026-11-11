"""Tests of the GitHub wrapper's ``repos`` family, ``github_api/families/repos.py`` (issue #27 ``change.md``; AC-1,
AC-3, AC-4, AC-6, AC-7).

Every expected value here is transcribed from ``docs/api-reference/github/rest/*.md`` and ``conventions.md``, never
read from the records or from ``commands/call.py``:

- ``REPOS_OPERATION_IDS``: the operation ID of every section whose operation line names a ``repos/`` ID, in
  ``branches.md``, ``collaborators.md``, ``commits.md``, ``deploy-keys.md``, ``deployments.md``, ``metrics.md``,
  ``orgs.md``, ``pages.md``, ``releases.md`` and ``repos.md``; ``repos/upload-release-asset`` stays pending (DL-002);
- ``MULTI_SEGMENT_PARAMETERS``: for each section with one, the path parameters whose ``Parameter`` row reads "may
  contain `/` (multi-segment path)" (AC-3);
- ``LIST_RECORDS``: each section with a ``Paging:`` line or a ``Link`` response header (AC-4), but
  ``repos/get-commit`` and ``repos/compare-commits``, whose ``Paging:`` line names two keys: its path, the one key
  after "items in" (``None`` where the ``Paging:`` line or the ``200`` response gives the body as an array), and
  whether its ``Parameter`` table documents ``per_page``;
- ``BRANCH_WRITING_CALLS``: AC-7's records of this family, each called with every path parameter but ``owner`` and
  ``repo`` and every required body member its section documents, so only a refusal keeps the request from being sent.

``test_a_list_record_prints_every_item`` is #28 design D8's slice test: one golden case per ``Paging.LINK`` record,
argv ``call <id>`` with ``--path NAME=VALUE`` for each path parameter but ``owner`` and ``repo``, plus ``--query
per_page=1`` where the section documents ``per_page``, against a fake host serving two items under the record's item
key, one per page; standard output is both as one JSON array. ``repos/list-commit-statuses-for-ref`` is called with a
``ref`` holding ``/`` (``conventions.md`` "Path parameters": ``heads/BRANCH``), whose route is reached only with the
slash kept literal (AC-3). Each case runs with ``fx.run_product_case`` through the product entry script's
``main(argv=...)`` in the fixture project (``origin`` ``o/r``), which judges its exit code, its standard output
exactly, its requests other than ``GET`` (none at all for a refusal) and that every request was routed.

The fake host module is loaded by path as ``test_github_api_call.py`` loads it. No test opens a connection.

Run: ``python scripts/run_tests.py src/payload/test/test_github_api_repos.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import logging
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Tuple

import pytest

HERE = Path(__file__).resolve().parent
FIXTURES_PATH = HERE / "github_wrapper_fixtures.py"
FIXTURES_MODULE = "github_wrapper_fixtures"


def _load_fixtures() -> ModuleType:
    """The fake host module, loaded by path once per process; ``sys.modules`` holds it for its dataclasses."""
    loaded = sys.modules.get(FIXTURES_MODULE)
    if loaded is not None and Path(str(loaded.__file__)).resolve() == FIXTURES_PATH:
        return loaded
    spec = importlib.util.spec_from_file_location(name=FIXTURES_MODULE, location=FIXTURES_PATH)
    assert spec is not None and spec.loader is not None, f"cannot load {FIXTURES_PATH}"
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[FIXTURES_MODULE] = module
    spec.loader.exec_module(module=module)
    return module


fx = _load_fixtures()

REGISTRY = "registry"
TRANSPORT = "transport"
FAMILY = "repos"
FAMILY_MODULE = f"{fx.PACKAGE}.families.{FAMILY}"
FAMILY_FILE = fx.SCRIPTS_DIR / fx.PACKAGE / "families" / f"{FAMILY}.py"

AC_6 = "AC-6"
AC_7 = "AC-7"
CALL = "call"
OPTION_PATH = "--path"
OPTION_QUERY = "--query"
OPTION_RAW_FIELD = "--raw-field"
PATH_OWNER = "owner"
PATH_REPO = "repo"
#: The path parameters ``call`` defaults to the ``origin`` repository, so no case gives them.
ORIGIN_PARAMETERS = (PATH_OWNER, PATH_REPO)
QUERY_ONE_PER_PAGE = f"{fx.QUERY_PER_PAGE}=1"
#: A ``{name}`` placeholder of a path template (``conventions.md`` "Path parameters").
PATH_PLACEHOLDER = re.compile(r"\{([^{}]+)\}")
NON_ALPHANUMERIC = re.compile(r"[^A-Za-z0-9]")
TEST_VALUE_PREFIX = "v"
#: ``run_product_case`` reads standard error along with standard output; no case here withholds a value, so
#: ``fx.assert_log`` judges the log records alone.
STDERR_READ_BY_THE_RUN = ""

UPLOAD_RELEASE_ASSET = "repos/upload-release-asset"

#: Every ``repos/`` operation ID of ``rest/*.md``, one per section.
REPOS_OPERATION_IDS = frozenset(
    {
        "repos/accept-invitation-for-authenticated-user",
        "repos/add-app-access-restrictions",
        "repos/add-collaborator",
        "repos/add-status-check-contexts",
        "repos/add-team-access-restrictions",
        "repos/add-user-access-restrictions",
        "repos/cancel-pages-deployment",
        "repos/check-automated-security-fixes",
        "repos/check-collaborator",
        "repos/check-immutable-releases",
        "repos/check-private-vulnerability-reporting",
        "repos/check-vulnerability-alerts",
        "repos/codeowners-errors",
        "repos/compare-commits",
        "repos/create-attestation",
        "repos/create-autolink",
        "repos/create-commit-comment",
        "repos/create-commit-signature-protection",
        "repos/create-commit-status",
        "repos/create-deploy-key",
        "repos/create-deployment",
        "repos/create-deployment-branch-policy",
        "repos/create-deployment-protection-rule",
        "repos/create-deployment-status",
        "repos/create-dispatch-event",
        "repos/create-for-authenticated-user",
        "repos/create-fork",
        "repos/create-in-org",
        "repos/create-or-update-environment",
        "repos/create-or-update-file-contents",
        "repos/create-org-ruleset",
        "repos/create-pages-deployment",
        "repos/create-pages-site",
        "repos/create-release",
        "repos/create-repo-ruleset",
        "repos/create-using-template",
        "repos/create-webhook",
        "repos/custom-properties-for-repos-create-or-update-repository-values",
        "repos/custom-properties-for-repos-get-repository-values",
        "repos/decline-invitation-for-authenticated-user",
        "repos/delete",
        "repos/delete-access-restrictions",
        "repos/delete-admin-branch-protection",
        "repos/delete-an-environment",
        "repos/delete-autolink",
        "repos/delete-branch-protection",
        "repos/delete-commit-comment",
        "repos/delete-commit-signature-protection",
        "repos/delete-deploy-key",
        "repos/delete-deployment",
        "repos/delete-deployment-branch-policy",
        "repos/delete-file",
        "repos/delete-invitation",
        "repos/delete-org-ruleset",
        "repos/delete-pages-site",
        "repos/delete-pull-request-review-protection",
        "repos/delete-release",
        "repos/delete-release-asset",
        "repos/delete-repo-ruleset",
        "repos/delete-webhook",
        "repos/disable-automated-security-fixes",
        "repos/disable-deployment-protection-rule",
        "repos/disable-immutable-releases",
        "repos/disable-private-vulnerability-reporting",
        "repos/disable-vulnerability-alerts",
        "repos/download-tarball-archive",
        "repos/download-zipball-archive",
        "repos/enable-automated-security-fixes",
        "repos/enable-immutable-releases",
        "repos/enable-private-vulnerability-reporting",
        "repos/enable-vulnerability-alerts",
        "repos/generate-release-notes",
        "repos/get",
        "repos/get-access-restrictions",
        "repos/get-admin-branch-protection",
        "repos/get-all-deployment-protection-rules",
        "repos/get-all-environments",
        "repos/get-all-status-check-contexts",
        "repos/get-all-topics",
        "repos/get-apps-with-access-to-protected-branch",
        "repos/get-autolink",
        "repos/get-branch",
        "repos/get-branch-protection",
        "repos/get-branch-rules",
        "repos/get-clones",
        "repos/get-code-frequency-stats",
        "repos/get-collaborator-permission-level",
        "repos/get-combined-status-for-ref",
        "repos/get-commit",
        "repos/get-commit-activity-stats",
        "repos/get-commit-comment",
        "repos/get-commit-signature-protection",
        "repos/get-community-profile-metrics",
        "repos/get-content",
        "repos/get-contributors-stats",
        "repos/get-custom-deployment-protection-rule",
        "repos/get-deploy-key",
        "repos/get-deployment",
        "repos/get-deployment-branch-policy",
        "repos/get-deployment-status",
        "repos/get-environment",
        "repos/get-hash-algorithm",
        "repos/get-latest-pages-build",
        "repos/get-latest-release",
        "repos/get-org-rule-suite",
        "repos/get-org-rule-suites",
        "repos/get-org-ruleset",
        "repos/get-org-rulesets",
        "repos/get-pages",
        "repos/get-pages-build",
        "repos/get-pages-deployment",
        "repos/get-pages-health-check",
        "repos/get-participation-stats",
        "repos/get-pull-request-review-protection",
        "repos/get-punch-card-stats",
        "repos/get-readme",
        "repos/get-readme-in-directory",
        "repos/get-release",
        "repos/get-release-asset",
        "repos/get-release-by-tag",
        "repos/get-repo-rule-suite",
        "repos/get-repo-rule-suites",
        "repos/get-repo-ruleset",
        "repos/get-repo-ruleset-history",
        "repos/get-repo-ruleset-version",
        "repos/get-repo-rulesets",
        "repos/get-status-checks-protection",
        "repos/get-teams-with-access-to-protected-branch",
        "repos/get-top-paths",
        "repos/get-top-referrers",
        "repos/get-users-with-access-to-protected-branch",
        "repos/get-views",
        "repos/get-webhook",
        "repos/get-webhook-config-for-repo",
        "repos/get-webhook-delivery",
        "repos/list-activities",
        "repos/list-attestations",
        "repos/list-autolinks",
        "repos/list-branches",
        "repos/list-branches-for-head-commit",
        "repos/list-collaborators",
        "repos/list-comments-for-commit",
        "repos/list-commit-comments-for-repo",
        "repos/list-commit-statuses-for-ref",
        "repos/list-commits",
        "repos/list-contributors",
        "repos/list-custom-deployment-rule-integrations",
        "repos/list-deploy-keys",
        "repos/list-deployment-branch-policies",
        "repos/list-deployment-statuses",
        "repos/list-deployments",
        "repos/list-for-authenticated-user",
        "repos/list-for-org",
        "repos/list-for-user",
        "repos/list-forks",
        "repos/list-invitations",
        "repos/list-invitations-for-authenticated-user",
        "repos/list-issue-types",
        "repos/list-languages",
        "repos/list-pages-builds",
        "repos/list-public",
        "repos/list-pull-requests-associated-with-commit",
        "repos/list-release-assets",
        "repos/list-releases",
        "repos/list-tags",
        "repos/list-teams",
        "repos/list-webhook-deliveries",
        "repos/list-webhooks",
        "repos/merge",
        "repos/merge-upstream",
        "repos/ping-webhook",
        "repos/redeliver-webhook-delivery",
        "repos/remove-app-access-restrictions",
        "repos/remove-collaborator",
        "repos/remove-status-check-contexts",
        "repos/remove-status-check-protection",
        "repos/remove-team-access-restrictions",
        "repos/remove-user-access-restrictions",
        "repos/rename-branch",
        "repos/replace-all-topics",
        "repos/request-pages-build",
        "repos/set-admin-branch-protection",
        "repos/set-app-access-restrictions",
        "repos/set-status-check-contexts",
        "repos/set-team-access-restrictions",
        "repos/set-user-access-restrictions",
        "repos/test-push-webhook",
        "repos/transfer",
        "repos/update",
        "repos/update-branch-protection",
        "repos/update-commit-comment",
        "repos/update-deployment-branch-policy",
        "repos/update-information-about-pages-site",
        "repos/update-invitation",
        "repos/update-org-ruleset",
        "repos/update-pull-request-review-protection",
        "repos/update-release",
        "repos/update-release-asset",
        "repos/update-repo-ruleset",
        "repos/update-status-check-protection",
        "repos/update-webhook",
        "repos/update-webhook-config-for-repo",
        "repos/upload-release-asset",
    }
)
#: AC-1: the IDs ``OPERATIONS`` holds a record of, each once: every ``repos/`` ID but the one left pending.
RECORDED_IDS = REPOS_OPERATION_IDS - {UPLOAD_RELEASE_ASSET}

#: AC-3: for each ``repos/`` section with one, its path parameters whose row reads "may contain `/` (multi-segment
#: path)".
MULTI_SEGMENT_PARAMETERS: Dict[str, FrozenSet[str]] = {
    "repos/add-app-access-restrictions": frozenset({"branch"}),
    "repos/add-status-check-contexts": frozenset({"branch"}),
    "repos/add-team-access-restrictions": frozenset({"branch"}),
    "repos/add-user-access-restrictions": frozenset({"branch"}),
    "repos/compare-commits": frozenset({"basehead"}),
    "repos/create-commit-comment": frozenset({"commit_sha"}),
    "repos/create-commit-signature-protection": frozenset({"branch"}),
    "repos/create-commit-status": frozenset({"sha"}),
    "repos/create-or-update-file-contents": frozenset({"path"}),
    "repos/delete-access-restrictions": frozenset({"branch"}),
    "repos/delete-admin-branch-protection": frozenset({"branch"}),
    "repos/delete-branch-protection": frozenset({"branch"}),
    "repos/delete-commit-signature-protection": frozenset({"branch"}),
    "repos/delete-file": frozenset({"path"}),
    "repos/delete-pull-request-review-protection": frozenset({"branch"}),
    "repos/download-tarball-archive": frozenset({"ref"}),
    "repos/download-zipball-archive": frozenset({"ref"}),
    "repos/get-access-restrictions": frozenset({"branch"}),
    "repos/get-admin-branch-protection": frozenset({"branch"}),
    "repos/get-all-status-check-contexts": frozenset({"branch"}),
    "repos/get-apps-with-access-to-protected-branch": frozenset({"branch"}),
    "repos/get-branch": frozenset({"branch"}),
    "repos/get-branch-protection": frozenset({"branch"}),
    "repos/get-branch-rules": frozenset({"branch"}),
    "repos/get-combined-status-for-ref": frozenset({"ref"}),
    "repos/get-commit": frozenset({"ref"}),
    "repos/get-commit-signature-protection": frozenset({"branch"}),
    "repos/get-content": frozenset({"path"}),
    "repos/get-pull-request-review-protection": frozenset({"branch"}),
    "repos/get-readme-in-directory": frozenset({"dir"}),
    "repos/get-release-by-tag": frozenset({"tag"}),
    "repos/get-status-checks-protection": frozenset({"branch"}),
    "repos/get-teams-with-access-to-protected-branch": frozenset({"branch"}),
    "repos/get-users-with-access-to-protected-branch": frozenset({"branch"}),
    "repos/list-attestations": frozenset({"subject_digest"}),
    "repos/list-branches-for-head-commit": frozenset({"commit_sha"}),
    "repos/list-comments-for-commit": frozenset({"commit_sha"}),
    "repos/list-commit-statuses-for-ref": frozenset({"ref"}),
    "repos/list-pull-requests-associated-with-commit": frozenset({"commit_sha"}),
    "repos/remove-app-access-restrictions": frozenset({"branch"}),
    "repos/remove-status-check-contexts": frozenset({"branch"}),
    "repos/remove-status-check-protection": frozenset({"branch"}),
    "repos/remove-team-access-restrictions": frozenset({"branch"}),
    "repos/remove-user-access-restrictions": frozenset({"branch"}),
    "repos/rename-branch": frozenset({"branch"}),
    "repos/set-admin-branch-protection": frozenset({"branch"}),
    "repos/set-app-access-restrictions": frozenset({"branch"}),
    "repos/set-status-check-contexts": frozenset({"branch"}),
    "repos/set-team-access-restrictions": frozenset({"branch"}),
    "repos/set-user-access-restrictions": frozenset({"branch"}),
    "repos/update-branch-protection": frozenset({"branch"}),
    "repos/update-pull-request-review-protection": frozenset({"branch"}),
    "repos/update-status-check-protection": frozenset({"branch"}),
}

#: A ``ref`` holding ``/``: ``conventions.md`` "Path parameters" (``commits/{ref}`` takes ``heads/BRANCH``; its example
#: branch is ``feature/login``).
REF_WITH_SLASHES = "heads/feature/login"


@dataclass(frozen=True)
class ListRecord:
    """A ``Paging.LINK`` record as its section documents it: the operation ID, the path template, the key its items
    sit under (``None``: the body is the array), whether it documents ``per_page``, and each path value the case gives
    in place of ``path_value``'s, as ``(name, value)`` pairs."""

    operation_id: str
    path: str
    item_key: Optional[str]
    per_page: bool
    values: Tuple[Tuple[str, str], ...] = ()


#: AC-4, AC-6: every ``repos/`` section with a ``Paging:`` line or a ``Link`` response header, but
#: ``repos/get-commit`` and ``repos/compare-commits``.
LIST_RECORDS: Tuple[ListRecord, ...] = (
    ListRecord(
        operation_id="repos/get-all-environments",
        path="/repos/{owner}/{repo}/environments",
        item_key="environments",
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/get-all-topics",
        path="/repos/{owner}/{repo}/topics",
        item_key="names",
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/get-branch-rules",
        path="/repos/{owner}/{repo}/rules/branches/{branch}",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/get-combined-status-for-ref",
        path="/repos/{owner}/{repo}/commits/{ref}/status",
        item_key="statuses",
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/get-org-rule-suites",
        path="/orgs/{org}/rulesets/rule-suites",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/get-org-rulesets",
        path="/orgs/{org}/rulesets",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/get-repo-rule-suites",
        path="/repos/{owner}/{repo}/rulesets/rule-suites",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/get-repo-ruleset-history",
        path="/repos/{owner}/{repo}/rulesets/{ruleset_id}/history",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/get-repo-rulesets",
        path="/repos/{owner}/{repo}/rulesets",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-activities",
        path="/repos/{owner}/{repo}/activity",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-attestations",
        path="/repos/{owner}/{repo}/attestations/{subject_digest}",
        item_key="attestations",
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-branches",
        path="/repos/{owner}/{repo}/branches",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-collaborators",
        path="/repos/{owner}/{repo}/collaborators",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-comments-for-commit",
        path="/repos/{owner}/{repo}/commits/{commit_sha}/comments",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-commit-comments-for-repo",
        path="/repos/{owner}/{repo}/comments",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-commit-statuses-for-ref",
        path="/repos/{owner}/{repo}/commits/{ref}/statuses",
        item_key=None,
        per_page=True,
        values=(("ref", REF_WITH_SLASHES),),
    ),
    ListRecord(
        operation_id="repos/list-commits",
        path="/repos/{owner}/{repo}/commits",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-contributors",
        path="/repos/{owner}/{repo}/contributors",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-custom-deployment-rule-integrations",
        path="/repos/{owner}/{repo}/environments/{environment_name}/deployment_protection_rules/apps",
        item_key="available_custom_deployment_protection_rule_integrations",
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-deploy-keys",
        path="/repos/{owner}/{repo}/keys",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-deployment-branch-policies",
        path="/repos/{owner}/{repo}/environments/{environment_name}/deployment-branch-policies",
        item_key="branch_policies",
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-deployment-statuses",
        path="/repos/{owner}/{repo}/deployments/{deployment_id}/statuses",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-deployments",
        path="/repos/{owner}/{repo}/deployments",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-for-authenticated-user",
        path="/user/repos",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-for-org",
        path="/orgs/{org}/repos",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-for-user",
        path="/users/{username}/repos",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-forks",
        path="/repos/{owner}/{repo}/forks",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-invitations",
        path="/repos/{owner}/{repo}/invitations",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-invitations-for-authenticated-user",
        path="/user/repository_invitations",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-pages-builds",
        path="/repos/{owner}/{repo}/pages/builds",
        item_key=None,
        per_page=True,
    ),
    # No ``Paging:`` line and no ``per_page``: the ``200`` response is an array with a ``Link`` header (ID cursor).
    ListRecord(
        operation_id="repos/list-public",
        path="/repositories",
        item_key=None,
        per_page=False,
    ),
    ListRecord(
        operation_id="repos/list-pull-requests-associated-with-commit",
        path="/repos/{owner}/{repo}/commits/{commit_sha}/pulls",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-release-assets",
        path="/repos/{owner}/{repo}/releases/{release_id}/assets",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-releases",
        path="/repos/{owner}/{repo}/releases",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-tags",
        path="/repos/{owner}/{repo}/tags",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-teams",
        path="/repos/{owner}/{repo}/teams",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-webhook-deliveries",
        path="/repos/{owner}/{repo}/hooks/{hook_id}/deliveries",
        item_key=None,
        per_page=True,
    ),
    ListRecord(
        operation_id="repos/list-webhooks",
        path="/repos/{owner}/{repo}/hooks",
        item_key=None,
        per_page=True,
    ),
)

#: The two items every list case serves, one per page where the record documents ``per_page``.
LISTED_ITEMS: Tuple[Dict[str, Any], ...] = (
    {fx.FIELD_ID: 1, fx.FIELD_NAME: "first"},
    {fx.FIELD_ID: 2, fx.FIELD_NAME: "second"},
)


@dataclass(frozen=True)
class BranchWritingCall:
    """An AC-7 record of this family and the arguments after ``call <id>``: every path parameter but ``owner`` and
    ``repo``, and every required body member its section documents."""

    operation_id: str
    arguments: Tuple[str, ...]


#: A contents path holding ``/``: ``conventions.md`` "Path parameters" (``PUT /repos/OWNER/REPO/contents/docs/guide/
#: intro.md``).
CONTENTS_PATH = "docs/guide/intro.md"
RENAMED_BRANCH = "issue-17-wrapper-renamed"
FILE_CONTENT = "SGVsbG8="  # ``Hello`` in Base64, as the contents API takes ``content``

#: AC-7: the records of this family whose call commits to, creates, moves or renames a branch.
BRANCH_WRITING_CALLS: Tuple[BranchWritingCall, ...] = (
    BranchWritingCall(
        operation_id="repos/merge",
        arguments=(OPTION_RAW_FIELD, f"base={fx.BRANCH_MAIN}", OPTION_RAW_FIELD, f"head={fx.FEATURE_BRANCH}"),
    ),
    BranchWritingCall(
        operation_id="repos/merge-upstream",
        arguments=(OPTION_RAW_FIELD, f"branch={fx.BRANCH_MAIN}"),
    ),
    BranchWritingCall(
        operation_id="repos/rename-branch",
        arguments=(OPTION_PATH, f"branch={fx.FEATURE_BRANCH}", OPTION_RAW_FIELD, f"new_name={RENAMED_BRANCH}"),
    ),
    BranchWritingCall(
        operation_id="repos/create-or-update-file-contents",
        arguments=(
            OPTION_PATH,
            f"path={CONTENTS_PATH}",
            OPTION_RAW_FIELD,
            "message=Add the guide",
            OPTION_RAW_FIELD,
            f"content={FILE_CONTENT}",
        ),
    ),
    BranchWritingCall(
        operation_id="repos/delete-file",
        arguments=(
            OPTION_PATH,
            f"path={CONTENTS_PATH}",
            OPTION_RAW_FIELD,
            "message=Remove the guide",
            OPTION_RAW_FIELD,
            f"sha={fx.HEAD_SHA}",
        ),
    ),
)
#: AC-7's refusal: the log record says that no subcommand sends the operation (``commands/call.py`` maps it to none).
NO_SUBCOMMAND_SENDS_IT = r"(?i)\bno\b[\w\s-]*\bsubcommand\b[\w\s-]*\bsends\b"


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here fails if anything it runs in this process opens a socket connection."""
    fx.refuse_connections(monkeypatch=monkeypatch)


def path_value(*, name: str) -> str:
    """A path parameter's test value: alphanumeric, so nothing needs encoding, and made from its name, so a value
    given under another name changes the path."""
    return f"{TEST_VALUE_PREFIX}{NON_ALPHANUMERIC.sub(repl='', string=name)}"


def path_values(*, listed: ListRecord) -> Dict[str, str]:
    """The value of each placeholder of ``listed.path``, in path order: the fixture's ``origin`` for ``owner`` and
    ``repo``, else the record's own value or ``path_value``'s."""
    origin = {PATH_OWNER: fx.OWNER, PATH_REPO: fx.REPOSITORY}
    given = dict(listed.values)
    return {
        name: origin.get(name, given.get(name, path_value(name=name)))
        for name in PATH_PLACEHOLDER.findall(string=listed.path)
    }


def expanded(*, path: str, values: Mapping[str, str]) -> str:
    """``path`` with each ``{name}`` replaced by ``values[name]`` as written, a ``/`` kept literal."""
    return PATH_PLACEHOLDER.sub(repl=lambda match: values[match.group(1)], string=path)


def list_argv(*, listed: ListRecord, values: Mapping[str, str]) -> Tuple[str, ...]:
    """``call <id>``, ``--path NAME=VALUE`` for each path parameter but ``owner`` and ``repo``, and ``--query
    per_page=1`` when the record documents ``per_page`` (#28 design D8)."""
    argv = [CALL, listed.operation_id]
    for name, value in values.items():
        if name not in ORIGIN_PARAMETERS:
            argv.extend((OPTION_PATH, f"{name}={value}"))
    if listed.per_page:
        argv.extend((OPTION_QUERY, QUERY_ONE_PER_PAGE))
    return tuple(argv)


def list_case(*, listed: ListRecord) -> Any:
    """#28 design D8's golden case of ``listed``: exit 0, standard output both items as one JSON array, against a list
    route serving them under the record's item key on its expanded path."""
    values = path_values(listed=listed)
    return fx.GoldenCase(
        name=f"{AC_6}/exit-0/{listed.operation_id}",
        argv=list_argv(listed=listed, values=values),
        stdout=fx.printed_json(value=list(LISTED_ITEMS)),
        exit_code=fx.EXIT_OK,
        routes=(
            fx.ListRouteSpec(
                url=expanded(path=listed.path, values=values), items=LISTED_ITEMS, item_key=listed.item_key
            ),
        ),
    )


def refusal_case(*, branch_writing: BranchWritingCall) -> Any:
    """AC-7's golden case of ``branch_writing``: exit 2, nothing on standard output, no request, and one log record
    naming the ID as ``json.dumps`` renders it (#28 D4) and that no subcommand sends it."""
    return fx.GoldenCase(
        name=f"{AC_7}/exit-2/{branch_writing.operation_id}",
        argv=(CALL, branch_writing.operation_id, *branch_writing.arguments),
        stdout="",
        exit_code=fx.EXIT_REFUSED,
        log=fx.LogExpectation(
            refusal=(re.escape(json.dumps(obj=branch_writing.operation_id)), NO_SUBCOMMAND_SENDS_IT), withheld=()
        ),
    )


def list_record_name(listed: ListRecord) -> str:
    """The test id of a ``LIST_RECORDS`` row."""
    return listed.operation_id


def branch_writing_name(branch_writing: BranchWritingCall) -> str:
    """The test id of a ``BRANCH_WRITING_CALLS`` row."""
    return branch_writing.operation_id


def repos_family() -> ModuleType:
    """``github_api.families.repos``, imported from the ``scripts`` directory beside this suite
    (``fx.import_api_module`` puts it on ``sys.path``); a copy imported from anywhere else fails here."""
    fx.import_api_module(name=REGISTRY)
    family = importlib.import_module(name=FAMILY_MODULE)
    loaded_from = Path(str(family.__file__)).resolve()
    assert loaded_from == FAMILY_FILE.resolve(), f"{FAMILY_MODULE} was imported from {loaded_from}"
    return family


def records_by_id(*, family: ModuleType) -> Dict[str, Any]:
    """Each ``RestOperation`` of ``family.OPERATIONS``, keyed by its operation ID."""
    registry = fx.import_api_module(name=REGISTRY)
    return {record.operation_id: record for record in family.OPERATIONS if isinstance(record, registry.RestOperation)}


def differences(*, declared: Mapping[str, Any], expected: Mapping[str, Any]) -> List[str]:
    """One line per ID whose value in ``declared`` is not its value in ``expected``, absent counted as a value."""
    return [
        f"{json.dumps(obj=operation_id)}: declared {declared.get(operation_id)!r}, "
        f"the section documents {expected.get(operation_id)!r}"
        for operation_id in sorted(set(declared) | set(expected))
        if declared.get(operation_id) != expected.get(operation_id)
    ]


def test_only_the_upload_is_pending() -> None:
    """AC-1: ``PENDING`` is exactly ``{"repos/upload-release-asset"}`` (DL-002), and ``OPERATIONS`` holds one record of
    every other ``repos/`` ID of the reference, none twice and none of another ID."""
    family = repos_family()
    counts = Counter(record.operation_id for record in family.OPERATIONS)
    problems = []
    pending = frozenset(family.PENDING)
    if pending != frozenset({UPLOAD_RELEASE_ASSET}):
        problems.append(f"PENDING holds {len(pending)} IDs, not only {UPLOAD_RELEASE_ASSET}: {sorted(pending)}")
    missing = sorted(RECORDED_IDS - set(counts))
    if missing:
        problems.append(f"{len(missing)} IDs have no record: {missing}")
    extra = sorted(set(counts) - RECORDED_IDS)
    if extra:
        problems.append(f"records of IDs that are not to be recorded: {extra}")
    twice = sorted(operation_id for operation_id, count in counts.items() if count > 1)
    if twice:
        problems.append(f"IDs with more than one record: {twice}")

    assert not problems, "\n".join(problems)


def test_every_record_sends_the_default_version_and_media_type() -> None:
    """AC-3: every ``repos/`` ID but the pending one has a record, and each declares ``API_VERSION_DEFAULT`` and
    ``ACCEPT_JSON``, so ``call`` sends them."""
    transport = fx.import_api_module(name=TRANSPORT)
    records = records_by_id(family=repos_family())
    problems = []
    for operation_id in sorted(RECORDED_IDS):
        record = records.get(operation_id)
        if record is None:
            problems.append(f"{json.dumps(obj=operation_id)}: no record")
            continue
        if record.api_version != transport.API_VERSION_DEFAULT:
            problems.append(f"{json.dumps(obj=operation_id)}: api_version {record.api_version!r}")
        if record.accept != transport.ACCEPT_JSON:
            problems.append(f"{json.dumps(obj=operation_id)}: accept {record.accept!r}")

    assert not problems, f"{len(problems)} problems:\n" + "\n".join(problems)


def test_the_multi_segment_parameters_are_the_sections() -> None:
    """AC-3: ``{operation_id: multi_segment}`` over the records with a multi-segment parameter is
    ``MULTI_SEGMENT_PARAMETERS``, the parameters whose row reads "may contain `/` (multi-segment path)"."""
    records = records_by_id(family=repos_family())
    declared = {
        operation_id: frozenset(record.multi_segment)
        for operation_id, record in records.items()
        if record.multi_segment
    }

    problems = differences(declared=declared, expected=MULTI_SEGMENT_PARAMETERS)

    assert not problems, f"{len(problems)} records differ from their sections:\n" + "\n".join(problems)


def test_every_list_record_has_a_case() -> None:
    """AC-4: the family's ``Paging.LINK`` records are exactly the sections of ``LIST_RECORDS``, so every other record,
    ``repos/get-commit`` and ``repos/compare-commits`` included, is ``Paging.NONE``."""
    registry = fx.import_api_module(name=REGISTRY)
    records = records_by_id(family=repos_family())
    paged = {operation_id for operation_id, record in records.items() if record.paging == registry.Paging.LINK}
    cased = {listed.operation_id for listed in LIST_RECORDS}

    assert paged == cased, (
        f"Paging.LINK records without a case: {sorted(paged - cased)}; "
        f"cases without a Paging.LINK record: {sorted(cased - paged)}"
    )


@pytest.mark.parametrize(argnames="listed", argvalues=LIST_RECORDS, ids=list_record_name)
def test_a_list_record_prints_every_item(
    listed: ListRecord, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-6 (#28 design D8): ``call <id>`` of a ``Paging.LINK`` record against a fake host serving two items under its
    item key prints both as one JSON array and exits 0, having asked for one page per item where the record documents
    ``per_page``; every request was routed, so a multi-segment value reached its path with its ``/`` (AC-3)."""
    requests = fx.run_product_case(case=list_case(listed=listed), root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    pages = len(LISTED_ITEMS) if listed.per_page else 1
    assert len(requests) == pages, f"{listed.operation_id}: {len(requests)} requests, {pages} pages expected"


@pytest.mark.parametrize(argnames="branch_writing", argvalues=BRANCH_WRITING_CALLS, ids=branch_writing_name)
def test_a_branch_writing_record_is_refused(
    branch_writing: BranchWritingCall,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-7: the record is declared and ``registry.lookup`` returns it, yet its complete ``call`` exits 2 with no
    request, and a log record names the ID and that no subcommand sends it."""
    registry = fx.import_api_module(name=REGISTRY)
    records = records_by_id(family=repos_family())
    assert branch_writing.operation_id in records, f"{branch_writing.operation_id} has no record in {FAMILY_FILE.name}"
    assert registry.lookup(operation_id=branch_writing.operation_id) == records[branch_writing.operation_id]
    case = refusal_case(branch_writing=branch_writing)
    caplog.set_level(level=logging.DEBUG)

    fx.run_product_case(case=case, root=tmp_path, monkeypatch=monkeypatch, capsys=capsys)

    fx.assert_log(case=case, records=caplog.records, stderr=STDERR_READ_BY_THE_RUN)
