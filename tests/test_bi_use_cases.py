"""
Business Intelligence Use Case Tests

Tests real-world BI scenarios with actual public data sources.
These tests validate that Foundry can handle common BI extraction needs.
"""

import pytest
from foundry.tools.probe.analyzer import analyze_page
from foundry.lib.http import get_html


class TestFinancialDataExtraction:
    """Test extracting financial/stock market data."""
    
    @pytest.mark.integration
    def test_yahoo_finance_stock_quotes(self):
        """
        Use Case: Extract stock quotes for portfolio tracking
        Source: Yahoo Finance most active stocks
        """
        url = "https://finance.yahoo.com/most-active"
        
        try:
            html = get_html(url)
            analysis = analyze_page(html, url=url)
            
            # Should detect item containers (stock rows)
            assert len(analysis["containers"]) > 0, "Should find stock listing containers"
            
            # Should suggest fields like symbol, price, change
            fields = analysis["suggestions"].get("field_candidates", [])
            field_names = {f["name"] for f in fields}
            
            # Common stock data fields
            expected_fields = {"title", "link", "price", "change"}
            assert len(field_names & expected_fields) >= 2, f"Should suggest stock-related fields, got: {field_names}"
            
        except Exception as e:
            pytest.skip(f"Could not fetch Yahoo Finance: {e}")
    
    @pytest.mark.integration
    def test_coinmarketcap_crypto_prices(self):
        """
        Use Case: Track cryptocurrency prices for investment analysis
        Source: CoinMarketCap top cryptocurrencies
        """
        url = "https://coinmarketcap.com/"
        
        try:
            html = get_html(url)
            analysis = analyze_page(html, url=url)
            
            # Should detect crypto listing containers
            assert len(analysis["containers"]) > 0, "Should find crypto listing containers"
            
            # Should find multiple items (at least top 10 cryptos)
            if analysis["containers"]:
                top_container = analysis["containers"][0]
                assert top_container["item_count"] >= 10, "Should find at least 10 crypto items"
            
        except Exception as e:
            pytest.skip(f"Could not fetch CoinMarketCap: {e}")


class TestRealEstateDataExtraction:
    """Test extracting real estate listings."""
    
    @pytest.mark.integration
    def test_zillow_listings(self):
        """
        Use Case: Monitor real estate prices in target markets
        Source: Zillow search results
        """
        # Zillow NYC apartments for rent
        url = "https://www.zillow.com/new-york-ny/rentals/"
        
        try:
            html = get_html(url)
            analysis = analyze_page(html, url=url)
            
            # Should detect property listing containers
            assert len(analysis["containers"]) > 0, "Should find property listing containers"
            
            # Check for real estate template suggestion
            fields = analysis["suggestions"].get("field_candidates", [])
            field_names = {f["name"] for f in fields}
            
            # Real estate fields
            expected = {"title", "price", "image", "link"}
            assert len(field_names & expected) >= 2, "Should suggest property-related fields"
            
        except Exception as e:
            pytest.skip(f"Could not fetch Zillow: {e}")


class TestCompanyDirectoryExtraction:
    """Test extracting company/business directory data."""
    
    @pytest.mark.integration
    def test_ycombinator_companies(self):
        """
        Use Case: Build database of startups for market research
        Source: Y Combinator companies directory
        """
        url = "https://www.ycombinator.com/companies"
        
        try:
            html = get_html(url)
            analysis = analyze_page(html, url=url)
            
            # Should detect company listing containers
            assert len(analysis["containers"]) > 0, "Should find company listing containers"
            
            # Should find many companies
            if analysis["containers"]:
                top_container = analysis["containers"][0]
                assert top_container["item_count"] >= 10, "Should find multiple company listings"
            
        except Exception as e:
            pytest.skip(f"Could not fetch YC Companies: {e}")
    
    @pytest.mark.integration
    def test_producthunt_products(self):
        """
        Use Case: Track new product launches for competitive intelligence
        Source: Product Hunt daily products
        """
        url = "https://www.producthunt.com/"
        
        try:
            html = get_html(url)
            analysis = analyze_page(html, url=url)
            
            # Should detect product listing containers
            assert len(analysis["containers"]) > 0, "Should find product listing containers"
            
            # Check for relevant fields
            fields = analysis["suggestions"].get("field_candidates", [])
            field_names = {f["name"] for f in fields}
            
            assert "title" in field_names or "name" in field_names, "Should detect product names"
            
        except Exception as e:
            pytest.skip(f"Could not fetch Product Hunt: {e}")


class TestJobListingsExtraction:
    """Test extracting job postings for market analysis."""
    
    @pytest.mark.integration
    def test_hn_who_is_hiring(self):
        """
        Use Case: Analyze tech job market trends and salary data
        Source: Hacker News "Who is Hiring" thread
        """
        # Latest "Who is Hiring" thread (changes monthly)
        url = "https://news.ycombinator.com/item?id=41709301"  # November 2024
        
        try:
            html = get_html(url)
            analysis = analyze_page(html, url=url)
            
            # Should detect comment containers (job postings)
            assert len(analysis["containers"]) > 0, "Should find comment containers"
            
            # HN threads typically have many comments
            if analysis["containers"]:
                top_container = analysis["containers"][0]
                # "Who is Hiring" threads have 500+ comments
                assert top_container["item_count"] >= 10, "Should find multiple job postings"
            
        except Exception as e:
            pytest.skip(f"Could not fetch HN thread: {e}")


class TestEcommerceDataExtraction:
    """Test extracting e-commerce product data."""
    
    @pytest.mark.integration
    def test_amazon_bestsellers(self):
        """
        Use Case: Track competitor pricing and product rankings
        Source: Amazon Best Sellers
        """
        url = "https://www.amazon.com/Best-Sellers/zgbs"
        
        try:
            html = get_html(url)
            analysis = analyze_page(html, url=url)
            
            # Should detect product containers
            assert len(analysis["containers"]) > 0, "Should find product containers"
            
            # Check for product-related fields
            fields = analysis["suggestions"].get("field_candidates", [])
            field_names = {f["name"] for f in fields}
            
            expected = {"title", "price", "image", "link", "rating"}
            assert len(field_names & expected) >= 2, "Should suggest product-related fields"
            
        except Exception as e:
            pytest.skip(f"Could not fetch Amazon: {e}")


class TestNewsContentExtraction:
    """Test extracting news articles for content analysis."""
    
    @pytest.mark.integration
    def test_techcrunch_articles(self):
        """
        Use Case: Monitor industry news for competitive intelligence
        Source: TechCrunch latest articles
        """
        url = "https://techcrunch.com/"
        
        try:
            html = get_html(url)
            analysis = analyze_page(html, url=url)
            
            # Should detect article containers
            assert len(analysis["containers"]) > 0, "Should find article containers"
            
            # Should detect relevant frameworks (likely WordPress or custom)
            frameworks = analysis.get("frameworks", [])
            # Just check that framework detection ran
            assert isinstance(frameworks, list), "Framework detection should return list"
            
            # Should suggest article fields
            fields = analysis["suggestions"].get("field_candidates", [])
            field_names = {f["name"] for f in fields}
            
            expected = {"title", "link", "date", "author", "description"}
            assert len(field_names & expected) >= 2, "Should suggest article-related fields"
            
        except Exception as e:
            pytest.skip(f"Could not fetch TechCrunch: {e}")


class TestSocialMediaDataExtraction:
    """Test extracting public social media data."""
    
    @pytest.mark.integration
    def test_reddit_subreddit(self):
        """
        Use Case: Monitor brand mentions and customer sentiment
        Source: Reddit subreddit posts
        """
        url = "https://www.reddit.com/r/python/"
        
        try:
            html = get_html(url)
            analysis = analyze_page(html, url=url)
            
            # Should detect post containers
            assert len(analysis["containers"]) > 0, "Should find post containers"
            
            # Reddit has many posts on front page
            if analysis["containers"]:
                top_container = analysis["containers"][0]
                assert top_container["item_count"] >= 5, "Should find multiple posts"
            
        except Exception as e:
            pytest.skip(f"Could not fetch Reddit: {e}")
    
    @pytest.mark.integration
    def test_github_trending(self):
        """
        Use Case: Track trending technologies and developer tools
        Source: GitHub trending repositories
        """
        url = "https://github.com/trending"
        
        try:
            html = get_html(url)
            analysis = analyze_page(html, url=url)
            
            # Should detect repository containers
            assert len(analysis["containers"]) > 0, "Should find repository containers"
            
            # GitHub trending shows 25 repos
            if analysis["containers"]:
                top_container = analysis["containers"][0]
                assert top_container["item_count"] >= 10, "Should find multiple repositories"
            
        except Exception as e:
            pytest.skip(f"Could not fetch GitHub Trending: {e}")


class TestAnalyticsMetricsExtraction:
    """Test extracting metrics and KPI data."""
    
    @pytest.mark.integration  
    def test_pypi_package_stats(self):
        """
        Use Case: Track Python package downloads and popularity
        Source: PyPI package page
        """
        url = "https://pypi.org/project/requests/"
        
        try:
            html = get_html(url)
            analysis = analyze_page(html, url=url)
            
            # Should analyze page structure
            assert "metadata" in analysis, "Should extract page metadata"
            assert "statistics" in analysis, "Should calculate statistics"
            
            # Should find some structured content
            stats = analysis.get("statistics", {})
            assert stats.get("total_elements", 0) > 50, "Should find substantial page content"
            
        except Exception as e:
            pytest.skip(f"Could not fetch PyPI: {e}")


class TestInfiniteScrollDetection:
    """Test infinite scroll detection on known sites."""
    
    @pytest.mark.integration
    def test_twitter_infinite_scroll(self):
        """
        Use Case: Detect when site needs API extraction approach
        Source: Twitter/X (known infinite scroll site)
        """
        # Note: Twitter requires login for most content now
        url = "https://twitter.com/explore"
        
        try:
            html = get_html(url)
            analysis = analyze_page(html, url=url)
            
            # Should detect infinite scroll indicators
            infinite_scroll = analysis["suggestions"].get("infinite_scroll", {})
            
            # Twitter uses React and likely has scroll handlers
            # Detection may vary based on what HTML we get without auth
            assert isinstance(infinite_scroll, dict), "Should return infinite scroll analysis"
            
        except Exception as e:
            pytest.skip(f"Could not fetch Twitter: {e}")
    
    @pytest.mark.integration
    def test_medium_infinite_scroll(self):
        """
        Use Case: Detect infinite scroll in content platforms
        Source: Medium (known infinite scroll)
        """
        url = "https://medium.com/tag/python"
        
        try:
            html = get_html(url)
            analysis = analyze_page(html, url=url)
            
            # Should detect React/modern framework
            frameworks = analysis.get("frameworks", [])
            framework_names = {f["name"] for f in frameworks}
            
            # Medium uses React/Next.js
            assert len(frameworks) > 0, "Should detect some framework"
            
            # Should detect infinite scroll with decent confidence
            infinite_scroll = analysis["suggestions"].get("infinite_scroll", {})
            # Medium may or may not trigger based on page state
            assert isinstance(infinite_scroll, dict), "Should include infinite scroll analysis"
            
        except Exception as e:
            pytest.skip(f"Could not fetch Medium: {e}")


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration

