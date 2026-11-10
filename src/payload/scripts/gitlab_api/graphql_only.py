"""The GraphQL-only capabilities of the GitLab wrapper: ``GraphQLOperation`` records that belong to no REST family.

``registry.lookup`` reads ``OPERATIONS`` beside every family module's records. Part 1 (issue #13) declares none; the
"Only in GraphQL" capabilities get their records here in part 2 (#15).
"""

from __future__ import annotations

from typing import Tuple

from gitlab_api.registry import GraphQLOperation

OPERATIONS: Tuple[GraphQLOperation, ...] = ()
