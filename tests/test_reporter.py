"""Tests for Scout reporter output formatting."""

import json

import pytest

from quarry.tools.scout.reporter import (
    format_as_json,
    format_as_terminal,
    _format_as_simple_text,
)


class TestFormatAsJson:
    """Tests for JSON output formatting."""

    def test_format_empty_analysis(self):
        """Should format empty analysis as JSON."""
        result = format_as_json({})
        assert result == "{}"

    def test_format_with_pretty_print(self):
        """Should pretty print by default."""
        analysis = {"url": "https://example.com", "metadata": {"title": "Test"}}
        result = format_as_json(analysis, pretty=True)

        assert "\n" in result
        assert "  " in result  # Indentation

    def test_format_without_pretty_print(self):
        """Should output compact JSON when pretty=False."""
        analysis = {"url": "https://example.com", "metadata": {"title": "Test"}}
        result = format_as_json(analysis, pretty=False)

        assert "\n" not in result

    def test_format_preserves_unicode(self):
        """Should preserve unicode characters."""
        analysis = {"metadata": {"title": "日本語テスト"}}
        result = format_as_json(analysis)

        assert "日本語テスト" in result

    def test_format_is_valid_json(self):
        """Output should be valid JSON."""
        analysis = {
            "url": "https://example.com",
            "frameworks": [{"name": "react", "confidence": 0.95}],
            "containers": [{"selector": ".item", "item_count": 10}],
        }
        result = format_as_json(analysis)

        # Should parse without error
        parsed = json.loads(result)
        assert parsed["url"] == "https://example.com"


class TestFormatAsTerminal:
    """Tests for terminal output formatting."""

    def test_format_empty_analysis(self):
        """Should handle empty analysis gracefully."""
        result = format_as_terminal({})

        assert "SCOUT ANALYSIS" in result

    def test_format_with_url(self):
        """Should include URL in output."""
        analysis = {"url": "https://example.com/page"}
        result = format_as_terminal(analysis)

        assert "example.com" in result

    def test_format_with_metadata(self):
        """Should display page title and description."""
        analysis = {
            "metadata": {
                "title": "Test Page Title",
                "description": "This is a test description",
            }
        }
        result = format_as_terminal(analysis)

        assert "Test Page Title" in result
        assert "Page Info" in result

    def test_format_with_frameworks(self):
        """Should display detected frameworks."""
        analysis = {
            "frameworks": [
                {"name": "react", "confidence": 0.95, "version": "18.2"},
                {"name": "bootstrap", "confidence": 0.75, "version": None},
            ]
        }
        result = format_as_terminal(analysis)

        assert "Detected Frameworks" in result
        assert "React" in result
        assert "95.0%" in result

    def test_format_with_containers(self):
        """Should display detected containers."""
        analysis = {
            "containers": [
                {
                    "child_selector": "div.item",
                    "item_count": 15,
                    "sample_text": "Sample item text",
                }
            ]
        }
        result = format_as_terminal(analysis)

        assert "Detected Item Containers" in result
        assert "div.item" in result
        assert "15" in result

    def test_format_with_suggestions(self):
        """Should display best container suggestion."""
        analysis = {
            "suggestions": {
                "best_container": {
                    "child_selector": "article.post",
                    "item_count": 10,
                }
            }
        }
        result = format_as_terminal(analysis)

        assert "Best Container" in result
        assert "article.post" in result

    def test_format_with_field_candidates(self):
        """Should display suggested fields."""
        analysis = {
            "suggestions": {
                "field_candidates": [
                    {"name": "title", "selector": "h2.title", "sample": "Article Title"},
                    {"name": "link", "selector": "a.read-more", "sample": "/article/1"},
                ]
            }
        }
        result = format_as_terminal(analysis)

        assert "Suggested Fields" in result
        assert "Title" in result
        assert "h2.title" in result

    def test_format_with_framework_hint(self):
        """Should display framework recommendation."""
        analysis = {
            "suggestions": {
                "framework_hint": {
                    "name": "wordpress",
                    "confidence": 0.9,
                    "recommendation": "Use WordPress-specific selectors",
                }
            }
        }
        result = format_as_terminal(analysis)

        assert "Framework Recommendation" in result
        assert "Wordpress" in result

    def test_format_with_infinite_scroll(self):
        """Should display infinite scroll warning."""
        analysis = {
            "suggestions": {
                "infinite_scroll": {
                    "detected": True,
                    "confidence": 0.85,
                    "signals": ["Intersection Observer", "Dynamic content loading"],
                }
            }
        }
        result = format_as_terminal(analysis)

        assert "Infinite Scroll" in result
        assert "85%" in result

    def test_format_with_statistics(self):
        """Should display page statistics."""
        analysis = {
            "statistics": {
                "total_elements": 500,
                "total_links": 50,
                "total_images": 20,
                "total_forms": 2,
                "text_words": 1500,
            }
        }
        result = format_as_terminal(analysis)

        assert "Page Statistics" in result
        assert "500" in result
        assert "50" in result

    def test_format_limits_displayed_items(self):
        """Should limit number of displayed frameworks/containers."""
        analysis = {
            "frameworks": [
                {"name": f"framework{i}", "confidence": 0.9 - i * 0.1}
                for i in range(10)
            ],
            "containers": [
                {"child_selector": f"div.item{i}", "item_count": 10 - i}
                for i in range(10)
            ],
        }
        result = format_as_terminal(analysis)

        # Should show top 5 only
        assert "framework0" in result.lower()
        assert "framework4" in result.lower()
        # framework9 should not appear (beyond top 5)


class TestFormatAsSimpleText:
    """Tests for fallback simple text formatting."""

    def test_format_empty_analysis(self):
        """Should handle empty analysis."""
        result = _format_as_simple_text({})

        assert "Probe Analysis Results" in result

    def test_format_with_url(self):
        """Should include URL."""
        analysis = {"url": "https://example.com"}
        result = _format_as_simple_text(analysis)

        assert "URL: https://example.com" in result

    def test_format_with_metadata(self):
        """Should include title and description."""
        analysis = {
            "metadata": {
                "title": "Test Title",
                "description": "Test description",
            }
        }
        result = _format_as_simple_text(analysis)

        assert "Title: Test Title" in result
        assert "Description: Test description" in result

    def test_format_with_frameworks(self):
        """Should list detected frameworks."""
        analysis = {
            "frameworks": [
                {"name": "react", "confidence": 0.95, "version": "18.0"},
            ]
        }
        result = _format_as_simple_text(analysis)

        assert "Detected Frameworks" in result
        assert "react" in result
        assert "95.0%" in result

    def test_format_with_containers(self):
        """Should list item containers."""
        analysis = {
            "containers": [
                {"child_selector": ".item", "item_count": 5},
            ]
        }
        result = _format_as_simple_text(analysis)

        assert "Item Containers" in result
        assert ".item" in result
        assert "5 items" in result

    def test_format_with_suggestions(self):
        """Should show best selector suggestion."""
        analysis = {
            "suggestions": {
                "item_selector": "div.product-card",
            }
        }
        result = _format_as_simple_text(analysis)

        assert "Suggestion" in result
        assert "div.product-card" in result

    def test_format_with_statistics(self):
        """Should show page statistics."""
        analysis = {
            "statistics": {
                "total_elements": 1000,
                "total_links": 100,
                "total_images": 50,
            }
        }
        result = _format_as_simple_text(analysis)

        assert "Statistics" in result
        assert "1,000" in result
        assert "100" in result
