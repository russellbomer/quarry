"""FDA recalls connector."""

import re
import warnings
from pathlib import Path
from typing import Any, cast
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from quarry.connectors.base import Raw
from quarry.lib.bs4_utils import attr_str
from quarry.lib.http import get_html


class FDAConnector:
    """Connector for FDA recalls."""

    # Compile regex once at class level for performance
    _SLUG_PATTERN = re.compile(r"/recalls-market-withdrawals-safety-alerts/([^/]+)$")

    def __init__(
        self,
        entry_url: str | None = None,
        allowlist: list[str] | None = None,
        rate_limit_rps: float = 1.0,
        **extras,
    ) -> None:
        """
        Initialize FDA connector.

        Args:
            entry_url: Listing page URL (required for new code).
            allowlist: Allowed domains (for live mode enforcement).
            rate_limit_rps: Rate limit in requests per second.
            **extras: Additional configuration (ignored).
        """
        if entry_url is None:
            warnings.warn(
                "FDAConnector.__init__() missing entry_url argument. "
                "This is deprecated and will be required in a future version.",
                DeprecationWarning,
                stacklevel=2,
            )
            entry_url = "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts"
        self.entry_url = entry_url
        self.allowlist = allowlist or []
        self.rate_limit_rps = rate_limit_rps

    def collect(
        self, cursor: str | None, max_items: int, offline: bool = True
    ) -> tuple[list[Raw], str | None]:
        """Collect FDA recall records."""
        if offline:
            html = self._load_fixture("tests/fixtures/fda_list.html")
        else:
            html = get_html(self.entry_url)

        records = self.list_parser(html, self.entry_url)

        # Apply cursor filtering (stop when seen)
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

        # Enrich with detail if fixture available (offline) or in live mode
        detail_html_path = Path("tests/fixtures/fda_detail.html")
        if offline and detail_html_path.exists():
            detail_html = detail_html_path.read_text(encoding="utf-8")
            detail_data = self.detail_parser(detail_html)
            # Merge detail into first record as example
            if records and detail_data:
                first = cast(dict[str, Any], records[0])
                first.update(detail_data)

        next_cursor = records[0].get("id") if records else None
        return records, next_cursor

    def _load_fixture(self, path: str) -> str:
        """Load HTML fixture."""
        fixture_path = Path(path)
        if not fixture_path.exists():
            raise FileNotFoundError(f"Fixture not found: {path}")
        return fixture_path.read_text(encoding="utf-8")

    def list_parser(self, html: str, entry_url: str) -> list[Raw]:
        """
        Parse FDA list page HTML and extract real URLs from anchors.

        Args:
            html: HTML content of the listing page.
            entry_url: Base URL for resolving relative hrefs.

        Returns:
            List of Raw records with id, title, url, posted_at.
        """
        soup = BeautifulSoup(html, "html.parser")
        records: list[Raw] = []

        # Select anchors matching FDA recall path pattern
        anchors = soup.select("a[href*='/safety/recalls-market-withdrawals-safety-alerts/']")

        for anchor in anchors:
            href = attr_str(anchor, "href")
            if not href:
                continue

            # Build absolute URL
            url = urljoin(entry_url, href)

            # Extract slug for ID (last path segment)
            slug_match = self._SLUG_PATTERN.search(href)
            if slug_match:
                item_id = slug_match.group(1)
            else:
                # Fallback to absolute URL if no slug match
                item_id = url

            # Extract title from anchor text
            title = anchor.get_text(strip=True) or item_id or "Untitled"

            # Try to extract posted date from nearby elements
            posted_at = ""
            parent = anchor.parent
            if isinstance(parent, Tag):
                time_elem = parent.find("time")
                if time_elem:
                    posted_at = time_elem.get_text(strip=True) or attr_str(time_elem, "datetime")

            records.append(
                {
                    "id": item_id,
                    "title": title,
                    "url": url,
                    "posted_at": posted_at,
                }
            )

        return records

    def detail_parser(self, html: str) -> dict[str, Any]:
        """Parse FDA detail page HTML."""
        soup = BeautifulSoup(html, "html.parser")
        detail: dict[str, Any] = {}

        # Extract detail fields (simplified)
        class_elem = soup.find(class_="recall-class") or soup.find(
            string=lambda x: x and "Class" in x
        )
        if class_elem:
            class_text = (
                class_elem.get_text(strip=True)
                if hasattr(class_elem, "get_text")
                else str(class_elem)
            )
            if "Class I" in class_text:
                detail["class"] = "I"
            elif "Class II" in class_text:
                detail["class"] = "II"
            elif "Class III" in class_text:
                detail["class"] = "III"

        category_elem = soup.find(class_="category") or soup.find("h2")
        if category_elem:
            detail["category"] = category_elem.get_text(strip=True)

        return detail

    def enrich_with_detail(
        self, records: list[Raw], detail_parser_name: str, offline: bool = True
    ) -> list[Raw]:
        """Enrich records with detail parser (stub for live mode)."""
        # In live mode, would fetch each record's detail URL
        # For now, return records as-is
        return records
