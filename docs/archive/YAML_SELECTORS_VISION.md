# Example: YAML-Configured Scraping (Future Feature)

## **What It Could Look Like**

### Job with YAML Selectors (Not Implemented Yet)

```yaml
version: "1.0"
job: hackernews_stories

source:
  parser: generic  # NEW: Generic selector-based parser
  entry: https://news.ycombinator.com
  
  selectors:
    # Container for each item
    item: .athing
    
    # Fields to extract from each item
    fields:
      id:
        selector: ::attr(id)
        type: string
      
      title:
        selector: .titleline > a
        extract: text
        type: string
      
      url:
        selector: .titleline > a
        extract: attr(href)
        type: url
      
      points:
        selector: + tr .score  # Next sibling row
        extract: text
        regex: '(\d+) points'
        type: integer
        default: 0
      
      comments:
        selector: + tr .subtext a[href*='item']
        extract: text
        regex: '(\d+)\s+comments?'
        type: integer
        default: 0

transform:
  pipeline:
    - map_fields:
        # Map extracted fields to output schema
        id: id
        title: title
        url: url
        score: points
        comment_count: comments
        source: 
          value: hackernews  # Constant
        scraped_at:
          function: now()  # Built-in function

sink:
  kind: parquet
  path: data/cache/{job}/%Y%m%dT%H%M%SZ.parquet
```

---

## **How It Would Work**

### 1. Generic Connector (New Implementation)

```python
class GenericConnector:
    """YAML-configured connector using CSS selectors."""
    
    def __init__(self, entry_url: str, selectors: dict, **kwargs):
        self.entry_url = entry_url
        self.selectors = selectors
        
    def list_parser(self, html: str) -> list[Raw]:
        soup = BeautifulSoup(html, "html.parser")
        records = []
        
        # Find all items using container selector
        item_selector = self.selectors.get("item")
        items = soup.select(item_selector)
        
        # Extract fields from each item
        for item in items:
            record = {}
            
            for field_name, field_config in self.selectors["fields"].items():
                value = self._extract_field(item, field_config)
                record[field_name] = value
            
            records.append(record)
        
        return records
    
    def _extract_field(self, element, config):
        """Extract a single field using config."""
        selector = config.get("selector")
        extract = config.get("extract", "text")
        
        # Find element
        if selector.startswith("::attr"):
            # Extract attribute from current element
            attr_name = selector.replace("::attr(", "").replace(")", "")
            return element.get(attr_name, "")
        
        target = element.select_one(selector)
        if not target:
            return config.get("default", "")
        
        # Extract value
        if extract == "text":
            value = target.get_text(strip=True)
        elif extract.startswith("attr("):
            attr_name = extract.replace("attr(", "").replace(")", "")
            value = target.get(attr_name, "")
        else:
            value = str(target)
        
        # Apply regex if specified
        regex = config.get("regex")
        if regex:
            import re
            match = re.search(regex, value)
            value = match.group(1) if match else config.get("default", "")
        
        # Type conversion
        field_type = config.get("type", "string")
        return self._convert_type(value, field_type, config.get("default"))
    
    def _convert_type(self, value, field_type, default=None):
        """Convert extracted value to specified type."""
        try:
            if field_type == "integer":
                return int(value)
            elif field_type == "float":
                return float(value)
            elif field_type == "url":
                # Handle relative URLs
                from urllib.parse import urljoin
                return urljoin(self.entry_url, value)
            else:  # string
                return str(value)
        except (ValueError, TypeError):
            return default
```

---

## **Example Job Configs for Popular Sites**

### Reddit (Old Reddit)

```yaml
job: reddit_python
source:
  parser: generic
  entry: https://old.reddit.com/r/python
  
  selectors:
    item: .thing
    fields:
      id:
        selector: ::attr(data-fullname)
        type: string
      
      title:
        selector: .title
        extract: text
        type: string
      
      url:
        selector: .title
        extract: attr(href)
        type: url
      
      score:
        selector: .score.unvoted
        extract: text
        type: integer
        default: 0
      
      author:
        selector: .author
        extract: text
        type: string
      
      subreddit:
        selector: .subreddit
        extract: text
        type: string
      
      comments:
        selector: .comments
        extract: text
        regex: '(\d+) comments?'
        type: integer
        default: 0
```

### Product Hunt

```yaml
job: producthunt_today
source:
  parser: generic
  entry: https://www.producthunt.com
  
  selectors:
    item: '[data-test="post-item"]'
    fields:
      id:
        selector: ::attr(data-test-id)
        type: string
      
      title:
        selector: 'h3'
        extract: text
        type: string
      
      tagline:
        selector: '[data-test="post-tagline"]'
        extract: text
        type: string
      
      url:
        selector: 'a[data-test="post-url"]'
        extract: attr(href)
        type: url
      
      upvotes:
        selector: '[data-test="vote-count"]'
        extract: text
        type: integer
        default: 0
```

### Medium

```yaml
job: medium_topic
source:
  parser: generic
  entry: https://medium.com/tag/python
  
  selectors:
    item: article
    fields:
      title:
        selector: h2
        extract: text
        type: string
      
      url:
        selector: a[data-action="open-post"]
        extract: attr(href)
        type: url
      
      author:
        selector: '[data-testid="authorName"]'
        extract: text
        type: string
      
      read_time:
        selector: '[data-testid="readingTime"]'
        extract: text
        regex: '(\d+) min read'
        type: integer
        default: 0
      
      claps:
        selector: '[data-testid="claps"]'
        extract: text
        regex: '(\d+\.?\d*[KM]?)'
        type: string
```

---

## **Why This Would Be Better**

### Current Approach
```python
# Have to write Python code for each site
class HackerNewsConnector:
    def list_parser(self, html):
        # 50 lines of custom BeautifulSoup code
```

### YAML Approach
```yaml
# Just define selectors in YAML
selectors:
  item: .athing
  fields:
    title:
      selector: .titleline > a
      extract: text
```

### Benefits
1. **No code required** - Users define extraction in YAML
2. **Faster iteration** - Change YAML, rerun job (no code changes)
3. **Easier to share** - Job configs are portable
4. **Testable** - Validate selectors against fixtures
5. **Library of templates** - Share configs for popular sites

---

## **Implementation Checklist**

To build this feature:

- [ ] Create `GenericConnector` class (2 days)
  - [ ] CSS selector evaluation
  - [ ] Field extraction logic
  - [ ] Type conversion
  - [ ] Regex support
  - [ ] Default values
  - [ ] Error handling

- [ ] Update job YAML schema (0.5 day)
  - [ ] Add `selectors` section
  - [ ] Add `fields` configuration
  - [ ] Validation rules

- [ ] Add field mapping to transforms (1 day)
  - [ ] Generic transform with field mapping
  - [ ] Type coercion rules
  - [ ] Built-in functions (now(), etc.)

- [ ] Testing framework (1 day)
  - [ ] Selector validation
  - [ ] Extraction verification
  - [ ] Type conversion tests

- [ ] Documentation (0.5 day)
  - [ ] How to inspect HTML
  - [ ] Writing CSS selectors
  - [ ] Common patterns
  - [ ] Example configs

- [ ] Template library (1 day)
  - [ ] Hacker News
  - [ ] Reddit
  - [ ] Product Hunt
  - [ ] Medium
  - [ ] Stack Overflow

**Total: ~6 days work**

---

## **Migration Path**

### Phase 1: Keep existing connectors
```
connectors/
  fda.py        # Hand-coded (still works)
  nws.py        # Hand-coded (still works)
  custom.py     # Stub (deprecated)
  generic.py    # NEW: YAML-configured
```

### Phase 2: Add YAML configs
```
examples/jobs/
  fda.yml                  # Uses FDAConnector (legacy)
  fda_generic.yml          # Uses GenericConnector (new!)
  hackernews.yml           # Uses GenericConnector
  reddit.yml               # Uses GenericConnector
```

### Phase 3: Deprecate hand-coded
```
# Eventually convert FDA/NWS to YAML configs
# Keep Python connectors only for complex logic
```

---

This would transform Quarry from a **framework for developers** into a **tool for users** who can scrape sites just by writing YAML configs!
