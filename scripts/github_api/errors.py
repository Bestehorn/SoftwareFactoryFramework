"""The GitHub wrapper's exceptions: ``GitHubAPIError`` and the subclasses the transport raises.

Every failure the wrapper reports is a ``GitHubAPIError``, so the entry script's one handler reports it and exits 1.
A subclass is named with the base's prefix, as the fork names ``GitHubRedirectRefusedError``, and adds no fields:
``status_code`` and ``details`` carry what each failure knows.
"""

from __future__ import annotations

from typing import Any, Optional


class GitHubAPIError(Exception):
    """A GitHub request failed or was refused: ``status_code`` is the HTTP status when a response was received
    (``None`` when none was), ``details`` the parsed error body GitHub sent (``None`` when it is not JSON)."""

    def __init__(self, message: str, status_code: Optional[int] = None, details: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.details = details


class GitHubRateLimitError(GitHubAPIError):
    """A rate limit still applied after the transport's bounded retries: ``status_code`` is the last response's status
    and ``details`` its parsed body; the message names the ``x-ratelimit-resource`` bucket, else the kind of limit."""


class GitHubGraphQLResponseError(GitHubAPIError):
    """A GraphQL response carried a top-level ``errors`` array, whatever its HTTP status and whether or not ``data``
    is present: ``status_code`` is the HTTP status and ``details`` the ``errors`` array."""
