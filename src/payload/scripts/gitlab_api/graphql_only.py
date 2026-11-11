"""The GraphQL-only capabilities of the GitLab wrapper: ``GraphQLOperation`` records that belong to no REST family
(issue #44, design.md D1, D2, D6).

``registry.lookup`` reads ``OPERATIONS`` beside every family module's records. ``OPERATIONS`` holds one record per
query and per mutation that a row of the table under ``### Only in GraphQL`` in
``docs/api-reference/gitlab/graphql/conventions.md`` names, so a capability has as many records as it has operations,
and each record's ``capability`` is its row's first cell, verbatim. The coverage rule (issue #41, design D6) has no
exclusion: every first cell is served by a record or held in ``PENDING_CAPABILITIES``, and neither names a capability
the table lacks (``test/test_gitlab_wrapper_coverage.py``). Every row is served, so ``PENDING_CAPABILITIES`` is empty.

A record's operation ID is ``graphql#`` followed by the member as the row's code span writes it, without arguments or
selection: a mutation (``graphql#branchRuleCreate``), a root field (``graphql#workItem``, or
``graphql#Query.vulnerabilities`` where the row names the type), or ``<Type>.<field>``
(``graphql#Project.branchRules``); ``graphql#WorkItem.widgets`` is row 2's ``WorkItem`` with its ``widgets``. No REST
ID starts with ``graphql#``: a REST ID's stem is a ``rest/<stem>.md`` page, and no page is ``rest/graphql.md``.

Each document is one unnamed ``query`` or ``mutation``:

- A query selects its root field and the fields below it, each argument a ``$variable`` the caller gives or a
  constant; a variable the caller leaves out leaves its argument out. A query that pages a connection selects it along
  one path, whose keys are its ``connection``: the path's last field takes ``first: 100`` and ``after: $after`` and
  selects ``nodes`` and ``pageInfo { hasNextPage endCursor }``, and ``Transport.graphql_nodes`` sets ``$after`` on
  every page. A query without a ``connection`` prints its ``data``.
- A mutation is ``mutation($input: <I>!) { <m>(input: $input) { <selection> errors } }``, ``<I>`` the input type of
  ``<m>``'s signature line in the reference; the caller gives the whole input object as its one variable, ``input``.
- Three mutations write their input object into the document, each of its fields a variable of its own:
  ``graphql#designManagementUpload`` and ``graphql#workItemsCsvImport``, whose ``Upload`` variable takes its file with
  ``--file``, and ``graphql#pipelineCreate``, whose input holds ``async: true``.

Every mutation selects ``errors`` beside its selection: every payload returns it (``conventions.md`` "Mutations"), and
``transport.graphql_error_messages`` reads it. No record builds a global ID; the caller gives one another record
printed.

``OP_WORK_ITEM_CREATE`` (``graphql#workItemCreate``) and ``OP_WORK_ITEMS_CSV_IMPORT`` (``graphql#workItemsCsvImport``)
are refused by ``commands/call.py``'s ``GATED_OPERATIONS`` before any request, as no subcommand sends them: each record
is declared here, so its capability is served and its document is held to the reference, but it is never sent.

A record whose reference section carries ``Notes: experiment`` or ``Notes: **deprecated**`` says so in its comment.
``test/test_gitlab_graphql_contract.py`` holds every document to ``docs/api-reference/gitlab/graphql/``.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import GraphQLOperation

GRAPHQL_ID_PREFIX = "graphql#"

# The first cells of the "Only in GraphQL" table, verbatim and in the table's order.
CAPABILITY_WORK_ITEMS = "Work items"
CAPABILITY_EPICS = "Epics with new features (assignees, health status, links to other item types)"
CAPABILITY_BRANCH_RULES = "Branch rules"
CAPABILITY_VULNERABILITIES = "Group-wide and instance-wide vulnerability lists"
CAPABILITY_DESIGN_UPLOADS = "Design uploads"
CAPABILITY_ASYNC_PIPELINES = "Asynchronous pipeline creation"
CAPABILITY_CSV_IMPORT = "Work item CSV import"
CAPABILITY_QUERY_COST = "Query cost introspection"

# The two mutations that create work items, refused before any request (design D6); commands/call.py's
# GATED_OPERATIONS reads their IDs.
MUTATION_WORK_ITEM_CREATE = "workItemCreate"
MUTATION_WORK_ITEMS_CSV_IMPORT = "workItemsCsvImport"
OP_WORK_ITEM_CREATE = f"{GRAPHQL_ID_PREFIX}{MUTATION_WORK_ITEM_CREATE}"
OP_WORK_ITEMS_CSV_IMPORT = f"{GRAPHQL_ID_PREFIX}{MUTATION_WORK_ITEMS_CSV_IMPORT}"

# The keys of a connection's path under `data`, each record's `connection`.
FIELD_PROJECT = "project"
FIELD_GROUP = "group"
FIELD_NAMESPACE = "namespace"
FIELD_WORK_ITEMS = "workItems"
FIELD_WORK_ITEMS_BY_REFERENCE = "workItemsByReference"
FIELD_BRANCH_RULES = "branchRules"
FIELD_VULNERABILITIES = "vulnerabilities"

# What several documents select: a work item (design D1's W), a vulnerability (D1's U), and a page's cursor.
WORK_ITEM_FIELDS = "id iid title state webUrl workItemType { id name }"
VULNERABILITY_FIELDS = "id title severity state reportType detectedAt project { fullPath }"
PAGE_INFO = "pageInfo { hasNextPage endCursor }"
# The maximum page size of conventions.md "Connections and cursor pagination".
PAGE_SIZE = 100


def _work_item_list(*, type_name: str, root: str) -> GraphQLOperation:
    """The record ``graphql#<type_name>.workItems``: the work items of the project, group or namespace the root field
    ``root`` reads by its ``fullPath``, filtered by the optional ``state`` and ``types``, paged at
    ``(root, "workItems")``."""
    return GraphQLOperation(
        operation_id=f"{GRAPHQL_ID_PREFIX}{type_name}.{FIELD_WORK_ITEMS}",
        capability=CAPABILITY_WORK_ITEMS,
        document=(
            "query($fullPath: ID!, $state: IssuableState, $types: [IssueType!], $after: String) { "
            f"{root}(fullPath: $fullPath) {{ {FIELD_WORK_ITEMS}(state: $state, types: $types, first: {PAGE_SIZE}, "
            f"after: $after) {{ nodes {{ {WORK_ITEM_FIELDS} }} {PAGE_INFO} }} }} }}"
        ),
        connection=(root, FIELD_WORK_ITEMS),
    )


def _input_mutation(*, capability: str, name: str, input_type: str, selection: str) -> GraphQLOperation:
    """The record ``graphql#<name>`` of the mutation ``name``: its input object the one variable ``$input`` of the
    non-null ``input_type``, the input type of ``name``'s signature line; it selects ``selection`` and ``errors``."""
    return GraphQLOperation(
        operation_id=f"{GRAPHQL_ID_PREFIX}{name}",
        capability=capability,
        document=f"mutation($input: {input_type}!) {{ {name}(input: $input) {{ {selection} errors }} }}",
    )


OPERATIONS: Tuple[GraphQLOperation, ...] = (
    # Work items. The workItem query is an experiment (`Notes: experiment`). Its `id`, and the input `id` of
    # workItemUpdate and workItemDelete, is a node `id` of a work-item list below.
    GraphQLOperation(
        operation_id=f"{GRAPHQL_ID_PREFIX}workItem",
        capability=CAPABILITY_WORK_ITEMS,
        document=f"query($id: WorkItemID!) {{ workItem(id: $id) {{ {WORK_ITEM_FIELDS} }} }}",
    ),
    # The workItemsByReference query is an experiment (`Notes: experiment`).
    GraphQLOperation(
        operation_id=f"{GRAPHQL_ID_PREFIX}{FIELD_WORK_ITEMS_BY_REFERENCE}",
        capability=CAPABILITY_WORK_ITEMS,
        document=(
            "query($refs: [String!]!, $contextNamespacePath: ID, $after: String) { "
            f"{FIELD_WORK_ITEMS_BY_REFERENCE}(refs: $refs, contextNamespacePath: $contextNamespacePath, "
            f"first: {PAGE_SIZE}, after: $after) {{ nodes {{ {WORK_ITEM_FIELDS} }} {PAGE_INFO} }} }}"
        ),
        connection=(FIELD_WORK_ITEMS_BY_REFERENCE,),
    ),
    # The reference's Notes for Project.workItems: "**deprecated** in 15.9; experiment since 15.1".
    _work_item_list(type_name="Project", root=FIELD_PROJECT),
    # The reference's Notes for Group.workItems: "**deprecated** in 15.9; experiment since 17.10". An epic is a node
    # of this list called with -F 'types=["EPIC"]'.
    _work_item_list(type_name="Group", root=FIELD_GROUP),
    # The reference's Notes for Namespace.workItems: "**deprecated** in 15.9; experiment since 18.1".
    _work_item_list(type_name="Namespace", root=FIELD_NAMESPACE),
    # Creating a work item is refused (design D6). The workItemCreate mutation is an experiment (`Notes: experiment`).
    _input_mutation(
        capability=CAPABILITY_WORK_ITEMS,
        name=MUTATION_WORK_ITEM_CREATE,
        input_type="WorkItemCreateInput",
        selection="workItem { id iid webUrl }",
    ),
    # The workItemUpdate mutation is an experiment (`Notes: experiment`).
    _input_mutation(
        capability=CAPABILITY_WORK_ITEMS,
        name="workItemUpdate",
        input_type="WorkItemUpdateInput",
        selection="workItem { id iid title state }",
    ),
    # The workItemDelete mutation is an experiment (`Notes: experiment`).
    _input_mutation(
        capability=CAPABILITY_WORK_ITEMS,
        name="workItemDelete",
        input_type="WorkItemDeleteInput",
        selection="namespace { fullPath }",
    ),
    # The workItemExport mutation is deprecated (`Notes: **deprecated** in 18.0`); the reference also documents
    # workItemsCsvExport with the same input. Its input `workItemTypeIds` are `workItemType.id`s of work-item nodes.
    _input_mutation(
        capability=CAPABILITY_WORK_ITEMS,
        name="workItemExport",
        input_type="WorkItemExportInput",
        selection="message",
    ),
    # Epics with new features: a work item with its widgets, three of them read in full. The workItem query is an
    # experiment (`Notes: experiment`), and the reference's Notes for WorkItemWidgetLinkedItems.linkedItems:
    # "experiment since 16.3".
    GraphQLOperation(
        operation_id=f"{GRAPHQL_ID_PREFIX}WorkItem.widgets",
        capability=CAPABILITY_EPICS,
        document=(
            "query($id: WorkItemID!) { workItem(id: $id) { id iid title workItemType { id name } widgets { type "
            "... on WorkItemWidgetAssignees { assignees { nodes { id username } } } "
            "... on WorkItemWidgetHealthStatus { healthStatus } "
            "... on WorkItemWidgetLinkedItems { linkedItems { nodes { linkType workItem { id } } } } } } }"
        ),
    ),
    # Branch rules: a project's rules (a node `id` is the input `id` of branchRuleUpdate and branchRuleDelete), then
    # the mutations, each an experiment (`Notes: experiment`).
    GraphQLOperation(
        operation_id=f"{GRAPHQL_ID_PREFIX}Project.{FIELD_BRANCH_RULES}",
        capability=CAPABILITY_BRANCH_RULES,
        document=(
            f"query($fullPath: ID!, $after: String) {{ {FIELD_PROJECT}(fullPath: $fullPath) {{ "
            f"{FIELD_BRANCH_RULES}(first: {PAGE_SIZE}, after: $after) {{ "
            f"nodes {{ id name isDefault isProtected matchingBranchesCount }} {PAGE_INFO} }} }} }}"
        ),
        connection=(FIELD_PROJECT, FIELD_BRANCH_RULES),
    ),
    _input_mutation(
        capability=CAPABILITY_BRANCH_RULES,
        name="branchRuleCreate",
        input_type="BranchRuleCreateInput",
        selection="branchRule { id name }",
    ),
    _input_mutation(
        capability=CAPABILITY_BRANCH_RULES,
        name="branchRuleUpdate",
        input_type="BranchRuleUpdateInput",
        selection="branchRule { id name }",
    ),
    _input_mutation(
        capability=CAPABILITY_BRANCH_RULES,
        name="branchRuleDelete",
        input_type="BranchRuleDeleteInput",
        selection="branchRule { id name }",
    ),
    # Vulnerability lists: a group's and the instance security dashboard's, whose node `id` is the `id` of
    # graphql#Query.vulnerability. The reference's Notes for Group.vulnerabilities: "experiment since 18.8".
    GraphQLOperation(
        operation_id=f"{GRAPHQL_ID_PREFIX}Group.{FIELD_VULNERABILITIES}",
        capability=CAPABILITY_VULNERABILITIES,
        document=(
            f"query($fullPath: ID!, $after: String) {{ {FIELD_GROUP}(fullPath: $fullPath) {{ "
            f"{FIELD_VULNERABILITIES}(first: {PAGE_SIZE}, after: $after) {{ "
            f"nodes {{ {VULNERABILITY_FIELDS} }} {PAGE_INFO} }} }} }}"
        ),
        connection=(FIELD_GROUP, FIELD_VULNERABILITIES),
    ),
    GraphQLOperation(
        operation_id=f"{GRAPHQL_ID_PREFIX}Query.{FIELD_VULNERABILITIES}",
        capability=CAPABILITY_VULNERABILITIES,
        document=(
            f"query($after: String) {{ {FIELD_VULNERABILITIES}(first: {PAGE_SIZE}, after: $after) {{ "
            f"nodes {{ {VULNERABILITY_FIELDS} }} {PAGE_INFO} }} }}"
        ),
        connection=(FIELD_VULNERABILITIES,),
    ),
    GraphQLOperation(
        operation_id=f"{GRAPHQL_ID_PREFIX}Query.vulnerability",
        capability=CAPABILITY_VULNERABILITIES,
        document=f"query($id: VulnerabilityID!) {{ vulnerability(id: $id) {{ {VULNERABILITY_FIELDS} }} }}",
    ),
    # Design uploads: each design a file of the list `$files`, given with --file files=PATH.
    GraphQLOperation(
        operation_id=f"{GRAPHQL_ID_PREFIX}designManagementUpload",
        capability=CAPABILITY_DESIGN_UPLOADS,
        document=(
            "mutation($projectPath: ID!, $iid: ID!, $files: [Upload!]!) { "
            "designManagementUpload(input: {projectPath: $projectPath, iid: $iid, files: $files}) { "
            "designs { id filename } skippedDesigns { id filename } errors } }"
        ),
    ),
    # Asynchronous pipeline creation: pipelineCreate with `async: true` prints a `requestId`, the `requestId` of
    # graphql#Project.ciPipelineCreationRequest. The reference's Notes for PipelineCreateInput.async and
    # PipelineCreatePayload.requestId: "experiment since 17.8"; for Project.ciPipelineCreationRequest: "experiment
    # since 17.9".
    GraphQLOperation(
        operation_id=f"{GRAPHQL_ID_PREFIX}pipelineCreate",
        capability=CAPABILITY_ASYNC_PIPELINES,
        document=(
            "mutation($projectPath: ID!, $ref: String!, $variables: [CiVariableInput!], $inputs: [CiInputsInput!], "
            "$mergeRequestIid: String) { pipelineCreate(input: {projectPath: $projectPath, ref: $ref, "
            "variables: $variables, inputs: $inputs, mergeRequestIid: $mergeRequestIid, async: true}) { "
            "requestId pipeline { id iid status } errors } }"
        ),
    ),
    GraphQLOperation(
        operation_id=f"{GRAPHQL_ID_PREFIX}Project.ciPipelineCreationRequest",
        capability=CAPABILITY_ASYNC_PIPELINES,
        document=(
            f"query($fullPath: ID!, $requestId: String!) {{ {FIELD_PROJECT}(fullPath: $fullPath) {{ "
            "ciPipelineCreationRequest(requestId: $requestId) { "
            "id status error pipelineId pipeline { id iid status } } } }"
        ),
    ),
    # Importing work items from a CSV file is refused (design D6). The workItemsCsvImport mutation is an experiment
    # (`Notes: experiment`).
    GraphQLOperation(
        operation_id=OP_WORK_ITEMS_CSV_IMPORT,
        capability=CAPABILITY_CSV_IMPORT,
        document=(
            f"mutation($projectPath: ID!, $file: Upload!) {{ {MUTATION_WORK_ITEMS_CSV_IMPORT}(input: "
            "{projectPath: $projectPath, file: $file}) { message errors } }"
        ),
    ),
    # Query cost introspection: the score and the limit of this query.
    GraphQLOperation(
        operation_id=f"{GRAPHQL_ID_PREFIX}queryComplexity",
        capability=CAPABILITY_QUERY_COST,
        document="query { queryComplexity { score limit } }",
    ),
)

PENDING_CAPABILITIES: FrozenSet[str] = frozenset()
