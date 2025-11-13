"""Test GenericConnector with real HTML."""

import pytest


def test_generic_connector_basic(monkeypatch):
    """Test GenericConnector with simple HTML."""
    html = """
    <html>
        <div class="item">
            <h2 class="title">Article 1</h2>
            <a href="/post/1">Read more</a>
        </div>
        <div class="item">
            <h2 class="title">Article 2</h2>
            <a href="/post/2">Read more</a>
        </div>
        <div class="item">
            <h2 class="title">Article 3</h2>
            <a href="/post/3">Read more</a>
        </div>
    </html>
    """
    
    config = {
        "selectors": {
            "item": ".item",
            "fields": {
                "title": "h2.title",
                "url": "a::attr(href)",
            }
        }
    }
    
    # Mock get_html using monkeypatch
    def mock_get_html(url):
        return html
    
    import foundry.connectors.generic
    monkeypatch.setattr(foundry.connectors.generic, "get_html", mock_get_html)
    
    from foundry.connectors.generic import GenericConnector
    
    connector = GenericConnector(
        entry_url="https://example.com/",
        config=config,
    )
    
    records, cursor = connector.collect(cursor=None, max_items=10, offline=False)
    
    assert len(records) == 3, f"Expected 3 records, got {len(records)}"
    assert records[0]["title"] == "Article 1"
    assert records[0]["url"] == "/post/1"
    assert records[1]["title"] == "Article 2"
    assert records[2]["title"] == "Article 3"
    assert cursor == "/post/3"  # Last URL


def test_generic_connector_attribute_extraction(monkeypatch):
    """Test ::attr() syntax for extracting attributes."""
    html = """
    <html>
        <article class="post" data-id="123">
            <h1>Title</h1>
            <time datetime="2024-01-15T10:00:00Z">Jan 15</time>
            <img src="/image.jpg" alt="Thumbnail" />
        </article>
    </html>
    """
    
    config = {
        "selectors": {
            "item": ".post",
            "fields": {
                "id": "::attr(data-id)",
                "title": "h1",
                "date": "time::attr(datetime)",
                "image": "img::attr(src)",
            }
        }
    }
    
    def mock_get_html(url):
        return html
    
    import foundry.connectors.generic
    monkeypatch.setattr(foundry.connectors.generic, "get_html", mock_get_html)
    
    from foundry.connectors.generic import GenericConnector
    
    connector = GenericConnector(
        entry_url="https://example.com/",
        config=config,
    )
    
    records, cursor = connector.collect(cursor=None, max_items=10, offline=False)
    
    assert len(records) == 1
    assert records[0]["id"] == "123"
    assert records[0]["title"] == "Title"
    assert records[0]["date"] == "2024-01-15T10:00:00Z"
    assert records[0]["image"] == "/image.jpg"


def test_generic_connector_missing_selectors():
    """Test error handling for missing selectors config."""
    from foundry.connectors.generic import GenericConnector
    
    connector = GenericConnector(
        entry_url="https://example.com/",
        config={},  # No selectors
    )
    
    with pytest.raises(ValueError, match="requires 'selectors.item'"):
        connector.collect(cursor=None, max_items=10, offline=False)
