"""The exceptions of the GitLab wrapper package: one hierarchy under ``GitLabAPIError``.

``GitLabAPIError(message, status_code=0, details=None)`` keeps the signature of the skeleton wrapper's exception, so
``gitlab_wrapper.py`` still maps any of them to exit code 1. ``status_code`` is the HTTP status of the response that
caused the error, 0 when no response did (a refused value, a connection failure); ``details`` carries the raw response
body, never the request or its credential.
"""

from __future__ import annotations

from typing import Any


class GitLabAPIError(RuntimeError):
    """A GitLab request the wrapper refuses to send, or a response it reports as a failure."""

    def __init__(self, message: str, status_code: int = 0, details: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.details = details


class GitLabRateLimitError(GitLabAPIError):
    """``429`` on every attempt, after the transport's retries are spent."""


class GitLabGraphQLResponseError(GitLabAPIError):
    """A GraphQL response carrying top-level ``errors``, or a mutation payload whose ``errors`` list is non-empty."""


class GitLabClaimError(GitLabAPIError):
    """An ``issue start`` claim that is refused, or that the re-read does not confirm."""
