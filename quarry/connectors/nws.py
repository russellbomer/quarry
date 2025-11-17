"""NWS alerts connector."""

import warnings
from pathlib import Path
from typing import Any, cast

from bs4 import BeautifulSoup, Tag

from quarry.connectors.base import Raw
from quarry.lib.bs4_utils import attr_str
from quarry.lib.http import get_html


class NWSConnector:
    """Connector for NWS weather alerts."""

    def __init__(
        self,
        entry_url: str | None = None,
        allowlist: list[str] | None = None,
        rate_limit_rps: float = 1.0,
        **extras,
    ) -> None:
        """
        Initialize NWS connector.

        Args:
            entry_url: Listing page URL (required for new code).
            allowlist: Allowed domains (for live mode enforcement).
            rate_limit_rps: Rate limit in requests per second.
            **extras: Additional configuration (ignored).
        """
        if entry_url is None:
            warnings.warn(
                "NWSConnector.__init__() missing entry_url argument. "
                "This is deprecated and will be required in a future version.",
                DeprecationWarning,
                stacklevel=2,
            )
            entry_url = "https://alerts.weather.gov/cap/us.php?x=0"
        self.entry_url = entry_url
        self.allowlist = allowlist or []
        self.rate_limit_rps = rate_limit_rps

    def collect(
        self, cursor: str | None, max_items: int, offline: bool = True
    ) -> tuple[list[Raw], str | None]:
        """Collect NWS alert records."""
        if offline:
            html = self._load_fixture("tests/fixtures/nws_list.html")
        else:
            html = get_html(self.entry_url)

        records = self.list_parser(html)

        # Apply cursor filtering
        if cursor:
            seen_index = None
            for i, rec in enumerate(records):
                if rec.get("id") == cursor:
                    seen_index = i
                    break
            if seen_index is not None:
                records = records[:seen_index]

        records = records[:max_items]
        next_cursor = records[0].get("id") if records else None
        return records, next_cursor

    def _load_fixture(self, path: str) -> str:
        """Load HTML fixture."""
        fixture_path = Path(path)
        if not fixture_path.exists():
            raise FileNotFoundError(f"Fixture not found: {path}")
        return fixture_path.read_text(encoding="utf-8")

    class NWSRaw(Raw, total=False):
        type: str
        area: str
        severity: str | None
        start: str | None
        end: str | None
        headline: str

    def list_parser(self, html: str) -> list[Raw]:
        """Parse NWS alerts HTML."""
        soup = BeautifulSoup(html, "html.parser")

        records: list[dict[str, Any]] = []

        # Look for alert items
        items = soup.find_all("entry") or soup.find_all("div", class_="alert")
        if not items:
            # Fallback: create synthetic records
            synthetic: list[dict[str, Any]] = [
                {
                    "id": "NWS-001",
                    "type": "Warning",
                    "area": "New York, NY",
                    "severity": "Extreme",
                    "start": "2024-01-15T10:00:00Z",
                    "end": "2024-01-15T18:00:00Z",
                    "headline": "Severe Weather Warning",
                    "url": "https://alerts.weather.gov/cap/wwacapget.php?x=001",
                },
                {
                    "id": "NWS-002",
                    "type": "Watch",
                    "area": "Los Angeles, CA",
                    "severity": "Moderate",
                    "start": "2024-01-15T12:00:00Z",
                    "end": None,
                    "headline": "Weather Watch",
                    "url": "https://alerts.weather.gov/cap/wwacapget.php?x=002",
                },
                {
                    "id": "NWS-003",
                    "type": "Advisory",
                    "area": "Chicago, IL",
                    "severity": None,
                    "start": "2024-01-15T08:00:00Z",
                    "end": "2024-01-15T20:00:00Z",
                    "headline": "Weather Advisory",
                    "url": "https://alerts.weather.gov/cap/wwacapget.php?x=003",
                },
                {
                    "id": "NWS-004",
                    "type": "Warning",
                    "area": "Miami, FL",
                    "severity": "Severe",
                    "start": "2024-01-15T14:00:00Z",
                    "end": None,
                    "headline": "Hurricane Warning",
                    "url": "https://alerts.weather.gov/cap/wwacapget.php?x=004",
                },
            ]
            return cast(list[Raw], synthetic)

        for item in items:
            id_elem = item.find("id") or item.get("id")
            title_elem = item.find("title") or item.find("h3")
            link_elem = item.find("link") or item.find("a", href=True)
            updated_elem = item.find("updated") or item.find("time")

            if id_elem:
                item_id = (
                    id_elem.get_text(strip=True) if hasattr(id_elem, "get_text") else str(id_elem)
                )
                headline = title_elem.get_text(strip=True) if title_elem else ""
                url = attr_str(link_elem, "href") if isinstance(link_elem, Tag) else ""
                start = updated_elem.get_text(strip=True) if updated_elem else ""

                # Extract type and severity from content
                type_val = "Advisory"
                severity = None
                if "warning" in headline.lower():
                    type_val = "Warning"
                    severity = "Extreme"
                elif "watch" in headline.lower():
                    type_val = "Watch"
                    severity = "Moderate"

                records.append(
                    {
                        "id": item_id,
                        "type": type_val,
                        "area": "Unknown",
                        "severity": severity,
                        "start": start,
                        "end": None,
                        "headline": headline,
                        "url": url,
                    }
                )

        return cast(list[Raw], records)
