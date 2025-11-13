"""Tests for Probe tool."""

from pathlib import Path

import pytest

from foundry.tools.probe.analyzer import analyze_page
from foundry.tools.probe.reporter import format_as_json, format_as_terminal


class TestProbeAnalyzer:
    """Test the Probe analyzer."""
    
    def test_analyze_page_basic(self):
        """Test basic page analysis."""
        html = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <ul class="items">
                <li><h3>Item 1</h3><p>Description 1</p></li>
                <li><h3>Item 2</h3><p>Description 2</p></li>
                <li><h3>Item 3</h3><p>Description 3</p></li>
            </ul>
        </body>
        </html>
        """
        
        result = analyze_page(html, url="https://example.com")
        
        # Check structure
        assert "url" in result
        assert "frameworks" in result
        assert "containers" in result
        assert "metadata" in result
        assert "statistics" in result
        assert "suggestions" in result
        
        # Check URL
        assert result["url"] == "https://example.com"
        
        # Check containers found
        assert len(result["containers"]) > 0
        container = result["containers"][0]
        assert container["item_count"] == 3
        assert "li" in container["child_selector"]
        
        # Check statistics
        stats = result["statistics"]
        assert stats["total_elements"] > 0
        assert stats["total_lists"] == 1
    
    def test_analyze_fda_fixture(self):
        """Test analysis of FDA fixture."""
        fixture_path = Path("tests/fixtures/fda_list.html")
        if not fixture_path.exists():
            pytest.skip("Fixture not found")
        
        html = fixture_path.read_text()
        result = analyze_page(html)
        
        # Should detect containers
        assert len(result["containers"]) > 0
        
        # Should have metadata
        assert result["metadata"]["title"] == "FDA Recalls"
        
        # Should have suggestions
        assert result["suggestions"]["best_container"] is not None
    
    def test_analyze_empty_html(self):
        """Test analysis of empty HTML."""
        result = analyze_page("", url="https://example.com")
        
        # Should return empty but valid structure
        assert result["url"] == "https://example.com"
        assert result["frameworks"] == []
        assert result["containers"] == []
        assert result["metadata"] == {}


class TestProbeReporter:
    """Test the Probe reporter."""
    
    def test_format_as_json(self):
        """Test JSON formatting."""
        analysis = {
            "url": "https://example.com",
            "frameworks": [],
            "containers": [],
            "metadata": {"title": "Test"},
            "statistics": {},
            "suggestions": {},
        }
        
        result = format_as_json(analysis, pretty=True)
        
        # Should be valid JSON
        import json
        parsed = json.loads(result)
        assert parsed["url"] == "https://example.com"
        assert parsed["metadata"]["title"] == "Test"
    
    def test_format_as_json_compact(self):
        """Test compact JSON formatting."""
        analysis = {
            "url": "https://example.com",
            "frameworks": [],
            "containers": [],
            "metadata": {},
            "statistics": {},
            "suggestions": {},
        }
        
        result = format_as_json(analysis, pretty=False)
        
        # Should be on one line
        assert "\n" not in result
    
    def test_format_as_terminal(self):
        """Test terminal formatting."""
        analysis = {
            "url": "https://example.com",
            "frameworks": [
                {"name": "bootstrap", "confidence": 0.95, "version": "5.0"},
            ],
            "containers": [
                {
                    "child_selector": ".item",
                    "item_count": 10,
                    "sample_text": "Sample item text",
                }
            ],
            "metadata": {"title": "Test Page"},
            "statistics": {
                "total_elements": 100,
                "total_links": 20,
                "total_images": 5,
                "text_words": 500,
            },
            "suggestions": {
                "best_container": {
                    "child_selector": ".item",
                    "item_count": 10,
                }
            },
        }
        
        result = format_as_terminal(analysis)
        
        # Should contain key information
        assert "PROBE ANALYSIS" in result
        assert "Test Page" in result
        assert "bootstrap" in result.lower()
        assert ".item" in result
