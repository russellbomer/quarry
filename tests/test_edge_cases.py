"""Tests for edge cases and error handling."""

from scrapesuite.inspector import find_item_selector, inspect_html, preview_extraction


def test_inspect_html_empty_string():
    """Empty HTML returns safe defaults."""
    result = inspect_html("")
    assert result["title"] == ""
    assert result["total_links"] == 0
    assert result["repeated_classes"] == []


def test_inspect_html_whitespace_only():
    """Whitespace-only HTML returns safe defaults."""
    result = inspect_html("   \n\t  ")
    assert result["title"] == ""
    assert result["total_links"] == 0


def test_inspect_html_minimal():
    """Minimal valid HTML works."""
    result = inspect_html("<html><body><p>Test</p></body></html>")
    assert "title" in result
    assert "total_links" in result


def test_find_item_selector_empty_html():
    """Empty HTML returns empty candidates list."""
    candidates = find_item_selector("")
    assert candidates == []


def test_find_item_selector_no_items():
    """HTML with no repeated items returns empty list."""
    html = "<html><body><p>One item</p></body></html>"
    candidates = find_item_selector(html, min_items=3)
    assert candidates == []


def test_find_item_selector_malformed_html():
    """Malformed HTML is handled gracefully."""
    html = "<div><span>Unclosed tags<div><p>More stuff"
    # Should not crash, BeautifulSoup auto-fixes
    candidates = find_item_selector(html)
    # May or may not find items, but shouldn't crash
    assert isinstance(candidates, list)


def test_find_item_selector_very_large_html():
    """Large HTML with many items doesn't hang."""
    # Create HTML with 100 repeated items
    items = "\n".join([f'<div class="item">Item {i}</div>' for i in range(100)])
    html = f"<html><body>{items}</body></html>"
    
    candidates = find_item_selector(html, min_items=10)
    assert len(candidates) > 0
    
    # Should find .item with count=100
    item_candidate = next((c for c in candidates if "item" in c["selector"]), None)
    assert item_candidate is not None
    assert item_candidate["count"] >= 100


def test_find_item_selector_deeply_nested():
    """Deeply nested items are detected."""
    html = """
    <html>
    <body>
        <div><div><div><div><div>
            <article class="post">Post 1</article>
            <article class="post">Post 2</article>
            <article class="post">Post 3</article>
        </div></div></div></div></div>
    </body>
    </html>
    """
    candidates = find_item_selector(html, min_items=3)
    assert len(candidates) > 0
    # Should find article.post or .post
    assert any("post" in c["selector"] for c in candidates)


def test_find_item_selector_unicode_content():
    """Unicode and emoji content is handled."""
    html = """
    <html><body>
        <div class="item">🎉 Item 1: 日本語</div>
        <div class="item">🚀 Item 2: Español</div>
        <div class="item">✨ Item 3: Français</div>
    </body></html>
    """
    candidates = find_item_selector(html, min_items=3)
    assert len(candidates) > 0
    item_candidate = next((c for c in candidates if "item" in c["selector"]), None)
    assert item_candidate is not None
    # Sample should contain unicode
    assert "Item" in item_candidate["sample_title"]


def test_preview_extraction_empty_html():
    """Empty HTML returns empty preview."""
    result = preview_extraction("", "div.item", {"title": ".title"})
    assert result == []


def test_preview_extraction_invalid_selector():
    """Invalid item selector returns empty preview."""
    html = "<html><body><div class='item'>Test</div></body></html>"
    # Invalid CSS selector syntax
    result = preview_extraction(html, "div[[[invalid", {"title": ".title"})
    assert result == []


def test_preview_extraction_empty_selector():
    """Empty item selector returns empty preview."""
    html = "<html><body><div>Test</div></body></html>"
    result = preview_extraction(html, "", {"title": "div"})
    assert result == []


def test_preview_extraction_no_items_match():
    """Selector that matches nothing returns empty preview."""
    html = "<html><body><div class='item'>Test</div></body></html>"
    result = preview_extraction(html, ".nonexistent", {"title": ".title"})
    assert result == []


def test_preview_extraction_empty_field_selector():
    """Empty field selectors handled gracefully."""
    html = """
    <html><body>
        <div class="item">
            <h2 class="title">Test</h2>
        </div>
    </body></html>
    """
    result = preview_extraction(html, "div.item", {"title": "", "url": ".link"})
    assert len(result) == 1
    assert result[0]["title"] == ""
    assert result[0]["url"] == ""


def test_preview_extraction_invalid_field_selector():
    """Invalid field selector returns error marker."""
    html = """
    <html><body>
        <div class="item">
            <h2 class="title">Test</h2>
        </div>
    </body></html>
    """
    result = preview_extraction(html, "div.item", {"title": "div[[[broken"})
    assert len(result) == 1
    assert result[0]["title"] == "[extraction failed]"


def test_preview_extraction_attribute_extraction():
    """Attribute extraction works correctly."""
    html = """
    <html><body>
        <div class="item">
            <a href="https://example.com" class="link">Link</a>
        </div>
    </body></html>
    """
    result = preview_extraction(html, "div.item", {"url": "a.link::attr(href)"})
    assert len(result) == 1
    assert result[0]["url"] == "https://example.com"


def test_preview_extraction_missing_attribute():
    """Missing attribute returns empty string."""
    html = """
    <html><body>
        <div class="item">
            <a class="link">No href</a>
        </div>
    </body></html>
    """
    result = preview_extraction(html, "div.item", {"url": "a.link::attr(href)"})
    assert len(result) == 1
    assert result[0]["url"] == ""


def test_preview_extraction_limits_to_three():
    """Preview limits to first 3 items."""
    items = "\n".join([f'<div class="item"><h2>Item {i}</h2></div>' for i in range(10)])
    html = f"<html><body>{items}</body></html>"
    
    result = preview_extraction(html, "div.item", {"title": "h2"})
    assert len(result) == 3
    assert result[0]["title"] == "Item 0"
    assert result[2]["title"] == "Item 2"


def test_find_item_selector_javascript_comments():
    """HTML with JavaScript comments doesn't confuse parser."""
    html = """
    <html><body>
        <!-- <div class="fake">Not real</div> -->
        <div class="item">Item 1</div>
        <div class="item">Item 2</div>
        <div class="item">Item 3</div>
    </body></html>
    """
    candidates = find_item_selector(html, min_items=3)
    assert len(candidates) > 0
    # Should find .item, not .fake
    assert any("item" in c["selector"] for c in candidates)


def test_find_item_selector_with_scripts_and_styles():
    """Script and style tags don't interfere with detection."""
    html = """
    <html>
    <head>
        <style>.item { color: red; }</style>
        <script>var item = "fake";</script>
    </head>
    <body>
        <div class="item">Item 1</div>
        <div class="item">Item 2</div>
        <div class="item">Item 3</div>
    </body>
    </html>
    """
    candidates = find_item_selector(html, min_items=3)
    assert len(candidates) > 0
    assert any("item" in c["selector"] for c in candidates)


def test_inspect_html_with_no_title():
    """HTML without title tag returns empty title."""
    html = "<html><body><p>No title tag</p></body></html>"
    result = inspect_html(html)
    # Should not crash, returns empty or default
    assert isinstance(result["title"], str)


def test_find_item_selector_mixed_content():
    """Items with mixed text and HTML content work."""
    html = """
    <html><body>
        <div class="item">
            <strong>Bold</strong> and <em>italic</em> text
        </div>
        <div class="item">
            <strong>More</strong> mixed content
        </div>
        <div class="item">
            <strong>Third</strong> item
        </div>
    </body></html>
    """
    candidates = find_item_selector(html, min_items=3)
    assert len(candidates) > 0


def test_find_item_selector_special_characters_in_class():
    """Class names with special characters (hyphens, underscores) work."""
    html = """
    <html><body>
        <div class="item-card_v2">Item 1</div>
        <div class="item-card_v2">Item 2</div>
        <div class="item-card_v2">Item 3</div>
    </body></html>
    """
    candidates = find_item_selector(html, min_items=3)
    assert len(candidates) > 0
    assert any("item-card_v2" in c["selector"] for c in candidates)


def test_preview_extraction_self_attribute():
    """Extracting attribute from item itself works."""
    html = """
    <html><body>
        <div class="item" data-id="123">
            <p>Content</p>
        </div>
    </body></html>
    """
    result = preview_extraction(html, "div.item", {"id": "::attr(data-id)"})
    assert len(result) == 1
    assert result[0]["id"] == "123"
