"""Tests for quarry/framework_profiles/universal/opengraph.py."""

import pytest
from bs4 import BeautifulSoup

from quarry.framework_profiles.universal.opengraph import OpenGraphProfile


class TestOpenGraphDetect:
    """Tests for OpenGraphProfile.detect method."""

    def test_detect_no_og_tags(self):
        """Test detection returns 0 for HTML without OG tags."""
        html = "<html><head><title>Test</title></head></html>"
        score = OpenGraphProfile.detect(html)
        assert score == 0

    def test_detect_single_og_tag(self):
        """Test detection returns low score for single OG tag."""
        html = '<html><head><meta property="og:title" content="Test"></head></html>'
        score = OpenGraphProfile.detect(html)
        assert score >= 25  # Few OG tags + og:title bonus

    def test_detect_three_og_tags(self):
        """Test detection returns medium score for 3+ OG tags."""
        html = """
        <html><head>
            <meta property="og:title" content="Test">
            <meta property="og:description" content="Desc">
            <meta property="og:image" content="img.jpg">
        </head></html>
        """
        score = OpenGraphProfile.detect(html)
        assert score >= 40

    def test_detect_five_og_tags(self):
        """Test detection returns high score for 5+ OG tags."""
        html = """
        <html><head>
            <meta property="og:title" content="Test">
            <meta property="og:description" content="Desc">
            <meta property="og:image" content="img.jpg">
            <meta property="og:url" content="http://example.com">
            <meta property="og:type" content="article">
        </head></html>
        """
        score = OpenGraphProfile.detect(html)
        assert score >= 50

    def test_detect_title_bonus(self):
        """Test og:title adds bonus to score."""
        html_with_title = '<meta property="og:title" content="Test">'
        html_without_title = '<meta property="og:other" content="Test">'

        score_with = OpenGraphProfile.detect(html_with_title)
        score_without = OpenGraphProfile.detect(html_without_title)

        assert score_with > score_without

    def test_detect_all_common_tags(self):
        """Test all common OG tags add to score."""
        html = """
        <html><head>
            <meta property="og:title" content="Title">
            <meta property="og:description" content="Desc">
            <meta property="og:image" content="img.jpg">
            <meta property="og:url" content="http://example.com">
            <meta property="og:type" content="article">
        </head></html>
        """
        score = OpenGraphProfile.detect(html)
        # Should include bonuses for title, description, image, url, type
        assert score >= 80


class TestOpenGraphItemSelectorHints:
    """Tests for get_item_selector_hints method."""

    def test_returns_semantic_fallbacks(self):
        """Test returns semantic element selectors."""
        hints = OpenGraphProfile.get_item_selector_hints()
        assert "article" in hints
        assert "main" in hints
        assert "[role='main']" in hints

    def test_returns_list(self):
        """Test returns a list."""
        hints = OpenGraphProfile.get_item_selector_hints()
        assert isinstance(hints, list)
        assert len(hints) > 0


class TestOpenGraphFieldMappings:
    """Tests for get_field_mappings method."""

    def test_returns_dict(self):
        """Test returns a dictionary."""
        mappings = OpenGraphProfile.get_field_mappings()
        assert isinstance(mappings, dict)

    def test_includes_title_mapping(self):
        """Test includes title field mapping."""
        mappings = OpenGraphProfile.get_field_mappings()
        assert "title" in mappings
        assert any("og:title" in s for s in mappings["title"])

    def test_includes_url_mappings(self):
        """Test includes url/link field mappings."""
        mappings = OpenGraphProfile.get_field_mappings()
        assert "url" in mappings
        assert "link" in mappings

    def test_includes_description_mapping(self):
        """Test includes description field mapping."""
        mappings = OpenGraphProfile.get_field_mappings()
        assert "description" in mappings

    def test_includes_image_mapping(self):
        """Test includes image field mapping."""
        mappings = OpenGraphProfile.get_field_mappings()
        assert "image" in mappings

    def test_includes_date_mapping(self):
        """Test includes date field mapping."""
        mappings = OpenGraphProfile.get_field_mappings()
        assert "date" in mappings
        assert any("published_time" in s for s in mappings["date"])

    def test_includes_author_mapping(self):
        """Test includes author field mapping."""
        mappings = OpenGraphProfile.get_field_mappings()
        assert "author" in mappings

    def test_all_mappings_use_attr_syntax(self):
        """Test all mappings use ::attr(content) syntax."""
        mappings = OpenGraphProfile.get_field_mappings()
        for field, selectors in mappings.items():
            for selector in selectors:
                assert "::attr(content)" in selector


class TestOpenGraphExtractMetadata:
    """Tests for extract_metadata method."""

    def test_extract_empty_html(self):
        """Test extract from empty HTML returns empty dict."""
        result = OpenGraphProfile.extract_metadata("")
        assert result == {}

    def test_extract_no_og_tags(self):
        """Test extract from HTML without OG tags."""
        html = "<html><head><title>Test</title></head></html>"
        result = OpenGraphProfile.extract_metadata(html)
        assert result == {}

    def test_extract_basic_og_tags(self):
        """Test extract basic OG tags."""
        html = """
        <html><head>
            <meta property="og:title" content="My Title">
            <meta property="og:description" content="My Description">
        </head></html>
        """
        result = OpenGraphProfile.extract_metadata(html)
        assert result["title"] == "My Title"
        assert result["description"] == "My Description"

    def test_extract_strips_og_prefix(self):
        """Test og: prefix is stripped from keys."""
        html = '<meta property="og:title" content="Test">'
        result = OpenGraphProfile.extract_metadata(html)
        assert "title" in result
        assert "og:title" not in result

    def test_extract_all_og_properties(self):
        """Test extracts all OG properties."""
        html = """
        <html><head>
            <meta property="og:title" content="Title">
            <meta property="og:description" content="Description">
            <meta property="og:image" content="https://example.com/img.jpg">
            <meta property="og:url" content="https://example.com/page">
            <meta property="og:type" content="article">
            <meta property="og:site_name" content="Example Site">
        </head></html>
        """
        result = OpenGraphProfile.extract_metadata(html)
        assert result["title"] == "Title"
        assert result["description"] == "Description"
        assert result["image"] == "https://example.com/img.jpg"
        assert result["url"] == "https://example.com/page"
        assert result["type"] == "article"
        assert result["site_name"] == "Example Site"

    def test_extract_article_namespace(self):
        """Test extracts article: namespace tags."""
        html = """
        <html><head>
            <meta property="article:published_time" content="2024-01-15T10:00:00Z">
            <meta property="article:author" content="John Doe">
            <meta property="article:section" content="Technology">
        </head></html>
        """
        result = OpenGraphProfile.extract_metadata(html)
        assert result["published_time"] == "2024-01-15T10:00:00Z"
        assert result["author"] == "John Doe"
        assert result["section"] == "Technology"

    def test_extract_skips_empty_content(self):
        """Test skips tags with empty content."""
        html = """
        <html><head>
            <meta property="og:title" content="Valid Title">
            <meta property="og:description" content="">
        </head></html>
        """
        result = OpenGraphProfile.extract_metadata(html)
        assert "title" in result
        assert "description" not in result

    def test_extract_mixed_og_and_article(self):
        """Test extracts both og: and article: namespaces."""
        html = """
        <html><head>
            <meta property="og:title" content="Article Title">
            <meta property="article:author" content="Jane Smith">
        </head></html>
        """
        result = OpenGraphProfile.extract_metadata(html)
        assert result["title"] == "Article Title"
        assert result["author"] == "Jane Smith"


class TestOpenGraphProfileName:
    """Tests for profile name attribute."""

    def test_name_is_opengraph(self):
        """Test profile name is 'opengraph'."""
        assert OpenGraphProfile.name == "opengraph"
