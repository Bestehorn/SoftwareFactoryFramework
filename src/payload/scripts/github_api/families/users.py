"""The ``users`` family of the GitHub operations index: accounts, and their blocks, emails, followers, GPG and SSH keys,
social accounts and attestations.

``users/get-authenticated`` is the index row ``GET /user``, whose ``rest/users.md`` section documents no query or
body parameter; ``start-issue``, ``release-issue`` and the ``label-add``, ``label-remove``, ``assign`` row of D5's
table read the authenticated account through it.

Every other record is the section of ``docs/api-reference/github/rest/users.md`` its operation ID names: its method and
path, the names of its ``query`` rows, and the first-level fields of its request body, a leading variant label removed
(``{variant 1}.emails`` is ``emails``). ``subject_digest`` of ``users/list-attestations`` and
``users/delete-attestations-by-subject-digest`` is the family's one path parameter whose row reads "may contain ``/``
(multi-segment path)" (``conventions.md`` "Path parameters"): its value keeps its ``/`` (``sha256/<hex>``). Every
``GET`` section with a ``Paging:`` line pages by ``link``: ``users/list-attestations`` with its items in
``attestations`` (``conventions.md`` "Lists wrapped in an object"), every other one a bare array with no item key.
``users/list-attestations-bulk`` is a ``POST`` that pages by cursor without a ``Link`` header, so it sends one request
(#28 D3), as every other record does.

Every record is sent by ``call <operation-id>`` (#28). No operation of the family is pending.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from github_api.registry import Paging, RestOperation
from github_api.transport import ACCEPT_JSON, API_VERSION_DEFAULT

FAMILY = "users"

OPERATIONS: Tuple[RestOperation, ...] = (
    RestOperation(
        operation_id="users/get-authenticated",
        method="GET",
        path="/user",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "List attestations by bulk subject digests": a POST that pages by cursor without a ``Link`` header,
    # so it sends one request (#28 D3); query ``per_page``, ``before``, ``after``; body ``subject_digests`` and
    # ``predicate_type``.
    RestOperation(
        operation_id="users/list-attestations-bulk",
        method="POST",
        path="/users/{username}/attestations/bulk-list",
        query_params=frozenset({"per_page", "before", "after"}),
        body_params=frozenset({"subject_digests", "predicate_type"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Delete attestations in bulk": body ``{variant 1}.subject_digests`` or
    # ``{variant 2}.attestation_ids``.
    RestOperation(
        operation_id="users/delete-attestations-bulk",
        method="POST",
        path="/users/{username}/attestations/delete-request",
        query_params=frozenset(),
        body_params=frozenset({"subject_digests", "attestation_ids"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Delete attestations by subject digest": ``subject_digest`` may contain ``/``.
    RestOperation(
        operation_id="users/delete-attestations-by-subject-digest",
        method="DELETE",
        path="/users/{username}/attestations/digest/{subject_digest}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset({"subject_digest"}),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Delete attestations by ID": path parameters only.
    RestOperation(
        operation_id="users/delete-attestations-by-id",
        method="DELETE",
        path="/users/{username}/attestations/{attestation_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "List attestations": ``subject_digest`` may contain ``/``; cursor-based, items in
    # ``attestations``.
    RestOperation(
        operation_id="users/list-attestations",
        method="GET",
        path="/users/{username}/attestations/{subject_digest}",
        query_params=frozenset({"per_page", "before", "after", "predicate_type"}),
        body_params=frozenset(),
        multi_segment=frozenset({"subject_digest"}),
        paging=Paging.LINK,
        item_key="attestations",
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "List users blocked by the authenticated user": page-based, the body is the array.
    RestOperation(
        operation_id="users/list-blocked-by-authenticated-user",
        method="GET",
        path="/user/blocks",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Check if a user is blocked by the authenticated user": path parameters only; 204 when blocked.
    RestOperation(
        operation_id="users/check-blocked",
        method="GET",
        path="/user/blocks/{username}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Block a user": path parameters only, no body; 204 on success.
    RestOperation(
        operation_id="users/block",
        method="PUT",
        path="/user/blocks/{username}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Unblock a user": path parameters only; 204 on success.
    RestOperation(
        operation_id="users/unblock",
        method="DELETE",
        path="/user/blocks/{username}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Set primary email visibility for the authenticated user": body ``visibility``.
    RestOperation(
        operation_id="users/set-primary-email-visibility-for-authenticated-user",
        method="PATCH",
        path="/user/email/visibility",
        query_params=frozenset(),
        body_params=frozenset({"visibility"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "List email addresses for the authenticated user": page-based, the body is the array.
    RestOperation(
        operation_id="users/list-emails-for-authenticated-user",
        method="GET",
        path="/user/emails",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Add an email address for the authenticated user": body ``{variant 1}.emails``.
    RestOperation(
        operation_id="users/add-email-for-authenticated-user",
        method="POST",
        path="/user/emails",
        query_params=frozenset(),
        body_params=frozenset({"emails"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Delete an email address for the authenticated user": body ``{variant 1}.emails``; 204 on success.
    RestOperation(
        operation_id="users/delete-email-for-authenticated-user",
        method="DELETE",
        path="/user/emails",
        query_params=frozenset(),
        body_params=frozenset({"emails"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "List public email addresses for the authenticated user": page-based, the body is the array.
    RestOperation(
        operation_id="users/list-public-emails-for-authenticated-user",
        method="GET",
        path="/user/public_emails",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "List followers of the authenticated user": page-based, the body is the array.
    RestOperation(
        operation_id="users/list-followers-for-authenticated-user",
        method="GET",
        path="/user/followers",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "List the people the authenticated user follows": page-based, the body is the array.
    RestOperation(
        operation_id="users/list-followed-by-authenticated-user",
        method="GET",
        path="/user/following",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Check if a person is followed by the authenticated user": path parameters only; 204 when followed.
    RestOperation(
        operation_id="users/check-person-is-followed-by-authenticated",
        method="GET",
        path="/user/following/{username}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Follow a user": path parameters only, no body; 204 on success.
    RestOperation(
        operation_id="users/follow",
        method="PUT",
        path="/user/following/{username}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Unfollow a user": path parameters only; 204 on success.
    RestOperation(
        operation_id="users/unfollow",
        method="DELETE",
        path="/user/following/{username}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "List followers of a user": page-based, the body is the array.
    RestOperation(
        operation_id="users/list-followers-for-user",
        method="GET",
        path="/users/{username}/followers",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "List the people a user follows": page-based, the body is the array.
    RestOperation(
        operation_id="users/list-following-for-user",
        method="GET",
        path="/users/{username}/following",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Check if a user follows another user": path parameters only; 204 when it does.
    RestOperation(
        operation_id="users/check-following-for-user",
        method="GET",
        path="/users/{username}/following/{target_user}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "List GPG keys for the authenticated user": page-based, the body is the array.
    RestOperation(
        operation_id="users/list-gpg-keys-for-authenticated-user",
        method="GET",
        path="/user/gpg_keys",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Create a GPG key for the authenticated user": body ``name`` and ``armored_public_key``.
    RestOperation(
        operation_id="users/create-gpg-key-for-authenticated-user",
        method="POST",
        path="/user/gpg_keys",
        query_params=frozenset(),
        body_params=frozenset({"name", "armored_public_key"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Get a GPG key for the authenticated user": path parameters only; 200 with a ``gpg-key``.
    RestOperation(
        operation_id="users/get-gpg-key-for-authenticated-user",
        method="GET",
        path="/user/gpg_keys/{gpg_key_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Delete a GPG key for the authenticated user": path parameters only; 204 on success.
    RestOperation(
        operation_id="users/delete-gpg-key-for-authenticated-user",
        method="DELETE",
        path="/user/gpg_keys/{gpg_key_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "List GPG keys for a user": page-based, the body is the array.
    RestOperation(
        operation_id="users/list-gpg-keys-for-user",
        method="GET",
        path="/users/{username}/gpg_keys",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "List public SSH keys for the authenticated user": page-based, the body is the array.
    RestOperation(
        operation_id="users/list-public-ssh-keys-for-authenticated-user",
        method="GET",
        path="/user/keys",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Create a public SSH key for the authenticated user": body ``title`` and ``key``.
    RestOperation(
        operation_id="users/create-public-ssh-key-for-authenticated-user",
        method="POST",
        path="/user/keys",
        query_params=frozenset(),
        body_params=frozenset({"title", "key"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Get a public SSH key for the authenticated user": path parameters only; 200 with a ``key``.
    RestOperation(
        operation_id="users/get-public-ssh-key-for-authenticated-user",
        method="GET",
        path="/user/keys/{key_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Delete a public SSH key for the authenticated user": path parameters only; 204 on success.
    RestOperation(
        operation_id="users/delete-public-ssh-key-for-authenticated-user",
        method="DELETE",
        path="/user/keys/{key_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "List public keys for a user": page-based, the body is the array.
    RestOperation(
        operation_id="users/list-public-keys-for-user",
        method="GET",
        path="/users/{username}/keys",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "List social accounts for the authenticated user": page-based, the body is the array.
    RestOperation(
        operation_id="users/list-social-accounts-for-authenticated-user",
        method="GET",
        path="/user/social_accounts",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Add social accounts for the authenticated user": body ``account_urls``.
    RestOperation(
        operation_id="users/add-social-account-for-authenticated-user",
        method="POST",
        path="/user/social_accounts",
        query_params=frozenset(),
        body_params=frozenset({"account_urls"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Delete social accounts for the authenticated user": body ``account_urls``; 204 on success.
    RestOperation(
        operation_id="users/delete-social-account-for-authenticated-user",
        method="DELETE",
        path="/user/social_accounts",
        query_params=frozenset(),
        body_params=frozenset({"account_urls"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "List social accounts for a user": page-based, the body is the array.
    RestOperation(
        operation_id="users/list-social-accounts-for-user",
        method="GET",
        path="/users/{username}/social_accounts",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "List SSH signing keys for the authenticated user": page-based, the body is the array.
    RestOperation(
        operation_id="users/list-ssh-signing-keys-for-authenticated-user",
        method="GET",
        path="/user/ssh_signing_keys",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Create a SSH signing key for the authenticated user": body ``title`` and ``key``.
    RestOperation(
        operation_id="users/create-ssh-signing-key-for-authenticated-user",
        method="POST",
        path="/user/ssh_signing_keys",
        query_params=frozenset(),
        body_params=frozenset({"title", "key"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Get an SSH signing key for the authenticated user": path parameters only; 200 with a
    # ``ssh-signing-key``.
    RestOperation(
        operation_id="users/get-ssh-signing-key-for-authenticated-user",
        method="GET",
        path="/user/ssh_signing_keys/{ssh_signing_key_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Delete an SSH signing key for the authenticated user": path parameters only; 204 on success.
    RestOperation(
        operation_id="users/delete-ssh-signing-key-for-authenticated-user",
        method="DELETE",
        path="/user/ssh_signing_keys/{ssh_signing_key_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "List SSH signing keys for a user": page-based, the body is the array.
    RestOperation(
        operation_id="users/list-ssh-signing-keys-for-user",
        method="GET",
        path="/users/{username}/ssh_signing_keys",
        query_params=frozenset({"per_page", "page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Update the authenticated user": the first-level body fields; 200 with a ``private-user``.
    RestOperation(
        operation_id="users/update-authenticated",
        method="PATCH",
        path="/user",
        query_params=frozenset(),
        body_params=frozenset({"name", "email", "blog", "twitter_username", "company", "location", "hireable", "bio"}),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Get a user using their ID": path parameters only.
    RestOperation(
        operation_id="users/get-by-id",
        method="GET",
        path="/user/{account_id}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "List users": ``since`` is an ID cursor, ``per_page`` the page size; the body is the array.
    RestOperation(
        operation_id="users/list",
        method="GET",
        path="/users",
        query_params=frozenset({"since", "per_page"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.LINK,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Get a user": path parameters only.
    RestOperation(
        operation_id="users/get-by-username",
        method="GET",
        path="/users/{username}",
        query_params=frozenset(),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
    # rest/users.md "Get contextual information for a user": query ``subject_type`` and ``subject_id``.
    RestOperation(
        operation_id="users/get-context-for-user",
        method="GET",
        path="/users/{username}/hovercard",
        query_params=frozenset({"subject_type", "subject_id"}),
        body_params=frozenset(),
        multi_segment=frozenset(),
        paging=Paging.NONE,
        item_key=None,
        api_version=API_VERSION_DEFAULT,
        accept=ACCEPT_JSON,
    ),
)

PENDING: FrozenSet[str] = frozenset()
