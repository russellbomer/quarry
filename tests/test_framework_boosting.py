"""Test framework detection and pattern boosting in selector table."""

from foundry.inspector import find_item_selector


def test_drupal_views_boosting():
    """Test that Drupal Views patterns appear at top of selector table."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="Generator" content="Drupal 9" />
    </head>
    <body class="html not-front not-logged-in">
        <div class="view-content">
            <div class="views-row views-row-1 views-row-odd views-row-first">
                <div class="views-field views-field-field-date">
                    <span class="field-content">01/15/2024</span>
                </div>
                <div class="views-field views-field-title">
                    <span class="field-content"><a href="/node/1">Product Recall A</a></span>
                </div>
            </div>
            <div class="views-row views-row-2 views-row-even">
                <div class="views-field views-field-field-date">
                    <span class="field-content">01/14/2024</span>
                </div>
                <div class="views-field views-field-title">
                    <span class="field-content"><a href="/node/2">Product Recall B</a></span>
                </div>
            </div>
            <div class="views-row views-row-3 views-row-odd">
                <div class="views-field views-field-field-date">
                    <span class="field-content">01/13/2024</span>
                </div>
                <div class="views-field views-field-title">
                    <span class="field-content"><a href="/node/3">Product Recall C</a></span>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    results = find_item_selector(html)
    
    # Should find candidates
    assert len(results) > 0, "Should find selector candidates"
    
    # First result should be .views-row (framework-specific pattern)
    assert results[0]["selector"] == ".views-row", f"Expected .views-row at top, got {results[0]['selector']}"
    assert results[0]["count"] == 3, "Should find 3 views-row elements"
    
    # Should have very_high confidence due to framework match
    assert results[0]["confidence"] == "very_high", "Framework hints should have very_high confidence"


def test_wordpress_boosting():
    """Test that WordPress patterns appear at top of selector table."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="generator" content="WordPress 6.4" />
    </head>
    <body class="home blog">
        <div class="post-1 post type-post hentry">
            <h2 class="entry-title"><a href="/post1">First Post</a></h2>
            <div class="entry-content">Content here</div>
        </div>
        <div class="post-2 post type-post hentry">
            <h2 class="entry-title"><a href="/post2">Second Post</a></h2>
            <div class="entry-content">More content</div>
        </div>
        <div class="post-3 post type-post hentry">
            <h2 class="entry-title"><a href="/post3">Third Post</a></h2>
            <div class="entry-content">Even more content</div>
        </div>
    </body>
    </html>
    """
    
    results = find_item_selector(html)
    
    # Should find candidates
    assert len(results) > 0, "Should find selector candidates"
    
    # First result should be .hentry or .post (framework-specific patterns)
    top_selector = results[0]["selector"]
    assert top_selector in [".hentry", ".post"], f"Expected WordPress pattern at top, got {top_selector}"
    assert results[0]["count"] == 3, "Should find 3 post elements"


def test_bootstrap_card_boosting():
    """Test that Bootstrap card patterns are boosted."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="/bootstrap.min.css">
    </head>
    <body>
        <div class="container">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Card 1</h5>
                    <p class="card-text">Some text</p>
                </div>
            </div>
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Card 2</h5>
                    <p class="card-text">More text</p>
                </div>
            </div>
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Card 3</h5>
                    <p class="card-text">Even more</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    results = find_item_selector(html)
    
    # Should find candidates
    assert len(results) > 0, "Should find selector candidates"
    
    # .card should be in top results due to framework match
    card_result = None
    for result in results[:3]:  # Check top 3
        if result["selector"] == ".card":
            card_result = result
            break
    
    assert card_result is not None, "Bootstrap .card pattern should be in top 3 results"
    assert card_result["count"] == 3, "Should find 3 card elements"


def test_table_rows_high_priority():
    """Test that table rows get high priority even without framework."""
    html = """
    <!DOCTYPE html>
    <html>
    <body>
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Product</th>
                    <th>Company</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>2024-01-15</td>
                    <td>Product A</td>
                    <td>Company A</td>
                </tr>
                <tr>
                    <td>2024-01-14</td>
                    <td>Product B</td>
                    <td>Company B</td>
                </tr>
                <tr>
                    <td>2024-01-13</td>
                    <td>Product C</td>
                    <td>Company C</td>
                </tr>
            </tbody>
        </table>
    </body>
    </html>
    """
    
    results = find_item_selector(html)
    
    # Should find candidates
    assert len(results) > 0, "Should find selector candidates"
    
    # Table rows should be detected
    tr_result = None
    for result in results[:3]:  # Check top 3
        if "tr" in result["selector"]:
            tr_result = result
            break
    
    assert tr_result is not None, "Table rows should be in top 3 results"
    assert tr_result["count"] == 3, "Should find 3 data rows (excluding header)"
    assert tr_result["confidence"] == "high", "Table rows should have high confidence"


def test_no_framework_fallback():
    """Test that generic patterns still work when no framework detected."""
    html = """
    <!DOCTYPE html>
    <html>
    <body>
        <div class="item">
            <h3>Item 1</h3>
            <p>Description 1</p>
        </div>
        <div class="item">
            <h3>Item 2</h3>
            <p>Description 2</p>
        </div>
        <div class="item">
            <h3>Item 3</h3>
            <p>Description 3</p>
        </div>
    </body>
    </html>
    """
    
    results = find_item_selector(html)
    
    # Should find candidates
    assert len(results) > 0, "Should find selector candidates"
    
    # .item should be found
    item_result = None
    for result in results:
        if result["selector"] == ".item":
            item_result = result
            break
    
    assert item_result is not None, "Should find .item selector"
    assert item_result["count"] == 3, "Should find 3 items"
