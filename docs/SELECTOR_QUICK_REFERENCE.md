# Selector Quick Reference Guide

Quick guide for writing resilient selectors for modern websites.

## TL;DR

**✅ DO:**
- Use structural selectors: `h3 a`, `article > p`, `div > span`
- Use semantic HTML: `article`, `section`, `time`, `nav`
- Extract attributes: `a::attr(href)`, `img::attr(src)`, `time::attr(datetime)`
- Keep it simple: 2-3 levels max

**❌ DON'T:**
- Dynamic classes: `.css-17p10p8`, `.emotion-abc123`, `.sc-xyz`
- Deep nesting: `div > div > div > div > span > a`
- Generated IDs: `#item-12345`, `#product-uuid-abc`
- Framework internals: `[data-reactid]`, `[data-test-id]`

---

## Common Patterns

### Title Extraction

```yaml
# ❌ Brittle - will break when CSS changes
title: h3.css-17p10p8.headline-class a

# ✅ Resilient - structural hierarchy
title: h3 a

# ✅ Better - more specific but still structural
title: article h3 a
```

### URL Extraction

```yaml
# ✅ Attribute extraction is always stable
url: a::attr(href)

# ✅ More specific if needed
url: article > a::attr(href)
```

### Date Extraction

```yaml
# ✅ Semantic HTML with attribute
date: time::attr(datetime)

# ✅ Alternative with text content
date: .published-date time
```

### Image Extraction

```yaml
# ✅ Direct attribute extraction
image: img::attr(src)

# ✅ Specific image within article
image: article img::attr(src)

# ✅ Srcset for responsive images
image: img::attr(srcset)
```

### Description/Summary

```yaml
# ✅ First paragraph in article
description: article > p

# ✅ Specific semantic class (if stable)
description: .article-summary

# ❌ Dynamic class
description: p.css-xyz123
```

---

## Framework-Specific Patterns

### React / Next.js / CSS-in-JS

```yaml
# ✅ Ignore dynamic classes, use structure
title: h3 a
summary: article > div > p

# ✅ Use data attributes if present
author: [data-author-name]

# ❌ Avoid generated classes
title: .css-17p10p8  # Changes with every build
```

### Vue.js

```yaml
# ✅ Target semantic structure
title: h3 a

# ✅ Use v-bind stable attributes
category: [data-category]

# ❌ Avoid scoped CSS hashes
title: .title-xyz123  # Vue scoped CSS
```

### WordPress

```yaml
# ✅ WordPress uses stable classes
title: .entry-title a
content: .entry-content
author: .author-name
date: .published-date
```

### Drupal

```yaml
# ✅ Drupal field classes are stable
title: .field--name-title a
body: .field--type-text-with-summary
image: .field--name-field-image img::attr(src)
```

---

## Testing Your Selectors

### Quick Test in Python

```python
from bs4 import BeautifulSoup
import requests

url = "https://example.com"
html = requests.get(url).text
soup = BeautifulSoup(html, 'html.parser')

# Test your selector
items = soup.select('article h3 a')
print(f"Found {len(items)} items")

if items:
    print(f"First item: {items[0].text}")
```

### Use the Audit Tool

```bash
# Audit existing schema
python scripts/audit_schema_selectors.py examples/schemas/my_schema.yml

# Audit multiple schemas
python scripts/audit_schema_selectors.py examples/schemas/*.yml
```

### Validation Checklist

- [ ] Selector finds >0 items
- [ ] Selector doesn't use `.css-*`, `.emotion-*`, `.sc-*` classes
- [ ] Selector is 2-3 levels deep (not 5+)
- [ ] Selector works on multiple pages from same site
- [ ] Extracted values are not None/empty

---

## Migration Guide

### Step 1: Identify Problematic Selectors

```bash
python scripts/audit_schema_selectors.py my_schema.yml
```

### Step 2: Fetch Sample HTML

```python
import requests
from bs4 import BeautifulSoup

html = requests.get('https://example.com').text
soup = BeautifulSoup(html, 'html.parser')

# Find repeated elements
articles = soup.select('article')
print(f"Found {len(articles)} articles")

# Inspect first article
first = articles[0]
print(first.prettify()[:500])
```

### Step 3: Build Structural Selectors

```python
from quarry.lib.selectors import build_robust_selector

# Your current brittle selector
brittle = "h3.css-17p10p8.emotion-abc a"

# Convert to robust
robust = build_robust_selector(brittle, ['tag'])
print(robust)  # Output: h3 a
```

### Step 4: Validate New Selectors

```python
from quarry.lib.selectors import validate_selector

result = validate_selector(soup, 'h3 a')
print(f"Valid: {result['valid']}, Count: {result['count']}")
```

### Step 5: Update Schema

```yaml
# Before
selectors:
  item: article.css-xyz
  fields:
    title: h3.css-abc a.css-def

# After
selectors:
  item: article
  fields:
    title: h3 a
```

---

## Troubleshooting

### "No items extracted"

1. Check item selector: `soup.select('article')`
2. Try broader selector: `article` → `div` → `*` (wildcard)
3. Use wizard to analyze: `quarry init`

### "Fields extracting as None"

1. Field selectors are relative to item, not document
2. Test within item context:
   ```python
   item = soup.select_one('article')
   title = item.select_one('h3 a')
   ```
3. Remove item-specific classes, use structure

### "Selector broke after site update"

1. Site likely changed HTML structure (not just CSS)
2. Re-analyze with wizard: `quarry init`
3. Update structural selectors to match new hierarchy
4. Consider selector fallback chains (see DYNAMIC_CSS_STRATEGY.md)

---

## Advanced: Selector Fallback Chains

For maximum resilience, use fallback chains (future enhancement):

```yaml
# Proposed syntax (not yet implemented)
title:
  - h3.headline a          # Try specific first (fast)
  - h3 a                   # Fallback to structural
  - article a              # Final fallback

# Current workaround: use most structural selector
title: h3 a
```

---

## Resources

- **Full Strategy Guide:** [docs/DYNAMIC_CSS_STRATEGY.md](DYNAMIC_CSS_STRATEGY.md)
- **Utility Examples:** [examples/use_selector_utilities.py](../examples/use_selector_utilities.py)
- **Audit Tool:** [scripts/audit_schema_selectors.py](../scripts/audit_schema_selectors.py)
- **Resilient Schema Example:** [examples/schemas/nyt_resilient.yml](../examples/schemas/nyt_resilient.yml)

---

## Quick Decision Tree

```
Does selector use .css-*, .emotion-*, .sc-* classes?
├─ YES → Replace with structural equivalent
└─ NO → Is it deeper than 3 levels?
    ├─ YES → Simplify to 2-3 levels
    └─ NO → Does it use semantic HTML?
        ├─ YES → ✅ Good selector!
        └─ NO → Consider adding semantic tags
```

---

**Last Updated:** 2024
**Maintainer:** Quarry Team
