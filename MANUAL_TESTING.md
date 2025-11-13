# ScrapeSuite Manual Testing Plan

**Version**: 2.1  
**Date**: November 13, 2025  
**Focus**: Business Intelligence Use Cases + Infinite Scroll Detection

---

## Overview

This testing plan emphasizes **real-world business intelligence scenarios** and the new **infinite scroll detection** features. ScrapeSuite now includes:

- 🎯 **15 BI Templates** (Article, Product, Event, Job, Recipe, Review, Person + 8 BI-specific)
- 🔄 **Infinite Scroll Detection** with interactive API discovery guide
- 📊 **BI Use Case Validation** (Financial data, Real estate, Company directories, etc.)

---

## Prerequisites

```bash
# Ensure you're in the scrapesuite directory
cd /workspaces/scrapesuite

# Verify installation
python --version  # Should be 3.12+
pip list | grep -E "beautifulsoup4|pydantic|click|rich"

# Clean test environment
rm -rf /tmp/test_output
mkdir -p /tmp/test_output
```

---

## Part 1: Business Intelligence Features

### 1.1 Template System - Quick Schema Creation

**Test 1: Browse Available Templates**
```bash
# View all 15 templates
python -m scrapesuite.foundry blueprint create /tmp/test_output/template_test.yml

# When prompted:
# 1. Enter name: "bi_test"
# 2. Choose template option (e.g., "2" for Product template)
# 3. Customize fields or accept defaults
# 4. Skip pagination

# Verify generated schema uses template structure:
cat /tmp/test_output/template_test.yml
```

**Available Templates:**
1. **Article** - News, blog posts (title, author, date, description, image)
2. **Product** - E-commerce items (name, price, rating, availability, brand)
3. **Event** - Conferences, meetups (title, date, time, location, price)
4. **Job** - Job listings (title, company, location, salary, job_type)
5. **Recipe** - Cooking recipes (title, prep_time, cook_time, servings)
6. **Review** - User reviews (author, rating, content, date, verified)
7. **Person** - Profiles (name, title, email, phone, bio, organization)
8. **Financial Data** - Stock quotes (symbol, price, change, volume, market_cap)
9. **Real Estate** - Property listings (address, price, bedrooms, bathrooms, sqft)
10. **Company Directory** - Business listings (company_name, industry, location, revenue)
11. **Analytics Metrics** - KPIs (metric_name, value, unit, change, trend)
12. **Competitive Intel** - Competitor data (competitor_name, product, price, market_share)
13. **Supply Chain** - Inventory (sku, product_name, quantity, supplier, location)
14. **Sales Leads** - Prospects (company_name, contact_name, email, lead_score)
15. **Custom** - Build from scratch

**Test 2: Financial Data Template**
```bash
# Create schema for stock tracking
python -m scrapesuite.foundry blueprint create /tmp/test_output/stocks.yml

# Select template: "8" (Financial Data)
# This auto-configures fields: symbol, company_name, price, change, volume, market_cap
```

**Test 3: Real Estate Template**
```bash
# Create schema for property monitoring
python -m scrapesuite.foundry blueprint create /tmp/test_output/properties.yml

# Select template: "9" (Real Estate)
# Auto-configures: address, price, bedrooms, bathrooms, square_feet, agent
```

---

### 1.2 Infinite Scroll Detection & API Discovery

**Test 4: Interactive API Guide**
```bash
# Show the step-by-step API discovery guide
python -m scrapesuite.foundry probe --find-api

# Expected Output:
# - Rich formatted guide with DevTools instructions
# - Common pagination patterns (offset, page, cursor)
# - Example Python code for API scraping
# - Legal/ethical considerations
# - Links to full documentation
```

**Test 5: Auto-Detect Infinite Scroll**
```bash
# Create test HTML with infinite scroll indicators
cat > /tmp/test_output/infinite_scroll.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Infinite Scroll Test</title>
    <script src="https://unpkg.com/infinite-scroll@4/dist/infinite-scroll.pkgd.min.js"></script>
</head>
<body>
    <div class="container">
        <article class="post">
            <h2>Post 1</h2>
            <p>Content 1</p>
        </article>
        <article class="post">
            <h2>Post 2</h2>
            <p>Content 2</p>
        </article>
    </div>
    <div class="loading-spinner">Loading...</div>
    <script>
        window.addEventListener('scroll', function() {
            // Infinite scroll logic
        });
    </script>
</body>
</html>
EOF

# Analyze page
python -m scrapesuite.foundry probe --file /tmp/test_output/infinite_scroll.html

# Expected Output:
# - Yellow warning panel: "⚠ Infinite Scroll Detected"
# - Confidence percentage (e.g., 60%)
# - List of detected signals:
#   * infinite-scroll library detected
#   * No traditional pagination links found
#   * Scroll event handlers in JavaScript
# - Recommendation to run: foundry probe --find-api
```

**Test 6: Infinite Scroll Confidence Scoring**
```bash
# Test different confidence levels

# High confidence (multiple signals)
cat > /tmp/test_output/high_confidence.html << 'EOF'
<html>
<head>
    <script src="https://cdn.example.com/infinite-scroll.js"></script>
</head>
<body>
    <div class="feed" data-page="1" data-cursor="abc123">
        <article>Post 1</article>
    </div>
    <div class="loading"></div>
    <script>
        const observer = new IntersectionObserver(...);
        window.onscroll = () => loadMore();
    </script>
</body>
</html>
EOF

python -m scrapesuite.foundry probe --file /tmp/test_output/high_confidence.html | grep "Infinite Scroll"

# Should show high confidence (70%+)
```

---

### 1.3 Business Intelligence Use Cases

**Test 7: Financial Data Extraction (Yahoo Finance Style)**
```bash
# Analyze a stock listing page structure
python -m scrapesuite.foundry probe https://finance.yahoo.com/most-active

# Expected:
# - Detects stock row containers
# - Suggests fields: symbol, price, change, volume
# - May detect infinite scroll (Yahoo uses it)
# - Framework detection (React/Next.js likely)
```

**Test 8: Real Estate Extraction (Zillow Style)**
```bash
# Note: This is an example - may require actual URLs or fixtures

# Create mock real estate listing HTML
cat > /tmp/test_output/real_estate.html << 'EOF'
<html>
<body>
    <div class="search-results">
        <article class="property-card">
            <h3 class="property-address">123 Main St, NYC</h3>
            <span class="property-price">$2,500/mo</span>
            <div class="property-details">
                <span class="beds">2 bd</span>
                <span class="baths">1 ba</span>
                <span class="sqft">850 sqft</span>
            </div>
            <img src="property1.jpg" class="property-image" />
            <a href="/property/123" class="property-link">View Details</a>
        </article>
        <article class="property-card">
            <h3 class="property-address">456 Oak Ave, Brooklyn</h3>
            <span class="property-price">$3,200/mo</span>
            <div class="property-details">
                <span class="beds">3 bd</span>
                <span class="baths">2 ba</span>
                <span class="sqft">1200 sqft</span>
            </div>
            <img src="property2.jpg" class="property-image" />
            <a href="/property/456" class="property-link">View Details</a>
        </article>
    </div>
</body>
</html>
EOF

# Analyze structure
python -m scrapesuite.foundry probe --file /tmp/test_output/real_estate.html

# Expected:
# - Container: article.property-card
# - Suggested fields: address, price, bedrooms, bathrooms, sqft, image, link
# - Can use Real Estate template for quick schema creation
```

**Test 9: Company Directory Extraction**
```bash
# Create mock company directory
cat > /tmp/test_output/companies.html << 'EOF'
<html>
<body>
    <div class="directory">
        <div class="company-card">
            <h2 class="company-name">Acme Corp</h2>
            <span class="industry">Software</span>
            <span class="location">San Francisco, CA</span>
            <span class="employees">50-100</span>
            <a href="https://acme.com" class="website">acme.com</a>
            <p class="description">Cloud-based solutions...</p>
        </div>
        <div class="company-card">
            <h2 class="company-name">TechStart Inc</h2>
            <span class="industry">AI/ML</span>
            <span class="location">Austin, TX</span>
            <span class="employees">10-50</span>
            <a href="https://techstart.io" class="website">techstart.io</a>
            <p class="description">AI-powered analytics...</p>
        </div>
    </div>
</body>
</html>
EOF

# Analyze and create schema using template
python -m scrapesuite.foundry probe --file /tmp/test_output/companies.html

# Then create schema with Company Directory template
python -m scrapesuite.foundry blueprint create /tmp/test_output/company_schema.yml
# Select template: "10" (Company Directory)
# Container selector: .company-card
# Customize field selectors based on probe output
```

**Test 10: Analytics Dashboard Extraction**
```bash
# Mock analytics metrics table
cat > /tmp/test_output/analytics.html << 'EOF'
<html>
<body>
    <table class="metrics-table">
        <tbody>
            <tr class="metric-row">
                <td class="metric-name">Active Users</td>
                <td class="metric-value">15,432</td>
                <td class="metric-change">+12.3%</td>
                <td class="metric-trend">↑</td>
            </tr>
            <tr class="metric-row">
                <td class="metric-name">Revenue</td>
                <td class="metric-value">$45,678</td>
                <td class="metric-change">+8.5%</td>
                <td class="metric-trend">↑</td>
            </tr>
            <tr class="metric-row">
                <td class="metric-name">Churn Rate</td>
                <td class="metric-value">2.1%</td>
                <td class="metric-change">-0.5%</td>
                <td class="metric-trend">↓</td>
            </tr>
        </tbody>
    </table>
</body>
</html>
EOF

# Analyze
python -m scrapesuite.foundry probe --file /tmp/test_output/analytics.html

# Create schema with Analytics Metrics template
python -m scrapesuite.foundry blueprint create /tmp/test_output/metrics_schema.yml
# Template: "11" (Analytics Metrics)
# Container: tr.metric-row
```

---

## Part 2: Foundry Suite Core Testing

### 2.1 Probe - Enhanced Analysis

**Test 11: Framework Detection with BI Context**
```bash
# Test probe on fixture with framework hints
python -m scrapesuite.foundry probe --file tests/fixtures/fda_list.html

# Expected Output:
# - Framework detection (Drupal/Views likely)
# - Container suggestions ranked by content score
# - Boilerplate filtering (skips headers/footers)
# - Field suggestions with sample values
# - Page statistics
```

**Test 12: JSON Output for Automation**
```bash
# Get analysis in JSON format for programmatic use
python -m scrapesuite.foundry probe \
  --file tests/fixtures/fda_list.html \
  --format json \
  --output /tmp/test_output/analysis.json

# Verify structure includes new fields:
cat /tmp/test_output/analysis.json | python -c "
import json, sys
data = json.load(sys.stdin)
print('Has infinite_scroll:', 'infinite_scroll' in data.get('suggestions', {}))
print('Containers found:', len(data.get('containers', [])))
if data['containers']:
    print('Top container:', data['containers'][0]['child_selector'])
    print('Item count:', data['containers'][0]['item_count'])
    print('Content score:', data['containers'][0].get('content_score', 0))
"
```

**Test 13: Probe with Auto-Analysis in Blueprint**
```bash
# Blueprint now auto-runs Probe when URL provided
python -m scrapesuite.foundry blueprint create /tmp/test_output/auto_probe.yml

# When prompted:
# - Enter URL: https://news.ycombinator.com
# - Probe automatically analyzes the page
# - Shows table of detected containers with samples
# - Shows table of suggested fields with samples
# - Can select from suggestions or customize
```

---

### 2.2 Blueprint - Template-Driven Schema Creation

**Test 14: Article Template (News/Blog)**
```bash
# Quick schema for news extraction
python -m scrapesuite.foundry blueprint create /tmp/test_output/news_schema.yml

# Steps:
# 1. Name: "tech_news"
# 2. Template: "1" (Article)
# 3. URL: https://techcrunch.com (optional)
# 4. If URL provided, Probe runs and suggests containers
# 5. Select container or enter custom
# 6. Review/customize fields (title, link, author, date, description, image, category)
# 7. Add pagination if needed
# 8. Save

# Result: Ready-to-use schema with common article fields pre-configured
cat /tmp/test_output/news_schema.yml
```

**Test 15: Product Template (E-commerce)**
```bash
# Schema for product scraping
python -m scrapesuite.foundry blueprint create /tmp/test_output/products_schema.yml

# Template: "2" (Product)
# Pre-configured fields:
# - name, link, price, image, rating, availability, brand

# Verify schema structure:
grep -A 20 "fields:" /tmp/test_output/products_schema.yml
```

**Test 16: Job Template (Recruitment)**
```bash
# Schema for job board scraping
python -m scrapesuite.foundry blueprint create /tmp/test_output/jobs_schema.yml

# Template: "4" (Job)
# Fields: title, company, location, salary, description, job_type

# Use with Hacker News "Who is Hiring" or job boards
```

---

### 2.3 Forge - BI Data Extraction

**Test 17: Extract with Template Schema**
```bash
# Use a template-based schema to extract data
# First create schema with Product template, then:

cat > /tmp/test_output/simple_product_schema.yml << 'EOF'
name: simple_products
item_selector: .product-card
fields:
  name:
    selector: h3.product-name
    required: true
  price:
    selector: .price
    required: true
  image:
    selector: img
    attribute: src
EOF

# Create matching HTML
cat > /tmp/test_output/products.html << 'EOF'
<div class="products">
    <div class="product-card">
        <h3 class="product-name">Widget Pro</h3>
        <span class="price">$29.99</span>
        <img src="widget.jpg" />
    </div>
    <div class="product-card">
        <h3 class="product-name">Gadget Plus</h3>
        <span class="price">$49.99</span>
        <img src="gadget.jpg" />
    </div>
</div>
EOF

# Extract
python -m scrapesuite.foundry forge \
  /tmp/test_output/simple_product_schema.yml \
  --file /tmp/test_output/products.html \
  --output /tmp/test_output/extracted_products.jsonl

# Verify
cat /tmp/test_output/extracted_products.jsonl | python -m json.tool
```

**Test 18: BI Pipeline - Financial Data**
```bash
# Complete workflow for financial data extraction

# Step 1: Analyze structure
python -m scrapesuite.foundry probe \
  --file /tmp/test_output/stocks.html \
  --output /tmp/test_output/stocks_analysis.json

# Step 2: Create schema with Financial Data template
# (Manual: select template 8, configure selectors)

# Step 3: Extract data
python -m scrapesuite.foundry forge \
  /tmp/test_output/financial_schema.yml \
  --file /tmp/test_output/stocks.html \
  --output /tmp/test_output/stock_data.jsonl

# Step 4: Clean and dedupe
python -m scrapesuite.foundry polish \
  /tmp/test_output/stock_data.jsonl \
  --dedupe \
  --dedupe-keys symbol \
  --output /tmp/test_output/stock_data_clean.jsonl

# Step 5: Export to database for BI tools
python -m scrapesuite.foundry crate \
  /tmp/test_output/stock_data_clean.jsonl \
  /tmp/test_output/stocks.db \
  --table stock_quotes
```

---

### 2.4 Polish - BI Data Transformations

**Test 19: Clean Financial Data**
```bash
# Create sample financial data with messy formatting
cat > /tmp/test_output/messy_financial.jsonl << 'EOF'
{"symbol": "  AAPL  ", "price": "$150.25", "change": "+2.5%", "volume": "45,234,567"}
{"symbol": "GOOGL", "price": "$2,800.00", "change": "-1.2%", "volume": "1,234,567"}
{"symbol": "  MSFT  ", "price": "$380.50", "change": "+0.8%", "volume": "23,456,789"}
EOF

# Clean and normalize
python -m scrapesuite.foundry polish \
  /tmp/test_output/messy_financial.jsonl \
  --transform symbol:normalize_text \
  --transform price:extract_number \
  --transform change:extract_number \
  --transform volume:extract_number \
  --output /tmp/test_output/clean_financial.jsonl

# Verify cleaned data:
cat /tmp/test_output/clean_financial.jsonl | python -m json.tool
```

**Test 20: Deduplicate Company Data**
```bash
# Sample company data with duplicates
cat > /tmp/test_output/companies_dupes.jsonl << 'EOF'
{"company_name": "Acme Corp", "industry": "Software", "employees": "50-100"}
{"company_name": "TechStart", "industry": "AI/ML", "employees": "10-50"}
{"company_name": "Acme Corp", "industry": "Software", "employees": "50-100"}
{"company_name": "DataCo", "industry": "Analytics", "employees": "100-500"}
EOF

# Deduplicate by company name
python -m scrapesuite.foundry polish \
  /tmp/test_output/companies_dupes.jsonl \
  --dedupe \
  --dedupe-keys company_name \
  --stats \
  --output /tmp/test_output/companies_unique.jsonl

# Should show: 4 input, 1 duplicate removed, 3 output
```

---

### 2.5 Crate - BI Exports

**Test 21: Export to BI-Friendly Formats**
```bash
# Create sample BI data
cat > /tmp/test_output/bi_data.jsonl << 'EOF'
{"date": "2024-01-15", "metric": "revenue", "value": 45678, "region": "US"}
{"date": "2024-01-15", "metric": "users", "value": 15432, "region": "US"}
{"date": "2024-01-15", "metric": "revenue", "value": 23456, "region": "EU"}
EOF

# Export to CSV for Excel/Tableau
python -m scrapesuite.foundry crate \
  /tmp/test_output/bi_data.jsonl \
  /tmp/test_output/bi_metrics.csv

# Export to SQLite for SQL analysis
python -m scrapesuite.foundry crate \
  /tmp/test_output/bi_data.jsonl \
  /tmp/test_output/bi_metrics.db \
  --table daily_metrics

# Query in SQL
sqlite3 /tmp/test_output/bi_metrics.db "
SELECT region, metric, SUM(value) as total
FROM daily_metrics
GROUP BY region, metric
ORDER BY region, metric;
"
```

---

## Part 3: Integration Testing - BI Workflows

### 3.1 Complete BI Pipeline: Stock Portfolio Tracker

**Test 22: End-to-End Stock Tracking**
```bash
# Workflow: Analyze → Schema → Extract → Clean → Export

# 1. Create mock stock data HTML
cat > /tmp/test_output/stock_market.html << 'EOF'
<table class="stocks">
    <tr class="stock-row">
        <td class="symbol">AAPL</td>
        <td class="company">Apple Inc.</td>
        <td class="price">$150.25</td>
        <td class="change positive">+2.50</td>
        <td class="volume">45.2M</td>
        <td class="market-cap">$2.5T</td>
    </tr>
    <tr class="stock-row">
        <td class="symbol">GOOGL</td>
        <td class="company">Alphabet Inc.</td>
        <td class="price">$2800.00</td>
        <td class="change negative">-15.30</td>
        <td class="volume">1.2M</td>
        <td class="market-cap">$1.8T</td>
    </tr>
    <tr class="stock-row">
        <td class="symbol">MSFT</td>
        <td class="company">Microsoft Corp.</td>
        <td class="price">$380.50</td>
        <td class="change positive">+3.10</td>
        <td class="volume">23.4M</td>
        <td class="market-cap">$2.8T</td>
    </tr>
</table>
EOF

# 2. Analyze structure
python -m scrapesuite.foundry probe \
  --file /tmp/test_output/stock_market.html \
  --format json \
  --output /tmp/test_output/stock_analysis.json

# 3. Create schema using Financial Data template
cat > /tmp/test_output/stock_schema.yml << 'EOF'
name: stock_tracker
description: Track stock prices and market data
item_selector: tr.stock-row
fields:
  symbol:
    selector: .symbol
    required: true
  company_name:
    selector: .company
  price:
    selector: .price
  change:
    selector: .change
  volume:
    selector: .volume
  market_cap:
    selector: .market-cap
EOF

# 4. Extract data
python -m scrapesuite.foundry forge \
  /tmp/test_output/stock_schema.yml \
  --file /tmp/test_output/stock_market.html \
  --output /tmp/test_output/stock_raw.jsonl

# 5. Clean and normalize
python -m scrapesuite.foundry polish \
  /tmp/test_output/stock_raw.jsonl \
  --transform price:extract_number \
  --transform change:extract_number \
  --dedupe \
  --dedupe-keys symbol \
  --output /tmp/test_output/stock_clean.jsonl

# 6. Export to database for tracking
python -m scrapesuite.foundry crate \
  /tmp/test_output/stock_clean.jsonl \
  /tmp/test_output/portfolio.db \
  --table stock_prices

# 7. Query portfolio
sqlite3 /tmp/test_output/portfolio.db "
SELECT symbol, company_name, price, change 
FROM stock_prices 
ORDER BY CAST(change AS REAL) DESC;
"

# Success: Complete BI pipeline for stock tracking!
```

### 3.2 Real Estate Market Analysis

**Test 23: Property Monitoring Pipeline**
```bash
# Use the real estate HTML from Test 8

# 1. Analyze
python -m scrapesuite.foundry probe \
  --file /tmp/test_output/real_estate.html

# 2. Create schema (Real Estate template)
cat > /tmp/test_output/properties_schema.yml << 'EOF'
name: rental_properties
item_selector: article.property-card
fields:
  address:
    selector: .property-address
    required: true
  price:
    selector: .property-price
    required: true
  bedrooms:
    selector: .beds
  bathrooms:
    selector: .baths
  square_feet:
    selector: .sqft
  image:
    selector: .property-image
    attribute: src
  link:
    selector: .property-link
    attribute: href
EOF

# 3. Extract
python -m scrapesuite.foundry forge \
  /tmp/test_output/properties_schema.yml \
  --file /tmp/test_output/real_estate.html \
  --output /tmp/test_output/properties.jsonl

# 4. Export for analysis
python -m scrapesuite.foundry crate \
  /tmp/test_output/properties.jsonl \
  /tmp/test_output/real_estate.csv

# View properties
cat /tmp/test_output/real_estate.csv
```

### 3.3 Competitive Intelligence Workflow

**Test 24: Monitor Competitor Products**
```bash
# Track competitor pricing and features

# 1. Create competitor product listing
cat > /tmp/test_output/competitors.html << 'EOF'
<div class="comparison-table">
    <div class="competitor-row">
        <h3 class="competitor">CompanyA</h3>
        <div class="product">Widget Pro</div>
        <span class="price">$99/mo</span>
        <span class="market-share">35%</span>
        <ul class="features">
            <li>Feature 1</li>
            <li>Feature 2</li>
        </ul>
    </div>
    <div class="competitor-row">
        <h3 class="competitor">CompanyB</h3>
        <div class="product">Gadget Plus</div>
        <span class="price">$79/mo</span>
        <span class="market-share">28%</span>
        <ul class="features">
            <li>Feature 1</li>
            <li>Feature 3</li>
        </ul>
    </div>
</div>
EOF

# 2. Create schema (Competitive Intel template)
cat > /tmp/test_output/competitive_schema.yml << 'EOF'
name: competitor_tracking
item_selector: .competitor-row
fields:
  competitor_name:
    selector: .competitor
    required: true
  product_name:
    selector: .product
  price:
    selector: .price
  market_share:
    selector: .market-share
  features:
    selector: .features
EOF

# 3. Extract and track
python -m scrapesuite.foundry forge \
  /tmp/test_output/competitive_schema.yml \
  --file /tmp/test_output/competitors.html \
  --output /tmp/test_output/competitor_data.jsonl

# 4. Export to database
python -m scrapesuite.foundry crate \
  /tmp/test_output/competitor_data.jsonl \
  /tmp/test_output/competitive_intel.db \
  --table competitor_products

# 5. Analyze pricing
sqlite3 /tmp/test_output/competitive_intel.db "
SELECT competitor_name, product_name, price, market_share
FROM competitor_products
ORDER BY CAST(REPLACE(market_share, '%', '') AS REAL) DESC;
"
```

---

## Part 4: Infinite Scroll & API Discovery

### 4.1 Detection Tests

**Test 25: Various Infinite Scroll Patterns**
```bash
# Test different JS libraries/patterns

# IntersectionObserver (modern approach)
cat > /tmp/test_output/intersection_observer.html << 'EOF'
<html>
<head><title>Modern Infinite Scroll</title></head>
<body>
    <div class="feed"><article>Post 1</article></div>
    <script>
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    loadMore();
                }
            });
        });
    </script>
</body>
</html>
EOF

python -m scrapesuite.foundry probe --file /tmp/test_output/intersection_observer.html | grep -A 10 "Infinite Scroll"

# React infinite scroll
cat > /tmp/test_output/react_infinite.html << 'EOF'
<html>
<head><script src="react-infinite-scroll-component.js"></script></head>
<body>
    <div data-reactroot="" class="feed">
        <article>Post 1</article>
    </div>
</body>
</html>
EOF

python -m scrapesuite.foundry probe --file /tmp/test_output/react_infinite.html | grep "Infinite Scroll"

# Waypoints library
cat > /tmp/test_output/waypoints.html << 'EOF'
<html>
<head><script src="waypoints.min.js"></script></head>
<body>
    <div class="posts"><article>Post 1</article></div>
    <div class="waypoint" data-page="2"></div>
</body>
</html>
EOF

python -m scrapesuite.foundry probe --file /tmp/test_output/waypoints.html | grep "Infinite Scroll"
```

**Test 26: No False Positives**
```bash
# Traditional pagination should NOT trigger warning
cat > /tmp/test_output/normal_pagination.html << 'EOF'
<html>
<body>
    <div class="articles">
        <article>Article 1</article>
        <article>Article 2</article>
    </div>
    <nav class="pagination">
        <a href="?page=1">1</a>
        <a href="?page=2" class="next">Next</a>
    </nav>
</body>
</html>
EOF

python -m scrapesuite.foundry probe --file /tmp/test_output/normal_pagination.html

# Should NOT show infinite scroll warning (has pagination links)
```

### 4.2 API Discovery Guide Usage

**Test 27: Interactive Guide Walkthrough**
```bash
# Launch the full guide
python -m scrapesuite.foundry probe --find-api

# Verify output includes:
# - DevTools instructions (F12, Network tab)
# - Filter by Fetch/XHR
# - Common patterns section (News sites, WordPress, E-commerce, GraphQL)
# - Pagination patterns (offset, page, cursor)
# - Example Python code
# - Legal considerations
# - Link to full documentation
```

**Test 28: Integration Test - Detect & Guide**
```bash
# Workflow: Detect infinite scroll → Guide user to API

# 1. Analyze page with infinite scroll
python -m scrapesuite.foundry probe --file /tmp/test_output/infinite_scroll.html

# Should show warning with:
# "Run: foundry probe --find-api"

# 2. Follow the recommendation
python -m scrapesuite.foundry probe --find-api

# User now has complete guide to find the API endpoint
```

---

## Part 5: Error Handling & Edge Cases

### 5.1 Template Edge Cases

**Test 29: Invalid Template Selection**
```bash
# Try to use non-existent template
# (Interactive test - select invalid option during blueprint create)

python -m scrapesuite.foundry blueprint create /tmp/test_output/test.yml
# Enter: "99" for template selection
# Expected: Error message, prompt to select valid template
```

**Test 30: Empty Container After Template**
```bash
# Template selected but no items match selector
cat > /tmp/test_output/no_items.html << 'EOF'
<html><body><div class="empty"></div></body></html>
EOF

cat > /tmp/test_output/empty_schema.yml << 'EOF'
name: empty_test
item_selector: .non-existent
fields:
  title:
    selector: h2
EOF

python -m scrapesuite.foundry forge \
  /tmp/test_output/empty_schema.yml \
  --file /tmp/test_output/no_items.html \
  --output /tmp/test_output/empty_result.jsonl

# Should create empty JSONL or show warning
test ! -s /tmp/test_output/empty_result.jsonl && echo "Empty output as expected"
```

---

## Part 6: Integration Tests (Network-Dependent)

These tests require internet connection and may be skipped if sites are unavailable.

### 6.1 Real-World BI Scenarios

**Test 31: GitHub Trending (Company Directory)**
```bash
# Analyze GitHub trending repos
python -m scrapesuite.foundry probe https://github.com/trending

# Expected:
# - Detects repository containers
# - Suggests fields: name, description, stars, language
# - May detect infinite scroll
```

**Test 32: Hacker News (News/Content)**
```bash
# Analyze HN front page
python -m scrapesuite.foundry probe https://news.ycombinator.com

# Expected:
# - Detects story rows (.athing)
# - Suggests: title, url, points, comments
# - Framework: likely generic/none
```

**Test 33: Product Hunt (Product Listings)**
```bash
# Analyze Product Hunt
python -m scrapesuite.foundry probe https://www.producthunt.com/

# Expected:
# - Detects product cards
# - May show infinite scroll warning (PH uses it)
# - Suggests Product template fields
```

---

## Part 7: Performance & Validation

### 7.1 Integration Test Suite

**Test 34: Run BI Use Case Tests**
```bash
# Run the full BI integration test suite
python -m pytest tests/test_bi_use_cases.py -v

# Tests cover:
# - Financial data (Yahoo Finance, CoinMarketCap)
# - Real estate (Zillow)
# - Company directories (YC, Product Hunt)
# - Job listings (HN Who is Hiring)
# - E-commerce (Amazon)
# - News (TechCrunch)
# - Social (Reddit, GitHub)
# - Analytics (PyPI)
# - Infinite scroll detection (Twitter, Medium)

# Note: Tests may be skipped if sites are unavailable
```

**Test 35: Run Integration Tests Only**
```bash
# Run only integration tests (marked with @pytest.mark.integration)
python -m pytest tests/test_bi_use_cases.py -m integration -v

# Or run specific use case category:
python -m pytest tests/test_bi_use_cases.py::TestFinancialDataExtraction -v
python -m pytest tests/test_bi_use_cases.py::TestRealEstateDataExtraction -v
python -m pytest tests/test_bi_use_cases.py::TestInfiniteScrollDetection -v
```

---

## Verification Checklist

After completing tests, verify:

### Business Intelligence Features
- [ ] All 15 templates are available in blueprint
- [ ] Financial Data template creates proper schema
- [ ] Real Estate template includes property-specific fields
- [ ] Company Directory template has business fields
- [ ] Analytics Metrics template configured correctly
- [ ] Templates auto-populate common selectors
- [ ] Template customization works

### Infinite Scroll Detection
- [ ] `--find-api` flag shows complete guide
- [ ] Auto-detection triggers on infinite scroll pages
- [ ] Confidence scoring works (30%+ shows warning)
- [ ] Multiple signals detected (libraries, scroll handlers, etc.)
- [ ] Warning panel displays in probe output
- [ ] Recommendation to use `--find-api` appears
- [ ] No false positives on normal pagination

### Core Functionality
- [ ] Probe analysis includes new BI features
- [ ] Blueprint auto-runs Probe when URL provided
- [ ] Blueprint shows container/field tables with samples
- [ ] Forge extracts using template schemas
- [ ] Polish transforms work on BI data types
- [ ] Crate exports to BI-friendly formats (CSV, SQLite)
- [ ] Complete BI pipelines work end-to-end

### Integration
- [ ] BI use case tests run successfully
- [ ] Real-world URL tests work (when available)
- [ ] Template-based extraction validated
- [ ] API discovery guide is comprehensive
- [ ] All 197 core tests still pass

---

## Quick Smoke Test (60 seconds)

Rapid validation of new BI features:

```bash
# 1. Test infinite scroll detection
cat > /tmp/quick_infinite.html << 'EOF'
<html><head><script src="infinite-scroll.js"></script></head>
<body><div class="feed"><article>Post</article></div>
<script>window.onscroll = loadMore;</script></body></html>
EOF

python -m scrapesuite.foundry probe --file /tmp/quick_infinite.html | grep "Infinite Scroll"

# 2. Test API guide
python -m scrapesuite.foundry probe --find-api | head -20

# 3. Test template creation
python -m scrapesuite.foundry blueprint create /tmp/quick_template.yml <<EOF
quick_test
2
n
EOF

# 4. Verify template created with Product fields
grep -A 10 "fields:" /tmp/quick_template.yml

# 5. Run BI integration tests (subset)
python -m pytest tests/test_bi_use_cases.py::TestInfiniteScrollDetection -v

# All pass? Features working! ✅
```

---

## Troubleshooting

**Issue**: Template not showing expected fields
- **Fix**: Re-run blueprint create, carefully select template number

**Issue**: Infinite scroll not detected
- **Fix**: Check HTML has scroll indicators (see Test 25 for patterns)

**Issue**: API guide not formatting properly
- **Fix**: Ensure Rich library installed: `pip install rich`

**Issue**: Integration tests all skipped
- **Fix**: Check internet connection, some sites may be blocking

**Issue**: SQLite export fails with template data
- **Fix**: Ensure fields have valid names (no special chars)

---

## Summary

**New in v2.1:**
- 🎯 15 BI-focused templates for instant schema creation
- 🔄 Intelligent infinite scroll detection with confidence scoring
- 📚 Interactive API discovery guide (`--find-api`)
- 🧪 14 real-world BI use case tests
- 📊 Enhanced Probe analysis with content scoring
- ⚡ Template-driven workflow for common scenarios

**Test Coverage:**
- Financial data extraction (stocks, crypto)
- Real estate monitoring
- Company/product directories
- Competitive intelligence
- Analytics dashboards
- Sales lead generation
- Supply chain tracking
- Infinite scroll handling

**Time Estimates:**
- Quick smoke test: 1 minute
- BI features (Part 1): 20 minutes
- Infinite scroll (Part 4): 10 minutes
- Integration tests (Part 6): 15 minutes
- **Full suite**: ~45 minutes

**Success Criteria:**
✅ All templates accessible and functional  
✅ Infinite scroll detected with >60% confidence  
✅ API guide shows complete instructions  
✅ BI pipelines work end-to-end  
✅ Integration tests pass (when sites available)  
✅ 197 core tests still passing
````

```bash
# Ensure you're in the scrapesuite directory
cd /workspaces/scrapesuite

# Verify installation
python --version  # Should be 3.12+
pip list | grep -E "beautifulsoup4|pydantic|click|rich"

# Clean test environment
rm -rf /tmp/test_output
mkdir -p /tmp/test_output
```

---

## Part 1: Foundry Suite Testing (5 Tools)

### 1.1 Probe - HTML Analysis

**Test 1: Analyze Live URL**
```bash
# Test probe on real website
python -m scrapesuite.foundry probe https://news.ycombinator.com

# Expected Output:
# - Framework detection (likely "None" or generic)
# - List of repeated patterns
# - Field suggestions
# - Statistics (links, forms, etc.)
```

**Test 2: Analyze Local File**
```bash
# Test with fixture file
python -m scrapesuite.foundry probe \
  --file tests/fixtures/fda_list.html

# Expected Output:
# - Should detect patterns
# - Show .views-row or similar containers
# - Suggest title, date, link fields
```

**Test 3: JSON Output**
```bash
# Test JSON format
python -m scrapesuite.foundry probe \
  --file tests/fixtures/fda_list.html \
  --format json \
  --output /tmp/test_output/probe_result.json

# Verify:
cat /tmp/test_output/probe_result.json | python -m json.tool | head -20

# Expected: Valid JSON with frameworks, patterns, fields
```

**Test 4: Framework Detection**
```bash
# Test WordPress detection
python -m scrapesuite.foundry probe \
  --file tests/fixtures/fda_list.html

# Should show framework(s) detected with confidence scores
```

---

### 1.2 Blueprint - Schema Designer

**Test 5: Create Schema Interactively**
```bash
# Interactive schema creation (will prompt for input)
python -m scrapesuite.foundry blueprint create /tmp/test_output/test_schema.yml

# When prompted, enter:
# - URL: https://example.com
# - Container selector: .article
# - Fields: title (h2), url (a::attr(href)), date (.date)
# - Pagination: (press Enter to skip)

# Verify file created:
cat /tmp/test_output/test_schema.yml
```

**Test 6: Validate Schema**
```bash
# Create a test schema first
cat > /tmp/test_output/valid_schema.yml << 'EOF'
url: https://example.com
container: .article
fields:
  - name: title
    selector: h2
  - name: url
    selector: a::attr(href)
  - name: date
    selector: .date
EOF

# Validate it
python -m scrapesuite.foundry blueprint validate /tmp/test_output/valid_schema.yml

# Expected: "✓ Schema is valid"
```

**Test 7: Preview Extraction**
```bash
# Test preview with actual HTML
python -m scrapesuite.foundry blueprint preview \
  examples/jobs/fda.yml \
  --file tests/fixtures/fda_list.html

# Expected: Shows extracted items in table format
```

**Test 8: Invalid Schema**
```bash
# Test validation with bad schema
cat > /tmp/test_output/bad_schema.yml << 'EOF'
url: not-a-url
fields: "this should be a list"
EOF

python -m scrapesuite.foundry blueprint validate /tmp/test_output/bad_schema.yml

# Expected: Validation errors shown
```

---

### 1.3 Forge - Data Extraction

**Test 9: Extract from File**
```bash
# Basic extraction
python -m scrapesuite.foundry forge \
  examples/jobs/fda.yml \
  --file tests/fixtures/fda_list.html \
  --output /tmp/test_output/extracted.jsonl

# Verify output:
cat /tmp/test_output/extracted.jsonl | wc -l  # Should show number of records
head -1 /tmp/test_output/extracted.jsonl | python -m json.tool
```

**Test 10: Extract from URL (with rate limiting)**
```bash
# Extract from live URL
python -m scrapesuite.foundry forge \
  examples/jobs/fda.yml \
  --url https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts \
  --output /tmp/test_output/live_extracted.jsonl \
  --max-pages 1

# Verify:
wc -l /tmp/test_output/live_extracted.jsonl
```

**Test 11: Pagination Test**
```bash
# Test with max pages limit
python -m scrapesuite.foundry forge \
  examples/jobs/fda.yml \
  --file tests/fixtures/fda_list.html \
  --max-pages 2 \
  --output /tmp/test_output/paginated.jsonl

# Should stop after 2 pages (or when pagination fails with fixture)
```

**Test 12: Metadata Test**
```bash
# Extract and check metadata
python -m scrapesuite.foundry forge \
  examples/jobs/fda.yml \
  --file tests/fixtures/fda_list.html \
  --output /tmp/test_output/with_meta.jsonl

# Check for _metadata fields:
head -1 /tmp/test_output/with_meta.jsonl | python -c "
import sys, json
data = json.load(sys.stdin)
print('Metadata fields:', [k for k in data.keys() if k.startswith('_')])
"
```

---

### 1.4 Polish - Data Transformation

**Test 13: Basic Deduplication**
```bash
# Create test data with duplicates
cat > /tmp/test_output/dupes.jsonl << 'EOF'
{"id": "1", "title": "Article A", "url": "http://example.com/a"}
{"id": "2", "title": "Article B", "url": "http://example.com/b"}
{"id": "1", "title": "Article A", "url": "http://example.com/a"}
{"id": "3", "title": "Article C", "url": "http://example.com/c"}
EOF

# Deduplicate
python -m scrapesuite.foundry polish \
  /tmp/test_output/dupes.jsonl \
  --dedupe \
  --dedupe-keys id \
  --output /tmp/test_output/deduped.jsonl

# Verify: should have 3 lines instead of 4
wc -l /tmp/test_output/deduped.jsonl
```

**Test 14: Field Transformations**
```bash
# Create test data
cat > /tmp/test_output/transform_test.jsonl << 'EOF'
{"title": "  ARTICLE TITLE  ", "url": "https://example.com/page?utm_source=test", "date": "2024-01-15"}
{"title": "another title", "url": "https://subdomain.example.org/article", "date": "2024-02-20"}
EOF

# Apply transformations
python -m scrapesuite.foundry polish \
  /tmp/test_output/transform_test.jsonl \
  --transform title:normalize_text \
  --transform url:extract_domain \
  --transform date:parse_date \
  --output /tmp/test_output/transformed.jsonl

# Check results:
cat /tmp/test_output/transformed.jsonl | python -m json.tool
```

**Test 15: Validation**
```bash
# Create data with invalid emails
cat > /tmp/test_output/validate_test.jsonl << 'EOF'
{"email": "valid@example.com", "url": "https://example.com"}
{"email": "invalid-email", "url": "not-a-url"}
{"email": "another@test.org", "url": "https://test.org"}
EOF

# Validate and filter
python -m scrapesuite.foundry polish \
  /tmp/test_output/validate_test.jsonl \
  --validate email:email \
  --validate url:url \
  --skip-invalid \
  --output /tmp/test_output/validated.jsonl

# Should keep only valid records (2 records)
wc -l /tmp/test_output/validated.jsonl
```

**Test 16: Statistics**
```bash
# Get statistics
python -m scrapesuite.foundry polish \
  /tmp/test_output/dupes.jsonl \
  --dedupe \
  --dedupe-keys id \
  --stats

# Expected: Shows input count, duplicates removed, output count
```

---

### 1.5 Crate - Data Export

**Test 17: Export to CSV**
```bash
# Create test data
cat > /tmp/test_output/export_test.jsonl << 'EOF'
{"title": "Article 1", "author": "John Doe", "date": "2024-01-15"}
{"title": "Article 2", "author": "Jane Smith", "date": "2024-02-20"}
{"title": "Article 3", "author": "Bob Jones", "date": "2024-03-10"}
EOF

# Export to CSV
python -m scrapesuite.foundry crate \
  /tmp/test_output/export_test.jsonl \
  /tmp/test_output/output.csv

# Verify:
cat /tmp/test_output/output.csv
```

**Test 18: Export to JSON**
```bash
# Export to pretty JSON
python -m scrapesuite.foundry crate \
  /tmp/test_output/export_test.jsonl \
  /tmp/test_output/output.json \
  --pretty

# Verify:
cat /tmp/test_output/output.json
```

**Test 19: Export to SQLite**
```bash
# Export to SQLite
python -m scrapesuite.foundry crate \
  /tmp/test_output/export_test.jsonl \
  /tmp/test_output/output.db \
  --table articles

# Verify:
sqlite3 /tmp/test_output/output.db "SELECT * FROM articles;"
sqlite3 /tmp/test_output/output.db ".schema articles"
```

**Test 20: Export with Metadata Exclusion**
```bash
# Create data with metadata
cat > /tmp/test_output/with_metadata.jsonl << 'EOF'
{"title": "Article", "_source": "web", "_timestamp": "2024-01-01"}
EOF

# Export excluding metadata
python -m scrapesuite.foundry crate \
  /tmp/test_output/with_metadata.jsonl \
  /tmp/test_output/no_meta.csv \
  --exclude-meta

# Verify metadata fields are excluded:
cat /tmp/test_output/no_meta.csv
```

**Test 21: SQLite Replace/Append Modes**
```bash
# Create initial export
python -m scrapesuite.foundry crate \
  /tmp/test_output/export_test.jsonl \
  /tmp/test_output/mode_test.db \
  --table items

# Check count:
sqlite3 /tmp/test_output/mode_test.db "SELECT COUNT(*) FROM items;"

# Append more data
python -m scrapesuite.foundry crate \
  /tmp/test_output/export_test.jsonl \
  /tmp/test_output/mode_test.db \
  --table items \
  --if-exists append

# Should have 6 records now:
sqlite3 /tmp/test_output/mode_test.db "SELECT COUNT(*) FROM items;"

# Replace all data
python -m scrapesuite.foundry crate \
  /tmp/test_output/export_test.jsonl \
  /tmp/test_output/mode_test.db \
  --table items \
  --if-exists replace

# Back to 3 records:
sqlite3 /tmp/test_output/mode_test.db "SELECT COUNT(*) FROM items;"
```

---

### 1.6 Complete Pipeline Test

**Test 22: End-to-End Foundry Pipeline**
```bash
# Step 1: Analyze
python -m scrapesuite.foundry probe \
  --file tests/fixtures/fda_list.html \
  --format json \
  --output /tmp/test_output/pipeline_analysis.json

# Step 2: Extract (using existing schema)
python -m scrapesuite.foundry forge \
  examples/jobs/fda.yml \
  --file tests/fixtures/fda_list.html \
  --output /tmp/test_output/pipeline_raw.jsonl

# Step 3: Clean and deduplicate
python -m scrapesuite.foundry polish \
  /tmp/test_output/pipeline_raw.jsonl \
  --dedupe \
  --dedupe-keys title \
  --transform title:normalize_text \
  --output /tmp/test_output/pipeline_clean.jsonl

# Step 4: Export to CSV
python -m scrapesuite.foundry crate \
  /tmp/test_output/pipeline_clean.jsonl \
  /tmp/test_output/pipeline_final.csv

# Step 5: Export to SQLite
python -m scrapesuite.foundry crate \
  /tmp/test_output/pipeline_clean.jsonl \
  /tmp/test_output/pipeline_final.db \
  --table fda_recalls

# Verify all outputs exist:
ls -lh /tmp/test_output/pipeline_*

# Check CSV content:
cat /tmp/test_output/pipeline_final.csv

# Check SQLite content:
sqlite3 /tmp/test_output/pipeline_final.db "SELECT title FROM fda_recalls LIMIT 3;"
```

---

## Part 2: Legacy Wizard Testing

### 2.1 Interactive Wizard

**Test 23: Run Wizard (Manual)**
```bash
# Launch interactive wizard
python -m scrapesuite.cli init

# Follow prompts:
# 1. Choose template or paste HTML
# 2. Enter job details
# 3. Configure selectors
# 4. Save job file

# Verify job was created:
ls -l jobs/
```

**Test 24: Run Generated Job**
```bash
# Run a job created by wizard (use actual filename)
python -m scrapesuite.cli run jobs/YOUR_JOB.yml --offline --max-items 5

# Expected: Extracts data using configured selectors
```

---

### 2.2 Job Execution

**Test 25: Run Example Job (Offline)**
```bash
# Run FDA example offline
python -m scrapesuite.cli run examples/jobs/fda.yml --offline --max-items 10

# Expected: Runs without network, uses cached/fixture data
```

**Test 26: Run Job (Live)**
```bash
# Run live job with limits
python -m scrapesuite.cli run examples/jobs/fda.yml --live --max-items 5

# Expected: 
# - Fetches from actual URL
# - Respects rate limiting
# - Saves to data/cache/
```

**Test 27: Job with Rate Limiting**
```bash
# Run with custom rate limit
python -m scrapesuite.cli run examples/jobs/fda.yml \
  --live \
  --max-items 10 \
  --rps 0.5

# Expected: Slower execution due to rate limit
```

---

### 2.3 State Management

**Test 28: View State**
```bash
# Check state database
python -m scrapesuite.cli state

# Expected: Shows jobs, cursor positions, item counts
```

**Test 29: Reset Job State**
```bash
# Reset state for specific job
python -m scrapesuite.cli reset fda_recalls

# Verify state was cleared:
python -m scrapesuite.cli state
```

---

### 2.4 Robots.txt Testing

**Test 30: Check Robots.txt**
```bash
# Check if URL is allowed by robots.txt
python -c "
from scrapesuite import check_robots

url = 'https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts'
allowed = check_robots(url, 'ScrapeSuite')
print(f'Allowed: {allowed}')
"

# Expected: True or False based on robots.txt
```

---

## Part 3: Error Handling & Edge Cases

### 3.1 Invalid Input Tests

**Test 31: Invalid Schema File**
```bash
# Try to use non-existent schema
python -m scrapesuite.foundry forge /tmp/nonexistent.yml \
  --file tests/fixtures/fda_list.html

# Expected: Clear error message
```

**Test 32: Invalid HTML File**
```bash
# Try with non-existent HTML
python -m scrapesuite.foundry probe --file /tmp/nonexistent.html

# Expected: File not found error
```

**Test 33: Malformed JSONL**
```bash
# Create malformed JSONL
echo "not valid json" > /tmp/test_output/bad.jsonl

# Try to process it
python -m scrapesuite.foundry polish /tmp/test_output/bad.jsonl \
  --dedupe \
  --output /tmp/test_output/out.jsonl

# Expected: Error with line number
```

**Test 34: Empty Input**
```bash
# Create empty file
touch /tmp/test_output/empty.jsonl

# Try to export it
python -m scrapesuite.foundry crate \
  /tmp/test_output/empty.jsonl \
  /tmp/test_output/empty.csv

# Expected: Handles gracefully (empty CSV or error message)
```

---

### 3.2 Network Error Handling

**Test 35: Invalid URL**
```bash
# Try invalid URL
python -m scrapesuite.foundry probe https://this-domain-does-not-exist-12345.com

# Expected: Network error handling
```

**Test 36: Timeout Handling**
```bash
# Try URL that times out (example)
python -m scrapesuite.foundry forge examples/jobs/fda.yml \
  --url https://httpbin.org/delay/30 \
  --max-pages 1

# Expected: Should timeout gracefully
```

---

## Part 4: Performance & Load Testing

### 4.1 Large File Handling

**Test 37: Large JSONL File**
```bash
# Create large JSONL file (1000 records)
python -c "
import json
with open('/tmp/test_output/large.jsonl', 'w') as f:
    for i in range(1000):
        f.write(json.dumps({'id': i, 'title': f'Article {i}', 'content': 'Lorem ipsum ' * 50}) + '\n')
"

# Process it
time python -m scrapesuite.foundry polish \
  /tmp/test_output/large.jsonl \
  --dedupe \
  --dedupe-keys id \
  --output /tmp/test_output/large_clean.jsonl

# Export to database
time python -m scrapesuite.foundry crate \
  /tmp/test_output/large_clean.jsonl \
  /tmp/test_output/large.db \
  --table records

# Verify count:
sqlite3 /tmp/test_output/large.db "SELECT COUNT(*) FROM records;"
```

**Test 38: Memory Usage**
```bash
# Monitor memory while processing large file
/usr/bin/time -v python -m scrapesuite.foundry crate \
  /tmp/test_output/large.jsonl \
  /tmp/test_output/large_export.csv 2>&1 | grep "Maximum resident"
```

---

## Part 5: Integration Tests

### 5.1 Foundry + Legacy Integration

**Test 39: Export Legacy Job Output with Foundry**
```bash
# Run legacy job to create output
python -m scrapesuite.cli run examples/jobs/fda.yml --offline --max-items 10

# Find the output file
OUTPUT_FILE=$(ls -t data/cache/fda/*.parquet 2>/dev/null | head -1)

# Convert parquet to JSONL (if needed, using pandas)
python -c "
import pandas as pd
import sys
try:
    df = pd.read_parquet('$OUTPUT_FILE')
    df.to_json('/tmp/test_output/legacy_output.jsonl', orient='records', lines=True)
    print('Converted successfully')
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
"

# Process with Foundry tools
python -m scrapesuite.foundry polish \
  /tmp/test_output/legacy_output.jsonl \
  --dedupe \
  --stats \
  --output /tmp/test_output/polished_legacy.jsonl

# Export
python -m scrapesuite.foundry crate \
  /tmp/test_output/polished_legacy.jsonl \
  /tmp/test_output/legacy_final.csv
```

---

## Part 6: Help & Documentation

**Test 40: Help Commands**
```bash
# Main help
python -m scrapesuite.foundry --help

# Tool-specific help
python -m scrapesuite.foundry probe --help
python -m scrapesuite.foundry blueprint --help
python -m scrapesuite.foundry forge --help
python -m scrapesuite.foundry polish --help
python -m scrapesuite.foundry crate --help

# Legacy CLI help
python -m scrapesuite.cli --help
python -m scrapesuite.cli run --help
python -m scrapesuite.cli state --help
```

---

## Verification Checklist

After completing all tests, verify:

- [ ] All Foundry tools execute without errors
- [ ] Pipeline works end-to-end (probe → blueprint → forge → polish → crate)
- [ ] CSV, JSON, and SQLite exports work correctly
- [ ] Deduplication and transformations work as expected
- [ ] Legacy wizard still functional
- [ ] State management works
- [ ] Rate limiting is respected
- [ ] Error messages are clear and helpful
- [ ] Help commands display properly
- [ ] Large files are handled efficiently
- [ ] All output files are created correctly

---

## Cleanup

```bash
# Clean up test outputs
rm -rf /tmp/test_output

# Optional: Reset test state
python -m scrapesuite.cli reset fda_recalls
python -m scrapesuite.cli reset test_job

# Remove test job files if created
rm -f jobs/test_*.yml
```

---

## Quick Smoke Test (30 seconds)

For rapid validation, run these 5 tests:

```bash
# 1. Probe
python -m scrapesuite.foundry probe --file tests/fixtures/fda_list.html

# 2. Blueprint validate
python -m scrapesuite.foundry blueprint validate examples/jobs/fda.yml

# 3. Forge extract
python -m scrapesuite.foundry forge examples/jobs/fda.yml \
  --file tests/fixtures/fda_list.html --output /tmp/quick.jsonl

# 4. Polish dedupe
python -m scrapesuite.foundry polish /tmp/quick.jsonl \
  --dedupe --output /tmp/quick_clean.jsonl

# 5. Crate export
python -m scrapesuite.foundry crate /tmp/quick_clean.jsonl /tmp/quick.csv

# Verify: All 5 commands succeed and files are created
ls -lh /tmp/quick*
```

---

## Troubleshooting

**Issue**: `ModuleNotFoundError`
- **Fix**: Ensure you're in the scrapesuite directory and have installed requirements

**Issue**: `Permission denied` errors
- **Fix**: Use `/tmp` for test outputs or check directory permissions

**Issue**: Tests timeout or hang
- **Fix**: Check network connectivity, use `--max-pages 1` for URL tests

**Issue**: SQLite errors
- **Fix**: Ensure sqlite3 is installed: `sqlite3 --version`

**Issue**: Import errors after cleanup
- **Fix**: Run `python -m pytest -q` to verify all imports still work

---

## Summary

This test plan covers:
- ✅ All 5 Foundry tools
- ✅ Complete end-to-end pipeline
- ✅ Legacy wizard functionality
- ✅ Error handling
- ✅ Performance considerations
- ✅ Integration between old and new systems

**Total Tests**: 40+ manual test scenarios  
**Estimated Time**: 
- Quick smoke test: 1 minute
- Part 1 (Foundry): 20 minutes
- Part 2 (Legacy): 10 minutes
- Parts 3-5 (Edge cases): 15 minutes
- **Full suite**: ~45 minutes
