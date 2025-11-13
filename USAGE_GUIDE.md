# Quarry Usage Guide

Complete guide to using **Quarry** - a modern web data extraction toolkit with intelligent templates and interactive workflows.

---

## 📚 Table of Contents

1. [Quick Start](#-quick-start)
2. [The Quarry Workflow](#-the-quarry-workflow)
3. [Tool Reference](#-tool-reference)
   - [Scout](#1-scout---discover--analyze)
   - [Survey](#2-survey---map-data-structures)
   - [Excavate](#3-excavate---extract-data)
   - [Polish](#4-polish---refine-data)
   - [Ship](#5-ship---export-data)
4. [Complete Examples](#-complete-examples)
5. [Advanced Usage](#-advanced-usage)
6. [Best Practices](#-best-practices)

---

## 🚀 Quick Start

### Your First Extraction

```bash
# 1. Analyze a webpage
quarry.scout https://example.com

# 2. Create an extraction schema
quarry.survey create

# 3. Extract data
quarry.excavate schema.yml --url https://example.com

# 4. Clean the data
quarry.polish output.jsonl --dedupe

# 5. Export to CSV
quarry.ship output.jsonl output.csv
```

---

## 🔄 The Quarry Workflow

Quarry follows a **mining metaphor** for web data extraction:

```
┌─────────┐      ┌─────────┐      ┌──────────┐      ┌────────┐      ┌──────┐
│ SCOUT   │  →   │ SURVEY  │  →   │ EXCAVATE │  →   │ POLISH │  →   │ SHIP │
│ Discover│      │ Map     │      │ Extract  │      │ Refine │      │Export│
└─────────┘      └─────────┘      └──────────┘      └────────┘      └──────┘
  Analyze          Design           Execute           Clean          Package
  the site         schemas          extraction        data           results
```

### Seamless Tool Chaining

Quarry tools can automatically pass data to the next tool in the workflow. When using interactive mode, each tool will offer to launch the next step with your data already loaded:

- **Survey → Excavate**: After creating a schema, survey offers to run excavate with it
- **Excavate → Polish**: After extraction, excavate offers to clean the data
- **Polish → Ship**: After polishing, polish offers to export the results

This creates a smooth end-to-end workflow without manually specifying file paths.

### When to Use Each Tool

| Tool | Use When | Output |
|------|----------|--------|
| **Scout** | Exploring a new website | Analysis JSON (patterns, frameworks) |
| **Survey** | Designing extraction rules | Schema YAML file |
| **Excavate** | Running the actual scraping | Data (JSONL format) |
| **Polish** | Data needs cleaning | Cleaned/transformed data |
| **Ship** | Exporting to final format | CSV/JSON/SQLite/Parquet |

---

## 🛠️ Tool Reference

### 1. Scout - Discover & Analyze

**Purpose**: Analyze HTML structure, detect frameworks, find patterns, suggest selectors.

#### Interactive Mode

```bash
quarry.scout
# → Prompts for URL or file
# → Choose output format
# → Save results (optional)
```

#### Batch Mode

```bash
# Analyze a URL
quarry.scout https://example.com

# Analyze local HTML file
quarry.scout page.html

# Save analysis as JSON
quarry.scout https://example.com --format json --output analysis.json

# Show API endpoint guide (for infinite scroll sites)
quarry.scout https://example.com --find-api
```

#### Output Fields

```json
{
  "url": "https://example.com",
  "frameworks": ["react", "bootstrap"],
  "containers": [
    {
      "selector": "div.product-list > div.product-card",
      "item_count": 20,
      "sample_text": "Product Name $99.99",
      "content_score": 85,
      "is_content": true
    }
  ],
  "metadata": {
    "title": "E-commerce Store",
    "description": "...",
    "language": "en"
  },
  "pagination": {
    "detected": true,
    "type": "numbered",
    "selector": "a.next-page"
  }
}
```

#### Common Use Cases

**Finding content containers:**
```bash
quarry.scout https://news-site.com --format json | jq '.containers[] | select(.is_content==true)'
```

**Detecting frameworks:**
```bash
quarry.scout https://app.com | grep frameworks
```

**Troubleshooting infinite scroll:**
```bash
quarry.scout https://spa-site.com --find-api
```

---

### 2. Survey - Map Data Structures

**Purpose**: Design extraction schemas (interactively or from templates).

#### Interactive Mode

```bash
quarry.survey create
# → Schema name
# → Use template? (y/n)
# → Template type (article/product/financial_data/...)
# → Target URL (optional)
# → Define fields interactively
```

#### Using Templates

```bash
# List available templates
quarry.survey templates

# Create from template
quarry.survey create --template article

# Preview with URL
quarry.survey preview schema.yml --url https://example.com
```

#### Available Templates

- **article** - Blog posts, news articles
- **product** - E-commerce products
- **financial_data** - Stock prices, financial reports
- **job_listing** - Job boards
- **real_estate** - Property listings
- **recipe** - Cooking recipes
- **event** - Event calendars
- **review** - Product/service reviews
- **person** - People profiles
- **organization** - Company/org info
- **research_paper** - Academic papers
- **social_media_post** - Social posts
- **video_metadata** - Video info
- **podcast_episode** - Podcast data
- **course** - Online courses

#### Schema Structure

```yaml
name: product_extraction
version: 1.0
description: Extract product listings from e-commerce site

fields:
  title:
    selector: h2.product-title
    type: text
    required: true
  
  price:
    selector: span.price
    type: text
    transform: extract_number
  
  image:
    selector: img.product-image
    attribute: src
    type: url
  
  rating:
    selector: div.rating
    attribute: data-rating
    type: number
  
  in_stock:
    selector: span.stock-status
    type: boolean
    transform: contains("In Stock")

pagination:
  next_selector: a.next-page
  max_pages: 10

container:
  selector: div.product-card
```

#### Field Types

- `text` - Plain text content
- `number` - Numeric values
- `boolean` - True/false
- `url` - URLs (auto-resolved to absolute)
- `date` - Date/time values
- `list` - Arrays of values

#### Transformations

- `extract_number` - Extract numeric value
- `clean_text` - Remove extra whitespace
- `to_lowercase` / `to_uppercase`
- `strip_html` - Remove HTML tags
- `parse_date` - Parse date strings
- `extract_domain` - Get domain from URL

---

### 3. Excavate - Extract Data

**Purpose**: Execute extraction at scale using schemas.

#### Interactive Mode

```bash
quarry.excavate
# → Select schema file
# → Choose source (URL/File/Use schema URL)
# → Enter URL or file path
# → Output filename
```

#### Batch Mode

```bash
# Extract from URL
quarry.excavate schema.yml --url https://example.com

# Extract from local HTML
quarry.excavate schema.yml --file page.html

# Specify output file
quarry.excavate schema.yml --url https://example.com --output products.jsonl

# Respect robots.txt (default: true)
quarry.excavate schema.yml --url https://example.com --respect-robots

# Skip robots.txt (for testing)
quarry.excavate schema.yml --url https://example.com --no-respect-robots

# Rate limiting
quarry.excavate schema.yml --url https://example.com --delay 2.0
```

#### Pagination

Excavate automatically follows pagination based on schema:

```yaml
pagination:
  next_selector: a.next
  max_pages: 50
  delay: 1.5  # seconds between requests
```

#### Output Format

Default output is **JSONL** (JSON Lines):

```jsonl
{"title": "Product 1", "price": 99.99, "in_stock": true}
{"title": "Product 2", "price": 149.99, "in_stock": false}
{"title": "Product 3", "price": 79.99, "in_stock": true}
```

---

### 4. Polish - Refine Data

**Purpose**: Clean, deduplicate, transform, and validate extracted data.

#### Interactive Mode

```bash
quarry.polish
# → Input file
# → Operations (dedupe/transform/validate/stats)
# → Transform fields (if selected)
# → Output file
```

#### Batch Mode

```bash
# Deduplicate
quarry.polish data.jsonl --dedupe

# Deduplicate on specific field
quarry.polish data.jsonl --dedupe --dedupe-key title

# Transform fields
quarry.polish data.jsonl --transform price:extract_number

# Multiple transforms
quarry.polish data.jsonl \
  --transform price:extract_number \
  --transform title:clean_text \
  --transform url:extract_domain

# Validate required fields
quarry.polish data.jsonl --validate --required title,price

# Show statistics
quarry.polish data.jsonl --stats

# Combine operations
quarry.polish data.jsonl \
  --dedupe \
  --transform price:extract_number \
  --validate \
  --output clean_data.jsonl
```

#### Available Transforms

```bash
# String operations
title:clean_text          # Remove extra whitespace
title:to_lowercase        # Convert to lowercase
title:to_uppercase        # Convert to uppercase
title:strip_html          # Remove HTML tags

# Numeric operations
price:extract_number      # Extract "99.99" from "$99.99"
rating:round:1            # Round to 1 decimal place

# Date operations
date:parse_date           # Parse to ISO format

# URL operations
link:extract_domain       # "example.com" from "https://example.com/page"
link:to_absolute:https://example.com  # Resolve relative URLs

# Boolean operations
in_stock:to_boolean       # Convert "yes"/"no" to true/false
```

#### Validation

```bash
# Validate required fields exist
quarry.polish data.jsonl --validate --required title,price,url

# Validate field types
quarry.polish data.jsonl --validate --types price:number,in_stock:boolean

# Validate URL format
quarry.polish data.jsonl --validate --url-fields image,link
```

---

### 5. Ship - Export Data

**Purpose**: Export data to various formats (CSV, JSON, SQLite, Parquet).

#### Interactive Mode

```bash
quarry.ship
# → Input file
# → Export format (CSV/JSON/SQLite/Parquet)
# → Format options (delimiter, table name, etc.)
# → Output file
```

#### Batch Mode

##### CSV Export

```bash
# Basic CSV
quarry.ship data.jsonl output.csv

# Custom delimiter
quarry.ship data.jsonl output.tsv --format csv --delimiter '\t'

# Select specific fields
quarry.ship data.jsonl output.csv --fields title,price,url

# Include header row
quarry.ship data.jsonl output.csv --header
```

##### JSON Export

```bash
# Pretty JSON array
quarry.ship data.jsonl output.json --format json --pretty

# Compact JSON
quarry.ship data.jsonl output.json --format json --compact

# JSON Lines (keep as JSONL)
quarry.ship data.jsonl output.jsonl --format jsonl
```

##### SQLite Export

```bash
# Create SQLite database
quarry.ship data.jsonl products.db --format sqlite --table products

# Append to existing table
quarry.ship data.jsonl products.db --format sqlite --table products --append

# Replace existing table
quarry.ship data.jsonl products.db --format sqlite --table products --replace
```

##### Parquet Export

```bash
# Export to Parquet (efficient columnar format)
quarry.ship data.jsonl output.parquet --format parquet

# With compression
quarry.ship data.jsonl output.parquet --format parquet --compression snappy
```

#### Format Comparison

| Format | Use Case | File Size | Query Speed |
|--------|----------|-----------|-------------|
| **CSV** | Excel, human-readable | Medium | Slow |
| **JSON** | APIs, web apps | Large | Slow |
| **JSONL** | Streaming, line-by-line | Large | Fast |
| **SQLite** | SQL queries, relationships | Medium | Fast |
| **Parquet** | Big data, analytics | Small | Very Fast |

---

## 💡 Complete Examples

### Example 1: E-commerce Product Scraping

```bash
# 1. Scout the site
quarry.scout https://shop.example.com/products --output products_analysis.json

# 2. Create schema (using template)
quarry.survey create --template product --output product_schema.yml

# 3. Extract products
quarry.excavate product_schema.yml \
  --url https://shop.example.com/products \
  --output raw_products.jsonl

# 4. Clean data
quarry.polish raw_products.jsonl \
  --dedupe \
  --transform price:extract_number \
  --transform title:clean_text \
  --validate --required title,price \
  --output clean_products.jsonl

# 5. Export to CSV
quarry.ship clean_products.jsonl products.csv --format csv
```

### Example 2: News Article Collection

```bash
# 1. Analyze news site
quarry.scout https://news.example.com

# 2. Create article schema
quarry.survey create --template article --output article_schema.yml

# 3. Extract articles (with pagination)
quarry.excavate article_schema.yml \
  --url https://news.example.com \
  --output articles.jsonl

# 4. Process dates and deduplicate
quarry.polish articles.jsonl \
  --transform published_date:parse_date \
  --dedupe --dedupe-key url \
  --output clean_articles.jsonl

# 5. Export to SQLite for querying
quarry.ship clean_articles.jsonl articles.db \
  --format sqlite --table articles
```

### Example 3: Real Estate Listings

```bash
# Full pipeline in interactive mode
quarry.scout  # Analyze site
quarry.survey create  # Design schema
quarry.excavate  # Extract data
quarry.polish  # Clean data
quarry.ship  # Export

# Or batch mode
quarry.excavate real_estate_schema.yml \
  --url https://listings.example.com \
  | quarry.polish --dedupe --transform price:extract_number \
  | quarry.ship - output.parquet --format parquet
```

---

## 🎯 Advanced Usage

### Programmatic API

Use Quarry in Python scripts:

```python
from quarry.tools.scout.analyzer import analyze_page
from quarry.lib.schemas import load_schema
from quarry.tools.excavate.executor import execute_extraction

# Analyze HTML
analysis = analyze_page("<html>...</html>", url="https://example.com")
print(analysis['containers'])

# Load schema
schema = load_schema("schema.yml")

# Execute extraction
results = execute_extraction(schema, url="https://example.com")
for item in results:
    print(item)
```

### Custom Transformations

Add custom transforms in `polish`:

```python
# In your code
from quarry.tools.polish.transformers import register_transform

@register_transform("custom_clean")
def custom_clean(value):
    return value.strip().replace("  ", " ")

# Then use in CLI
quarry.polish data.jsonl --transform title:custom_clean
```

### Environment Variables

Configure behavior via environment variables:

```bash
# Skip robots.txt globally
export QUARRY_IGNORE_ROBOTS=true

# Force interactive mode
export QUARRY_INTERACTIVE=true

# Set default delay
export QUARRY_DEFAULT_DELAY=2.0

# Cache directory
export QUARRY_CACHE_DIR=~/.cache/quarry
```

### Batch Processing

Process multiple sites:

```bash
# Extract from multiple URLs
for url in $(cat urls.txt); do
  quarry.excavate schema.yml --url "$url" --output "$(echo $url | md5).jsonl"
done

# Merge results
cat *.jsonl > combined.jsonl

# Process
quarry.polish combined.jsonl --dedupe --output final.jsonl
```

---

## ✨ Best Practices

### 1. **Always Scout First**
Before creating schemas, analyze the site to understand its structure.

```bash
quarry.scout https://example.com --output analysis.json
# Review analysis.json to find best selectors
```

### 2. **Use Templates When Possible**
Templates provide battle-tested schemas for common use cases.

```bash
quarry.survey create --template article  # vs manual creation
```

### 3. **Respect robots.txt**
Be a good web citizen:

```bash
# Default (respects robots.txt)
quarry.excavate schema.yml --url https://example.com

# Only ignore for testing/development
quarry.excavate schema.yml --url https://example.com --no-respect-robots
```

### 4. **Use Rate Limiting**
Avoid overwhelming servers:

```yaml
# In schema.yml
pagination:
  delay: 2.0  # 2 seconds between requests
```

### 5. **Clean Data Immediately**
Polish data right after extraction:

```bash
quarry.excavate schema.yml --url https://example.com \
  | quarry.polish --dedupe --validate \
  > clean_data.jsonl
```

### 6. **Version Your Schemas**
Track schema changes:

```yaml
name: products
version: 1.2
description: Updated selectors for new site design
```

### 7. **Use Appropriate Export Formats**

- **CSV**: For Excel, human review
- **SQLite**: For complex queries
- **Parquet**: For big data, analytics
- **JSON**: For APIs, web apps

### 8. **Test with Small Samples**
Limit pages during development:

```yaml
pagination:
  max_pages: 2  # Test with 2 pages first
```

### 9. **Handle Errors Gracefully**
```bash
# Continue on errors, log failures
quarry.excavate schema.yml --url https://example.com \
  --continue-on-error \
  --error-log errors.log
```

### 10. **Document Your Schemas**
```yaml
description: |
  Extracts product listings from Shop XYZ.
  Updated 2025-11-13: Changed price selector to span.new-price
  Maintainer: data-team@example.com
```

---

## 🐛 Troubleshooting

### No Data Extracted

**Check selectors**:
```bash
quarry.scout https://example.com --format json | jq '.containers'
# Update schema with correct selectors
```

### Pagination Not Working

**Check pagination selector**:
```bash
quarry.scout https://example.com | grep pagination
# Update next_selector in schema
```

### Blocked by Website

**Use delays and respect robots.txt**:
```yaml
pagination:
  delay: 3.0  # Increase delay
```

### Invalid Data

**Add validation**:
```bash
quarry.polish data.jsonl \
  --validate \
  --required title,price \
  --types price:number
```

---

## 📖 Additional Resources

- **[INSTALLATION.md](INSTALLATION.md)** - Installation guide
- **[MANUAL_TESTING.md](MANUAL_TESTING.md)** - Hands-on test scenarios
- **[REFACTOR_SUMMARY.md](REFACTOR_SUMMARY.md)** - Migration from v1.x
- **[GitHub Wiki](https://github.com/russellbomer/quarry/wiki)** - Extended documentation
- **[Examples](examples/)** - Sample schemas and scripts

---

## 🆘 Getting Help

- **Issues**: [GitHub Issues](https://github.com/russellbomer/quarry/issues)
- **Discussions**: [GitHub Discussions](https://github.com/russellbomer/quarry/discussions)
- **Email**: support@quarry.dev *(coming soon)*

Happy quarrying! 🪨⛏️
