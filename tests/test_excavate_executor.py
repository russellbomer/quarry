"""Tests for excavate executor module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quarry.tools.excavate.executor import (
    ExcavateExecutor,
    ForgeError,
    append_jsonl,
    write_jsonl,
)


class TestExcavateExecutor:
    """Tests for ExcavateExecutor class."""

    @pytest.fixture
    def sample_schema_dict(self):
        """Sample schema dictionary."""
        return {
            "name": "test-schema",
            "item_selector": "article.post",
            "fields": {
                "title": {"selector": "h2"},
                "link": {"selector": "a", "attribute": "href"},
            },
        }

    @pytest.fixture
    def sample_schema_file(self, tmp_path, sample_schema_dict):
        """Create a temporary schema file."""
        import yaml

        schema_path = tmp_path / "test_schema.yml"
        schema_path.write_text(yaml.dump(sample_schema_dict), encoding="utf-8")
        return schema_path

    @pytest.fixture
    def sample_html(self):
        """Sample HTML content for testing."""
        return """
        <html>
        <body>
            <article class="post">
                <h2>First Article</h2>
                <a href="https://example.com/1">Link 1</a>
            </article>
            <article class="post">
                <h2>Second Article</h2>
                <a href="https://example.com/2">Link 2</a>
            </article>
        </body>
        </html>
        """

    def test_init_with_schema_path(self, sample_schema_file):
        """Test initialization with schema file path."""
        executor = ExcavateExecutor(sample_schema_file)

        assert executor.schema.name == "test-schema"
        assert executor.stats["urls_fetched"] == 0

    def test_init_with_string_path(self, sample_schema_file):
        """Test initialization with string path."""
        executor = ExcavateExecutor(str(sample_schema_file))

        assert executor.schema.name == "test-schema"

    @patch("quarry.tools.excavate.executor.get_html")
    def test_fetch_url_success(self, mock_get_html, sample_schema_file, sample_html):
        """Test successful URL fetch."""
        mock_get_html.return_value = sample_html
        executor = ExcavateExecutor(sample_schema_file)

        items = executor.fetch_url("https://example.com/page")

        assert len(items) == 2
        assert items[0]["title"] == "First Article"
        assert items[1]["title"] == "Second Article"
        assert executor.stats["urls_fetched"] == 1
        assert executor.stats["items_extracted"] == 2

    @patch("quarry.tools.excavate.executor.get_html")
    def test_fetch_url_with_metadata(self, mock_get_html, sample_schema_file, sample_html):
        """Test that metadata is added to items."""
        mock_get_html.return_value = sample_html
        executor = ExcavateExecutor(sample_schema_file)

        items = executor.fetch_url("https://example.com/page", include_metadata=True)

        assert "_meta" in items[0]
        assert items[0]["_meta"]["url"] == "https://example.com/page"
        assert items[0]["_meta"]["schema"] == "test-schema"
        assert "fetched_at" in items[0]["_meta"]

    @patch("quarry.tools.excavate.executor.get_html")
    def test_fetch_url_without_metadata(self, mock_get_html, sample_schema_file, sample_html):
        """Test fetching without metadata."""
        mock_get_html.return_value = sample_html
        executor = ExcavateExecutor(sample_schema_file)

        items = executor.fetch_url("https://example.com/page", include_metadata=False)

        assert "_meta" not in items[0]

    @patch("quarry.tools.excavate.executor.get_html")
    def test_fetch_url_error(self, mock_get_html, sample_schema_file):
        """Test error handling during fetch."""
        mock_get_html.side_effect = Exception("Network error")
        executor = ExcavateExecutor(sample_schema_file)

        with pytest.raises(ForgeError) as exc_info:
            executor.fetch_url("https://example.com/page")

        assert "Failed to fetch" in str(exc_info.value)
        assert executor.stats["errors"] == 1

    def test_get_stats(self, sample_schema_file):
        """Test getting stats returns a copy."""
        executor = ExcavateExecutor(sample_schema_file)
        executor.stats["urls_fetched"] = 5

        stats = executor.get_stats()

        assert stats["urls_fetched"] == 5
        # Modifying returned dict shouldn't affect internal stats
        stats["urls_fetched"] = 100
        assert executor.stats["urls_fetched"] == 5


class TestPagination:
    """Tests for pagination functionality."""

    @pytest.fixture
    def paginated_schema_dict(self):
        """Schema with pagination configuration."""
        return {
            "name": "paginated-schema",
            "item_selector": "article",
            "fields": {"title": {"selector": "h2"}},
            "pagination": {"next_selector": "a.next", "max_pages": 3, "wait_seconds": 0},
        }

    @pytest.fixture
    def paginated_schema_file(self, tmp_path, paginated_schema_dict):
        """Create a temporary paginated schema file."""
        import yaml

        schema_path = tmp_path / "paginated_schema.yml"
        schema_path.write_text(yaml.dump(paginated_schema_dict), encoding="utf-8")
        return schema_path

    @patch("quarry.tools.excavate.executor.get_html")
    def test_fetch_with_pagination_single_page(self, mock_get_html, paginated_schema_file):
        """Test pagination when there's only one page."""
        html = """
        <html>
        <body>
            <article><h2>Item 1</h2></article>
        </body>
        </html>
        """
        mock_get_html.return_value = html
        executor = ExcavateExecutor(paginated_schema_file)

        items = executor.fetch_with_pagination("https://example.com/page1")

        assert len(items) == 1
        assert items[0]["_meta"]["page"] == 1

    @patch("quarry.tools.excavate.executor.get_html")
    def test_fetch_with_pagination_multiple_pages(self, mock_get_html, paginated_schema_file):
        """Test pagination across multiple pages."""
        page1 = """
        <html>
        <body>
            <article><h2>Item 1</h2></article>
            <a class="next" href="/page2">Next</a>
        </body>
        </html>
        """
        page2 = """
        <html>
        <body>
            <article><h2>Item 2</h2></article>
            <a class="next" href="/page3">Next</a>
        </body>
        </html>
        """
        page3 = """
        <html>
        <body>
            <article><h2>Item 3</h2></article>
        </body>
        </html>
        """
        mock_get_html.side_effect = [page1, page2, page3]
        executor = ExcavateExecutor(paginated_schema_file)

        items = executor.fetch_with_pagination("https://example.com/page1")

        assert len(items) == 3
        assert items[0]["title"] == "Item 1"
        assert items[2]["title"] == "Item 3"

    @patch("quarry.tools.excavate.executor.get_html")
    def test_fetch_respects_max_pages(self, mock_get_html, paginated_schema_file):
        """Test that max_pages limit is respected."""
        page = """
        <html>
        <body>
            <article><h2>Item</h2></article>
            <a class="next" href="/next">Next</a>
        </body>
        </html>
        """
        mock_get_html.return_value = page
        executor = ExcavateExecutor(paginated_schema_file)

        items = executor.fetch_with_pagination("https://example.com/page1", max_pages=2)

        # Should stop at 2 pages
        assert executor.stats["urls_fetched"] == 2

    @patch("quarry.tools.excavate.executor.get_html")
    def test_fetch_stops_on_duplicate_url(self, mock_get_html, paginated_schema_file):
        """Test pagination stops on duplicate URL (circular reference)."""
        page = """
        <html>
        <body>
            <article><h2>Item</h2></article>
            <a class="next" href="https://example.com/page1">Next</a>
        </body>
        </html>
        """
        mock_get_html.return_value = page
        executor = ExcavateExecutor(paginated_schema_file)

        items = executor.fetch_with_pagination("https://example.com/page1")

        # Should only fetch once since next points to same URL
        assert executor.stats["urls_fetched"] == 1


class TestWriteJsonl:
    """Tests for write_jsonl function."""

    def test_write_jsonl_basic(self, tmp_path):
        """Test writing items to JSONL file."""
        items = [
            {"id": 1, "name": "First"},
            {"id": 2, "name": "Second"},
        ]
        output_path = tmp_path / "output.jsonl"

        count = write_jsonl(items, output_path)

        assert count == 2
        assert output_path.exists()

        # Verify content
        lines = output_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["id"] == 1

    def test_write_jsonl_creates_directories(self, tmp_path):
        """Test that write_jsonl creates parent directories."""
        items = [{"id": 1}]
        output_path = tmp_path / "nested" / "dirs" / "output.jsonl"

        count = write_jsonl(items, output_path)

        assert count == 1
        assert output_path.exists()

    def test_write_jsonl_empty_list(self, tmp_path):
        """Test writing empty list."""
        items = []
        output_path = tmp_path / "empty.jsonl"

        count = write_jsonl(items, output_path)

        assert count == 0
        assert output_path.exists()
        assert output_path.read_text() == ""

    def test_write_jsonl_unicode(self, tmp_path):
        """Test writing items with unicode characters."""
        items = [{"name": "日本語"}, {"name": "émoji 🎉"}]
        output_path = tmp_path / "unicode.jsonl"

        count = write_jsonl(items, output_path)

        assert count == 2
        lines = output_path.read_text(encoding="utf-8").strip().split("\n")
        assert json.loads(lines[0])["name"] == "日本語"


class TestAppendJsonl:
    """Tests for append_jsonl function."""

    def test_append_jsonl_to_existing(self, tmp_path):
        """Test appending to existing file."""
        output_path = tmp_path / "output.jsonl"
        output_path.write_text('{"id": 1}\n', encoding="utf-8")

        new_items = [{"id": 2}, {"id": 3}]
        count = append_jsonl(new_items, output_path)

        assert count == 2
        lines = output_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 3

    def test_append_jsonl_creates_new(self, tmp_path):
        """Test appending to non-existent file creates it."""
        output_path = tmp_path / "new.jsonl"
        items = [{"id": 1}]

        count = append_jsonl(items, output_path)

        assert count == 1
        assert output_path.exists()

    def test_append_jsonl_creates_directories(self, tmp_path):
        """Test append creates parent directories."""
        items = [{"id": 1}]
        output_path = tmp_path / "nested" / "dirs" / "output.jsonl"

        count = append_jsonl(items, output_path)

        assert count == 1
        assert output_path.exists()


class TestForgeError:
    """Tests for ForgeError exception."""

    def test_forge_error_message(self):
        """Test ForgeError with message."""
        error = ForgeError("Something went wrong")
        assert str(error) == "Something went wrong"

    def test_forge_error_inheritance(self):
        """Test ForgeError is an Exception."""
        error = ForgeError("test")
        assert isinstance(error, Exception)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
