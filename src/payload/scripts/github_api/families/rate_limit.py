"""The ``rate-limit`` operations of the GitHub REST API: no record yet, every one pending (design D2)."""

FAMILY = "rate-limit"
OPERATIONS = ()
PENDING = frozenset({"rate-limit/get"})
