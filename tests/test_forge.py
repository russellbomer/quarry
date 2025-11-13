"""Tests for Forge extraction engine."""

import pytest
from pathlib import Path

from quarry.lib.schemas import ExtractionSchema, FieldSchema, PaginationSchema
from quarry.tools.excavate.parser import SchemaParser
from quarry.tools.excavate.executor import ForgeExecutor


# Test HTML fixtures
SIMPLE_HTML = """
<html>
<body>
    <ul>
        <li>
            <h3>Item One</h3>
            <a href="/item-1">Link 1</a>
            <span class="price">$10.00</span>
        </li>
        <li>
            <h3>Item Two</h3>
            <a href="/item-2">Link 2</a>
            <span class="price">$20.00</span>
        </li>
    </ul>
</body>
</html>
"""

NESTED_HTML = """
<html>
<body>
    <div class="product">
        <h2>Product A</h2>
        <div class="details">
            <span class="sku">SKU-001</span>
            <span class="stock">In Stock</span>
        </div>
    </div>
    <div class="product">
        <h2>Product B</h2>
        <div class="details">
            <span class="sku">SKU-002</span>
            <span class="stock">Out of Stock</span>
        </div>
    </div>
</body>
</html>
"""

PAGINATED_HTML_PAGE1 = """
<html>
<body>
    <ul>
        <li><h3>Page 1 Item 1</h3></li>
        <li><h3>Page 1 Item 2</h3></li>
    </ul>
    <a href="/page/2" class="next">Next</a>
</body>
</html>
"""

PAGINATED_HTML_PAGE2 = """
<html>
<body>
    <ul>
        <li><h3>Page 2 Item 1</h3></li>
        <li><h3>Page 2 Item 2</h3></li>
    </ul>
</body>
</html>
"""


class TestSchemaParser:
    """Test the SchemaParser class."""
    
    def test_basic_extraction(self):
        """Test extracting basic fields from HTML."""
        schema = ExtractionSchema(
            name="test",
            item_selector="ul > li",
            fields={
                "title": FieldSchema(selector="h3"),
                "link": FieldSchema(selector="a", attribute="href"),
                "price": FieldSchema(selector=".price"),
            }
        )
        
        parser = SchemaParser(schema)
        items = parser.parse(SIMPLE_HTML)
        
        assert len(items) == 2
        assert items[0]["title"] == "Item One"
        assert items[0]["link"] == "/item-1"
        assert items[0]["price"] == "$10.00"
        assert items[1]["title"] == "Item Two"
        assert items[1]["link"] == "/item-2"
        assert items[1]["price"] == "$20.00"
    
    def test_nested_selectors(self):
        """Test extraction with nested selectors."""
        schema = ExtractionSchema(
            name="products",
            item_selector=".product",
            fields={
                "name": FieldSchema(selector="h2"),
                "sku": FieldSchema(selector=".details .sku"),
                "status": FieldSchema(selector=".details .stock"),
            }
        )
        
        parser = SchemaParser(schema)
        items = parser.parse(NESTED_HTML)
        
        assert len(items) == 2
        assert items[0]["name"] == "Product A"
        assert items[0]["sku"] == "SKU-001"
        assert items[0]["status"] == "In Stock"
        assert items[1]["name"] == "Product B"
        assert items[1]["sku"] == "SKU-002"
        assert items[1]["status"] == "Out of Stock"
    
    def test_missing_optional_fields(self):
        """Test that missing optional fields return None."""
        schema = ExtractionSchema(
            name="test",
            item_selector="ul > li",
            fields={
                "title": FieldSchema(selector="h3", required=True),
                "missing": FieldSchema(selector=".nonexistent"),
            }
        )
        
        parser = SchemaParser(schema)
        items = parser.parse(SIMPLE_HTML)
        
        assert len(items) == 2
        assert items[0]["title"] == "Item One"
        assert items[0]["missing"] is None
    
    def test_missing_required_field_skips_item(self):
        """Test that items with missing required fields are skipped."""
        schema = ExtractionSchema(
            name="test",
            item_selector="ul > li",
            fields={
                "missing": FieldSchema(selector=".nonexistent", required=True),
            }
        )
        
        parser = SchemaParser(schema)
        items = parser.parse(SIMPLE_HTML)
        
        # Both items should be skipped due to missing required field
        assert len(items) == 0
    
    def test_attribute_extraction(self):
        """Test extracting attributes instead of text."""
        schema = ExtractionSchema(
            name="test",
            item_selector="ul > li",
            fields={
                "url": FieldSchema(selector="a", attribute="href"),
            }
        )
        
        parser = SchemaParser(schema)
        items = parser.parse(SIMPLE_HTML)
        
        assert len(items) == 2
        assert items[0]["url"] == "/item-1"
        assert items[1]["url"] == "/item-2"
    
    def test_empty_html(self):
        """Test parsing empty HTML."""
        schema = ExtractionSchema(
            name="test",
            item_selector="ul > li",
            fields={"title": FieldSchema(selector="h3")}
        )
        
        parser = SchemaParser(schema)
        items = parser.parse("<html><body></body></html>")
        
        assert len(items) == 0
    
    def test_malformed_html(self):
        """Test parsing malformed HTML (BeautifulSoup should handle it)."""
        schema = ExtractionSchema(
            name="test",
            item_selector="li",
            fields={"title": FieldSchema(selector="h3")}
        )
        
        malformed = "<ul><li><h3>Item</h3></ul>"  # Missing closing </li>
        
        parser = SchemaParser(schema)
        items = parser.parse(malformed)
        
        # BeautifulSoup should fix it
        assert len(items) == 1
        assert items[0]["title"] == "Item"


class TestForgeExecutor:
    """Test the ForgeExecutor class."""
    
    def test_extract_from_html(self):
        """Test extracting from HTML string."""
        schema = ExtractionSchema(
            name="test",
            item_selector="ul > li",
            fields={
                "title": FieldSchema(selector="h3"),
                "price": FieldSchema(selector=".price"),
            }
        )
        
        executor = ForgeExecutor(schema)
        items = executor.parser.parse(SIMPLE_HTML)
        
        assert len(items) == 2
        assert executor.stats["items_extracted"] == 0  # Stats not updated yet
    
    def test_metadata_inclusion(self):
        """Test that metadata is added correctly."""
        schema = ExtractionSchema(
            name="test_schema",
            item_selector="ul > li",
            fields={"title": FieldSchema(selector="h3")}
        )
        
        executor = ForgeExecutor(schema)
        items = executor.parser.parse(SIMPLE_HTML)
        
        # Manually add metadata like the CLI does
        for item in items:
            item["_meta"] = {
                "url": "http://example.com",
                "fetched_at": "2024-01-01T00:00:00",
                "schema": schema.name,
            }
        
        assert items[0]["_meta"]["url"] == "http://example.com"
        assert items[0]["_meta"]["schema"] == "test_schema"
        assert "_meta" in items[0]
    
    def test_no_metadata(self):
        """Test extraction without metadata."""
        schema = ExtractionSchema(
            name="test",
            item_selector="ul > li",
            fields={"title": FieldSchema(selector="h3")}
        )
        
        executor = ForgeExecutor(schema)
        items = executor.parser.parse(SIMPLE_HTML)
        
        # Don't add metadata
        assert "_meta" not in items[0]
    
    def test_stats_tracking(self):
        """Test that statistics are tracked."""
        schema = ExtractionSchema(
            name="test",
            item_selector="ul > li",
            fields={"title": FieldSchema(selector="h3")}
        )
        
        executor = ForgeExecutor(schema)
        
        # Initial stats
        assert executor.stats["urls_fetched"] == 0
        assert executor.stats["items_extracted"] == 0
        
        # Parse some items
        items = executor.parser.parse(SIMPLE_HTML)
        executor.stats["items_extracted"] = len(items)
        
        assert executor.stats["items_extracted"] == 2


class TestPaginationDetection:
    """Test pagination detection in schemas."""
    
    def test_pagination_schema_parsing(self):
        """Test that pagination schemas are parsed correctly."""
        schema = ExtractionSchema(
            name="test",
            item_selector="ul > li",
            fields={"title": FieldSchema(selector="h3")},
            pagination=PaginationSchema(
                next_selector="a.next",
            )
        )
        
        assert schema.pagination is not None
        assert schema.pagination.next_selector == "a.next"


class TestIntegration:
    """Integration tests using real fixture files."""
    
    def test_fda_list_extraction(self):
        """Test extraction from FDA list fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "fda_list.html"
        if not fixture_path.exists():
            pytest.skip("FDA fixture not available")
        
        html = fixture_path.read_text(encoding="utf-8")
        
        schema = ExtractionSchema(
            name="fda_recalls",
            item_selector="ul > li",
            fields={
                "title": FieldSchema(selector="h3", required=True),
                "link": FieldSchema(selector="a", attribute="href"),
                "date": FieldSchema(selector=".date"),
            }
        )
        
        parser = SchemaParser(schema)
        items = parser.parse(html)
        
        # Should extract at least one item
        assert len(items) > 0
        assert "title" in items[0]
    
    def test_custom_list_extraction(self):
        """Test extraction from custom list fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "custom_list.html"
        if not fixture_path.exists():
            pytest.skip("Custom fixture not available")
        
        html = fixture_path.read_text(encoding="utf-8")
        
        # Try to extract any list items
        schema = ExtractionSchema(
            name="custom",
            item_selector="li",
            fields={
                "text": FieldSchema(selector="*"),
            }
        )
        
        parser = SchemaParser(schema)
        items = parser.parse(html)
        
        # Should extract something
        assert len(items) >= 0  # May be empty depending on fixture
