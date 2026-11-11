"""Tests for ``gitlab_api/families/software_supply_chain_security.py``, the ``software-supply-chain-security`` endpoint
family of the GitLab wrapper (issue #42, the security slice of the wrapper rewrite; ``change.md`` AC-1, AC-2, AC-4,
AC-5 and AC-7).

Every expected value is a literal table transcribed from the reference, never read from the records:
``docs/api-reference/gitlab/operations-index.md`` (the rows whose Reference is
``rest/software-supply-chain-security.md``) and ``docs/api-reference/gitlab/rest/software-supply-chain-security.md``
(each section's endpoints, its heading, and the ``In``, ``Type``, ``Required`` and ``Notes`` columns of its
``| Attribute | In | Type |`` table). A "new record" is one whose ID is not part 1's (``#as-a-regular-user``,
``GET /users``; ``#as-a-regular-user-1``, ``GET /user``), which ``test_gitlab_wrapper_compat.py`` pins. What is
pinned:

- AC-1: ``{(method, path): operation_id}`` over the new records is every key ``PENDING`` held at 3beba95 but AC-2's,
  each with the Reference of one of its rows: ``PUT /application/appearance`` by ``#update-application-appearance``,
  ``GET /users/:id`` by ``#retrieve-a-single-user-as-a-regular-user``, and a section with several endpoints by its
  ``/projects/:id/`` endpoint, else its first;
- AC-2: ``PENDING`` is the other endpoints of those sections ("Custom Attributes API", the four access-request
  sections, "Set your user status"), ``GET https://HOST/oauth/token/info`` and the external control's status ``PATCH``
  (DL-003);
- AC-3, its ``body`` and ``fixed`` clause: every record, part 1's two included, has ``body`` ``BodyFormat.JSON`` and
  no ``fixed`` pair, and the family declares a record;
- AC-4: the ``Kind`` of every ``Param`` that is not ``SCALAR`` (``FILE`` for a row noted "file upload" and for
  ``avatar`` on ``PUT /user/avatar``, ``POST /users`` and ``PUT /users/:id``; ``ARRAY_OF_HASHES`` for an ``array`` row
  with ``name[].…`` rows; ``ARRAY`` for any other Type naming an array), and the ``required`` ``Param`` names of each
  record, exactly its Required ``yes`` query and body rows (a ``name[].…`` row is its parent's, no ``Param``);
- AC-5: the new ``Paging.OFFSET`` records are the ``GET`` sections headed "List" or "Get all" but
  ``#list-all-token-associations``, which answers one object; no record is ``Paging.KEYSET``;
- AC-7: each such record, called through the product's ``main(argv=["call", ...])`` with ``--path`` for every
  placeholder of its path against a fake host serving one item on each of two pages chained by ``x-next-page: 2``,
  exits 0, requests both pages at their exact URLs and prints both items as one JSON array (``print_json``).

AC-3 and AC-6 are proven by ``test/test_gitlab_wrapper_contract.py``, which finds every record by discovery.

``src/payload/scripts`` (``scripts/`` once installed) goes on ``sys.path`` and ``gitlab_api`` is imported inside each
test, as ``test/test_gitlab_wrapper_coverage.py`` imports it, so the module collects whatever the package lacks. The
fake GitLab host and the socket guard (``gitlab_wrapper_fixtures.py``, loaded by path as
``test_gitlab_api_call.py`` loads it) are installed for every test.

Run: ``python scripts/run_tests.py src/payload/test/test_gitlab_api_software_supply_chain_security.py`` (no network).
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import AbstractSet, Any, Dict, FrozenSet, List, Mapping, Sequence, Tuple

import pytest

TEST_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
FIXTURES_FILE = TEST_DIR / "gitlab_wrapper_fixtures.py"
FIXTURES_MODULE = "gitlab_wrapper_fixtures"
WRAPPER_MODULE = "gitlab_wrapper_software_supply_chain_security_under_test"
PACKAGE = "gitlab_api"
REGISTRY = f"{PACKAGE}.registry"
FAMILY_MODULE = f"{PACKAGE}.families.software_supply_chain_security"
MODULE_SEPARATOR = "."

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

# The keys of config/gitlab.json (templates/config/gitlab.json.template; #13 design.md D7).
FIELD_HOSTNAME = "hostname"
FIELD_PROJECT_ID = "project_id"
FIELD_TOKEN = "token"  # a config key name, not a secret
TOKEN = "glpat-gitlab-api-software-supply-chain-security-test"  # pragma: allowlist secret
PROJECT_ID = 4242

CALL = "call"
EXIT_OK = 0
OPTION_PATH = "--path"
ASSIGNED = "="
ID_SEPARATOR = "#"
METHOD_GET = "GET"
REST_BASE = fixtures.REST_BASE
TEXT_ENCODING = "utf-8"
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_NEXT_PAGE = "x-next-page"
CONTENT_TYPE_JSON = "application/json"
# The query of a list's first page: the transport adds `per_page=100` (conventions.md "Offset-based", #13 AC-2.5), and
# the next page repeats it with `page` set to the `x-next-page` value.
FIRST_PAGE_QUERY = "per_page=100"
NEXT_PAGE = "2"
NEXT_PAGE_QUERY = f"page={NEXT_PAGE}"
LAST_PAGE = ""  # an empty `x-next-page`: no next page
# The `print_json` form (commands/_common.py): JSON indented by 2, then a line end.
JSON_INDENT = 2
LINE_END = "\n"

# A path parameter as operations-index.md and rest/software-supply-chain-security.md write it: `:` and an identifier.
PLACEHOLDER = re.compile(pattern=r":(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
GROUP_NAME = "name"
# Each placeholder of a list path is given a distinct number, in path order, so a swapped value shows in the URL.
FIRST_PATH_VALUE = 101

# The item each page holds.
FIELD_ID = "id"
PAGE_ITEMS: Tuple[Dict[str, Any], ...] = ({FIELD_ID: 1}, {FIELD_ID: 2})

# The `registry.Kind` member names a non-SCALAR attribute takes (AC-4).
KIND_ARRAY = "ARRAY"
KIND_ARRAY_OF_HASHES = "ARRAY_OF_HASHES"
KIND_FILE = "FILE"

# Part 1's records (issue #13 design.md D6), not this slice's: `issue start` and `issue assign` compose them (UB-1).
PART_ONE_IDS: FrozenSet[str] = frozenset(
    {
        "software-supply-chain-security#as-a-regular-user",
        "software-supply-chain-security#as-a-regular-user-1",
    }
)

# --- The tables, transcribed from docs/api-reference/gitlab ----------------------------------------------------------

# operations-index.md and rest/software-supply-chain-security.md: every key PENDING held at 3beba95 but AC-2's, sorted,
# with the Reference, written `software-supply-chain-security#<anchor>`, of the one row that maps it (AC-1). Of the
# keys with several rows, `PUT /application/appearance` (also "Update application logo") and `GET /users/:id` (also
# "As an administrator") are mapped as AC-1 names. Of a section with several endpoints the key is its
# `/projects/:id/` endpoint, else its first.
KEY_IDS: Dict[Tuple[str, str], str] = {
    ("DELETE", "/admin/token"): "software-supply-chain-security#revoke-a-token",
    ("DELETE", "/applications/:id"): "software-supply-chain-security#delete-an-application",
    ("DELETE", "/groups/:id/access_tokens/:token_id"): "software-supply-chain-security#revoke-a-group-access-token",
    ("DELETE", "/groups/:id/enterprise_users/:user_id"): "software-supply-chain-security#delete-an-enterprise-user",
    (
        "DELETE",
        "/groups/:id/member_roles/:member_role_id",
    ): "software-supply-chain-security#remove-member-role-of-a-group",
    ("DELETE", "/groups/:id/saml/:uid"): "software-supply-chain-security#delete-a-single-saml-identity",
    (
        "DELETE",
        "/groups/:id/saml_group_links/:saml_group_name",
    ): "software-supply-chain-security#delete-a-saml-group-link",
    (
        "DELETE",
        "/groups/:id/service_accounts/:user_id",
    ): "software-supply-chain-security#delete-a-group-service-account",
    ("DELETE", "/groups/:id/service_accounts/:user_id/personal_access_tokens/:token_id"): (
        "software-supply-chain-security#revoke-a-personal-access-token-for-a-group-service-account"
    ),
    ("DELETE", "/member_roles/:member_role_id"): "software-supply-chain-security#delete-an-instance-member-role",
    ("DELETE", "/personal_access_tokens/:id"): "software-supply-chain-security#revoke-a-personal-access-token",
    ("DELETE", "/projects/:id/access_requests/:user_id"): "software-supply-chain-security#deny-an-access-request",
    ("DELETE", "/projects/:id/access_tokens/:token_id"): "software-supply-chain-security#revoke-a-project-access-token",
    ("DELETE", "/projects/:id/custom_attributes/:key"): "software-supply-chain-security#delete-custom-attribute",
    ("DELETE", "/projects/:id/service_accounts/:user_id"): (
        "software-supply-chain-security#delete-a-project-service-account"
    ),
    ("DELETE", "/projects/:id/service_accounts/:user_id/personal_access_tokens/:token_id"): (
        "software-supply-chain-security#revoke-a-personal-access-token-for-a-project-service-account"
    ),
    ("DELETE", "/user/applications/:id"): "software-supply-chain-security#delete-an-application-1",
    ("DELETE", "/user/emails/:email_id"): "software-supply-chain-security#delete-an-email-address",
    ("DELETE", "/user/gpg_keys/:key_id"): "software-supply-chain-security#delete-a-gpg-key",
    ("DELETE", "/user/keys/:key_id"): "software-supply-chain-security#delete-an-ssh-key",
    ("DELETE", "/users/:id"): "software-supply-chain-security#delete-a-user",
    ("DELETE", "/users/:id/emails/:email_id"): "software-supply-chain-security#delete-an-email-address-for-a-user",
    ("DELETE", "/users/:id/gpg_keys/:key_id"): "software-supply-chain-security#delete-a-gpg-key-for-a-user",
    ("DELETE", "/users/:id/identities/:provider"): (
        "software-supply-chain-security#delete-authentication-identity-from-a-user"
    ),
    ("DELETE", "/users/:id/keys/:key_id"): "software-supply-chain-security#delete-an-ssh-key-for-a-user",
    ("DELETE", "/users/:user_id/impersonation_tokens/:impersonation_token_id"): (
        "software-supply-chain-security#revoke-an-impersonation-token"
    ),
    ("GET", "/application/appearance"): "software-supply-chain-security#retrieve-application-appearance",
    ("GET", "/application/plan_limits"): "software-supply-chain-security#retrieve-current-plan-limits",
    ("GET", "/application/settings"): (
        "software-supply-chain-security#retrieve-details-on-current-application-settings"
    ),
    ("GET", "/application/statistics"): "software-supply-chain-security#retrieve-application-statistics",
    ("GET", "/applications"): "software-supply-chain-security#list-all-applications",
    ("GET", "/audit_events"): "software-supply-chain-security#list-all-instance-audit-events",
    ("GET", "/audit_events/:id"): "software-supply-chain-security#retrieve-an-instance-audit-event",
    ("GET", "/avatar"): "software-supply-chain-security#retrieve-user-account-avatar",
    ("GET", "/groups/:id/access_tokens"): "software-supply-chain-security#list-all-group-access-tokens",
    ("GET", "/groups/:id/access_tokens/:token_id"): (
        "software-supply-chain-security#retrieve-details-on-a-group-access-token"
    ),
    ("GET", "/groups/:id/audit_events"): "software-supply-chain-security#list-all-group-audit-events",
    ("GET", "/groups/:id/audit_events/:audit_event_id"): "software-supply-chain-security#retrieve-a-group-audit-event",
    ("GET", "/groups/:id/enterprise_users"): "software-supply-chain-security#list-all-enterprise-users",
    ("GET", "/groups/:id/enterprise_users/:user_id"): "software-supply-chain-security#retrieve-an-enterprise-user",
    ("GET", "/groups/:id/member_roles"): "software-supply-chain-security#get-all-group-member-roles",
    ("GET", "/groups/:id/saml/:uid"): "software-supply-chain-security#retrieve-a-single-saml-identity",
    ("GET", "/groups/:id/saml/identities"): "software-supply-chain-security#list-all-saml-identities-for-a-group",
    ("GET", "/groups/:id/saml_group_links"): "software-supply-chain-security#list-all-saml-group-links",
    (
        "GET",
        "/groups/:id/saml_group_links/:saml_group_name",
    ): "software-supply-chain-security#retrieve-a-saml-group-link",
    ("GET", "/groups/:id/service_accounts"): "software-supply-chain-security#list-all-group-service-accounts",
    ("GET", "/groups/:id/service_accounts/:user_id"): "software-supply-chain-security#retrieve-a-group-service-account",
    ("GET", "/groups/:id/service_accounts/:user_id/personal_access_tokens"): (
        "software-supply-chain-security#list-all-personal-access-tokens-for-a-group-service-account"
    ),
    ("GET", "/member_roles"): "software-supply-chain-security#get-all-instance-member-roles",
    ("GET", "/personal_access_tokens"): "software-supply-chain-security#list-all-personal-access-tokens",
    ("GET", "/personal_access_tokens/:id"): "software-supply-chain-security#retrieve-a-personal-access-token",
    ("GET", "/personal_access_tokens/self/associations"): "software-supply-chain-security#list-all-token-associations",
    ("GET", "/projects/:id/access_requests"): (
        "software-supply-chain-security#list-all-access-requests-for-a-group-or-project"
    ),
    ("GET", "/projects/:id/access_tokens"): "software-supply-chain-security#list-all-project-access-tokens",
    ("GET", "/projects/:id/access_tokens/:token_id"): (
        "software-supply-chain-security#retrieve-details-on-a-project-access-token"
    ),
    ("GET", "/projects/:id/audit_events"): "software-supply-chain-security#list-all-project-audit-events",
    ("GET", "/projects/:id/audit_events/:audit_event_id"): (
        "software-supply-chain-security#retrieve-a-project-audit-event"
    ),
    ("GET", "/projects/:id/custom_attributes"): "software-supply-chain-security#list-all-custom-attributes",
    ("GET", "/projects/:id/custom_attributes/:key"): "software-supply-chain-security#retrieve-a-custom-attribute",
    ("GET", "/projects/:id/google_cloud/setup/integrations.sh"): (
        "software-supply-chain-security#script-to-set-up-a-google-cloud-integration"
    ),
    ("GET", "/projects/:id/google_cloud/setup/runner_deployment_project.sh"): (
        "software-supply-chain-security#script-to-configure-a-google-cloud-project-for-runner-provisioning"
    ),
    ("GET", "/projects/:id/google_cloud/setup/wlif.sh"): (
        "software-supply-chain-security#workload-identity-federation-creation-script"
    ),
    ("GET", "/projects/:id/service_accounts"): "software-supply-chain-security#list-all-project-service-accounts",
    ("GET", "/projects/:id/service_accounts/:user_id"): (
        "software-supply-chain-security#retrieve-a-project-service-account"
    ),
    ("GET", "/projects/:id/service_accounts/:user_id/personal_access_tokens"): (
        "software-supply-chain-security#list-all-personal-access-tokens-for-a-project-service-account"
    ),
    ("GET", "/service_accounts"): "software-supply-chain-security#list-all-instance-service-accounts",
    ("GET", "/user/activities"): "software-supply-chain-security#list-a-users-activity",
    ("GET", "/user/applications"): "software-supply-chain-security#list-all-applications-1",
    ("GET", "/user/applications/:id"): "software-supply-chain-security#retrieve-a-specific-application",
    ("GET", "/user/emails"): "software-supply-chain-security#list-all-email-addresses",
    ("GET", "/user/emails/:email_id"): "software-supply-chain-security#retrieve-details-on-an-email-address",
    ("GET", "/user/gpg_keys"): "software-supply-chain-security#list-all-gpg-keys",
    ("GET", "/user/gpg_keys/:key_id"): "software-supply-chain-security#retrieve-a-gpg-key",
    ("GET", "/user/keys"): "software-supply-chain-security#list-all-ssh-keys",
    ("GET", "/user/keys/:key_id"): "software-supply-chain-security#retrieve-an-ssh-key",
    ("GET", "/user/preferences"): "software-supply-chain-security#retrieve-your-user-preferences",
    ("GET", "/user/status"): "software-supply-chain-security#retrieve-your-user-status",
    ("GET", "/user/support_pin"): "software-supply-chain-security#get-details-on-a-support-pin",
    ("GET", "/user_counts"): (
        "software-supply-chain-security#retrieve-a-count-of-your-assigned-issues-merge-requests-and-reviews"
    ),
    ("GET", "/users/:id"): "software-supply-chain-security#retrieve-a-single-user-as-a-regular-user",
    ("GET", "/users/:id/associations_count"): (
        "software-supply-chain-security#retrieve-a-count-of-a-users-projects-groups-issues-and-merge-requests"
    ),
    ("GET", "/users/:id/emails"): "software-supply-chain-security#list-all-email-addresses-for-a-user",
    ("GET", "/users/:id/followers"): "software-supply-chain-security#list-all-accounts-that-follow-a-user",
    ("GET", "/users/:id/following"): "software-supply-chain-security#list-all-accounts-followed-by-a-user",
    ("GET", "/users/:id/gpg_keys"): "software-supply-chain-security#list-all-gpg-keys-for-a-user",
    ("GET", "/users/:id/gpg_keys/:key_id"): "software-supply-chain-security#retrieve-a-gpg-key-for-a-user",
    ("GET", "/users/:id/keys/:key_id"): "software-supply-chain-security#retrieve-an-ssh-key-for-a-user",
    ("GET", "/users/:id/memberships"): (
        "software-supply-chain-security#list-projects-and-groups-that-a-user-is-a-member-of"
    ),
    ("GET", "/users/:id/support_pin"): "software-supply-chain-security#get-a-support-pin-for-a-user",
    ("GET", "/users/:id_or_username/keys"): "software-supply-chain-security#list-all-ssh-keys-for-a-user",
    ("GET", "/users/:id_or_username/status"): "software-supply-chain-security#retrieve-the-status-of-a-user",
    ("GET", "/users/:user_id/impersonation_tokens"): (
        "software-supply-chain-security#list-all-impersonation-tokens-for-a-user"
    ),
    ("GET", "/users/:user_id/impersonation_tokens/:impersonation_token_id"): (
        "software-supply-chain-security#retrieve-an-impersonation-token-for-a-user"
    ),
    ("PATCH", "/groups/:id/enterprise_users/:user_id"): "software-supply-chain-security#update-an-enterprise-user",
    ("PATCH", "/groups/:id/enterprise_users/:user_id/disable_two_factor"): (
        "software-supply-chain-security#disable-two-factor-authentication-for-an-enterprise-user"
    ),
    ("PATCH", "/groups/:id/saml/:uid"): "software-supply-chain-security#update-extern_uid-field-for-a-saml-identity",
    ("PATCH", "/groups/:id/service_accounts/:user_id"): "software-supply-chain-security#update-a-group-service-account",
    ("PATCH", "/projects/:id/service_accounts/:user_id"): (
        "software-supply-chain-security#update-a-project-service-account"
    ),
    ("PATCH", "/service_accounts/:id"): "software-supply-chain-security#update-an-instance-service-account",
    ("PATCH", "/users/:id/disable_two_factor"): (
        "software-supply-chain-security#disable-two-factor-authentication-for-a-user"
    ),
    ("POST", "/admin/token"): "software-supply-chain-security#retrieve-token-information",
    ("POST", "/applications"): "software-supply-chain-security#create-an-application",
    ("POST", "/applications/:id/renew-secret"): "software-supply-chain-security#renew-an-application-secret",
    ("POST", "/groups/:id/access_tokens"): "software-supply-chain-security#create-a-group-access-token",
    (
        "POST",
        "/groups/:id/access_tokens/:token_id/rotate",
    ): "software-supply-chain-security#rotate-a-group-access-token",
    ("POST", "/groups/:id/member_roles"): "software-supply-chain-security#add-a-member-role-to-a-group",
    ("POST", "/groups/:id/saml_group_links"): "software-supply-chain-security#add-a-saml-group-link",
    ("POST", "/groups/:id/service_accounts"): "software-supply-chain-security#create-a-group-service-account",
    ("POST", "/groups/:id/service_accounts/:user_id/personal_access_tokens"): (
        "software-supply-chain-security#create-a-personal-access-token-for-a-group-service-account"
    ),
    ("POST", "/groups/:id/service_accounts/:user_id/personal_access_tokens/:token_id/rotate"): (
        "software-supply-chain-security#rotate-a-personal-access-token-for-a-group-service-account"
    ),
    ("POST", "/member_roles"): "software-supply-chain-security#create-an-instance-member-role",
    ("POST", "/personal_access_tokens/:id/rotate"): "software-supply-chain-security#rotate-a-personal-access-token",
    ("POST", "/projects/:id/access_requests"): "software-supply-chain-security#request-access-to-a-group-or-project",
    ("POST", "/projects/:id/access_tokens"): "software-supply-chain-security#create-a-project-access-token",
    ("POST", "/projects/:id/access_tokens/:token_id/rotate"): (
        "software-supply-chain-security#rotate-a-project-access-token"
    ),
    ("POST", "/projects/:id/service_accounts"): "software-supply-chain-security#create-a-project-service-account",
    ("POST", "/projects/:id/service_accounts/:user_id/personal_access_tokens"): (
        "software-supply-chain-security#create-a-personal-access-token-for-a-project-service-account"
    ),
    ("POST", "/projects/:id/service_accounts/:user_id/personal_access_tokens/:token_id/rotate"): (
        "software-supply-chain-security#rotate-a-personal-access-token-for-a-project-service-account"
    ),
    ("POST", "/service_accounts"): "software-supply-chain-security#create-an-instance-service-account",
    ("POST", "/user/applications"): "software-supply-chain-security#create-an-application-1",
    ("POST", "/user/emails"): "software-supply-chain-security#add-an-email-address",
    ("POST", "/user/gpg_keys"): "software-supply-chain-security#add-a-gpg-key",
    ("POST", "/user/keys"): "software-supply-chain-security#add-an-ssh-key",
    ("POST", "/user/personal_access_tokens"): "software-supply-chain-security#create-a-personal-access-token",
    ("POST", "/user/runners"): "software-supply-chain-security#create-a-runner-linked-to-a-user",
    ("POST", "/user/support_pin"): "software-supply-chain-security#create-a-support-pin",
    ("POST", "/users"): "software-supply-chain-security#create-a-user",
    ("POST", "/users/:id/activate"): "software-supply-chain-security#reactivate-a-user",
    ("POST", "/users/:id/approve"): "software-supply-chain-security#approve-access-to-a-user",
    ("POST", "/users/:id/ban"): "software-supply-chain-security#ban-a-user",
    ("POST", "/users/:id/block"): "software-supply-chain-security#block-access-to-a-user",
    ("POST", "/users/:id/deactivate"): "software-supply-chain-security#deactivate-a-user",
    ("POST", "/users/:id/emails"): "software-supply-chain-security#add-an-email-address-for-a-user",
    ("POST", "/users/:id/follow"): "software-supply-chain-security#follow-a-user",
    ("POST", "/users/:id/gpg_keys"): "software-supply-chain-security#add-a-gpg-key-for-a-user",
    ("POST", "/users/:id/keys"): "software-supply-chain-security#add-an-ssh-key-for-a-user",
    ("POST", "/users/:id/reject"): "software-supply-chain-security#reject-access-to-a-user",
    ("POST", "/users/:id/support_pin/revoke"): "software-supply-chain-security#revoke-a-support-pin-for-a-user",
    ("POST", "/users/:id/unban"): "software-supply-chain-security#unban-a-user",
    ("POST", "/users/:id/unblock"): "software-supply-chain-security#unblock-access-to-a-user",
    ("POST", "/users/:id/unfollow"): "software-supply-chain-security#unfollow-a-user",
    ("POST", "/users/:user_id/impersonation_tokens"): "software-supply-chain-security#create-an-impersonation-token",
    ("POST", "/users/:user_id/personal_access_tokens"): (
        "software-supply-chain-security#create-a-personal-access-token-for-a-user"
    ),
    ("PUT", "/application/appearance"): "software-supply-chain-security#update-application-appearance",
    ("PUT", "/application/plan_limits"): "software-supply-chain-security#update-plan-limits",
    ("PUT", "/application/settings"): "software-supply-chain-security#update-application-settings",
    (
        "PUT",
        "/projects/:id/access_requests/:user_id/approve",
    ): "software-supply-chain-security#approve-an-access-request",
    ("PUT", "/projects/:id/custom_attributes/:key"): "software-supply-chain-security#update-a-custom-attribute",
    ("PUT", "/user/applications/:id"): "software-supply-chain-security#update-an-application",
    ("PUT", "/user/avatar"): "software-supply-chain-security#upload-an-avatar-for-yourself",
    ("PUT", "/user/preferences"): "software-supply-chain-security#update-your-user-preferences",
    ("PUT", "/user/status"): "software-supply-chain-security#set-your-user-status",
    ("PUT", "/users/:id"): "software-supply-chain-security#modify-a-user",
}

# AC-2 (DL-003): the endpoints of the sections with several endpoints that are not their record's — the `/users/:id/`
# and `/groups/:id/` endpoints of the four "Custom Attributes API" sections, the `/groups/:id/` endpoints of the four
# "Group and project access requests API" sections, and `PATCH /user/status` of "Set your user status" — plus the
# `https://HOST` path of "Retrieve the token information" and the endpoint of "Set status of an external control",
# whose required `X-Gitlab-*` request headers #41 does not build.
PENDING_KEYS: FrozenSet[Tuple[str, str]] = frozenset(
    {
        ("GET", "/users/:id/custom_attributes"),
        ("GET", "/groups/:id/custom_attributes"),
        ("GET", "/users/:id/custom_attributes/:key"),
        ("GET", "/groups/:id/custom_attributes/:key"),
        ("PUT", "/users/:id/custom_attributes/:key"),
        ("PUT", "/groups/:id/custom_attributes/:key"),
        ("DELETE", "/users/:id/custom_attributes/:key"),
        ("DELETE", "/groups/:id/custom_attributes/:key"),
        ("GET", "/groups/:id/access_requests"),
        ("POST", "/groups/:id/access_requests"),
        ("PUT", "/groups/:id/access_requests/:user_id/approve"),
        ("DELETE", "/groups/:id/access_requests/:user_id"),
        ("PATCH", "/user/status"),
        ("GET", "https://HOST/oauth/token/info"),
        ("PATCH", "/projects/:id/compliance_external_controls/:external_control_id/status"),
    }
)

# rest/software-supply-chain-security.md: every query, body or form row of a new record whose Kind is not SCALAR, by
# (record ID, attribute name) (AC-4). FILE: the four rows of "Update application appearance" noted "file upload
# (multipart/form-data)", and `avatar` of "Upload an avatar for yourself", "Create a user" and "Modify a user".
# ARRAY_OF_HASHES: `granular_scopes`, Type `array`, with its `granular_scopes[].…` rows. ARRAY: `scopes`, Type
# `Array[String]` or `array`. No row of the page is Type `object`.
TYPED_ATTRIBUTES: Dict[Tuple[str, str], str] = {
    ("software-supply-chain-security#create-a-group-access-token", "scopes"): KIND_ARRAY,
    ("software-supply-chain-security#create-a-personal-access-token", "granular_scopes"): KIND_ARRAY_OF_HASHES,
    ("software-supply-chain-security#create-a-personal-access-token", "scopes"): KIND_ARRAY,
    ("software-supply-chain-security#create-a-personal-access-token-for-a-group-service-account", "scopes"): KIND_ARRAY,
    ("software-supply-chain-security#create-a-personal-access-token-for-a-project-service-account", "scopes"): (
        KIND_ARRAY
    ),
    ("software-supply-chain-security#create-a-personal-access-token-for-a-user", "granular_scopes"): (
        KIND_ARRAY_OF_HASHES
    ),
    ("software-supply-chain-security#create-a-personal-access-token-for-a-user", "scopes"): KIND_ARRAY,
    ("software-supply-chain-security#create-a-project-access-token", "scopes"): KIND_ARRAY,
    ("software-supply-chain-security#create-a-user", "avatar"): KIND_FILE,
    ("software-supply-chain-security#create-an-application", "granular_scopes"): KIND_ARRAY_OF_HASHES,
    ("software-supply-chain-security#create-an-impersonation-token", "granular_scopes"): KIND_ARRAY_OF_HASHES,
    ("software-supply-chain-security#create-an-impersonation-token", "scopes"): KIND_ARRAY,
    ("software-supply-chain-security#modify-a-user", "avatar"): KIND_FILE,
    ("software-supply-chain-security#update-application-appearance", "favicon"): KIND_FILE,
    ("software-supply-chain-security#update-application-appearance", "header_logo"): KIND_FILE,
    ("software-supply-chain-security#update-application-appearance", "logo"): KIND_FILE,
    ("software-supply-chain-security#update-application-appearance", "pwa_icon"): KIND_FILE,
    ("software-supply-chain-security#upload-an-avatar-for-yourself", "avatar"): KIND_FILE,
}

# rest/software-supply-chain-security.md: the query and body rows whose Required reads `yes`, in table order, by new
# record (AC-4). `conditional` is not `yes`, and a `granular_scopes[].…` row is part of `granular_scopes`, no Param.
# No other new record has such a row.
REQUIRED_ATTRIBUTES: Dict[str, FrozenSet[str]] = {
    "software-supply-chain-security#add-a-gpg-key": frozenset({"key"}),
    "software-supply-chain-security#add-a-gpg-key-for-a-user": frozenset({"key"}),
    "software-supply-chain-security#add-a-saml-group-link": frozenset({"saml_group_name", "access_level"}),
    "software-supply-chain-security#add-an-email-address": frozenset({"email"}),
    "software-supply-chain-security#add-an-email-address-for-a-user": frozenset({"email"}),
    "software-supply-chain-security#add-an-ssh-key": frozenset({"title", "key"}),
    "software-supply-chain-security#add-an-ssh-key-for-a-user": frozenset({"title", "key"}),
    "software-supply-chain-security#create-a-group-access-token": frozenset({"name", "scopes"}),
    "software-supply-chain-security#create-a-personal-access-token": frozenset({"name"}),
    "software-supply-chain-security#create-a-personal-access-token-for-a-group-service-account": frozenset(
        {"name", "scopes"}
    ),
    "software-supply-chain-security#create-a-personal-access-token-for-a-project-service-account": frozenset(
        {"name", "scopes"}
    ),
    "software-supply-chain-security#create-a-personal-access-token-for-a-user": frozenset({"name"}),
    "software-supply-chain-security#create-a-project-access-token": frozenset({"name", "scopes"}),
    "software-supply-chain-security#create-a-runner-linked-to-a-user": frozenset({"runner_type"}),
    "software-supply-chain-security#create-a-user": frozenset({"username", "name", "email"}),
    "software-supply-chain-security#create-an-application": frozenset({"name", "redirect_uri", "scopes"}),
    "software-supply-chain-security#create-an-application-1": frozenset({"name", "redirect_uri", "scopes"}),
    "software-supply-chain-security#create-an-impersonation-token": frozenset({"name", "expires_at"}),
    "software-supply-chain-security#create-an-instance-member-role": frozenset({"name", "base_access_level"}),
    "software-supply-chain-security#retrieve-token-information": frozenset({"token"}),
    "software-supply-chain-security#retrieve-user-account-avatar": frozenset({"email"}),
    "software-supply-chain-security#revoke-a-token": frozenset({"token"}),
    "software-supply-chain-security#script-to-configure-a-google-cloud-project-for-runner-provisioning": frozenset(
        {"google_cloud_project_id"}
    ),
    "software-supply-chain-security#script-to-set-up-a-google-cloud-integration": frozenset(
        {"enable_google_cloud_artifact_registry", "google_cloud_artifact_registry_project_id"}
    ),
    "software-supply-chain-security#update-a-custom-attribute": frozenset({"value"}),
    "software-supply-chain-security#update-plan-limits": frozenset({"plan_name"}),
    "software-supply-chain-security#update-your-user-preferences": frozenset(
        {"view_diffs_file_by_file", "show_whitespace_in_diffs", "pass_user_identities_to_ci_jwt"}
    ),
    "software-supply-chain-security#upload-an-avatar-for-yourself": frozenset({"avatar"}),
    "software-supply-chain-security#workload-identity-federation-creation-script": frozenset(
        {"google_cloud_project_id"}
    ),
}

# rest/software-supply-chain-security.md: every `GET` section of a new record headed "List" or "Get all" but
# `#list-all-token-associations` (AC-5), with its record's path — the section's endpoint, or of several the one under
# `/projects/:id/` (AC-1).
LIST_ENDPOINTS: Tuple[Tuple[str, str], ...] = (
    ("software-supply-chain-security#get-all-group-member-roles", "/groups/:id/member_roles"),
    ("software-supply-chain-security#get-all-instance-member-roles", "/member_roles"),
    ("software-supply-chain-security#list-a-users-activity", "/user/activities"),
    (
        "software-supply-chain-security#list-all-access-requests-for-a-group-or-project",
        "/projects/:id/access_requests",
    ),
    ("software-supply-chain-security#list-all-accounts-followed-by-a-user", "/users/:id/following"),
    ("software-supply-chain-security#list-all-accounts-that-follow-a-user", "/users/:id/followers"),
    ("software-supply-chain-security#list-all-applications", "/applications"),
    ("software-supply-chain-security#list-all-applications-1", "/user/applications"),
    ("software-supply-chain-security#list-all-custom-attributes", "/projects/:id/custom_attributes"),
    ("software-supply-chain-security#list-all-email-addresses", "/user/emails"),
    ("software-supply-chain-security#list-all-email-addresses-for-a-user", "/users/:id/emails"),
    ("software-supply-chain-security#list-all-enterprise-users", "/groups/:id/enterprise_users"),
    ("software-supply-chain-security#list-all-gpg-keys", "/user/gpg_keys"),
    ("software-supply-chain-security#list-all-gpg-keys-for-a-user", "/users/:id/gpg_keys"),
    ("software-supply-chain-security#list-all-group-access-tokens", "/groups/:id/access_tokens"),
    ("software-supply-chain-security#list-all-group-audit-events", "/groups/:id/audit_events"),
    ("software-supply-chain-security#list-all-group-service-accounts", "/groups/:id/service_accounts"),
    ("software-supply-chain-security#list-all-impersonation-tokens-for-a-user", "/users/:user_id/impersonation_tokens"),
    ("software-supply-chain-security#list-all-instance-audit-events", "/audit_events"),
    ("software-supply-chain-security#list-all-instance-service-accounts", "/service_accounts"),
    ("software-supply-chain-security#list-all-personal-access-tokens", "/personal_access_tokens"),
    (
        "software-supply-chain-security#list-all-personal-access-tokens-for-a-group-service-account",
        "/groups/:id/service_accounts/:user_id/personal_access_tokens",
    ),
    (
        "software-supply-chain-security#list-all-personal-access-tokens-for-a-project-service-account",
        "/projects/:id/service_accounts/:user_id/personal_access_tokens",
    ),
    ("software-supply-chain-security#list-all-project-access-tokens", "/projects/:id/access_tokens"),
    ("software-supply-chain-security#list-all-project-audit-events", "/projects/:id/audit_events"),
    ("software-supply-chain-security#list-all-project-service-accounts", "/projects/:id/service_accounts"),
    ("software-supply-chain-security#list-all-saml-group-links", "/groups/:id/saml_group_links"),
    ("software-supply-chain-security#list-all-saml-identities-for-a-group", "/groups/:id/saml/identities"),
    ("software-supply-chain-security#list-all-ssh-keys", "/user/keys"),
    ("software-supply-chain-security#list-all-ssh-keys-for-a-user", "/users/:id_or_username/keys"),
    (
        "software-supply-chain-security#list-projects-and-groups-that-a-user-is-a-member-of",
        "/users/:id/memberships",
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
    """``name`` (``gitlab_api.registry``, ``gitlab_api.families.software_supply_chain_security``) imported inside a
    test, as ``test/test_gitlab_wrapper_coverage.py`` imports the registry: while it is absent the test fails on this
    assertion."""
    parts = name.split(MODULE_SEPARATOR)
    owners = {MODULE_SEPARATOR.join(parts[:count]) for count in range(1, len(parts) + 1)}
    try:
        return importlib.import_module(name=name)
    except ModuleNotFoundError as missing:
        if missing.name not in owners:
            raise
        raise AssertionError(f"{name} is not importable from {SCRIPTS_DIR}: {missing}") from missing


def new_records() -> Tuple[Any, ...]:
    """The family's records but part 1's, in declaration order."""
    family = gitlab_module(name=FAMILY_MODULE)
    return tuple(record for record in family.OPERATIONS if record.operation_id not in PART_ONE_IDS)


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


def repeated(*, items: Sequence[Any]) -> List[Any]:
    """Every item ``items`` holds more than once, sorted."""
    return sorted({item for item in items if items.count(item) > 1})


def path_values(*, path: str) -> Dict[str, str]:
    """A distinct number for each placeholder of ``path``, in path order: ``101``, ``102``, ..."""
    names = dict.fromkeys(match.group(GROUP_NAME) for match in PLACEHOLDER.finditer(string=path))
    return {name: str(FIRST_PATH_VALUE + position) for position, name in enumerate(names)}


def expanded(*, path: str, values: Mapping[str, str]) -> str:
    """``path`` with each placeholder replaced by its value (the values are digits, so nothing is encoded)."""
    return PLACEHOLDER.sub(repl=lambda match: values[match.group(GROUP_NAME)], string=path)


def run_call(*, root: Path, argv: Sequence[str]) -> Any:
    """Write ``config/gitlab.json`` (hostname the fake host's) under ``root``, the working directory, and return the
    exit code of the product's ``main(argv=["call", *argv])``."""
    config: Dict[str, Any] = {FIELD_HOSTNAME: fixtures.HOST, FIELD_PROJECT_ID: PROJECT_ID, FIELD_TOKEN: TOKEN}
    fixtures.write_config(root=root, config=config)
    return fixtures.run_main(wrapper=fixtures.load_wrapper(module_name=WRAPPER_MODULE), argv=[CALL, *argv])


def script_page(*, fake: Any, url: str, item: Mapping[str, Any], next_page: str) -> None:
    """Script one JSON page for ``GET url``: a one-item array, ``x-next-page`` set to ``next_page``."""
    fake.script(
        method=METHOD_GET,
        url=url,
        headers=((HEADER_CONTENT_TYPE, CONTENT_TYPE_JSON), (HEADER_NEXT_PAGE, next_page)),
        body=json.dumps(obj=[item]).encode(encoding=TEXT_ENCODING),
    )


def printed_json(*, value: Any) -> str:
    """``value`` as ``commands/_common.print_json`` writes it."""
    return json.dumps(obj=value, indent=JSON_INDENT) + LINE_END


def list_params() -> List[Any]:
    """One case per entry of ``LIST_ENDPOINTS``, named by its anchor."""
    return [
        pytest.param(operation_id, path, id=operation_id.partition(ID_SEPARATOR)[2])
        for operation_id, path in LIST_ENDPOINTS
    ]


# --- AC-1, AC-2: the records and what stays pending -------------------------------------------------------------


def test_every_key_has_its_record() -> None:
    """AC-1: each key ``PENDING`` held at 3beba95 but AC-2's is the method and path of one new record, whose ID is the
    Reference of one of its rows; no key and no ID is declared twice."""
    family = gitlab_module(name=FAMILY_MODULE)
    keys = [(record.method, record.path) for record in family.OPERATIONS]
    assert repeated(items=keys) == [], f"keys declared by more than one record: {repeated(items=keys)}"
    operation_ids = [record.operation_id for record in family.OPERATIONS]
    assert repeated(items=operation_ids) == [], f"IDs declared more than once: {repeated(items=operation_ids)}"
    declared = {(record.method, record.path): record.operation_id for record in new_records()}
    assert declared == KEY_IDS, "the new records are not the pending keys and their References (AC-1):\n" + (
        mapping_difference(declared=declared, expected=KEY_IDS)
    )


def test_only_the_unmapped_keys_are_pending() -> None:
    """AC-2: ``PENDING`` is exactly the second endpoints, the ``https://HOST`` path and the external control's
    status ``PATCH``."""
    family = gitlab_module(name=FAMILY_MODULE)
    pending = frozenset(family.PENDING)
    assert pending == PENDING_KEYS, "software_supply_chain_security.PENDING is not the keys AC-2 keeps pending:\n" + (
        set_difference(declared=pending, expected=PENDING_KEYS)
    )


# --- AC-3: body and fixed ---------------------------------------------------------------------------------------------


def test_every_body_is_json_and_unfixed() -> None:
    """AC-3: every record of ``OPERATIONS``, part 1's two included (they comply too), has ``body``
    ``BodyFormat.JSON`` and ``fixed`` empty; a family declaring no record fails, as the clause would then hold of
    nothing."""
    registry = gitlab_module(name=REGISTRY)
    family = gitlab_module(name=FAMILY_MODULE)
    records = tuple(family.OPERATIONS)
    assert records, f"{FAMILY_MODULE}.OPERATIONS declares no record, so no body or fixed is checked (AC-3)"
    offending = sorted(
        f"{record.operation_id}: body {record.body!r}, fixed {record.fixed!r}"
        for record in records
        if record.body is not registry.BodyFormat.JSON or record.fixed != ()
    )
    assert offending == [], "records whose body is not BodyFormat.JSON or whose fixed is not empty (AC-3):\n" + (
        "\n".join(offending)
    )


# --- AC-4: kinds and required attributes ------------------------------------------------------------------------


def test_every_kind_is_its_rows_type() -> None:
    """AC-4: every ``Param`` of a new record that is not ``SCALAR``, with its ``Kind``, is the table's non-SCALAR
    row."""
    registry = gitlab_module(name=REGISTRY)
    declared = {
        (record.operation_id, param.name): param.kind.name
        for record in new_records()
        for param in record.params
        if param.kind is not registry.Kind.SCALAR
    }
    assert declared == TYPED_ATTRIBUTES, "the non-SCALAR Params are not the sections' (AC-4):\n" + (
        mapping_difference(declared=declared, expected=TYPED_ATTRIBUTES)
    )


def test_the_required_attributes_are_the_sections() -> None:
    """AC-4: ``{operation_id: names}`` of the ``required`` ``Param``s, over the new records with any, is the table of
    the Required ``yes`` query and body rows."""
    required = {
        record.operation_id: frozenset(param.name for param in record.params if param.required)
        for record in new_records()
    }
    declared = {operation_id: names for operation_id, names in required.items() if names}
    assert declared == REQUIRED_ATTRIBUTES, "the required Params are not the sections' `yes` rows (AC-4):\n" + (
        mapping_difference(declared=declared, expected=REQUIRED_ATTRIBUTES)
    )


# --- AC-5, AC-7: the list records -----------------------------------------------------------------------------------


def test_every_list_record_has_a_case() -> None:
    """AC-5: the new ``Paging.OFFSET`` records are exactly ``LIST_ENDPOINTS``' IDs, and no record is
    ``Paging.KEYSET``."""
    registry = gitlab_module(name=REGISTRY)
    family = gitlab_module(name=FAMILY_MODULE)
    offset = {record.operation_id for record in new_records() if record.paging is registry.Paging.OFFSET}
    expected = {operation_id for operation_id, _ in LIST_ENDPOINTS}
    assert offset == expected, "the Paging.OFFSET records are not the sections' lists (AC-5):\n" + set_difference(
        declared=offset, expected=expected
    )
    keyset = sorted(record.operation_id for record in family.OPERATIONS if record.paging is registry.Paging.KEYSET)
    assert keyset == [], f"no software-supply-chain-security list is keyset-paged (AC-5), yet KEYSET: {keyset}"


@pytest.mark.parametrize(argnames=("operation_id", "path"), argvalues=list_params())
def test_a_list_record_prints_every_item(
    operation_id: str, path: str, project: Path, fake_gitlab: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-7: ``call <id> --path NAME=VALUE ...`` against two pages chained by ``x-next-page`` exits 0, requests both
    pages at their exact URLs and prints both items as one JSON array."""
    values = path_values(path=path)
    argv = [
        operation_id,
        *(part for name, value in values.items() for part in (OPTION_PATH, f"{name}{ASSIGNED}{value}")),
    ]
    first_url = f"{REST_BASE}{expanded(path=path, values=values)}?{FIRST_PAGE_QUERY}"
    next_url = f"{first_url}&{NEXT_PAGE_QUERY}"
    script_page(fake=fake_gitlab, url=first_url, item=PAGE_ITEMS[0], next_page=NEXT_PAGE)
    script_page(fake=fake_gitlab, url=next_url, item=PAGE_ITEMS[1], next_page=LAST_PAGE)
    code = run_call(root=project, argv=argv)
    captured = capsys.readouterr()
    assert code == EXIT_OK, f"call {argv} exits {EXIT_OK}, got {code}; stderr:\n{captured.err}"
    assert [(request.method, request.url) for request in fake_gitlab.requests] == [
        (METHOD_GET, first_url),
        (METHOD_GET, next_url),
    ], "each page requested as Transport.pages does (#13 AC-2.5)"
    assert fake_gitlab.remaining() == [], "every scripted page was served"
    assert captured.out == printed_json(value=list(PAGE_ITEMS)), (
        f"one JSON array of both items, in page order, as print_json writes it (AC-7):\n{captured.out}"
    )
