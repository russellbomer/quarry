"""Base connector interfaces."""

from typing import Protocol, TypedDict


class Raw(TypedDict, total=False):
    """Raw record from a connector."""

    id: str
    url: str
    title: str
    posted_at: str
    body: str


class Connector(Protocol):
    """Protocol for connectors that collect records."""

    def collect(
        self, cursor: str | None, max_items: int, offline: bool = True
    ) -> tuple[list[Raw], str | None]:
        """
        Collect records from source.

        Args:
            cursor: Optional cursor (e.g., last seen ID).
            max_items: Maximum number of items to collect.
            offline: If True, use fixtures; if False, fetch live.

        Returns:
            (records, next_cursor)
        """
        ...
