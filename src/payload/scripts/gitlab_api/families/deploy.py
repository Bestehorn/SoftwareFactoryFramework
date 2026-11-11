"""The ``deploy`` endpoint family of the GitLab wrapper: the model registry API's three ``ml_models`` file keys.

Each record is transcribed from its section of ``docs/api-reference/gitlab/rest/deploy.md`` (issue #40, design.md
D4): the ID its ``operations-index.md`` row's Reference without ``rest/`` and ``.md``, the method and the path as that
row writes them. Every row of the three sections is ``In`` ``path`` but one: ``id``, ``model_version_id``,
``file_name``, and ``path``, the parameter of the optional ``(*path/)`` group, a glob whose value keeps its ``/``, the
group written only when ``path`` is given (``registry.expand``). So no record declares a ``Param``. The one other row,
"Send the file"'s ``file``, is that record's raw body: ``PUT .../packages/ml_models/`` is a route Workhorse hands to
its ``requestBodyUploader``, which stores the body unparsed, so ``deploy#send-the-file`` sends the bytes ``call
--input`` gives as its ``CONTENT_TYPE_OCTET_STREAM`` body, not the multipart ``file`` part of docs.gitlab.com's
example. The other two records send no raw body. Every record keeps the defaults: a JSON body, no fixed query value
and no paging. The ``rest/openapi-only.md`` References of the same three keys are no record's IDs: the keys are this
family's. ``PENDING`` is empty: every index row of this family has its record.

Standard library only; Python 3.9.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple

from gitlab_api.registry import RestOperation
from gitlab_api.transport import CONTENT_TYPE_OCTET_STREAM

FAMILY = "deploy"

OPERATIONS: Tuple[RestOperation, ...] = (
    # "Model registry API: Download a machine learning model package file".
    RestOperation(
        operation_id="deploy#download-a-machine-learning-model-package-file",
        method="GET",
        path="/projects/:id/packages/ml_models/:model_version_id/files/(*path/):file_name",
    ),
    # "Model registry API: Authorize the upload".
    RestOperation(
        operation_id="deploy#authorize-the-upload",
        method="PUT",
        path="/projects/:id/packages/ml_models/:model_version_id/files/(*path/):file_name/authorize",
    ),
    # "Model registry API: Send the file"; its `file` row is the raw body `call --input` gives.
    RestOperation(
        operation_id="deploy#send-the-file",
        method="PUT",
        path="/projects/:id/packages/ml_models/:model_version_id/files/(*path/):file_name",
        content_type=CONTENT_TYPE_OCTET_STREAM,
    ),
)

PENDING: FrozenSet[Tuple[str, str]] = frozenset()
