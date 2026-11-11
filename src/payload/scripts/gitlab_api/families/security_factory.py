"""The ``security-factory`` endpoint family of the GitLab wrapper: project dependencies, license templates and the
project security settings.

Each record is transcribed from the attribute table of its section of
``docs/api-reference/gitlab/rest/security-factory.md`` (issue #13, design.md D1 and D5; issue #42, ``change.md`` AC-1
to AC-5): the method, the path as ``operations-index.md`` writes it, and one ``Param`` per query or body attribute with
the table's Type column as its ``Kind`` (``package_manager``, a ``string array``, is ``Kind.ARRAY``) and ``required``
where Required reads ``yes``.
Every section has one endpoint and every index key one row, so each key has one record, its ID the row's Reference. A
``GET`` section headed "List" is ``Paging.OFFSET`` but "List all project security settings", which answers one object.
``PENDING`` is empty: no key of the family is left unmapped.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import Kind, Location, Paging, Param, RestOperation

FAMILY = "security-factory"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "Dependencies API: List project dependencies".
    RestOperation(
        operation_id="security-factory#list-project-dependencies",
        method="GET",
        path="/projects/:id/dependencies",
        params=(Param(name="package_manager", location=Location.QUERY, kind=Kind.ARRAY),),
        paging=Paging.OFFSET,
    ),
    # "Licenses API: List all license templates".
    RestOperation(
        operation_id="security-factory#list-all-license-templates",
        method="GET",
        path="/templates/licenses",
        params=(Param(name="popular", location=Location.QUERY),),
        paging=Paging.OFFSET,
    ),
    # "Licenses API: Retrieve a single license template".
    RestOperation(
        operation_id="security-factory#retrieve-a-single-license-template",
        method="GET",
        path="/templates/licenses/:key",
        params=(
            Param(name="project", location=Location.QUERY),
            Param(name="fullname", location=Location.QUERY),
        ),
    ),
    # "Project security settings API: List all project security settings"; it answers one object, so the record is
    # not paged.
    RestOperation(
        operation_id="security-factory#list-all-project-security-settings",
        method="GET",
        path="/projects/:id/security_settings",
    ),
    # "Project security settings API: Update the `secret_push_protection_enabled` setting".
    RestOperation(
        operation_id="security-factory#update-the-secret_push_protection_enabled-setting",
        method="PUT",
        path="/projects/:id/security_settings",
        params=(Param(name="secret_push_protection_enabled", location=Location.BODY, required=True),),
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset()
