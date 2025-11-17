"""Executor for running extraction at scale."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from quarry.lib.bs4_utils import attr_str
from quarry.lib.http import get_html
from quarry.lib.schemas import ExtractionSchema, load_schema

from .parser import SchemaParser


class ExcavateExecutor:
    """
    Executes schema-based extraction on HTML content.

    Handles:
    - Fetching HTML from URLs
    - Parsing with SchemaParser
    - Pagination support
    - Metadata injection
    - Error handling
    """

    def __init__(self, schema: ExtractionSchema | str | Path):
        """
        Initialize executor.

        Args:
            schema: ExtractionSchema instance or path to schema file
        """
        if isinstance(schema, (str, Path)):
            self.schema = load_schema(schema)
        else:
            self.schema = schema

        self.parser = SchemaParser(self.schema)
        self.stats = {
            "urls_fetched": 0,
            "items_extracted": 0,
            "errors": 0,
        }

    def fetch_url(self, url: str, include_metadata: bool = True) -> list[dict[str, Any]]:
        """
        Fetch and parse a single URL.

        Args:
            url: URL to fetch
            include_metadata: Whether to add _meta field (default True)

        Returns:
            List of extracted items
        """
        try:
            html = get_html(url)
            items = self.parser.parse(html)

            # Add metadata
            if include_metadata:
                for item in items:
                    item["_meta"] = {
                        "url": url,
                        "fetched_at": datetime.now().isoformat(),
                        "schema": self.schema.name,
                    }

            self.stats["urls_fetched"] += 1
            self.stats["items_extracted"] += len(items)

            return items

        except Exception as e:
            self.stats["errors"] += 1
            raise ForgeError(f"Failed to fetch {url}: {e}") from e

    def fetch_with_pagination(
        self, start_url: str, max_pages: int | None = None, include_metadata: bool = True
    ) -> list[dict[str, Any]]:
        """
        Fetch multiple pages following pagination.

        Args:
            start_url: Initial URL to start from
            max_pages: Maximum pages to fetch (None = unlimited)
            include_metadata: Whether to add _meta field

        Returns:
            Combined list of all extracted items
        """
        if not self.schema.pagination:
            # No pagination configured, just fetch single page
            return self.fetch_url(start_url, include_metadata)

        all_items = []
        current_url: str | None = start_url
        page_count = 0
        seen_urls: set[str] = set()

        # Use max_pages from schema if not provided
        if max_pages is None:
            max_pages = self.schema.pagination.max_pages

        while current_url:
            # Narrow type for mypy
            assert current_url is not None
            if current_url in seen_urls:
                break
            seen_urls.add(current_url)

            # Check page limit
            if max_pages and page_count >= max_pages:
                break

            # Fetch current page
            try:
                html = get_html(current_url)
                items = self.parser.parse(html)

                # Add metadata
                if include_metadata:
                    for item in items:
                        item["_meta"] = {
                            "url": current_url,
                            "fetched_at": datetime.now().isoformat(),
                            "schema": self.schema.name,
                            "page": page_count + 1,
                        }

                all_items.extend(items)
                self.stats["urls_fetched"] += 1
                self.stats["items_extracted"] += len(items)
                page_count += 1

                # Find next page
                next_url = self._find_next_page(html, current_url)
                if next_url and next_url in seen_urls:
                    next_url = None
                if next_url and next_url == current_url:
                    next_url = None

                # Wait between pages if configured
                if next_url and self.schema.pagination.wait_seconds > 0:
                    import time

                    time.sleep(self.schema.pagination.wait_seconds)

                current_url = next_url

            except Exception:
                self.stats["errors"] += 1
                # Stop pagination on error
                break

        return all_items

    def _find_next_page(self, html: str, current_url: str) -> str | None:
        """
        Find next page URL from HTML.

        Args:
            html: Current page HTML
            current_url: Current page URL (for making absolute URLs)

        Returns:
            Next page URL or None if no next page
        """
        if not self.schema.pagination:
            return None

        soup = BeautifulSoup(html, "html.parser")

        try:
            next_link = soup.select_one(self.schema.pagination.next_selector)

            if not next_link:
                return None

            # Get href attribute safely as a string
            next_href = attr_str(next_link, "href")

            if not next_href:
                return None

            # Make absolute URL
            next_url = urljoin(current_url, next_href)

            return next_url

        except Exception:
            return None

    def get_stats(self) -> dict[str, int]:
        """Get execution statistics."""
        return self.stats.copy()


def write_jsonl(items: list[dict[str, Any]], output_path: str | Path) -> int:
    """
    Write items to JSONL file.

    Args:
        items: List of items to write
        output_path: Output file path

    Returns:
        Number of items written
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with output_path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            count += 1

    return count


def append_jsonl(items: list[dict[str, Any]], output_path: str | Path) -> int:
    """
    Append items to JSONL file.

    Args:
        items: List of items to append
        output_path: Output file path

    Returns:
        Number of items written
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with output_path.open("a", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            count += 1

    return count


class ForgeError(Exception):
    """Exception raised by Forge executor."""

    pass
