"""Tests for robust selector building."""

import pytest
from bs4 import BeautifulSoup

from quarry.lib.selectors import (
    build_robust_selector,
    _looks_dynamic,
    _get_stable_marker,
    _is_very_stable,
    simplify_selector,
    extract_structural_pattern,
    validate_selector,
    build_fallback_chain,
    SelectorChain,
)


class TestSelectorBuilder:
    """Test robust CSS selector generation."""

    def test_looks_dynamic(self):
        """Test dynamic class name detection."""
        # Dynamic names
        assert _looks_dynamic("css-1a2b3c4")
        assert _looks_dynamic("sc-1x2y3z")
        assert _looks_dynamic("jsx-2871293847")
        assert _looks_dynamic("MuiBox-root-123")
        assert _looks_dynamic("ab")  # Too short
        assert _looks_dynamic("item-12345678")  # Long numeric suffix

        # Stable names
        assert not _looks_dynamic("title")
        assert not _looks_dynamic("post-content")
        assert not _looks_dynamic("article-header")
        assert not _looks_dynamic("nav-item")

    def test_stable_marker_semantic_tag(self):
        """Test stable marker extraction for semantic tags."""
        html = '<article class="post"><h2>Title</h2></article>'
        soup = BeautifulSoup(html, 'html.parser')
        article = soup.find('article')

        marker = _get_stable_marker(article)
        assert marker == "article.post"

    def test_stable_marker_with_dynamic_class(self):
        """Test that dynamic classes are skipped."""
        html = '<div class="css-1a2b3c post-item"><h2>Title</h2></div>'
        soup = BeautifulSoup(html, 'html.parser')
        div = soup.find('div')

        marker = _get_stable_marker(div)
        assert marker == ".post-item"  # Should skip css-1a2b3c

    def test_robust_selector_with_id(self):
        """Test selector building when element has ID."""
        html = '<div id="main-content"><p>Text</p></div>'
        soup = BeautifulSoup(html, 'html.parser')
        p = soup.find('p')

        # Build selector from p to root
        selector = build_robust_selector(p)
        assert "#main-content" in selector

    def test_robust_selector_deep_nesting(self):
        """Test selector building with deep nesting."""
        html = '''
        <article class="post">
            <div><div><div><div><div><div><div><div><div><div>
                <h2 class="title">Deep Title</h2>
            </div></div></div></div></div></div></div></div></div></div>
        </article>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        h2 = soup.find('h2')

        selector = build_robust_selector(h2)

        # Should not include all 10 divs, should use descendant combinator
        assert selector.count('div') < 5  # Much fewer divs than actual nesting
        assert 'article' in selector or '.post' in selector
        assert 'title' in selector or 'h2' in selector

    def test_robust_selector_with_root(self):
        """Test selector building relative to a root element."""
        html = '''
        <body>
            <article class="post">
                <h2 class="title">Title</h2>
            </article>
        </body>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        article = soup.find('article')
        h2 = soup.find('h2')

        selector = build_robust_selector(h2, root=article)

        # Should not include body, should start from article
        assert 'body' not in selector.lower()
        assert 'article' in selector or 'post' in selector

    def test_simplify_selector(self):
        """Test selector simplification."""
        assert simplify_selector("div.container > div > div > a") == ".container a"
        assert simplify_selector("div > span > a") == "a"
        assert simplify_selector("article.post h2.title") == "article.post h2.title"
        assert simplify_selector("div") == "div"

    def test_obfuscated_classes(self):
        """Test handling of obfuscated/minified class names (Tailwind, CSS modules)."""
        html = '''
        <div class="flex items-center justify-between p-4 bg-white">
            <div class="css-1dbjc4n r-1awozwy r-18u37iz">
                <h2 class="text-lg font-bold item-title">Title</h2>
            </div>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        h2 = soup.find('h2')

        marker = _get_stable_marker(h2)

        # Should pick semantic class "item-title" over utility classes
        assert "item-title" in marker or "h2" in marker
        assert "css-" not in marker
        assert "text-lg" not in marker  # Utility class

    def test_nth_of_type_fallback(self):
        """Test nth-of-type fallback for generic tags without classes."""
        html = '''
        <ul>
            <li>First</li>
            <li>Second</li>
            <li>Third</li>
        </ul>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        lis = soup.find_all('li')

        marker1 = _get_stable_marker(lis[0])
        marker2 = _get_stable_marker(lis[1])

        # Should use nth-of-type for li elements
        assert "nth-of-type" in marker1 or marker1 == "li"
        assert marker1 != marker2  # Different markers for different positions


class TestSelectorChain:
    """Tests for SelectorChain class."""

    def test_select_one_first_match(self):
        """Test select_one returns first matching selector result."""
        html = '<div class="container"><p class="text">Hello</p></div>'
        soup = BeautifulSoup(html, 'html.parser')
        div = soup.find('div')

        chain = SelectorChain([".text", "p"])
        result = chain.select_one(div)

        assert result is not None
        assert result.get_text() == "Hello"

    def test_select_one_fallback(self):
        """Test select_one falls back to second selector if first fails."""
        html = '<div><p>Hello</p></div>'
        soup = BeautifulSoup(html, 'html.parser')
        div = soup.find('div')

        chain = SelectorChain([".nonexistent", "p"])
        result = chain.select_one(div)

        assert result is not None
        assert result.get_text() == "Hello"

    def test_select_one_no_match(self):
        """Test select_one returns None when no selectors match."""
        html = '<div><span>Hello</span></div>'
        soup = BeautifulSoup(html, 'html.parser')
        div = soup.find('div')

        chain = SelectorChain([".nonexistent", "p"])
        result = chain.select_one(div)

        assert result is None

    def test_select_one_invalid_selector(self):
        """Test select_one handles invalid selectors gracefully."""
        html = '<div><p>Hello</p></div>'
        soup = BeautifulSoup(html, 'html.parser')
        div = soup.find('div')

        # Invalid selector syntax should be skipped
        chain = SelectorChain(["[[[invalid", "p"])
        result = chain.select_one(div)

        assert result is not None
        assert result.name == "p"

    def test_select_returns_list(self):
        """Test select returns list of matching elements."""
        html = '<div><p>One</p><p>Two</p><p>Three</p></div>'
        soup = BeautifulSoup(html, 'html.parser')
        div = soup.find('div')

        chain = SelectorChain(["p"])
        results = chain.select(div)

        assert len(results) == 3
        assert results[0].get_text() == "One"

    def test_select_fallback(self):
        """Test select falls back when first selector fails."""
        html = '<div><span>One</span><span>Two</span></div>'
        soup = BeautifulSoup(html, 'html.parser')
        div = soup.find('div')

        chain = SelectorChain([".missing", "span"])
        results = chain.select(div)

        assert len(results) == 2

    def test_select_no_match(self):
        """Test select returns empty list when nothing matches."""
        html = '<div><span>Hello</span></div>'
        soup = BeautifulSoup(html, 'html.parser')
        div = soup.find('div')

        chain = SelectorChain([".missing", "p"])
        results = chain.select(div)

        assert results == []

    def test_select_invalid_selector(self):
        """Test select handles invalid selectors gracefully."""
        html = '<div><span>Hello</span></div>'
        soup = BeautifulSoup(html, 'html.parser')
        div = soup.find('div')

        chain = SelectorChain(["[[[invalid", "span"])
        results = chain.select(div)

        assert len(results) == 1


class TestIsVeryStable:
    """Tests for _is_very_stable function."""

    def test_id_is_very_stable(self):
        """Test that ID selectors are considered very stable."""
        assert _is_very_stable("#main-content")
        assert _is_very_stable("#header")
        assert _is_very_stable("#nav")

    def test_semantic_tag_with_class_is_stable(self):
        """Test semantic tags with classes are stable."""
        assert _is_very_stable("article.post")
        assert _is_very_stable("header.site-header")
        assert _is_very_stable("footer.page-footer")
        assert _is_very_stable("nav.main-nav")
        assert _is_very_stable("main.content")

    def test_semantic_tag_without_class_not_stable(self):
        """Test semantic tags without classes are not very stable."""
        assert not _is_very_stable("article")
        assert not _is_very_stable("header")
        assert not _is_very_stable("nav")

    def test_generic_tag_not_stable(self):
        """Test generic tags are not very stable."""
        assert not _is_very_stable("div.container")
        assert not _is_very_stable("span.text")
        assert not _is_very_stable("p.paragraph")


class TestExtractStructuralPattern:
    """Tests for extract_structural_pattern function."""

    def test_removes_css_dynamic_classes(self):
        """Test removal of CSS-in-JS classes."""
        assert extract_structural_pattern("h3.css-17p10p8 a") == "h3 a"
        # The leading dot is removed and space is cleaned
        assert extract_structural_pattern(".css-1jydbgl article") == "article"

    def test_removes_emotion_classes(self):
        """Test removal of Emotion CSS classes."""
        assert extract_structural_pattern("div.emotion-abc > span") == "div > span"

    def test_removes_underscore_hash_classes(self):
        """Test removal of CSS module hash classes."""
        assert extract_structural_pattern("div._abc123def a") == "div a"

    def test_preserves_normal_classes(self):
        """Test that normal classes are preserved."""
        result = extract_structural_pattern("article.post h2.title")
        assert "article.post" in result
        assert "h2.title" in result

    def test_cleans_extra_spaces(self):
        """Test that extra whitespace is cleaned up."""
        result = extract_structural_pattern("div   span")
        assert "  " not in result


class TestValidateSelector:
    """Tests for validate_selector function."""

    def test_valid_selector_matches(self):
        """Test validation of a working selector."""
        html = '<div><p class="text">Hello World</p></div>'
        soup = BeautifulSoup(html, 'html.parser')

        result = validate_selector(soup, "p.text")

        assert result["valid"] is True
        assert result["count"] == 1
        assert "Hello World" in result["sample_texts"][0]
        assert result["warnings"] == []

    def test_expected_count_match(self):
        """Test validation with expected count that matches."""
        html = '<div><p>One</p><p>Two</p><p>Three</p></div>'
        soup = BeautifulSoup(html, 'html.parser')

        result = validate_selector(soup, "p", expected_count=3)

        assert result["valid"] is True
        assert result["count"] == 3

    def test_expected_count_mismatch(self):
        """Test validation with expected count that doesn't match."""
        html = '<div><p>One</p><p>Two</p></div>'
        soup = BeautifulSoup(html, 'html.parser')

        result = validate_selector(soup, "p", expected_count=5)

        assert result["valid"] is False
        assert result["count"] == 2
        assert any("Expected 5" in w for w in result["warnings"])

    def test_no_matches_warning(self):
        """Test warning when selector matches nothing."""
        html = '<div><span>Hello</span></div>'
        soup = BeautifulSoup(html, 'html.parser')

        result = validate_selector(soup, "p")

        assert result["valid"] is False
        assert result["count"] == 0
        assert any("no elements" in w for w in result["warnings"])

    def test_empty_elements_warning(self):
        """Test warning when matched elements are empty."""
        html = '<div><p></p><p>   </p></div>'
        soup = BeautifulSoup(html, 'html.parser')

        result = validate_selector(soup, "p")

        assert result["count"] == 2
        assert any("empty" in w.lower() for w in result["warnings"])

    def test_dynamic_class_warning(self):
        """Test warning when selector contains dynamic classes."""
        html = '<div class="css-abc123"><p>Text</p></div>'
        soup = BeautifulSoup(html, 'html.parser')

        result = validate_selector(soup, ".css-abc123 p")

        assert result["count"] == 1
        assert any("dynamic" in w.lower() for w in result["warnings"])

    def test_invalid_selector_syntax(self):
        """Test handling of invalid selector syntax."""
        html = '<div><p>Hello</p></div>'
        soup = BeautifulSoup(html, 'html.parser')

        result = validate_selector(soup, "[[[invalid")

        assert result["valid"] is False
        assert result["count"] == 0
        assert any("failed" in w.lower() for w in result["warnings"])

    def test_sample_texts_truncated(self):
        """Test that sample texts are truncated to 100 chars."""
        long_text = "A" * 200
        html = f'<div><p>{long_text}</p></div>'
        soup = BeautifulSoup(html, 'html.parser')

        result = validate_selector(soup, "p")

        assert len(result["sample_texts"][0]) == 100

    def test_sample_texts_limit_three(self):
        """Test that only up to 3 sample texts are returned."""
        html = '<div>' + ''.join(f'<p>Text {i}</p>' for i in range(10)) + '</div>'
        soup = BeautifulSoup(html, 'html.parser')

        result = validate_selector(soup, "p")

        assert result["count"] == 10
        assert len(result["sample_texts"]) == 3


class TestBuildFallbackChain:
    """Tests for build_fallback_chain function."""

    def test_basic_chain(self):
        """Test basic fallback chain creation."""
        chain = build_fallback_chain("h3.css-abc123 a")

        assert len(chain.selectors) >= 2
        assert "h3.css-abc123 a" in chain.selectors

    def test_chain_includes_structural(self):
        """Test that chain includes structural variant."""
        chain = build_fallback_chain("div.css-abc123 h2.emotion-xyz")

        # Should have structural variant without dynamic classes
        assert any("h2" in s and "emotion" not in s for s in chain.selectors)

    def test_chain_includes_tag_only(self):
        """Test that chain includes tag-only variants."""
        chain = build_fallback_chain("article.post h2.title a")

        # Should include tag chain
        selectors = chain.selectors
        assert any("article" in s and "." not in s for s in selectors) or \
               any(s == "a" for s in selectors)

    def test_chain_ordered_specific_to_general(self):
        """Test that chain is ordered from specific to general."""
        chain = build_fallback_chain("h3.css-17p10p8 a")

        # First selector should be the primary
        assert chain.selectors[0] == "h3.css-17p10p8 a"


class TestLooksDynamicEdgeCases:
    """Additional edge case tests for _looks_dynamic function."""

    def test_hex_segments(self):
        """Test detection of hex hash segments."""
        assert _looks_dynamic("item-abc123def")  # 9 hex chars
        assert _looks_dynamic("container-deadbeef")  # 8 hex chars

    def test_uuid_pattern(self):
        """Test UUID pattern detection."""
        assert _looks_dynamic("550e8400-e29b-41d4-a716-446655440000")

    def test_styled_components(self):
        """Test styled-components prefix detection."""
        assert _looks_dynamic("styled-abc123")

    def test_mui_prefix(self):
        """Test MUI/Material-UI prefix detection."""
        assert _looks_dynamic("MuiBox-root")

    def test_empty_string(self):
        """Test empty name is considered dynamic."""
        assert _looks_dynamic("")

    def test_none_value(self):
        """Test None value is considered dynamic."""
        assert _looks_dynamic(None)

    def test_long_numeric_suffix(self):
        """Test long numeric suffix detection."""
        assert _looks_dynamic("element-123456789")  # 9+ digits


class TestBuildRobustSelectorEdgeCases:
    """Additional edge case tests for build_robust_selector."""

    def test_empty_element(self):
        """Test handling of empty/invalid element."""
        result = build_robust_selector(None)
        assert result == ""

    def test_string_element(self):
        """Test handling of non-Tag element (string)."""
        # Pass a plain string - should return empty
        result = build_robust_selector("")  # type: ignore
        assert result == ""

    def test_none_element(self):
        """Test handling of None element."""
        result = build_robust_selector(None)  # type: ignore
        assert result == ""

    def test_multiple_stable_classes(self):
        """Test element with multiple stable classes picks best one."""
        html = '<div class="container wrapper main-content"><p>Text</p></div>'
        soup = BeautifulSoup(html, 'html.parser')
        div = soup.find('div')

        marker = _get_stable_marker(div)
        # Should pick a stable class, not include all
        assert "." in marker or "div" in marker


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
