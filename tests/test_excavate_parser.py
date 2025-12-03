"""Tests for excavate parser module."""

import pytest
from bs4 import BeautifulSoup

from quarry.lib.schemas import ExtractionSchema, FieldSchema
from quarry.tools.excavate.parser import SchemaParser


class TestSchemaParser:
    """Tests for SchemaParser class."""

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
        </body>
        </html>
        """

    def test_parse_basic(self, basic_schema, sample_html):
        """Test basic parsing extracts all items."""
        parser = SchemaParser(basic_schema)
        results = parser.parse(sample_html)

        assert len(results) == 2
        assert results[0]["title"] == "First Article"
        assert results[0]["link"] == "https://example.com/1"
        assert results[1]["title"] == "Second Article"

    def test_parse_empty_html(self, basic_schema):
        """Test parsing empty HTML returns empty list."""
        parser = SchemaParser(basic_schema)
        results = parser.parse("")
        assert results == []

    def test_parse_whitespace_only_html(self, basic_schema):
        """Test parsing whitespace-only HTML returns empty list."""
        parser = SchemaParser(basic_schema)
        results = parser.parse("   \n\t  ")
        assert results == []

    def test_parse_no_items_found(self, basic_schema):
        """Test parsing HTML with no matching items."""
        html = "<html><body><div>No articles here</div></body></html>"
        parser = SchemaParser(basic_schema)
        results = parser.parse(html)
        assert results == []

    def test_parse_with_attribute_extraction(self):
        """Test extracting attribute values."""
        schema = ExtractionSchema(
            name="attr-test",
            item_selector="div.item",
            fields={
                "image": FieldSchema(selector="img", attribute="src"),
                "alt": FieldSchema(selector="img", attribute="alt"),
            },
        )
        html = '<div class="item"><img src="photo.jpg" alt="A photo"></div>'

        parser = SchemaParser(schema)
        results = parser.parse(html)

        assert len(results) == 1
        assert results[0]["image"] == "photo.jpg"
        assert results[0]["alt"] == "A photo"

    def test_parse_with_default_values(self):
        """Test default values when field not found."""
        schema = ExtractionSchema(
            name="default-test",
            item_selector="div.item",
            fields={
                "title": FieldSchema(selector="h2"),
                "author": FieldSchema(selector=".author", default="Unknown"),
            },
        )
        html = '<div class="item"><h2>Title</h2></div>'  # No author element

        parser = SchemaParser(schema)
        results = parser.parse(html)

        assert results[0]["title"] == "Title"
        assert results[0]["author"] == "Unknown"

    def test_parse_with_required_field_missing(self):
        """Test that missing required fields skip the item."""
        schema = ExtractionSchema(
            name="required-test",
            item_selector="div.item",
            fields={
                "title": FieldSchema(selector="h2", required=True),
            },
        )
        html = """
        <div class="item"><h2>Valid Title</h2></div>
        <div class="item"><p>No title here</p></div>
        """

        parser = SchemaParser(schema)
        results = parser.parse(html)

        # Second item should be skipped due to missing required field
        assert len(results) == 1
        assert results[0]["title"] == "Valid Title"

    def test_parse_with_multiple_values(self):
        """Test extracting multiple values for a field."""
        schema = ExtractionSchema(
            name="multiple-test",
            item_selector="div.item",
            fields={
                "tags": FieldSchema(selector=".tag", multiple=True),
            },
        )
        html = """
        <div class="item">
            <span class="tag">python</span>
            <span class="tag">web</span>
            <span class="tag">scraping</span>
        </div>
        """

        parser = SchemaParser(schema)
        results = parser.parse(html)

        assert len(results) == 1
        assert results[0]["tags"] == ["python", "web", "scraping"]

    def test_parse_multiple_empty_returns_default(self):
        """Test that multiple field with no matches returns default."""
        schema = ExtractionSchema(
            name="multiple-empty-test",
            item_selector="div.item",
            fields={
                "tags": FieldSchema(selector=".tag", multiple=True, default=[]),
            },
        )
        html = '<div class="item"><h2>No tags</h2></div>'

        parser = SchemaParser(schema)
        results = parser.parse(html)

        assert results[0]["tags"] == []

    def test_parse_text_extraction(self):
        """Test extracting text content."""
        schema = ExtractionSchema(
            name="text-test",
            item_selector="div.item",
            fields={
                "content": FieldSchema(selector="p"),
            },
        )
        html = '<div class="item"><p>  Hello World  </p></div>'

        parser = SchemaParser(schema)
        results = parser.parse(html)

        # Should strip whitespace
        assert results[0]["content"] == "Hello World"

    def test_parse_empty_element_text(self):
        """Test extracting from empty element returns None/default."""
        schema = ExtractionSchema(
            name="empty-test",
            item_selector="div.item",
            fields={
                "content": FieldSchema(selector="p", default="N/A"),
            },
        )
        html = '<div class="item"><p></p></div>'

        parser = SchemaParser(schema)
        results = parser.parse(html)

        assert results[0]["content"] == "N/A"

    def test_parse_invalid_item_selector_returns_empty(self):
        """Test that invalid item selector returns empty list (caught internally)."""
        schema = ExtractionSchema(
            name="invalid-test",
            item_selector="[[[invalid",  # Invalid CSS selector
            fields={"title": FieldSchema(selector="h2")},
        )
        html = "<html><body><h2>Test</h2></body></html>"

        parser = SchemaParser(schema)
        # select_list catches the exception and returns empty list
        results = parser.parse(html)
        assert results == []

    def test_parse_handles_extraction_errors_gracefully(self):
        """Test that field extraction errors are handled gracefully."""
        schema = ExtractionSchema(
            name="error-test",
            item_selector="div.item",
            fields={
                "title": FieldSchema(selector="h2"),
                "bad": FieldSchema(selector="[[[invalid", default="fallback"),
            },
        )
        html = '<div class="item"><h2>Title</h2></div>'

        parser = SchemaParser(schema)
        results = parser.parse(html)

        assert len(results) == 1
        assert results[0]["title"] == "Title"
        assert results[0]["bad"] == "fallback"

    def test_parse_complex_nested_html(self):
        """Test parsing complex nested HTML structure."""
        schema = ExtractionSchema(
            name="nested-test",
            item_selector="article",
            fields={
                "title": FieldSchema(selector="header h1"),
                "author": FieldSchema(selector=".meta .author"),
                "date": FieldSchema(selector=".meta time", attribute="datetime"),
            },
        )
        html = """
        <article>
            <header>
                <h1>Deep Article</h1>
            </header>
            <div class="meta">
                <span class="author">Alice</span>
                <time datetime="2024-01-15">Jan 15</time>
            </div>
        </article>
        """

        parser = SchemaParser(schema)
        results = parser.parse(html)

        assert results[0]["title"] == "Deep Article"
        assert results[0]["author"] == "Alice"
        assert results[0]["date"] == "2024-01-15"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
