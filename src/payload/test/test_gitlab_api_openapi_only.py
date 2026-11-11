"""Tests for ``gitlab_api/families/openapi_only.py``: the records of the operations only GitLab's OpenAPI file names,
and the path forms and uploads they declare (issue #40, design.md D4 and D6; AC-1.1, AC-1.3 to AC-1.6, AC-2.1 to
AC-2.3, AC-2.5, AC-2.6, AC-3.1, AC-3.2, AC-3.4 and UB-2), and the request header of the NuGet symbol file downloads
(issue #63, design.md D5, D8 and D9; AC-1.2, AC-6.2 and AC-8.3).

What is pinned:

- nothing is pending, and the records' operation IDs are the References of the index rows that link
  ``rest/openapi-only.md``, but the three ``ml_models`` file anchors, whose keys are ``deploy``'s (AC-1.1, AC-1.6);
- every ``Param`` is typed as its row: the ``Kind`` of its Type, ``required`` where Required reads ``yes``, the
  ``header`` row ``Symbolchecksum`` of both NuGet symbol file downloads included (#63 D8); the three raw-body records
  declare ``application/octet-stream`` and send every ``Param`` in the query; every record has a JSON body and no
  ``fixed`` pairs (AC-1.3, AC-3.2);
- each NuGet symbol file download, called with ``--header Symbolchecksum=SHA256:ab``, sends that header at that value
  beside the configured credential (#63 AC-6.2, AC-8.3);
- no ``Param`` names a path parameter, though a ``query``, ``body`` or ``form`` row may name a ``*name`` glob (AC-1.4);
- the eight ``GET`` records whose section has the ``page`` and ``per_page`` query rows are ``Paging.OFFSET`` and declare
  both rows, every other record is ``Paging.NONE`` (AC-1.5); each, called against two pages, the second asked for by
  ``x-next-page``, prints the items of both as one JSON array (AC-3.4);
- each path form, called through the product's ``main(argv=["call", ...])``, is sent as its route declares: a glob
  holding ``/``, an optional group given and left out, the NuGet escaped parentheses and ``$metadata`` (AC-2.1, AC-2.3,
  AC-2.5, AC-2.6, AC-3.1); a glob part that is no path segment sends nothing and exits 1 (AC-2.2);
- the job-artifacts upload sends the ``--file`` as its multipart part, and each raw upload sends the ``--input`` bytes,
  ``\\r\\n`` and ``\\xff`` included, unchanged as its body (AC-3.2);
- a runner's ``token`` attribute is the value given, and the configured token travels only in its header (UB-2).

Every expected ID, ``Kind``, required name, paged ID, media type, URL and body is a literal table transcribed from
``docs/api-reference/gitlab/operations-index.md`` and ``rest/openapi-only.md``, never read from the records. The names
and ``In`` of every ``Param``, and one call of every record, are proven by ``test/test_gitlab_wrapper_contract.py``.

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` so ``gitlab_api`` imports absolutely; the
family module is imported inside each test. The fake GitLab host and the socket guard (``gitlab_wrapper_fixtures.py``,
loaded by path) are installed for every test.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_openapi_only.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import logging
import sys
from email.message import Message
from pathlib import Path
from types import ModuleType
from typing import AbstractSet, Any, Dict, FrozenSet, List, Mapping, NamedTuple, Optional, Sequence, Tuple

import pytest

TEST_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
PACKAGE = "gitlab_api"
PACKAGE_DIR = SCRIPTS_DIR / PACKAGE
FIXTURES_FILE = TEST_DIR / "gitlab_wrapper_fixtures.py"
FIXTURES_MODULE = "gitlab_wrapper_fixtures"
WRAPPER_MODULE = "gitlab_wrapper_openapi_only_under_test"
MODULE_SUFFIX = ".py"
MODULE_SEPARATOR = "."
FAMILY_MODULE = "families.openapi_only"
REGISTRY = "registry"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def load_fixtures() -> ModuleType:
    """The fake host module, loaded by path once per process (it is neither a test module nor a package member)."""
    loaded = sys.modules.get(FIXTURES_MODULE)
    if loaded is not None:
        return loaded
    spec = importlib.util.spec_from_file_location(name=FIXTURES_MODULE, location=FIXTURES_FILE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec=spec)
    sys.modules[FIXTURES_MODULE] = module
    spec.loader.exec_module(module=module)
    return module


fixtures = load_fixtures()

CALL = "call"
REST_BASE = fixtures.REST_BASE

# The keys of config/gitlab.json (templates/config/gitlab.json.template; #13 design.md D7).
FIELD_HOSTNAME = "hostname"
FIELD_PROJECT_ID = "project_id"
FIELD_TOKEN = "token"  # a config key name, not a secret
TOKEN = "glpat-gitlab-api-openapi-only-test"  # pragma: allowlist secret
PROJECT_ID = 4242

EXIT_OK = 0
EXIT_API_ERROR = 1
STATUS_CREATED = 201
TEXT_ENCODING = "utf-8"
ASCII_ENCODING = "ascii"
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_CONTENT_DISPOSITION = "Content-Disposition"
HEADER_NEXT_PAGE = "x-next-page"
# The header a `private` token (the default token_type) travels in (conventions.md "Credential types").
HEADER_PRIVATE_TOKEN = "PRIVATE-TOKEN"
HEADER_SEPARATOR = ":"
CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_MULTIPART = "multipart/form-data"
CONTENT_TYPE_OCTET_STREAM = "application/octet-stream"
# RFC 7578 / RFC 2046 section 5.1.1: the boundary parameter, a part's name and filename, the delimiter's dashes.
PARAM_BOUNDARY = "boundary"
PARAM_NAME = "name"
PARAM_FILENAME = "filename"
CRLF = b"\r\n"
DASHES = b"--"
# The `print_json` form (commands/_common.py): JSON indented by 2, then a line end.
JSON_INDENT = 2
LINE_END = "\n"

METHOD_GET = "GET"
METHOD_PUT = "PUT"
METHOD_POST = "POST"
# The options of `call` (#41 design.md D2); `id` defaults to the configured project on a `/projects/:id` path only.
OPTION_PATH = "--path"
OPTION_QUERY = "--query"
OPTION_RAW_FIELD = "-f"
OPTION_FILE = "--file"
ASSIGNED = "="
ID_SEPARATOR = "#"
# Transport.pages: OFFSET adds `per_page=MAX_PER_PAGE` to the first request, and the next page's request sets `page` to
# the `x-next-page` value (#13 AC-2.5).
FIRST_PAGE_QUERY = "?per_page=100"
NEXT_PAGE = "2"
SECOND_PAGE_QUERY = f"?per_page=100&page={NEXT_PAGE}"
LAST_PAGE = ""
# The offset paging rows a paged record declares (conventions.md "Offset-based").
PAGING_ROWS: Tuple[str, ...] = ("page", "per_page")

# The `registry.Kind`, `registry.Paging` and `registry.Location` member names the tables hold.
KIND_ARRAY = "ARRAY"
KIND_HASH = "HASH"
KIND_ARRAY_OF_HASHES = "ARRAY_OF_HASHES"
KIND_FILE = "FILE"
PAGING_OFFSET = "OFFSET"
LOCATION_QUERY = "QUERY"

# --- The tables, transcribed from the reference -----------------------------------------------------------------

# The Reference of every row of operations-index.md that links rest/openapi-only.md, written `openapi-only#<anchor>`,
# in index order (sorted by path), but the three `ml_models` file anchors (`download-an-ml_model-package-file`,
# `workhorse-upload-model-package-file`, `workhorse-authorize-model-package-file`), whose keys `deploy` declares
# (AC-1.2). Each Reference carries one row.
OPERATION_IDS: Tuple[str, ...] = (
    "openapi-only#restart-a-batched-background-operation",
    "openapi-only#stop-a-batched-background-operation",
    "openapi-only#retrieve-a-batched-background-operation",
    "openapi-only#get-the-list-of-batched-background-operations",
    "openapi-only#getapiv4admindatabasesdatabasenamedictionarytablestablename",
    "openapi-only#receives-notifications-from-the-container-registry-when-an-operation-occurs",
    "openapi-only#list-dictionary-tables",
    "openapi-only#getapiv4featureflagsunleashprojectidclientfeatures",
    "openapi-only#postapiv4featureflagsunleashprojectidclientmetrics",
    "openapi-only#postapiv4featureflagsunleashprojectidclientregister",
    "openapi-only#get-a-list-of-features-v2-client-support",
    "openapi-only#getapiv4featureflagsunleashprojectid",
    "openapi-only#internal-endpoint-that-reports-persistent-verification-failures-to-the-primary",
    "openapi-only#query-the-graphql-endpoint-of-an-existing-geo-node",
    "openapi-only#internal-endpoint-that-returns-git-received-pack-output-for-git-push",
    "openapi-only#internal-endpoint-that-returns-info-refs-upload-pack-for-clone-or-pull-operations",
    "openapi-only#internal-endpoint-that-posts-git-receive-pack-for-git-push",
    "openapi-only#internal-endpoint-that-posts-git-upload-pack-for-clone-or-pull-operations",
    "openapi-only#determine-if-a-geo-site-should-proxy-requests",
    "openapi-only#used-by-secondary-runners-to-verify-the-secondary-instance-has-the-very-latest-version",
    "openapi-only#internal-endpoint-that-returns-a-replicable-file",
    "openapi-only#internal-endpoint-that-posts-the-current-node-status",
    "openapi-only#composer-packages-endpoint-at-group-level-for-package-versions-metadata",
    "openapi-only#the-binary-files-index",
    "openapi-only#the-binary-files-index-by-hash",
    "openapi-only#the-installer-udeb-binary-files-index",
    "openapi-only#the-installer-udeb-binary-files-index-by-hash",
    "openapi-only#the-source-files-index",
    "openapi-only#the-source-files-index-by-hash",
    "openapi-only#the-signed-release-file",
    "openapi-only#the-release-file-signature",
    "openapi-only#the-unsigned-release-file",
    "openapi-only#download-debian-package",
    "openapi-only#npm-registry-metadata-endpoint",
    "openapi-only#npm-registry-bulk-advisory-endpoint",
    "openapi-only#npm-registry-quick-audit-endpoint",
    "openapi-only#create-or-update-the-given-tag-for-the-given-npm-package-and-version",
    "openapi-only#deletes-the-given-tag",
    "openapi-only#get-all-tags-for-a-given-an-npm-package",
    "openapi-only#the-nuget-v3-feed-service-index",
    "openapi-only#the-nuget-metadata-service---package-name-and-version-level",
    "openapi-only#the-nuget-metadata-service---package-name-level",
    "openapi-only#the-nuget-search-service",
    "openapi-only#the-nuget-symbol-file-download-endpoint",
    "openapi-only#the-nuget-v2-feed-package-metadata-endpoint",
    "openapi-only#the-nuget-v2-feed-service-index",
    "openapi-only#rotate-a-group-access-token",
    "openapi-only#retrieve-an-emoji-reaction-from-an-epic",
    "openapi-only#delete-an-emoji-reaction-from-an-epic",
    "openapi-only#list-all-emoji-reactions-for-an-epic",
    "openapi-only#add-an-emoji-reaction-to-an-epic",
    "openapi-only#retrieve-an-emoji-reaction-from-an-epic-comment",
    "openapi-only#delete-an-emoji-reaction-from-an-epic-comment",
    "openapi-only#list-all-emoji-reactions-for-an-epic-comment",
    "openapi-only#add-an-emoji-reaction-to-an-epic-comment",
    "openapi-only#retrieve-integration-settings",
    "openapi-only#disable-an-integration",
    "openapi-only#create-or-update-the-apple-app-store-integration",
    "openapi-only#create-or-update-the-google-play-integration",
    "openapi-only#create-or-update-the-jenkins-integration",
    "openapi-only#create-or-update-the-mock-monitoring-integration",
    "openapi-only#create-or-update-the-zentao-integration",
    "openapi-only#workhorse-authorization-for-the-reassignment-csv-file",
    "openapi-only#postapiv4groupsidtransfertoorganization",
    "openapi-only#workhorse-authorize-the-file-upload",
    "openapi-only#workhorse-authorize-the-group-import-upload",
    "openapi-only#update-a-custom-header",
    "openapi-only#delete-a-custom-header",
    "openapi-only#subscribe-a-namespace-to-a-jiraconnectinstallation",
    "openapi-only#register-the-gitlab-for-jira-forge-system-token-for-direct-dev-info-sync",
    "openapi-only#update-the-gitlab-for-jira-forge-installation-instance-url",
    "openapi-only#delete-a-gitlab-for-jira-forge-namespace-subscription",
    "openapi-only#list-gitlab-for-jira-forge-namespace-subscriptions",
    "openapi-only#create-a-gitlab-for-jira-forge-namespace-subscription",
    "openapi-only#postapiv4integrationsslackevents",
    "openapi-only#process-slack-interaction-events",
    "openapi-only#get-slack-interactive-component-options",
    "openapi-only#authorize-artifacts-upload",
    "openapi-only#download-job-artifacts",
    "openapi-only#upload-job-artifacts",
    "openapi-only#get-the-runtime-environment-key-for-a-job",
    "openapi-only#patchapiv4jobsidtrace",
    "openapi-only#putapiv4jobsid",
    "openapi-only#request-a-job",
    "openapi-only#retrieve-namespace-subscription",
    "openapi-only#creates-a-storage-limit-exclusion-for-a-namespace",
    "openapi-only#removes-a-storage-limit-exclusion-for-a-namespace",
    "openapi-only#update-a-namespace",
    "openapi-only#retrieve-all-limit-exclusions",
    "openapi-only#get-offline-transfer-export-details",
    "openapi-only#list-all-offline-transfer-exports",
    "openapi-only#start-a-new-offline-transfer-export",
    "openapi-only#start-a-new-offline-transfer-import",
    "openapi-only#soft-delete-an-organization",
    "openapi-only#workhorse-authorize-the-conan-recipe-file",
    "openapi-only#workhorse-authorize-the-conan-package-file",
    "openapi-only#npm-registry-metadata-endpoint-1",
    "openapi-only#npm-registry-bulk-advisory-endpoint-1",
    "openapi-only#npm-registry-quick-audit-endpoint-1",
    "openapi-only#create-or-update-the-given-tag-for-the-given-npm-package-and-version-1",
    "openapi-only#deletes-the-given-tag-1",
    "openapi-only#get-all-tags-for-a-given-an-npm-package-1",
    "openapi-only#get-details-about-specific-version-of-a-module",
    "openapi-only#rotate-a-personal-access-token",
    "openapi-only#retrieve-a-personal-access-token",
    "openapi-only#revoke-a-personal-access-token",
    "openapi-only#rotate-a-project-access-token",
    "openapi-only#postapiv4projectsidalertmanagementalertsalertiidmetricimagesauthorize",
    "openapi-only#publish-a-new-component-project-release-as-version-to-the-cicd-catalog",
    "openapi-only#create-a-ci-configuration-merge-request",
    "openapi-only#import-a-project-from-a-git-url",
    "openapi-only#retrieve-integration-settings-1",
    "openapi-only#disable-an-integration-1",
    "openapi-only#create-or-update-the-apple-app-store-integration-1",
    "openapi-only#trigger-a-slash-command-for-mattermost-slash-commands",
    "openapi-only#create-or-update-the-mock-monitoring-integration-1",
    "openapi-only#create-or-update-the-zentao-integration-1",
    "openapi-only#authorize-metric-image-upload",
    "openapi-only#change-approval-related-configuration",
    "openapi-only#retrieve-an-emoji-reaction-from-a-merge-request-comment",
    "openapi-only#delete-an-emoji-reaction-from-a-merge-request-comment",
    "openapi-only#list-all-emoji-reactions-for-a-merge-request-comment",
    "openapi-only#add-an-emoji-reaction-to-a-merge-request-comment",
    "openapi-only#download-a-package-file",
    "openapi-only#get-the-sparse-index-for-a-cargo-crate-1-character-name",
    "openapi-only#get-the-sparse-index-for-a-cargo-crate-2-character-name",
    "openapi-only#get-the-sparse-index-for-a-cargo-crate-3-character-name",
    "openapi-only#download-a-cargo-crate",
    "openapi-only#get-the-sparse-index-for-a-cargo-crate-4-character-name",
    "openapi-only#get-configjson",
    "openapi-only#retrieve-a-recipe-snapshot",
    "openapi-only#workhorse-authorize-the-conan-recipe-file-1",
    "openapi-only#workhorse-authorize-the-conan-package-file-1",
    "openapi-only#workhorse-authorize-the-conan-recipe-file-2",
    "openapi-only#workhorse-authorize-the-conan-package-file-2",
    "openapi-only#list-all-package-files",
    "openapi-only#delete-recipe-revision",
    "openapi-only#authorize-debian-package-upload",
    "openapi-only#the-binary-files-index-1",
    "openapi-only#the-binary-files-index-by-hash-1",
    "openapi-only#the-installer-udeb-binary-files-index-1",
    "openapi-only#the-installer-udeb-binary-files-index-by-hash-1",
    "openapi-only#the-source-files-index-1",
    "openapi-only#the-source-files-index-by-hash-1",
    "openapi-only#the-signed-release-file-1",
    "openapi-only#the-release-file-signature-1",
    "openapi-only#the-unsigned-release-file-1",
    "openapi-only#workhorse-authorize-generic-package-file",
    "openapi-only#download-package-file",
    "openapi-only#upload-package-file",
    "openapi-only#authorize-a-chart-upload-from-workhorse",
    "openapi-only#workhorse-authorize-the-maven-package-file-upload",
    "openapi-only#npm-registry-metadata-endpoint-2",
    "openapi-only#npm-registry-bulk-advisory-endpoint-2",
    "openapi-only#npm-registry-quick-audit-endpoint-2",
    "openapi-only#create-or-update-the-given-tag-for-the-given-npm-package-and-version-2",
    "openapi-only#deletes-the-given-tag-2",
    "openapi-only#get-all-tags-for-a-given-an-npm-package-2",
    "openapi-only#the-nuget-package-authorize-endpoint",
    "openapi-only#the-nuget-v3-feed-service-index-1",
    "openapi-only#the-nuget-metadata-service---package-name-and-version-level-1",
    "openapi-only#the-nuget-metadata-service---package-name-level-1",
    "openapi-only#the-nuget-search-service-1",
    "openapi-only#the-nuget-symbol-file-download-endpoint-1",
    "openapi-only#the-nuget-symbol-package-authorize-endpoint",
    "openapi-only#the-nuget-v2-feed-package-metadata-endpoint-1",
    "openapi-only#the-nuget-v2-feed-package-authorize-endpoint",
    "openapi-only#the-nuget-v2-feed-service-index-1",
    "openapi-only#authorize-the-pypi-package-upload-from-workhorse",
    "openapi-only#download-rpm-package-files",
    "openapi-only#authorize-package-upload-from-workhorse",
    "openapi-only#download-repository-metadata-files",
    "openapi-only#upload-a-rpm-package",
    "openapi-only#authorize-a-gem-upload-from-workhorse",
    "openapi-only#workhorse-authorize-terraform-module-package-file",
    "openapi-only#upload-terraform-module-package-file",
    "openapi-only#download-the-latest-version-of-a-module",
    "openapi-only#getapiv4projectsidpagesaccess",
    "openapi-only#list-all-bridge-jobs-by-pipeline",
    "openapi-only#retrieve-file-archive-from-a-repository",
    "openapi-only#putapiv4projectsidrepositorybranchesbranchprotect",
    "openapi-only#putapiv4projectsidrepositorybranchesbranchunprotect",
    "openapi-only#headapiv4projectsidrepositorybranchesbranch",
    "openapi-only#start-a-task-to-recalculate-repository-size-for-a-project",
    "openapi-only#retrieve-integration-settings-2",
    "openapi-only#disable-an-integration-2",
    "openapi-only#create-or-update-the-apple-app-store-integration-2",
    "openapi-only#create-or-update-the-asana-integration",
    "openapi-only#create-or-update-the-assembla-integration",
    "openapi-only#create-or-update-the-bamboo-integration",
    "openapi-only#create-or-update-the-bugzilla-integration",
    "openapi-only#create-or-update-the-buildkite-integration",
    "openapi-only#create-or-update-the-campfire-integration",
    "openapi-only#create-or-update-the-clickup-integration",
    "openapi-only#create-or-update-the-confluence-integration",
    "openapi-only#create-or-update-the-custom-issue-tracker-integration",
    "openapi-only#create-or-update-the-datadog-integration",
    "openapi-only#create-or-update-the-diffblue-cover-integration",
    "openapi-only#create-or-update-the-discord-integration",
    "openapi-only#create-or-update-the-drone-ci-integration",
    "openapi-only#create-or-update-the-emails-on-push-integration",
    "openapi-only#create-or-update-the-ewm-integration",
    "openapi-only#create-or-update-the-external-wiki-integration",
    "openapi-only#create-or-update-the-git-guardian-integration",
    "openapi-only#create-or-update-the-github-integration",
    "openapi-only#create-or-update-the-gitlab-slack-application-integration",
    "openapi-only#create-or-update-the-google-cloud-platform-artifact-registry-integration",
    "openapi-only#create-or-update-the-google-cloud-platform-workload-identity-federation-integration",
    "openapi-only#create-or-update-the-google-play-integration-1",
    "openapi-only#create-or-update-the-hangouts-chat-integration",
    "openapi-only#create-or-update-the-harbor-integration",
    "openapi-only#create-or-update-the-irker-integration",
    "openapi-only#create-or-update-the-jenkins-integration-1",
    "openapi-only#create-or-update-the-jira-cloud-app-integration",
    "openapi-only#create-or-update-the-jira-integration",
    "openapi-only#create-or-update-the-linear-integration",
    "openapi-only#create-or-update-the-matrix-integration",
    "openapi-only#create-or-update-the-mattermost-slash-commands-integration",
    "openapi-only#trigger-a-slash-command-for-mattermost-slash-commands-1",
    "openapi-only#create-or-update-the-mattermost-integration",
    "openapi-only#create-or-update-the-microsoft-teams-integration",
    "openapi-only#create-or-update-the-mock-ci-integration",
    "openapi-only#create-or-update-the-mock-monitoring-integration-2",
    "openapi-only#create-or-update-the-packagist-integration",
    "openapi-only#create-or-update-the-phorge-integration",
    "openapi-only#create-or-update-the-pipelines-email-integration",
    "openapi-only#create-or-update-the-pivotaltracker-integration",
    "openapi-only#create-or-update-the-pumble-integration",
    "openapi-only#create-or-update-the-pushover-integration",
    "openapi-only#create-or-update-the-redmine-integration",
    "openapi-only#create-or-update-the-slack-integration",
    "openapi-only#create-or-update-the-squash-tm-integration",
    "openapi-only#create-or-update-the-teamcity-integration",
    "openapi-only#create-or-update-the-telegram-integration",
    "openapi-only#create-or-update-the-unify-circuit-integration",
    "openapi-only#create-or-update-the-webex-teams-integration",
    "openapi-only#create-or-update-the-youtrack-integration",
    "openapi-only#create-or-update-the-zentao-integration-2",
    "openapi-only#list-all-active-integrations",
    "openapi-only#retrieve-an-emoji-reaction-from-a-snippet-comment",
    "openapi-only#delete-an-emoji-reaction-from-a-snippet-comment",
    "openapi-only#list-all-emoji-reactions-for-a-snippet-comment",
    "openapi-only#add-an-emoji-reaction-to-a-snippet-comment",
    "openapi-only#authorize-terraform-state-upload",
    "openapi-only#lock-a-terraform-state",
    "openapi-only#unlock-a-terraform-state",
    "openapi-only#retrieve-a-terraform-state-version",
    "openapi-only#delete-a-terraform-state-version",
    "openapi-only#retrieve-a-terraform-state",
    "openapi-only#create-or-update-a-terraform-state",
    "openapi-only#delete-a-terraform-state",
    "openapi-only#update-a-terraform-state-protection-rule-for-a-project",
    "openapi-only#delete-a-terraform-state-protection-rule",
    "openapi-only#list-all-terraform-state-protection-rules-for-a-project",
    "openapi-only#create-a-terraform-state-protection-rule-for-a-project",
    "openapi-only#workhorse-authorize-the-file-upload-1",
    "openapi-only#the-nuget-v2-feed-find-packages-by-id-endpoint",
    "openapi-only#the-nuget-v2-feed-single-package-metadata-endpoint",
    "openapi-only#the-nuget-v2-feed-enumerate-packages-endpoint",
    "openapi-only#authorize-project-relation-import",
    "openapi-only#workhorse-authorize-the-project-import-upload",
    "openapi-only#list-runners-projects",
    "openapi-only#internal-endpoint-that-deletes-a-runner-manager-by-authentication-token-and-system-id",
    "openapi-only#trigger-a-global-slack-command",
    "openapi-only#track-usage-data-event",
    "openapi-only#postapiv4usagedataincrementuniqueusers",
    "openapi-only#track-multiple-internal-gitlab-events",
)

# The records AC-2.6 and AC-3.2 call, and UB-2's runner record.
OP_MAVEN_AUTHORIZE = "openapi-only#workhorse-authorize-the-maven-package-file-upload"
OP_DOWNLOAD_PACKAGE_FILE = "openapi-only#download-package-file"
OP_UPLOAD_PACKAGE_FILE = "openapi-only#upload-package-file"
OP_NUGET_SINGLE_PACKAGE = "openapi-only#the-nuget-v2-feed-single-package-metadata-endpoint"
OP_NUGET_ENUMERATE = "openapi-only#the-nuget-v2-feed-enumerate-packages-endpoint"
OP_NUGET_FIND_BY_ID = "openapi-only#the-nuget-v2-feed-find-packages-by-id-endpoint"
OP_NUGET_METADATA = "openapi-only#the-nuget-v2-feed-package-metadata-endpoint-1"
OP_UPLOAD_JOB_ARTIFACTS = "openapi-only#upload-job-artifacts"
OP_UPLOAD_TERRAFORM_MODULE = "openapi-only#upload-terraform-module-package-file"
OP_TERRAFORM_STATE = "openapi-only#create-or-update-a-terraform-state"
OP_REQUEST_A_JOB = "openapi-only#request-a-job"

# Every `Param` whose Kind is not SCALAR, by record: the `query`, `body` and `form` rows typed `array of string`
# (ARRAY), `object` (HASH), `array of object` (ARRAY_OF_HASHES) and `file` (FILE), but a raw-body record's `file` row,
# which is its body (design.md D4). Every other row's Type is `string`, `string (date)`, `integer (int32)` or `boolean`,
# a SCALAR.
KINDS: Dict[str, Dict[str, str]] = {
    "openapi-only#internal-endpoint-that-reports-persistent-verification-failures-to-the-primary": {
        "failures": KIND_ARRAY_OF_HASHES
    },
    "openapi-only#internal-endpoint-that-returns-git-received-pack-output-for-git-push": {"data": KIND_HASH},
    "openapi-only#internal-endpoint-that-returns-info-refs-upload-pack-for-clone-or-pull-operations": {
        "data": KIND_HASH
    },
    "openapi-only#internal-endpoint-that-posts-git-receive-pack-for-git-push": {"data": KIND_HASH},
    "openapi-only#internal-endpoint-that-posts-git-upload-pack-for-clone-or-pull-operations": {"data": KIND_HASH},
    "openapi-only#internal-endpoint-that-posts-the-current-node-status": {"data": KIND_HASH},
    "openapi-only#postapiv4integrationsslackevents": {"event": KIND_HASH, "authed_users": KIND_ARRAY},
    "openapi-only#upload-job-artifacts": {"file": KIND_FILE, "metadata": KIND_FILE},
    "openapi-only#putapiv4jobsid": {"output": KIND_HASH},
    "openapi-only#request-a-job": {"info": KIND_HASH, "session": KIND_HASH},
    "openapi-only#update-a-namespace": {"gitlab_subscription_attributes": KIND_HASH},
    "openapi-only#start-a-new-offline-transfer-export": {
        "aws_s3_configuration": KIND_HASH,
        "s3_compatible_configuration": KIND_HASH,
        "gcs_configuration": KIND_HASH,
        "gcs_hmac_configuration": KIND_HASH,
        "gcs_adc_configuration": KIND_HASH,
        "entities": KIND_ARRAY_OF_HASHES,
    },
    "openapi-only#start-a-new-offline-transfer-import": {
        "aws_s3_configuration": KIND_HASH,
        "s3_compatible_configuration": KIND_HASH,
        "gcs_configuration": KIND_HASH,
        "gcs_hmac_configuration": KIND_HASH,
        "gcs_adc_configuration": KIND_HASH,
        "entities": KIND_ARRAY_OF_HASHES,
    },
    "openapi-only#publish-a-new-component-project-release-as-version-to-the-cicd-catalog": {"metadata": KIND_HASH},
    "openapi-only#retrieve-file-archive-from-a-repository": {"exclude_paths": KIND_ARRAY},
    "openapi-only#create-or-update-the-jira-integration": {"project_keys": KIND_ARRAY},
    "openapi-only#track-multiple-internal-gitlab-events": {"events": KIND_ARRAY_OF_HASHES},
}

# The `query`, `body`, `form` and `header` rows whose Required reads `yes`, by record, in table order. A record with
# none is not listed. A `header` row is a `Location.HEADER` `Param` (issue #63, design.md D5 and D8): the NuGet symbol
# file downloads' `Symbolchecksum`. No `Param`, so never required (design.md D4): a `path` row; a row naming a `*name`
# glob of the record's path (the Debian `distribution`, the NPM `package_name`, the generic `package_version`, the
# NuGet `file_name`, ...); a raw-body record's `file` row.
REQUIRED: Dict[str, Tuple[str, ...]] = {
    "openapi-only#internal-endpoint-that-reports-persistent-verification-failures-to-the-primary": (
        "geo_node_id",
        "failures",
    ),
    "openapi-only#internal-endpoint-that-returns-git-received-pack-output-for-git-push": ("secret_token", "data"),
    "openapi-only#internal-endpoint-that-returns-info-refs-upload-pack-for-clone-or-pull-operations": (
        "secret_token",
        "data",
    ),
    "openapi-only#internal-endpoint-that-posts-git-receive-pack-for-git-push": ("secret_token", "data", "output"),
    "openapi-only#internal-endpoint-that-posts-git-upload-pack-for-clone-or-pull-operations": (
        "secret_token",
        "data",
        "output",
    ),
    "openapi-only#the-nuget-symbol-file-download-endpoint": ("Symbolchecksum",),
    "openapi-only#add-an-emoji-reaction-to-an-epic": ("name",),
    "openapi-only#add-an-emoji-reaction-to-an-epic-comment": ("name",),
    "openapi-only#create-or-update-the-apple-app-store-integration": (
        "app_store_issuer_id",
        "app_store_key_id",
        "app_store_private_key_file_name",
        "app_store_private_key",
    ),
    "openapi-only#create-or-update-the-google-play-integration": (
        "package_name",
        "service_account_key_file_name",
        "service_account_key",
    ),
    "openapi-only#create-or-update-the-jenkins-integration": ("jenkins_url", "project_name"),
    "openapi-only#create-or-update-the-zentao-integration": ("url", "api_token", "zentao_product_xid"),
    "openapi-only#postapiv4groupsidtransfertoorganization": ("organization_id",),
    "openapi-only#update-a-custom-header": ("value",),
    "openapi-only#subscribe-a-namespace-to-a-jiraconnectinstallation": ("jwt", "namespace_path"),
    "openapi-only#create-a-gitlab-for-jira-forge-namespace-subscription": ("namespace_path",),
    "openapi-only#upload-job-artifacts": ("file",),
    "openapi-only#putapiv4jobsid": ("token",),
    "openapi-only#request-a-job": ("token",),
    "openapi-only#creates-a-storage-limit-exclusion-for-a-namespace": ("reason",),
    "openapi-only#start-a-new-offline-transfer-export": ("bucket", "entities"),
    "openapi-only#start-a-new-offline-transfer-import": ("bucket", "export_prefix", "entities"),
    "openapi-only#publish-a-new-component-project-release-as-version-to-the-cicd-catalog": ("version", "metadata"),
    "openapi-only#import-a-project-from-a-git-url": ("import_url",),
    "openapi-only#create-or-update-the-apple-app-store-integration-1": (
        "app_store_issuer_id",
        "app_store_key_id",
        "app_store_private_key_file_name",
        "app_store_private_key",
    ),
    "openapi-only#trigger-a-slash-command-for-mattermost-slash-commands": ("token",),
    "openapi-only#create-or-update-the-zentao-integration-1": ("url", "api_token", "zentao_product_xid"),
    "openapi-only#change-approval-related-configuration": ("approvals_required",),
    "openapi-only#add-an-emoji-reaction-to-a-merge-request-comment": ("name",),
    "openapi-only#authorize-debian-package-upload": ("component",),
    "openapi-only#the-nuget-symbol-file-download-endpoint-1": ("Symbolchecksum",),
    "openapi-only#create-or-update-the-apple-app-store-integration-2": (
        "app_store_issuer_id",
        "app_store_key_id",
        "app_store_private_key_file_name",
        "app_store_private_key",
    ),
    "openapi-only#create-or-update-the-asana-integration": ("api_key",),
    "openapi-only#create-or-update-the-assembla-integration": ("token",),
    "openapi-only#create-or-update-the-bamboo-integration": ("bamboo_url", "build_key", "username", "password"),
    "openapi-only#create-or-update-the-bugzilla-integration": ("project_url", "issues_url", "new_issue_url"),
    "openapi-only#create-or-update-the-buildkite-integration": ("project_url", "token"),
    "openapi-only#create-or-update-the-campfire-integration": ("token",),
    "openapi-only#create-or-update-the-clickup-integration": ("project_url", "issues_url"),
    "openapi-only#create-or-update-the-confluence-integration": ("confluence_url",),
    "openapi-only#create-or-update-the-custom-issue-tracker-integration": (
        "project_url",
        "issues_url",
        "new_issue_url",
    ),
    "openapi-only#create-or-update-the-datadog-integration": ("api_key",),
    "openapi-only#create-or-update-the-diffblue-cover-integration": (
        "diffblue_license_key",
        "diffblue_access_token_name",
        "diffblue_access_token_secret",
    ),
    "openapi-only#create-or-update-the-discord-integration": ("webhook",),
    "openapi-only#create-or-update-the-drone-ci-integration": ("drone_url", "token"),
    "openapi-only#create-or-update-the-emails-on-push-integration": ("recipients",),
    "openapi-only#create-or-update-the-ewm-integration": ("project_url", "issues_url", "new_issue_url"),
    "openapi-only#create-or-update-the-external-wiki-integration": ("external_wiki_url",),
    "openapi-only#create-or-update-the-git-guardian-integration": ("token",),
    "openapi-only#create-or-update-the-github-integration": ("token", "repository_url"),
    "openapi-only#create-or-update-the-google-cloud-platform-artifact-registry-integration": (
        "artifact_registry_project_id",
        "artifact_registry_repositories",
        "artifact_registry_location",
    ),
    "openapi-only#create-or-update-the-google-cloud-platform-workload-identity-federation-integration": (
        "workload_identity_federation_project_id",
        "workload_identity_federation_project_number",
        "workload_identity_pool_id",
        "workload_identity_pool_provider_id",
    ),
    "openapi-only#create-or-update-the-google-play-integration-1": (
        "package_name",
        "service_account_key_file_name",
        "service_account_key",
    ),
    "openapi-only#create-or-update-the-hangouts-chat-integration": ("webhook",),
    "openapi-only#create-or-update-the-harbor-integration": ("url", "project_name", "username", "password"),
    "openapi-only#create-or-update-the-irker-integration": ("recipients",),
    "openapi-only#create-or-update-the-jenkins-integration-1": ("jenkins_url", "project_name"),
    "openapi-only#create-or-update-the-jira-integration": ("url", "password"),
    "openapi-only#create-or-update-the-linear-integration": ("workspace_url",),
    "openapi-only#create-or-update-the-matrix-integration": ("token", "room"),
    "openapi-only#create-or-update-the-mattermost-slash-commands-integration": ("token",),
    "openapi-only#trigger-a-slash-command-for-mattermost-slash-commands-1": ("token",),
    "openapi-only#create-or-update-the-mattermost-integration": ("webhook",),
    "openapi-only#create-or-update-the-microsoft-teams-integration": ("webhook",),
    "openapi-only#create-or-update-the-mock-ci-integration": ("mock_service_url",),
    "openapi-only#create-or-update-the-packagist-integration": ("username", "token"),
    "openapi-only#create-or-update-the-phorge-integration": ("project_url", "issues_url"),
    "openapi-only#create-or-update-the-pipelines-email-integration": ("recipients",),
    "openapi-only#create-or-update-the-pivotaltracker-integration": ("token",),
    "openapi-only#create-or-update-the-pumble-integration": ("webhook",),
    "openapi-only#create-or-update-the-pushover-integration": ("api_key", "user_key", "priority"),
    "openapi-only#create-or-update-the-redmine-integration": ("project_url", "issues_url", "new_issue_url"),
    "openapi-only#create-or-update-the-slack-integration": ("webhook",),
    "openapi-only#create-or-update-the-squash-tm-integration": ("url",),
    "openapi-only#create-or-update-the-teamcity-integration": ("teamcity_url", "build_type", "username", "password"),
    "openapi-only#create-or-update-the-telegram-integration": ("token", "room"),
    "openapi-only#create-or-update-the-unify-circuit-integration": ("webhook",),
    "openapi-only#create-or-update-the-webex-teams-integration": ("webhook",),
    "openapi-only#create-or-update-the-youtrack-integration": ("project_url", "issues_url"),
    "openapi-only#create-or-update-the-zentao-integration-2": ("url", "api_token", "zentao_product_xid"),
    "openapi-only#add-an-emoji-reaction-to-a-snippet-comment": ("name",),
    "openapi-only#lock-a-terraform-state": ("ID", "Operation", "Info", "Who", "Version", "Created", "Path"),
    "openapi-only#create-a-terraform-state-protection-rule-for-a-project": (
        "state_name",
        "minimum_access_level_for_write",
    ),
    "openapi-only#the-nuget-v2-feed-find-packages-by-id-endpoint": ("id",),
    "openapi-only#the-nuget-v2-feed-enumerate-packages-endpoint": ("$filter",),
    "openapi-only#internal-endpoint-that-deletes-a-runner-manager-by-authentication-token-and-system-id": (
        "token",
        "system_id",
    ),
    "openapi-only#trigger-a-global-slack-command": ("text",),
    "openapi-only#track-usage-data-event": ("event",),
    "openapi-only#postapiv4usagedataincrementuniqueusers": ("event",),
    "openapi-only#track-multiple-internal-gitlab-events": ("events",),
}

# The raw-body records and the media type of their body (design.md D4 "The uploads", D5): each section has a `file`
# row and its route is Workhorse's `requestBodyUploader`, so the body is the bytes `call --input` gives.
RAW_BODIES: Dict[str, str] = {
    OP_UPLOAD_PACKAGE_FILE: CONTENT_TYPE_OCTET_STREAM,
    OP_UPLOAD_TERRAFORM_MODULE: CONTENT_TYPE_OCTET_STREAM,
    OP_TERRAFORM_STATE: CONTENT_TYPE_OCTET_STREAM,
}

# The `GET` records whose section has the `query` rows `page` and `per_page` (design.md D4 "The paged records").
PAGED_RECORDS: Dict[str, str] = {
    "openapi-only#list-all-emoji-reactions-for-an-epic": PAGING_OFFSET,
    "openapi-only#list-all-emoji-reactions-for-an-epic-comment": PAGING_OFFSET,
    "openapi-only#list-all-emoji-reactions-for-a-merge-request-comment": PAGING_OFFSET,
    "openapi-only#list-all-emoji-reactions-for-a-snippet-comment": PAGING_OFFSET,
    "openapi-only#retrieve-all-limit-exclusions": PAGING_OFFSET,
    "openapi-only#list-all-offline-transfer-exports": PAGING_OFFSET,
    "openapi-only#list-all-bridge-jobs-by-pipeline": PAGING_OFFSET,
    "openapi-only#list-runners-projects": PAGING_OFFSET,
}

# --- The calls ----------------------------------------------------------------------------------------------------

# Response keys of an answer the fake host serves.
FIELD_ID = "id"
FIELD_MESSAGE = "message"
PAGE_ITEMS: Tuple[Dict[str, Any], ...] = ({FIELD_ID: 1}, {FIELD_ID: 2})
ANSWER: Dict[str, Any] = {FIELD_ID: 1}
UPLOAD_ANSWER: Dict[str, Any] = {FIELD_MESSAGE: "201 Created"}


class ListCase(NamedTuple):
    """A call of a paged record and the URL of its list before the query, which each page request extends."""

    argv: Tuple[str, ...]
    url: str


# AC-3.4: every paged record, its path values given (`id` the configured project on a `/projects/:id` path).
LIST_CASES = (
    pytest.param(
        ListCase(
            argv=("openapi-only#list-all-emoji-reactions-for-an-epic", OPTION_PATH, "id=12", OPTION_PATH, "epic_iid=3"),
            url=f"{REST_BASE}/groups/12/epics/3/award_emoji",
        ),
        id="list-all-emoji-reactions-for-an-epic",
    ),
    pytest.param(
        ListCase(
            argv=(
                "openapi-only#list-all-emoji-reactions-for-an-epic-comment",
                OPTION_PATH,
                "id=12",
                OPTION_PATH,
                "epic_iid=3",
                OPTION_PATH,
                "note_id=8",
            ),
            url=f"{REST_BASE}/groups/12/epics/3/notes/8/award_emoji",
        ),
        id="list-all-emoji-reactions-for-an-epic-comment",
    ),
    pytest.param(
        ListCase(
            argv=(
                "openapi-only#list-all-emoji-reactions-for-a-merge-request-comment",
                OPTION_PATH,
                "merge_request_iid=3",
                OPTION_PATH,
                "note_id=8",
            ),
            url=f"{REST_BASE}/projects/{PROJECT_ID}/merge_requests/3/notes/8/award_emoji",
        ),
        id="list-all-emoji-reactions-for-a-merge-request-comment",
    ),
    pytest.param(
        ListCase(
            argv=(
                "openapi-only#list-all-emoji-reactions-for-a-snippet-comment",
                OPTION_PATH,
                "snippet_id=3",
                OPTION_PATH,
                "note_id=8",
            ),
            url=f"{REST_BASE}/projects/{PROJECT_ID}/snippets/3/notes/8/award_emoji",
        ),
        id="list-all-emoji-reactions-for-a-snippet-comment",
    ),
    pytest.param(
        ListCase(
            argv=("openapi-only#retrieve-all-limit-exclusions",),
            url=f"{REST_BASE}/namespaces/storage/limit_exclusions",
        ),
        id="retrieve-all-limit-exclusions",
    ),
    pytest.param(
        ListCase(argv=("openapi-only#list-all-offline-transfer-exports",), url=f"{REST_BASE}/offline_exports"),
        id="list-all-offline-transfer-exports",
    ),
    pytest.param(
        ListCase(
            argv=("openapi-only#list-all-bridge-jobs-by-pipeline", OPTION_PATH, "pipeline_id=9"),
            url=f"{REST_BASE}/projects/{PROJECT_ID}/pipelines/9/bridges",
        ),
        id="list-all-bridge-jobs-by-pipeline",
    ),
    pytest.param(
        ListCase(
            argv=("openapi-only#list-runners-projects", OPTION_PATH, "id=6"), url=f"{REST_BASE}/runners/6/projects"
        ),
        id="list-runners-projects",
    ),
)


class SentCase(NamedTuple):
    """A call and the one request it sends: its method and URL, the query included."""

    argv: Tuple[str, ...]
    method: str
    url: str


# AC-2.6 (design.md Correctness Properties, its table): one call per path form. A value with no `/`, space or reserved
# character is sent as written; `a/rc 1` keeps its `/` and has its space encoded; `$filter` is `%24filter` in the query.
GENERIC_PACKAGE_ARGV: Tuple[str, ...] = (
    OP_DOWNLOAD_PACKAGE_FILE,
    OPTION_PATH,
    "package_name=pkg",
    OPTION_PATH,
    "package_version=1.0",
)
PATH_FORM_CASES = (
    pytest.param(
        SentCase(
            argv=(OP_MAVEN_AUTHORIZE, OPTION_PATH, "path=a/rc 1", OPTION_PATH, "file_name=x.jar"),
            method=METHOD_PUT,
            url=f"{REST_BASE}/projects/{PROJECT_ID}/packages/maven/a/rc%201/x.jar/authorize",
        ),
        id="glob-holding-a-slash",
    ),
    pytest.param(
        SentCase(
            argv=(*GENERIC_PACKAGE_ARGV, OPTION_PATH, "path=a/b", OPTION_PATH, "file_name=file.txt"),
            method=METHOD_GET,
            url=f"{REST_BASE}/projects/{PROJECT_ID}/packages/generic/pkg/1.0/a/b/file.txt",
        ),
        id="optional-group-given",
    ),
    pytest.param(
        SentCase(
            argv=(*GENERIC_PACKAGE_ARGV, OPTION_PATH, "file_name=file.txt"),
            method=METHOD_GET,
            url=f"{REST_BASE}/projects/{PROJECT_ID}/packages/generic/pkg/1.0/file.txt",
        ),
        id="optional-group-left-out",
    ),
    pytest.param(
        SentCase(
            argv=(
                OP_NUGET_SINGLE_PACKAGE,
                OPTION_PATH,
                "project_id=7",
                OPTION_PATH,
                "package_name=N",
                OPTION_PATH,
                "package_version=1.0",
            ),
            method=METHOD_GET,
            url=f"{REST_BASE}/projects/7/packages/nuget/v2/Packages(Id='N',Version='1.0')",
        ),
        id="escaped-parentheses-with-globs",
    ),
    pytest.param(
        SentCase(
            argv=(OP_NUGET_ENUMERATE, OPTION_PATH, "project_id=7", OPTION_QUERY, "$filter=x"),
            method=METHOD_GET,
            url=f"{REST_BASE}/projects/7/packages/nuget/v2/Packages()?%24filter=x",
        ),
        id="escaped-parentheses-empty",
    ),
    pytest.param(
        SentCase(
            argv=(OP_NUGET_FIND_BY_ID, OPTION_PATH, "project_id=7", OPTION_QUERY, "id=N"),
            method=METHOD_GET,
            url=f"{REST_BASE}/projects/7/packages/nuget/v2/FindPackagesById()?id=N",
        ),
        id="escaped-parentheses-beside-a-query-id",
    ),
    pytest.param(
        SentCase(
            argv=(OP_NUGET_METADATA,),
            method=METHOD_GET,
            url=f"{REST_BASE}/projects/{PROJECT_ID}/packages/nuget/v2/$metadata",
        ),
        id="dollar-metadata",
    ),
)

# AC-2.2: a glob value with a part that is no path segment once dot segments are resolved (RFC 3986 section 5.2.4).
GLOB_NAMED = "*path"
REFUSED_GLOB_VALUES = (
    pytest.param("a//b", id="empty-part"),
    pytest.param("/a", id="leading-slash"),
    pytest.param("a/../b", id="dot-dot-part"),
)

# AC-3.2: bytes a text-layer read would translate (`\r\n`) or fail to decode (`\xff`).
UPLOAD_BYTES = b"PK\x03\x04 first line\r\nsecond line\n\xff\xfe\x00 last"
UPLOAD_FILE_NAME = "upload.bin"
ARTIFACTS_FILE_NAME = "artifacts.zip"
# `call openapi-only#upload-job-artifacts --path id=5 --file file=<path> -f artifact_type=archive`.
JOB_ARTIFACTS_URL = f"{REST_BASE}/jobs/5/artifacts"
ATTRIBUTE_FILE = "file"
ATTRIBUTE_ARTIFACT_TYPE = "artifact_type"
ARTIFACT_TYPE = "archive"

# AC-3.2: the three raw-body records, each given its path values; the generic upload also its two query attributes.
RAW_UPLOAD_CASES = (
    pytest.param(
        SentCase(
            argv=(
                OP_UPLOAD_PACKAGE_FILE,
                OPTION_PATH,
                "package_name=pkg",
                OPTION_PATH,
                "package_version=1.0",
                OPTION_PATH,
                "file_name=f.bin",
                OPTION_QUERY,
                "status=hidden",
                OPTION_QUERY,
                "select=package_file",
            ),
            method=METHOD_PUT,
            url=f"{REST_BASE}/projects/{PROJECT_ID}/packages/generic/pkg/1.0/f.bin?status=hidden&select=package_file",
        ),
        id="upload-package-file",
    ),
    pytest.param(
        SentCase(
            argv=(
                OP_UPLOAD_TERRAFORM_MODULE,
                OPTION_PATH,
                "module_name=infra",
                OPTION_PATH,
                "module_system=aws",
                OPTION_PATH,
                "module_version=1.0.0",
            ),
            method=METHOD_PUT,
            url=f"{REST_BASE}/projects/{PROJECT_ID}/packages/terraform/modules/infra/aws/1.0.0/file",
        ),
        id="upload-terraform-module-package-file",
    ),
    pytest.param(
        SentCase(
            argv=(OP_TERRAFORM_STATE, OPTION_PATH, "name=production"),
            method=METHOD_POST,
            url=f"{REST_BASE}/projects/{PROJECT_ID}/terraform/state/production",
        ),
        id="create-or-update-a-terraform-state",
    ),
)

# UB-2: a runner's `token`, a body attribute of "Request a job", given with `-f`.
ATTRIBUTE_TOKEN = "token"
RUNNER_TOKEN = "runner-token"  # pragma: allowlist secret
REQUEST_A_JOB_URL = f"{REST_BASE}/jobs/request"

# Issue #63 AC-6.2 (design.md D5, Correctness Properties): both NuGet symbol file downloads with `--header
# Symbolchecksum=SHA256:ab`, the header their section's `header` row names, and a value for each `*name` glob of the
# path. The header's name is compared case-insensitively (RFC 9110 section 5.1; `RecordedRequest.header`).
OPTION_HEADER = "--header"
HEADER_SYMBOL_CHECKSUM = "Symbolchecksum"
SYMBOL_CHECKSUM = "SHA256:ab"
SYMBOL_FILE_ARGV: Tuple[str, ...] = (
    OPTION_PATH,
    "file_name=lib.pdb",
    OPTION_PATH,
    "signature=abc123",
    OPTION_PATH,
    "same_file_name=lib.pdb",
)
SYMBOL_DOWNLOAD_CASES = (
    pytest.param(
        SentCase(
            argv=("openapi-only#the-nuget-symbol-file-download-endpoint", OPTION_PATH, "id=12", *SYMBOL_FILE_ARGV),
            method=METHOD_GET,
            url=f"{REST_BASE}/groups/12/-/packages/nuget/symbolfiles/lib.pdb/abc123/lib.pdb",
        ),
        id="the-nuget-symbol-file-download-endpoint",
    ),
    pytest.param(
        SentCase(
            argv=("openapi-only#the-nuget-symbol-file-download-endpoint-1", *SYMBOL_FILE_ARGV),
            method=METHOD_GET,
            url=f"{REST_BASE}/projects/{PROJECT_ID}/packages/nuget/symbolfiles/lib.pdb/abc123/lib.pdb",
        ),
        id="the-nuget-symbol-file-download-endpoint-1",
    ),
)


# --- Fixtures and helpers ---------------------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def socket_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    fixtures.install_socket_guard(monkeypatch=monkeypatch)


@pytest.fixture(autouse=True)
def fake_gitlab(monkeypatch: pytest.MonkeyPatch) -> Any:
    return fixtures.FakeGitLab().install(monkeypatch=monkeypatch)


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A scratch project as the working directory; the entry script reads ``config/gitlab.json`` under it."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def gitlab_module(*, name: str) -> ModuleType:
    """Import ``gitlab_api.<name>`` (``families.openapi_only`` for the family) inside a test, after asserting its
    file."""
    source = PACKAGE_DIR.joinpath(*name.split(MODULE_SEPARATOR)).with_suffix(MODULE_SUFFIX)
    assert source.is_file(), f"{source} does not exist"
    return importlib.import_module(name=f"{PACKAGE}{MODULE_SEPARATOR}{name}")


def run_call(*, root: Path, argv: Sequence[str]) -> Any:
    """Write ``config/gitlab.json`` (hostname the fake host's) under ``root``, the working directory, and return the
    exit code of the product's ``main(argv=["call", *argv])``."""
    config: Dict[str, Any] = {FIELD_HOSTNAME: fixtures.HOST, FIELD_PROJECT_ID: PROJECT_ID, FIELD_TOKEN: TOKEN}
    fixtures.write_config(root=root, config=config)
    return fixtures.run_main(wrapper=fixtures.load_wrapper(module_name=WRAPPER_MODULE), argv=[CALL, *argv])


def sent(*, fake: Any) -> List[Tuple[str, str]]:
    """``(method, URL)`` of every request the fake host recorded, in order."""
    return [(request.method, request.url) for request in fake.requests]


def printed_json(*, value: Any) -> str:
    """``value`` as ``commands/_common.print_json`` writes it."""
    return json.dumps(obj=value, indent=JSON_INDENT) + LINE_END


def error_messages(*, caplog: pytest.LogCaptureFixture) -> List[str]:
    """The text of every log record at ERROR or above, in order: what the entry script writes to standard error."""
    return [record.getMessage() for record in caplog.records if record.levelno >= logging.ERROR]


def media_type(*, value: Optional[str]) -> Optional[str]:
    """The media type of a ``Content-Type`` value, lower-cased and without its parameters; ``None`` without one."""
    if value is None:
        return None
    message = Message()
    message[HEADER_CONTENT_TYPE] = value
    return message.get_content_type()


class Part(NamedTuple):
    """One part of a ``multipart/form-data`` body: its ``name``, its ``filename`` (``None`` for a form field) and its
    content, unchanged."""

    name: str
    filename: Optional[str]
    content: bytes


def part_disposition(*, head: bytes) -> Message:
    """The ``Content-Disposition`` header of one multipart part's header block, parsed."""
    message = Message()
    for line in head.split(sep=CRLF):
        name, _, value = line.decode(encoding=TEXT_ENCODING).partition(HEADER_SEPARATOR)
        if name.strip().lower() == HEADER_CONTENT_DISPOSITION.lower():
            message[HEADER_CONTENT_DISPOSITION] = value.strip()
    return message


def multipart_parts(*, body: bytes, content_type: str) -> List[Part]:
    """The parts of a ``multipart/form-data`` body in body order (RFC 7578, RFC 2046 section 5.1.1): each delimiter but
    the first follows a CRLF, which belongs to it, and the close delimiter ends in ``--``."""
    header = Message()
    header[HEADER_CONTENT_TYPE] = content_type
    boundary = header.get_param(param=PARAM_BOUNDARY)
    assert isinstance(boundary, str) and boundary, f"a multipart Content-Type names its boundary: {content_type!r}"
    delimiter = CRLF + DASHES + boundary.encode(encoding=ASCII_ENCODING)
    parts: List[Part] = []
    for section in (CRLF + body).split(sep=delimiter)[1:]:
        if section.startswith(DASHES):
            break
        head, _, content = section[len(CRLF) :].partition(CRLF + CRLF)
        disposition = part_disposition(head=head)
        name = disposition.get_param(param=PARAM_NAME, header=HEADER_CONTENT_DISPOSITION)
        filename = disposition.get_param(param=PARAM_FILENAME, header=HEADER_CONTENT_DISPOSITION)
        parts.append(Part(name=str(name), filename=None if filename is None else str(filename), content=content))
    return parts


def set_difference(*, declared: AbstractSet[Any], expected: AbstractSet[Any]) -> str:
    """What ``declared`` lacks and what it has beyond ``expected``, each sorted, one item per line."""
    lines = [f"missing: {item!r}" for item in sorted(expected - declared)]
    lines.extend(f"not expected: {item!r}" for item in sorted(declared - expected))
    return "\n".join(lines)


def mapping_difference(*, declared: Mapping[Any, Any], expected: Mapping[Any, Any]) -> str:
    """The keys ``declared`` lacks or has beyond ``expected``, and each key whose value differs."""
    lines = [set_difference(declared=set(declared), expected=set(expected))]
    lines.extend(
        f"{key!r}: declared {declared[key]!r}, expected {expected[key]!r}"
        for key in sorted(set(declared) & set(expected))
        if declared[key] != expected[key]
    )
    return "\n".join(line for line in lines if line)


def non_scalar_params(*, records: Sequence[Any], registry: ModuleType) -> Dict[str, Dict[str, str]]:
    """``{operation_id: {name: Kind name}}`` of every ``Param`` whose Kind is not SCALAR, over the records with any."""
    typed = {
        record.operation_id: {
            param.name: param.kind.name for param in record.params if param.kind is not registry.Kind.SCALAR
        }
        for record in records
    }
    return {operation_id: names for operation_id, names in typed.items() if names}


def required_params(*, records: Sequence[Any]) -> Dict[str, FrozenSet[str]]:
    """``{operation_id: names}`` of every ``Param`` declared ``required=True``, over the records with any."""
    required = {
        record.operation_id: frozenset(param.name for param in record.params if param.required) for record in records
    }
    return {operation_id: names for operation_id, names in required.items() if names}


# --- AC-1.1, AC-1.6: nothing is pending -------------------------------------------------------------------------------


def test_nothing_is_pending() -> None:
    """AC-1.1, AC-1.6: ``PENDING`` is empty, and ``OPERATIONS`` declares one record per Reference of the family's index
    rows but the three ``ml_models`` file anchors, each ID once."""
    family = gitlab_module(name=FAMILY_MODULE)
    pending = sorted(family.PENDING)
    assert pending == [], f"PENDING holds {len(pending)} key(s); each has its record (AC-1.6): {pending}"
    declared = sorted(record.operation_id for record in family.OPERATIONS)
    repeated = sorted({operation_id for operation_id in declared if declared.count(operation_id) > 1})
    assert declared == sorted(OPERATION_IDS), (
        f"OPERATIONS declares {len(declared)} record(s), the index has {len(OPERATION_IDS)} References (AC-1.1); "
        f"declared more than once: {repeated}\n" + set_difference(declared=set(declared), expected=set(OPERATION_IDS))
    )


# --- AC-1.3, AC-3.2: every Param typed as its row ---------------------------------------------------------------------


def test_every_param_is_typed_as_its_row() -> None:
    """AC-1.3, AC-3.2: the ``Param``s that are not ``Kind.SCALAR`` carry the ``Kind`` of their row's Type; the
    ``Param``s declared ``required`` are the rows whose Required reads ``yes``; the raw-body records, and only they,
    declare their body's media type and send every ``Param`` in the query; every record has a JSON body and no
    ``fixed`` pairs."""
    family = gitlab_module(name=FAMILY_MODULE)
    registry = gitlab_module(name=REGISTRY)
    records = tuple(family.OPERATIONS)
    typed = non_scalar_params(records=records, registry=registry)
    assert typed == KINDS, "the Params that are not Kind.SCALAR are not the rows' (AC-1.3):\n" + mapping_difference(
        declared=typed, expected=KINDS
    )
    required = required_params(records=records)
    expected_required = {operation_id: frozenset(names) for operation_id, names in REQUIRED.items()}
    assert required == expected_required, "required=True is not exactly where Required reads `yes` (AC-1.3):\n" + (
        mapping_difference(declared=required, expected=expected_required)
    )
    raw_bodies = {record.operation_id: record.content_type for record in records if record.content_type is not None}
    assert raw_bodies == RAW_BODIES, "the records with a content_type are not the raw-body uploads (AC-3.2):\n" + (
        mapping_difference(declared=raw_bodies, expected=RAW_BODIES)
    )
    misplaced = [
        (record.operation_id, param.name, param.location.name)
        for record in records
        if record.operation_id in RAW_BODIES
        for param in record.params
        if param.location.name != LOCATION_QUERY
    ]
    assert misplaced == [], f"a raw-body record sends every Param in the query (design.md D4): {misplaced}"
    misbodied = [
        record.operation_id for record in records if record.body is not registry.BodyFormat.JSON or record.fixed
    ]
    assert misbodied == [], f"every record has body BodyFormat.JSON and no fixed pairs (AC-1.3): {misbodied}"


# --- AC-1.4: no Param names a path parameter --------------------------------------------------------------------------


def test_no_param_names_a_path_parameter() -> None:
    """AC-1.4: no ``Param`` of any record names a path parameter of its record's path, a ``:name`` or a ``*name`` glob,
    inside an optional group or not, though the section may list a glob as a ``query``, ``body`` or ``form`` row."""
    family = gitlab_module(name=FAMILY_MODULE)
    registry = gitlab_module(name=REGISTRY)
    records = tuple(family.OPERATIONS)
    assert records, "openapi_only.OPERATIONS declares no record, so no Param can be checked (AC-1.4)"
    clashes = [
        (record.operation_id, param.name)
        for record in records
        for param in record.params
        if param.name in registry.placeholders(path=record.path)
    ]
    assert clashes == [], f"a Param names a path parameter of its record's path (AC-1.4): {clashes}"


# --- AC-1.5, AC-3.4: only the list records are paged ------------------------------------------------------------------


def test_only_the_list_records_are_paged() -> None:
    """AC-1.5: the eight list records are ``Paging.OFFSET`` and declare their ``page`` and ``per_page`` query rows;
    every other record is ``Paging.NONE``."""
    family = gitlab_module(name=FAMILY_MODULE)
    registry = gitlab_module(name=REGISTRY)
    records = tuple(family.OPERATIONS)
    paged = {record.operation_id: record.paging.name for record in records if record.paging is not registry.Paging.NONE}
    assert paged == PAGED_RECORDS, "the records not Paging.NONE are not the list records (AC-1.5):\n" + (
        mapping_difference(declared=paged, expected=PAGED_RECORDS)
    )
    rows = [registry.Param(name=name, location=registry.Location.QUERY) for name in PAGING_ROWS]
    undeclared = {
        record.operation_id: [row.name for row in rows if row not in record.params]
        for record in records
        if record.operation_id in PAGED_RECORDS
    }
    missing = {operation_id: names for operation_id, names in undeclared.items() if names}
    assert missing == {}, f"each paged record declares its page and per_page query rows (AC-1.5): {missing}"


@pytest.mark.parametrize(argnames="case", argvalues=LIST_CASES)
def test_a_list_record_prints_every_page(
    case: ListCase, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-3.4: two pages scripted at their exact URLs, the second named by the first's ``x-next-page``; the call exits
    0, every scripted page is served, and the items of both print as one JSON array."""
    first_page = f"{case.url}{FIRST_PAGE_QUERY}"
    second_page = f"{case.url}{SECOND_PAGE_QUERY}"
    fake_gitlab.script(
        method=METHOD_GET, url=first_page, headers=((HEADER_NEXT_PAGE, NEXT_PAGE),), body=[PAGE_ITEMS[0]]
    )
    fake_gitlab.script(
        method=METHOD_GET, url=second_page, headers=((HEADER_NEXT_PAGE, LAST_PAGE),), body=[PAGE_ITEMS[1]]
    )
    code = run_call(root=project, argv=case.argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {list(case.argv)} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(METHOD_GET, first_page), (METHOD_GET, second_page)], (
        "each page requested as Transport.pages does (#13 AC-2.5)"
    )
    assert fake_gitlab.remaining() == [], "every scripted page was served"
    assert captured.out == printed_json(value=list(PAGE_ITEMS)), (
        f"one JSON array of every item of both pages, in page order, as print_json writes it (AC-3.4):\n{captured.out}"
    )


# --- AC-2.1 to AC-2.6, AC-3.1: the path forms -------------------------------------------------------------------------


@pytest.mark.parametrize(argnames="case", argvalues=PATH_FORM_CASES)
def test_a_path_form_is_sent_as_the_route_declares(
    case: SentCase, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-2.1, AC-2.3, AC-2.5, AC-2.6, AC-3.1: the call exits 0 and sends one request, its method and URL the route's
    with each value written in: a glob with its ``/`` kept, an optional group whole or not at all, an escaped
    parenthesis without its backslash, ``$metadata`` as written."""
    fake_gitlab.script_next(body=ANSWER)
    code = run_call(root=project, argv=case.argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {list(case.argv)} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(case.method, case.url)], "the one request is sent as the route declares (AC-2.6)"


@pytest.mark.parametrize(argnames="value", argvalues=REFUSED_GLOB_VALUES)
def test_a_glob_part_that_is_no_segment_sends_nothing(
    value: str, project: Path, fake_gitlab: Any, caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-2.2: a ``*path`` value with an empty, ``.`` or ``..`` part is refused as ``registry.expand`` refuses it: exit
    1, no request, and an ERROR record naming ``*path``."""
    fake_gitlab.script_next(body=ANSWER)
    argv = (OP_MAVEN_AUTHORIZE, OPTION_PATH, f"path{ASSIGNED}{value}", OPTION_PATH, "file_name=x.jar")
    code = run_call(root=project, argv=argv)
    captured = capsys.readouterr()
    assert code == EXIT_API_ERROR, f"call {list(argv)} exits {EXIT_API_ERROR}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [], "a refused glob part sends no request (AC-2.2)"
    messages = error_messages(caplog=caplog)
    assert any(GLOB_NAMED in message for message in messages), (
        f"an ERROR record names {GLOB_NAMED} (AC-2.2): {messages}"
    )


# --- AC-3.2: the uploads ----------------------------------------------------------------------------------------------


def test_the_job_artifacts_upload_sends_the_file_as_its_part(
    project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-3.2: ``--file file=<path>`` and ``-f artifact_type=archive`` send one ``multipart/form-data`` ``POST``: the
    part named ``file`` carries a ``filename`` and the file's bytes unchanged, and ``artifact_type`` is a part with no
    ``filename`` holding its text."""
    artifacts = project / ARTIFACTS_FILE_NAME
    artifacts.write_bytes(data=UPLOAD_BYTES)
    fake_gitlab.script_next(status=STATUS_CREATED, body=UPLOAD_ANSWER)
    argv = (
        OP_UPLOAD_JOB_ARTIFACTS,
        OPTION_PATH,
        "id=5",
        OPTION_FILE,
        f"{ATTRIBUTE_FILE}{ASSIGNED}{artifacts}",
        OPTION_RAW_FIELD,
        f"{ATTRIBUTE_ARTIFACT_TYPE}{ASSIGNED}{ARTIFACT_TYPE}",
    )
    code = run_call(root=project, argv=argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {list(argv)} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(METHOD_POST, JOB_ARTIFACTS_URL)], "one POST to the job's artifacts"
    request = fake_gitlab.requests[0]
    content_type = request.header(name=HEADER_CONTENT_TYPE)
    assert media_type(value=content_type) == CONTENT_TYPE_MULTIPART, f"the body's Content-Type: {content_type!r}"
    assert request.body is not None, "the upload carries a body"
    parts = {part.name: part for part in multipart_parts(body=request.body, content_type=str(content_type))}
    assert sorted(parts) == sorted((ATTRIBUTE_FILE, ATTRIBUTE_ARTIFACT_TYPE)), f"the parts sent: {sorted(parts)}"
    assert parts[ATTRIBUTE_FILE].filename == ARTIFACTS_FILE_NAME, "the file part carries the file's name"
    assert parts[ATTRIBUTE_FILE].content == UPLOAD_BYTES, "the file part holds the file's bytes unchanged (AC-3.2)"
    assert parts[ATTRIBUTE_ARTIFACT_TYPE].filename is None, "the -f attribute is a form field, with no filename"
    assert parts[ATTRIBUTE_ARTIFACT_TYPE].content == ARTIFACT_TYPE.encode(encoding=TEXT_ENCODING), (
        "the -f attribute's part holds its text"
    )


@pytest.mark.parametrize(argnames="case", argvalues=RAW_UPLOAD_CASES)
def test_a_raw_upload_sends_the_bytes_as_its_body(
    case: SentCase, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-3.2: ``--input <path>`` sends one request, its method and URL the record's with the query given, whose
    ``Content-Type`` is ``application/octet-stream``, whose body is the file's bytes unchanged, and which carries the
    configured credential."""
    option_input = "--input"  # call's raw-body option (design.md D5)
    upload = project / UPLOAD_FILE_NAME
    upload.write_bytes(data=UPLOAD_BYTES)
    fake_gitlab.script_next(status=STATUS_CREATED, body=UPLOAD_ANSWER)
    argv = (*case.argv, option_input, str(upload))
    code = run_call(root=project, argv=argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {list(argv)} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(case.method, case.url)], "one request to the record's route, query included"
    request = fake_gitlab.requests[0]
    content_type = request.header(name=HEADER_CONTENT_TYPE)
    assert media_type(value=content_type) == CONTENT_TYPE_OCTET_STREAM, f"the body's Content-Type: {content_type!r}"
    assert request.body == UPLOAD_BYTES, "the body is the --input bytes unchanged, \\r\\n and \\xff included (AC-3.2)"
    assert request.header(name=HEADER_PRIVATE_TOKEN) == TOKEN, "the configured token travels in its one header"


# --- UB-2: a token attribute is the value given -----------------------------------------------------------------------


def test_a_token_attribute_is_the_value_given(
    project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """UB-2: ``-f token=runner-token`` on "Request a job" sends one ``POST`` whose JSON body is that token alone, while
    the configured token travels only in its ``PRIVATE-TOKEN`` header and in no body."""
    fake_gitlab.script_next(status=STATUS_CREATED, body=ANSWER)
    argv = (OP_REQUEST_A_JOB, OPTION_RAW_FIELD, f"{ATTRIBUTE_TOKEN}{ASSIGNED}{RUNNER_TOKEN}")
    code = run_call(root=project, argv=argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {list(argv)} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(METHOD_POST, REQUEST_A_JOB_URL)], "one POST to /jobs/request"
    request = fake_gitlab.requests[0]
    content_type = request.header(name=HEADER_CONTENT_TYPE)
    assert media_type(value=content_type) == CONTENT_TYPE_JSON, f"the body's Content-Type: {content_type!r}"
    assert request.json() == {ATTRIBUTE_TOKEN: RUNNER_TOKEN}, "the token attribute is the value given (UB-2)"
    assert request.header(name=HEADER_PRIVATE_TOKEN) == TOKEN, "the configured token travels in its one header"
    carrying = [each.url for each in fake_gitlab.requests if TOKEN.encode(encoding=TEXT_ENCODING) in (each.body or b"")]
    assert carrying == [], f"the configured token is in no body (UB-2): {carrying}"


# --- Issue #63 AC-6.2: the request header of the NuGet symbol file downloads ------------------------------------------


@pytest.mark.parametrize(argnames="case", argvalues=SYMBOL_DOWNLOAD_CASES)
def test_the_symbol_download_sends_its_checksum_header(
    case: SentCase, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """#63 AC-6.2, AC-8.3: ``--header Symbolchecksum=SHA256:ab`` on a NuGet symbol file download exits 0 and sends one
    ``GET`` to the record's route, each glob value in its place and no query, carrying ``Symbolchecksum`` (its name
    compared case-insensitively) at ``SHA256:ab`` beside the configured token in its one header."""
    argv = (*case.argv, OPTION_HEADER, f"{HEADER_SYMBOL_CHECKSUM}{ASSIGNED}{SYMBOL_CHECKSUM}")
    fake_gitlab.script_next(body=ANSWER)
    code = run_call(root=project, argv=argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {list(argv)} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert sent(fake=fake_gitlab) == [(case.method, case.url)], "one GET to the record's route, no query"
    request = fake_gitlab.requests[0]
    assert request.header(name=HEADER_SYMBOL_CHECKSUM) == SYMBOL_CHECKSUM, (
        f"the request carries {HEADER_SYMBOL_CHECKSUM}: {SYMBOL_CHECKSUM} (#63 AC-6.2); headers sent: {request.headers}"
    )
    assert request.header(name=HEADER_PRIVATE_TOKEN) == TOKEN, "the configured token travels in its one header"
