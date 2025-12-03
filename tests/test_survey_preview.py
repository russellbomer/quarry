"""Tests for survey preview module."""

import pytest

from quarry.lib.schemas import ExtractionSchema, FieldSchema
from quarry.tools.survey.preview import (
    _extract_value,
    _format_preview_simple,
    format_preview,
    preview_extraction,
)
from bs4 import BeautifulSoup


class TestPreviewExtraction:
    """Tests for preview_extraction function."""

    @pytest.fixture
    def basic_schema(self):
        """Create a basic extraction schema."""
        return ExtractionSchema(
            name="test-schema",
            item_selector="article.post",
            fields={
                "title": FieldSchema(selector="h2"),
                "link": FieldSchema(selector="a", attribute="href"),
            },
        )

    @pytest.fixture
    def sample_html(self):
        """Sample HTML with multiple items."""
        return """
        <html>
        <body>
            <article class="post">
                <h2>First Article</h2>
                <a href="https://example.com/1">Read More</a>
            </article>
            <article class="post">
                <h2>Second Article</h2>
                <a href="https://example.com/2">Read More</a>
            </article>
            <article class="post">
                <h2>Third Article</h2>
                <a href="https://example.com/3">Read More</a>
            </article>
        </body>
        </html>
        """

    def test_preview_basic(self, basic_schema, sample_html):
        """Test basic preview extraction."""
        results = preview_extraction(sample_html, basic_schema)

        assert len(results) == 3
        assert results[0]["title"] == "First Article"
        assert results[0]["link"] == "https://example.com/1"

    def test_preview_with_limit(self, basic_schema, sample_html):
        """Test preview with limit."""
        results = preview_extraction(sample_html, basic_schema, limit=2)

        assert len(results) == 2

    def test_preview_empty_html(self, basic_schema):
        """Test preview with empty HTML."""
        results = preview_extraction("", basic_schema)
        assert results == []

    def test_preview_whitespace_html(self, basic_schema):
        """Test preview with whitespace-only HTML."""
        results = preview_extraction("   \n\t  ", basic_schema)
        assert results == []

    def test_preview_no_matches(self, basic_schema):
        """Test preview with no matching items."""
        html = "<html><body><div>No articles here</div></body></html>"
        results = preview_extraction(html, basic_schema)
        assert results == []

    def test_preview_with_multiple_field(self):
        """Test preview with multiple value field."""
        schema = ExtractionSchema(
            name="test",
            item_selector="div.item",
            fields={
                "tags": FieldSchema(selector=".tag", multiple=True),
            },
        )
        html = """
        <div class="item">
            <span class="tag">python</span>
            <span class="tag">web</span>
        </div>
        """

        results = preview_extraction(html, schema)

        assert len(results) == 1
        assert results[0]["tags"] == ["python", "web"]

    def test_preview_with_default_value(self):
        """Test preview with default value for missing field."""
        schema = ExtractionSchema(
            name="test",
            item_selector="div.item",
            fields={
                "title": FieldSchema(selector="h2"),
                "author": FieldSchema(selector=".author", default="Unknown"),
            },
        )
        html = '<div class="item"><h2>Title</h2></div>'

        results = preview_extraction(html, schema)

        assert results[0]["title"] == "Title"
        assert results[0]["author"] == "Unknown"

    def test_preview_required_field_missing(self):
        """Test preview marks required missing field as None."""
        schema = ExtractionSchema(
            name="test",
            item_selector="div.item",
            fields={
                "title": FieldSchema(selector="h2", required=True),
            },
        )
        html = '<div class="item"><p>No title</p></div>'

        results = preview_extraction(html, schema)

        assert results[0]["title"] is None


class TestExtractValue:
    """Tests for _extract_value helper function."""

    def test_extract_text(self):
        """Test extracting text content."""
        soup = BeautifulSoup('<p>Hello World</p>', 'html.parser')
        p = soup.find('p')

        result = _extract_value(p, None)
        assert result == "Hello World"

    def test_extract_attribute(self):
        """Test extracting attribute."""
        soup = BeautifulSoup('<a href="https://example.com">Link</a>', 'html.parser')
        a = soup.find('a')

        result = _extract_value(a, "href")
        assert result == "https://example.com"

    def test_extract_empty_text(self):
        """Test extracting empty text returns None."""
        soup = BeautifulSoup('<p></p>', 'html.parser')
        p = soup.find('p')

        result = _extract_value(p, None)
        assert result is None

    def test_extract_missing_attribute(self):
        """Test extracting missing attribute returns None."""
        soup = BeautifulSoup('<a>Link</a>', 'html.parser')
        a = soup.find('a')

        result = _extract_value(a, "href")
        assert result is None


class TestFormatPreview:
    """Tests for format_preview function."""

    def test_format_empty_items(self):
        """Test formatting empty item list."""
        result = format_preview([])
        assert "No items extracted" in result

    def test_format_with_items(self):
        """Test formatting with items."""
        items = [
            {"title": "First", "author": "Alice"},
            {"title": "Second", "author": "Bob"},
        ]

        result = format_preview(items)

        assert "First" in result
        assert "Second" in result
        assert "2" in result  # item count

    def test_format_with_limit(self):
        """Test formatting respects limit."""
        items = [
            {"title": f"Item {i}"}
            for i in range(10)
        ]

        result = format_preview(items, limit=3)

        # Should show "more items" message
        assert "more" in result.lower()

    def test_format_with_list_values(self):
        """Test formatting items with list values."""
        items = [{"tags": ["a", "b", "c"]}]

        result = format_preview(items)

        # Should show count of items in list
        assert "3" in result or "items" in result.lower()


class TestFormatPreviewSimple:
    """Tests for _format_preview_simple fallback function."""

    def test_simple_format_empty(self):
        """Test simple format with empty items."""
        result = _format_preview_simple([])
        assert "No items extracted" in result

    def test_simple_format_with_items(self):
        """Test simple format with items."""
        items = [
            {"title": "First", "author": "Alice"},
            {"title": "Second", "author": "Bob"},
        ]

        result = _format_preview_simple(items)

        assert "First" in result
        assert "Second" in result
        assert "Item 1:" in result
        assert "Item 2:" in result

    def test_simple_format_with_limit(self):
        """Test simple format respects limit."""
        items = [{"title": f"Item {i}"} for i in range(10)]

        result = _format_preview_simple(items, limit=3)

        assert "Item 1:" in result
        assert "Item 3:" in result
        assert "more items" in result

    def test_simple_format_with_list_values(self):
        """Test simple format with list values."""
        items = [{"tags": ["a", "b", "c"]}]

        result = _format_preview_simple(items)

        assert "3 items" in result

    def test_simple_format_with_none_value(self):
        """Test simple format with None value."""
        items = [{"title": None}]

        result = _format_preview_simple(items)

        # Should show dash for None
        assert "—" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
