"""Generic connector using YAML-configured selectors."""

from typing import Any

from bs4 import BeautifulSoup, Tag

from quarry.connectors.base import Raw
from quarry.lib.bs4_utils import attr_str
from quarry.lib.http import get_html


class GenericConnector:
    """
    Generic connector that extracts data using CSS selectors from YAML config.

    YAML config format:
        selectors:
          item: ".article"  # Main item container
          fields:
            title: "h2.title"
            url: "a.link::attr(href)"  # Use ::attr() for attributes
            date: "time::attr(datetime)"
            score: ".points"
            author: ".user a"
    """

    def __init__(
        self,
        entry_url: str,
        allowlist: list[str] | None = None,
        rate_limit_rps: float = 1.0,
        config: dict[str, Any] | None = None,
        **extras,
    ) -> None:
        """
        Initialize generic connector.

        Args:
            entry_url: Listing page URL.
            allowlist: Allowed domains (for live mode enforcement).
            rate_limit_rps: Rate limit in requests per second.
            config: Full job config dict (contains selectors).
            **extras: Additional configuration (ignored).
        """
        self.entry_url = entry_url
        self.allowlist = allowlist or []
        self.rate_limit_rps = rate_limit_rps
        self.config = config or {}

    def collect(
        self, cursor: str | None, max_items: int, offline: bool = True
    ) -> tuple[list[Raw], str | None]:
        """
        Collect records using configured selectors.

        Returns:
            (records, next_cursor)
        """
        # Extract records using selectors
        selectors = self.config.get("selectors", {})
        item_selector = selectors.get("item")
        field_selectors = selectors.get("fields", {})

        if not item_selector:
            raise ValueError(
                "GenericConnector requires 'selectors.item' in config. "
                "Please add item selector to your YAML: selectors: { item: '.your-selector' }"
            )

        if not field_selectors:
            raise ValueError(
                "GenericConnector requires 'selectors.fields' in config. "
                "Please add field selectors to your YAML: selectors: { fields: { title: '.title', "
                "url: 'a::attr(href)' } }"
            )

        # Fetch HTML (always live for generic connector - no fixtures)
        if offline:
            # Generic connector works with live sites, no fixtures
            # Return empty for offline/smoke tests
            return [], None

        html = get_html(self.entry_url)
        soup = BeautifulSoup(html, "html.parser")

        items = soup.select(item_selector)
        records: list[Raw] = []

        for item in items[:max_items]:
            record: dict[str, Any] = {}

            for field_name, selector in field_selectors.items():
                record[field_name] = self._extract_field(item, selector)

            # Ensure required fields
            if "url" not in record:
                record["url"] = ""
            if "title" not in record:
                record["title"] = ""
            if "id" not in record:
                # Generate ID from URL or title
                record["id"] = record.get("url") or record.get("title", "")[:50]

            records.append(record)  # type: ignore

        # Simple cursor: use last item's ID or URL
        next_cursor = None
        if records:
            last_record = records[-1]
            next_cursor = last_record.get("id") or last_record.get("url")

        return records, next_cursor

    def _extract_field(self, element: Tag, selector: str) -> str:
        """
        Extract field value from element using selector.

        Supports:
        - CSS selector: "h2.title"
        - Attribute extraction: "a::attr(href)", "img::attr(src)"
        - Text extraction: "span.text"
        """
        if not selector:
            return ""

        try:
            # Handle attribute extraction
            if "::attr(" in selector:
                parts = selector.split("::attr(")
                child_selector = parts[0].strip()
                attr_name = parts[1].rstrip(")")

                if child_selector in ("", "::attr"):
                    # Extract from element itself
                    return attr_str(element, attr_name)
                else:
                    # Extract from child
                    child = element.select_one(child_selector)
                    return attr_str(child, attr_name) if isinstance(child, Tag) else ""

            # Text extraction
            child = element.select_one(selector)
            return child.get_text(strip=True) if child else ""

        except Exception as e:
            # Log error but don't crash
            print(f"Error extracting field with selector '{selector}': {e}")
            return ""
