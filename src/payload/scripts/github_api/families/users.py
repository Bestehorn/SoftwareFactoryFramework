"""The ``users`` family of the GitHub operations index: the one record the claim commands send (design D5).

``users/get-authenticated`` is the index row ``GET /user``, whose ``rest/users.md`` section documents no query or
body parameter; ``start-issue``, ``release-issue`` and the ``label-add``, ``label-remove``, ``assign`` row of D5's
table read the authenticated account through it.

Every other operation ID of the family is on ``PENDING`` until a record covers it (part 2, #14).
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
)

PENDING: FrozenSet[str] = frozenset(
    {
        "users/add-email-for-authenticated-user",
        "users/add-social-account-for-authenticated-user",
        "users/block",
        "users/check-blocked",
        "users/check-following-for-user",
        "users/check-person-is-followed-by-authenticated",
        "users/create-gpg-key-for-authenticated-user",
        "users/create-public-ssh-key-for-authenticated-user",
        "users/create-ssh-signing-key-for-authenticated-user",
        "users/delete-attestations-bulk",
        "users/delete-attestations-by-id",
        "users/delete-attestations-by-subject-digest",
        "users/delete-email-for-authenticated-user",
        "users/delete-gpg-key-for-authenticated-user",
        "users/delete-public-ssh-key-for-authenticated-user",
        "users/delete-social-account-for-authenticated-user",
        "users/delete-ssh-signing-key-for-authenticated-user",
        "users/follow",
        "users/get-by-id",
        "users/get-by-username",
        "users/get-context-for-user",
        "users/get-gpg-key-for-authenticated-user",
        "users/get-public-ssh-key-for-authenticated-user",
        "users/get-ssh-signing-key-for-authenticated-user",
        "users/list",
        "users/list-attestations",
        "users/list-attestations-bulk",
        "users/list-blocked-by-authenticated-user",
        "users/list-emails-for-authenticated-user",
        "users/list-followed-by-authenticated-user",
        "users/list-followers-for-authenticated-user",
        "users/list-followers-for-user",
        "users/list-following-for-user",
        "users/list-gpg-keys-for-authenticated-user",
        "users/list-gpg-keys-for-user",
        "users/list-public-emails-for-authenticated-user",
        "users/list-public-keys-for-user",
        "users/list-public-ssh-keys-for-authenticated-user",
        "users/list-social-accounts-for-authenticated-user",
        "users/list-social-accounts-for-user",
        "users/list-ssh-signing-keys-for-authenticated-user",
        "users/list-ssh-signing-keys-for-user",
        "users/set-primary-email-visibility-for-authenticated-user",
        "users/unblock",
        "users/unfollow",
        "users/update-authenticated",
    }
)
