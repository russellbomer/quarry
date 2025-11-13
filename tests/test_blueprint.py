"""Tests for Blueprint tool."""

from pathlib import Path

import pytest

from foundry.lib.schemas import (
    ExtractionSchema,
    FieldSchema,
    load_schema,
    save_schema,
    validate_schema_dict,
)
from foundry.tools.blueprint.preview import preview_extraction, format_preview


class TestSchemaModel:
    """Test schema data models."""
    
    def test_field_schema_basic(self):
        """Test basic field schema."""
        field = FieldSchema(selector=".title")
        assert field.selector == ".title"
        assert field.attribute is None
        assert field.required is False
        assert field.multiple is False
    
    def test_field_schema_with_attribute(self):
        """Test field schema with attribute extraction."""
        field = FieldSchema(selector="a", attribute="href", required=True)
        assert field.selector == "a"
        assert field.attribute == "href"
        assert field.required is True
    
    def test_field_schema_validation(self):
        """Test field schema validation."""
        with pytest.raises(ValueError, match="Selector cannot be empty"):
            FieldSchema(selector="")
    
    def test_extraction_schema_basic(self):
        """Test basic extraction schema."""
        schema = ExtractionSchema(
            name="test",
            item_selector=".item",
            fields={
                "title": FieldSchema(selector="h3"),
                "link": FieldSchema(selector="a", attribute="href"),
            }
        )
        
        assert schema.name == "test"
        assert schema.item_selector == ".item"
        assert len(schema.fields) == 2
        assert "title" in schema.fields
        assert "link" in schema.fields
    
    def test_extraction_schema_validation(self):
        """Test extraction schema validation."""
        # Name required
        with pytest.raises(ValueError):
            ExtractionSchema(
                name="",
                item_selector=".item",
                fields={"title": FieldSchema(selector="h3")}
            )
        
        # Item selector required
        with pytest.raises(ValueError):
            ExtractionSchema(
                name="test",
                item_selector="",
                fields={"title": FieldSchema(selector="h3")}
            )
        
        # At least one field required
        with pytest.raises(ValueError):
            ExtractionSchema(
                name="test",
                item_selector=".item",
                fields={}
            )


class TestSchemaIO:
    """Test schema loading and saving."""
    
    def test_save_and_load_schema(self, tmp_path):
        """Test saving and loading schema."""
        schema = ExtractionSchema(
            name="test_schema",
            description="Test description",
            item_selector=".article",
            fields={
                "title": FieldSchema(selector="h2", required=True),
                "url": FieldSchema(selector="a", attribute="href"),
            }
        )
        
        # Save
        schema_path = tmp_path / "test.yml"
        save_schema(schema, schema_path)
        
        assert schema_path.exists()
        
        # Load
        loaded = load_schema(schema_path)
        
        assert loaded.name == "test_schema"
        assert loaded.description == "Test description"
        assert loaded.item_selector == ".article"
        assert len(loaded.fields) == 2
        assert loaded.fields["title"].required is True
        assert loaded.fields["url"].attribute == "href"
    
    def test_load_invalid_file(self):
        """Test loading non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_schema("nonexistent.yml")
    
    def test_validate_schema_dict(self):
        """Test schema dict validation."""
        # Valid schema
        valid, error = validate_schema_dict({
            "name": "test",
            "item_selector": ".item",
            "fields": {
                "title": {"selector": "h3"}
            }
        })
        
        assert valid is True
        assert error == ""
        
        # Invalid schema (missing fields)
        valid, error = validate_schema_dict({
            "name": "test",
            "item_selector": ".item",
            "fields": {}
        })
        
        assert valid is False
        assert "field" in error.lower()


class TestPreview:
    """Test extraction preview."""
    
    def test_preview_basic_extraction(self):
        """Test basic extraction preview."""
        html = """
        <html>
        <body>
            <ul>
                <li class="item">
                    <h3>Title 1</h3>
                    <a href="/link1">Link</a>
                </li>
                <li class="item">
                    <h3>Title 2</h3>
                    <a href="/link2">Link</a>
                </li>
            </ul>
        </body>
        </html>
        """
        
        schema = ExtractionSchema(
            name="test",
            item_selector=".item",
            fields={
                "title": FieldSchema(selector="h3"),
                "link": FieldSchema(selector="a", attribute="href"),
            }
        )
        
        items = preview_extraction(html, schema)
        
        assert len(items) == 2
        assert items[0]["title"] == "Title 1"
        assert items[0]["link"] == "/link1"
        assert items[1]["title"] == "Title 2"
        assert items[1]["link"] == "/link2"
    
    def test_preview_with_limit(self):
        """Test preview respects limit parameter."""
        html = """
        <html>
        <body>
            <div class="item">Item 1</div>
            <div class="item">Item 2</div>
            <div class="item">Item 3</div>
            <div class="item">Item 4</div>
            <div class="item">Item 5</div>
        </body>
        </html>
        """
        
        schema = ExtractionSchema(
            name="test",
            item_selector=".item",
            fields={
                "text": FieldSchema(selector=".item"),  # Self selector
            }
        )
        
        items = preview_extraction(html, schema, limit=3)
        
        assert len(items) == 3
    
    def test_preview_missing_fields(self):
        """Test preview with missing optional fields."""
        html = """
        <html>
        <body>
            <div class="item">
                <h3>Title Only</h3>
            </div>
        </body>
        </html>
        """
        
        schema = ExtractionSchema(
            name="test",
            item_selector=".item",
            fields={
                "title": FieldSchema(selector="h3"),
                "link": FieldSchema(selector="a", attribute="href", required=False, default="N/A"),
            }
        )
        
        items = preview_extraction(html, schema)
        
        assert len(items) == 1
        assert items[0]["title"] == "Title Only"
        assert items[0]["link"] == "N/A"  # Default value
    
    def test_preview_empty_html(self):
        """Test preview with empty HTML."""
        schema = ExtractionSchema(
            name="test",
            item_selector=".item",
            fields={"title": FieldSchema(selector="h3")},
        )
        
        items = preview_extraction("", schema)
        
        assert len(items) == 0
    
    def test_preview_no_matches(self):
        """Test preview when selector doesn't match."""
        html = "<html><body><p>No items</p></body></html>"
        
        schema = ExtractionSchema(
            name="test",
            item_selector=".item",
            fields={"title": FieldSchema(selector="h3")},
        )
        
        items = preview_extraction(html, schema)
        
        assert len(items) == 0
    
    def test_format_preview(self):
        """Test preview formatting."""
        items = [
            {"title": "Item 1", "link": "http://example.com/1"},
            {"title": "Item 2", "link": "http://example.com/2"},
        ]
        
        output = format_preview(items, limit=5)
        
        # Should contain item data
        assert "Item 1" in output
        assert "Item 2" in output
    
    def test_preview_fda_fixture(self):
        """Test preview with real FDA fixture."""
        fixture_path = Path("tests/fixtures/fda_list.html")
        if not fixture_path.exists():
            pytest.skip("Fixture not found")
        
        html = fixture_path.read_text()
        
        schema = ExtractionSchema(
            name="fda_recalls",
            item_selector="ul > li",
            fields={
                "title": FieldSchema(selector="h3"),
                "link": FieldSchema(selector="a", attribute="href"),
            }
        )
        
        items = preview_extraction(html, schema, limit=5)
        
        # Should extract items
        assert len(items) > 0
        assert "title" in items[0]
        assert "link" in items[0]
