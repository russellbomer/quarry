"""Tests for robust selector building."""

import pytest
from bs4 import BeautifulSoup

from scrapesuite.selector_builder import (
    build_robust_selector,
    _looks_dynamic,
    _get_stable_marker,
    simplify_selector,
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
        marker3 = _get_stable_marker(lis[2])
        
        # Should use nth-of-type for li elements
        assert "nth-of-type" in marker1 or marker1 == "li"
        assert marker1 != marker2  # Different markers for different positions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
