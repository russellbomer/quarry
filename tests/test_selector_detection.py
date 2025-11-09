"""
Real-world selector detection test suite.

Tests wizard's ability to detect correct selectors on actual websites.
"""

import pytest
from bs4 import BeautifulSoup

from scrapesuite.inspector import find_item_selector, generate_field_selector


class TestRealWorldSelectorDetection:
    """Test selector detection on real-world HTML patterns."""
    
    def test_hacker_news_pattern(self):
        """Test Hacker News structure - vote buttons before title."""
        html = '''
        <table class="itemlist">
          <tr class="athing" id="123">
            <td><a href="vote?id=123"><div class="votearrow"></div></a></td>
            <td class="title"><span class="titleline">
              <a href="https://example.com/article">Amazing Article Title</a>
            </span></td>
          </tr>
          <tr class="athing" id="124">
            <td><a href="vote?id=124"><div class="votearrow"></div></a></td>
            <td class="title"><span class="titleline">
              <a href="https://example.com/article2">Another Great Read</a>
            </span></td>
          </tr>
          <tr class="athing" id="125">
            <td><a href="vote?id=125"><div class="votearrow"></div></a></td>
            <td class="title"><span class="titleline">
              <a href="https://example.com/article3">Third Article</a>
            </span></td>
          </tr>
        </table>
        '''
        
        # Should detect .athing as item selector
        candidates = find_item_selector(html, min_items=3)
        selectors = [c["selector"] for c in candidates]
        
        assert ".athing" in selectors or "tr.athing" in selectors, \
            f"Should detect .athing, got: {selectors}"
        
        # Should generate correct title selector (not vote button)
        soup = BeautifulSoup(html, 'html.parser')
        item = soup.select_one('.athing')
        
        title_selector = generate_field_selector(item, 'title')
        assert title_selector is not None, "Should detect title selector"
        
        # Verify it extracts correct content (not vote link)
        title_elem = item.select_one(title_selector.replace('::attr(href)', ''))
        assert title_elem is not None
        title_text = title_elem.get_text(strip=True)
        assert len(title_text) > 10, f"Title too short: {title_text}"
        assert "Article" in title_text, f"Should extract article title, got: {title_text}"
    
    def test_fda_fixture_pattern(self):
        """Test FDA fixture structure."""
        html = '''
        <html>
          <body>
            <h1>Recalls</h1>
            <ul>
              <li>
                <article class="recall-item">
                  <h3><a href="/safety/recalls-market-withdrawals-safety-alerts/acme-allergy">Acme Foods allergy alert</a></h3>
                  <time datetime="2024-01-15">2024-01-15</time>
                </article>
              </li>
              <li>
                <article class="recall-item">
                  <h3><a href="/safety/recalls-market-withdrawals-safety-alerts/contoso-dairy">Contoso Dairy recall</a></h3>
                  <time datetime="2024-01-14">2024-01-14</time>
                </article>
              </li>
              <li>
                <article class="recall-item">
                  <h3><a href="/safety/recalls-market-withdrawals-safety-alerts/fabrikam-snacks">Fabrikam Snacks recall</a></h3>
                  <time datetime="2024-01-13">2024-01-13</time>
                </article>
              </li>
            </ul>
          </body>
        </html>
        '''
        
        candidates = find_item_selector(html, min_items=3)
        selectors = [c["selector"] for c in candidates]
        
        assert ".recall-item" in selectors or "article.recall-item" in selectors, \
            f"Should detect .recall-item, got: {selectors}"
        
        # Test field generation
        soup = BeautifulSoup(html, 'html.parser')
        item = soup.select_one('.recall-item')
        
        title_selector = generate_field_selector(item, 'title')
        assert title_selector is not None
        
        date_selector = generate_field_selector(item, 'date')
        assert date_selector is not None
        assert "time" in date_selector.lower()
    
    def test_blog_post_pattern(self):
        """Test common blog post structure."""
        html = '''
        <main>
          <article class="post">
            <header>
              <h2><a href="/post/1">First Blog Post</a></h2>
              <p class="meta">
                <span class="author">John Doe</span>
                <time datetime="2024-01-15">January 15, 2024</time>
              </p>
            </header>
          </article>
          <article class="post">
            <header>
              <h2><a href="/post/2">Second Blog Post</a></h2>
              <p class="meta">
                <span class="author">Jane Smith</span>
                <time datetime="2024-01-14">January 14, 2024</time>
              </p>
            </header>
          </article>
          <article class="post">
            <header>
              <h2><a href="/post/3">Third Blog Post</a></h2>
              <p class="meta">
                <span class="author">Bob Wilson</span>
                <time datetime="2024-01-13">January 13, 2024</time>
              </p>
            </header>
          </article>
        </main>
        '''
        
        candidates = find_item_selector(html, min_items=3)
        selectors = [c["selector"] for c in candidates]
        
        assert ".post" in selectors or "article.post" in selectors, \
            f"Should detect .post, got: {selectors}"
        
        soup = BeautifulSoup(html, 'html.parser')
        item = soup.select_one('.post')
        
        # Should detect h2 for title
        title_selector = generate_field_selector(item, 'title')
        assert title_selector is not None
        assert "h2" in title_selector.lower()
        
        # Should detect author
        author_selector = generate_field_selector(item, 'author')
        assert author_selector is not None
        assert "author" in author_selector.lower()
        
        # Should detect date
        date_selector = generate_field_selector(item, 'date')
        assert date_selector is not None
        assert "time" in date_selector.lower()
    
    def test_no_class_list_items(self):
        """Test structure without explicit classes (harder case)."""
        html = '''
        <ul id="results">
          <li>
            <h3><a href="/item/1">First Item</a></h3>
            <p>Description here</p>
          </li>
          <li>
            <h3><a href="/item/2">Second Item</a></h3>
            <p>Description here</p>
          </li>
          <li>
            <h3><a href="/item/3">Third Item</a></h3>
            <p>Description here</p>
          </li>
        </ul>
        '''
        
        candidates = find_item_selector(html, min_items=3)
        selectors = [c["selector"] for c in candidates]
        
        # Should at least detect 'li' as repeated pattern
        assert "li" in selectors or any("li" in s for s in selectors), \
            f"Should detect li elements, got: {selectors}"
    
    def test_table_rows_pattern(self):
        """Test table-based listings."""
        html = '''
        <table class="data-table">
          <tbody>
            <tr class="data-row">
              <td><a href="/item/1">Item One</a></td>
              <td>2024-01-15</td>
              <td>John</td>
            </tr>
            <tr class="data-row">
              <td><a href="/item/2">Item Two</a></td>
              <td>2024-01-14</td>
              <td>Jane</td>
            </tr>
            <tr class="data-row">
              <td><a href="/item/3">Item Three</a></td>
              <td>2024-01-13</td>
              <td>Bob</td>
            </tr>
          </tbody>
        </table>
        '''
        
        candidates = find_item_selector(html, min_items=3)
        selectors = [c["selector"] for c in candidates]
        
        assert ".data-row" in selectors or "tr.data-row" in selectors, \
            f"Should detect .data-row, got: {selectors}"
    
    def test_unicode_and_emoji_content(self):
        """Test non-ASCII content."""
        html = '''
        <div>
          <div class="item">
            <a href="/post/1">中文标题 Chinese Title</a>
          </div>
          <div class="item">
            <a href="/post/2">🔥 Hot Take</a>
          </div>
          <div class="item">
            <a href="/post/3">Überraschung! German Title</a>
          </div>
        </div>
        '''
        
        candidates = find_item_selector(html, min_items=3)
        selectors = [c["selector"] for c in candidates]
        
        assert ".item" in selectors or "div.item" in selectors
        
        soup = BeautifulSoup(html, 'html.parser')
        item = soup.select_one('.item')
        
        title_selector = generate_field_selector(item, 'title')
        assert title_selector is not None
        
        # Verify it extracts unicode/emoji correctly
        title_elem = item.select_one(title_selector.replace('::attr(href)', ''))
        assert title_elem is not None
        title_text = title_elem.get_text(strip=True)
        assert len(title_text) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
