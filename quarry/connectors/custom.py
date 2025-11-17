"""Custom connector stub for user-defined jobs."""

import warnings
from pathlib import Path

from bs4 import BeautifulSoup

from quarry.connectors.base import Raw
from quarry.lib.bs4_utils import attr_str


class CustomConnector:
    """Stub connector for custom jobs."""

    def __init__(
        self,
        entry_url: str,
        allowlist: list[str] | None = None,
        rate_limit_rps: float = 1.0,
        **extras,
    ) -> None:
        """
        Initialize custom connector.

        Args:
            entry_url: Listing page URL (required).
            allowlist: Allowed domains (for live mode enforcement).
            rate_limit_rps: Rate limit in requests per second.
            **extras: Additional configuration (ignored).
        """
        self.entry_url = entry_url
        self.allowlist = allowlist or []
        self.rate_limit_rps = rate_limit_rps

    def collect(
        self, cursor: str | None, max_items: int, offline: bool = True
    ) -> tuple[list[Raw], str | None]:
        """
        Collect custom records.

        Args:
            cursor: Optional cursor (e.g., last seen ID).
            max_items: Maximum number of items to collect.
            offline: If True, use fixtures; if False, fetch live.

        Returns:
            (records, next_cursor)

        Raises:
            NotImplementedError: In live mode (requires implementation).
        """
        if not offline:
            raise NotImplementedError(
                "Custom connector requires implementation for live mode. "
                "Please implement custom connector logic or use offline mode with fixtures."
            )

        # Try to load fixture
        fixture_path = Path("tests/fixtures/custom_list.html")
        if fixture_path.exists():
            html = fixture_path.read_text(encoding="utf-8")
            records = self.list_parser(html)
        else:
            # Synthesize records with warning
            warnings.warn(
                f"Fixture not found: {fixture_path}. Synthesizing records.",
                UserWarning,
                stacklevel=2,
            )
            records = self._synthesize_records()

        # Apply cursor filtering
        if cursor:
            seen_index = None
            for i, rec in enumerate(records):
                if rec.get("id") == cursor:
                    seen_index = i
                    break
            if seen_index is not None:
                records = records[:seen_index]

        # Limit to max_items
        records = records[:max_items]
        next_cursor = records[0].get("id") if records else None
        return records, next_cursor

    def list_parser(self, html: str) -> list[Raw]:
        """
        Parse custom list page HTML.

        Args:
            html: HTML content of the listing page.

        Returns:
            List of Raw records.
        """
        soup = BeautifulSoup(html, "html.parser")
        records: list[Raw] = []

        # Simple parser: look for anchor tags
        anchors = soup.find_all("a", href=True)
        for anchor in anchors[:3]:  # Limit to first 3 for stub
            href = attr_str(anchor, "href")
            title = anchor.get_text(strip=True) or "Untitled"

            records.append(
                {
                    "id": (href.split("/")[-1] if href else "") or f"custom-{len(records) + 1}",
                    "title": title,
                    "url": href
                    if href.startswith("http")
                    else (f"{self.entry_url}{href}" if href else self.entry_url),
                    "posted_at": "2024-01-15T00:00:00Z",
                }
            )

        return records or self._synthesize_records()

    def _synthesize_records(self) -> list[Raw]:
        """Synthesize deterministic records for offline testing."""
        return [
            {
                "id": "custom-001",
                "title": "Custom Item 1",
                "url": f"{self.entry_url}/item/1",
                "posted_at": "2024-01-15T00:00:00Z",
            },
            {
                "id": "custom-002",
                "title": "Custom Item 2",
                "url": f"{self.entry_url}/item/2",
                "posted_at": "2024-01-15T01:00:00Z",
            },
            {
                "id": "custom-003",
                "title": "Custom Item 3",
                "url": f"{self.entry_url}/item/3",
                "posted_at": "2024-01-15T02:00:00Z",
            },
        ]
