# ScrapeSuite Architecture & Limitations

## **Current Reality: Hard-Coded Parsers**

### What Actually Works Today

ScrapeSuite currently has **3 hand-coded parsers** that work because we wrote custom code for each site:

```
┌─────────────────────────────────────────────────────────┐
│                    CURRENT ARCHITECTURE                  │
└─────────────────────────────────────────────────────────┘

Site                Parser               What It Does
─────────────────────────────────────────────────────────
FDA.gov          → FDAConnector        → Hard-coded CSS selectors
                                         for FDA's HTML structure

weather.gov      → NWSConnector        → Hard-coded CSS selectors
                                         for NWS's HTML structure

(any other)      → CustomConnector     → Generic "find all <a> tags"
                                         (BREAKS on real sites!)
```

### Example: FDA Parser

```python
# This ONLY works for FDA's specific HTML
anchors = soup.select("a[href*='/safety/recalls-market-withdrawals-safety-alerts/']")
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      Hard-coded path pattern specific to FDA.gov

for anchor in anchors:
    href = anchor.get("href", "")
    slug_match = slug_pattern.search(href)  # Regex for FDA slug format
    title = anchor.get_text(strip=True)     # Assumes title in anchor text
    # ...
```

**This code is useless for:**
- Hacker News (different HTML structure)
- Reddit (different HTML structure)  
- Any blog (different HTML structure)
- E-commerce sites (different HTML structure)

---

## **The "Custom Connector" Illusion**

The `CustomConnector` pretends to be generic but is actually just:

```python
def list_parser(self, html: str) -> list[Raw]:
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.find_all("a", href=True)  # Find ALL links (way too broad!)
    
    for anchor in anchors[:3]:  # Only take first 3!
        # Extract data assuming a structure that doesn't exist
```

**What happens in practice:**

```
Hacker News:
  Found: "Untitled", "Hacker News", "new" (navigation links, not stories!)
  
Reddit:
  Found: "Home", "Popular", "All" (header links, not posts!)
  
Product Hunt:
  Found: Random navigation items (not products!)
```

It's essentially **broken by design** for anything except trivial HTML.

---

## **Why Each Site Needs Custom Code**

Every website has different HTML structure:

### Example 1: Hacker News

```html
<tr class="athing" id="42742066">
  <td class="title">
    <span class="titleline">
      <a href="https://ironclad-os.org/">Ironclad – formally verified OS</a>
    </span>
  </td>
</tr>
```

**Requires:**
- CSS selector: `.athing`
- Title in: `.titleline > a`
- URL in: anchor's `href`
- ID in: `<tr id="...">`

### Example 2: Reddit (Old Reddit)

```html
<div class="thing" data-fullname="t3_xyz">
  <a class="title" href="/r/python/comments/xyz/my-post">
    My Post Title
  </a>
  <div class="score">123 points</div>
</div>
```

**Requires:**
- CSS selector: `.thing`
- Title in: `.title`
- ID in: `data-fullname` attribute
- Score in: `.score`

### Example 3: FDA.gov (What we support)

```html
<a href="/safety/recalls-market-withdrawals-safety-alerts/acme-foods-allergy">
  Acme Foods allergy alert
</a>
```

**Requires:**
- CSS selector: `a[href*='/safety/recalls-market-withdrawals-safety-alerts/']`
- Title in: anchor text
- ID from: URL slug extraction

---

## **Current Capabilities Matrix**

| Site Type | Works? | Why/Why Not |
|-----------|--------|-------------|
| **FDA.gov** | ✅ Yes | Hand-coded parser |
| **weather.gov** | ✅ Yes | Hand-coded parser |
| **Hacker News** | ❌ No | Different HTML structure |
| **Reddit** | ❌ No | Different HTML structure |
| **Stack Overflow** | ❌ No | Different HTML structure |
| **GitHub** | ❌ No | Different HTML structure |
| **Product Hunt** | ❌ No | Different HTML structure |
| **Medium** | ❌ No | Different HTML structure |
| **Any blog** | ❌ Maybe | Only if extremely simple |
| **E-commerce** | ❌ No | Complex, dynamic |

---

## **The Transform Problem**

Even if you parse data correctly, transforms are also hard-coded:

```python
# FDA transform
def normalize(records: list[dict]) -> Frame:
    rows = []
    for rec in records:
        class_val = rec.get("class", "")  # FDA-specific field
        class_weight = _CLASS_WEIGHT.get(class_val, 1)  # FDA-specific logic
        
        rows.append({
            "id": rec.get("id", ""),
            "source": "fda",  # Hard-coded source
            "title": rec.get("title", ""),
            "class": class_val,  # FDA-specific
            "class_weight": class_weight,  # FDA-specific
            "category": rec.get("category", ""),  # FDA-specific
        })
```

**This transform assumes:**
- Records have a "class" field (I, II, III)
- Categories exist
- Specific schema structure

**Won't work for:**
- Hacker News (has points, comments, not classes)
- Reddit (has upvotes, subreddit, not categories)
- Blogs (has tags, author, not classes)

---

## **What Would Be Needed for Generic Scraping**

To scrape arbitrary websites, you'd need:

### Option 1: YAML-Defined Selectors (Scrapy/Apify style)

```yaml
job: hackernews
source:
  entry: https://news.ycombinator.com
  selectors:
    item: .athing
    title: .titleline > a
    url: .titleline > a::attr(href)
    id: ::attr(id)
    points: .score::text
```

**Complexity:** Medium  
**Flexibility:** High  
**Problem:** User must understand CSS selectors and HTML structure

### Option 2: AI-Powered Extraction (Diffbot/Apify Auto-Extract style)

```yaml
job: any_site
source:
  entry: https://example.com
  extract:
    - type: article
      fields: [title, author, date, content]
```

**Complexity:** High (requires ML model)  
**Flexibility:** Very high  
**Problem:** Expensive, requires API service or local model

### Option 3: Visual Selector Builder (Octoparse style)

```
User clicks on elements in browser
→ Tool generates CSS selectors
→ YAML config created automatically
```

**Complexity:** Very high (requires browser automation + UI)  
**Flexibility:** Very high  
**Problem:** Complex implementation

### Option 4: Template Library (Current approach)

```python
# Each site needs a custom connector
class HackerNewsConnector:
    def list_parser(self, html):
        soup = BeautifulSoup(html, "html.parser")
        stories = soup.select(".athing")
        # Custom logic for HN...

class RedditConnector:
    def list_parser(self, html):
        soup = BeautifulSoup(html, "html.parser")
        posts = soup.select(".thing")
        # Custom logic for Reddit...
```

**Complexity:** Low (per site)  
**Flexibility:** Low (1 site per connector)  
**Problem:** Doesn't scale (need code for each site)

---

## **Actual Test: Custom Connector on Real Sites**

```bash
# What the custom connector actually extracts:

Site: Hacker News
├─ Found: "Untitled", "Hacker News", "new"
└─ Reality: These are navigation links, not stories!

Site: Reddit
├─ Found: "Home", "Popular", "All"
└─ Reality: These are header links, not posts!

Site: Product Hunt
├─ Found: Random navigation items
└─ Reality: Not products at all!
```

---

## **Bottom Line**

### ✅ **What Works:**
1. FDA.gov recalls (hand-coded)
2. weather.gov alerts (hand-coded)
3. Any site **if you write a custom connector** with:
   - Site-specific CSS selectors
   - Site-specific parsing logic
   - Site-specific transform functions

### ❌ **What Doesn't Work:**
1. Generic scraping of arbitrary sites
2. "Point and click" scraping
3. AI-powered auto-extraction
4. Visual selector building
5. The `CustomConnector` on real sites (it's a stub)

### 🚧 **To Make It Generic, You'd Need:**
1. **YAML selector definitions** (2-3 days work)
   - CSS selector configuration
   - Field mapping syntax
   - Validation logic

2. **Selector test framework** (1 day)
   - Test selectors against fixtures
   - Validate extraction results

3. **Better custom connector** (2 days)
   - Accept selector config from YAML
   - Apply selectors dynamically
   - Handle missing fields gracefully

4. **Transform configurability** (1 day)
   - Field mapping in YAML
   - Type coercion rules
   - Default values

5. **Documentation & examples** (1 day)
   - How to inspect HTML
   - How to write selectors
   - Common patterns library

**Total effort:** ~1 week to get basic YAML-configured scraping working

---

## **Recommendation for Product Positioning**

### Option A: **Positioned as "Template Library"**
> "ScrapeSuite: Pre-built connectors for common data sources (FDA, NWS, etc.) + framework for adding your own"

- ✅ Honest about limitations
- ✅ Shows off working examples
- ✅ Extensible architecture
- ❌ Limited market appeal

### Option B: **Add YAML Selectors (1 week work)**
> "ScrapeSuite: Define scraping jobs in YAML - no code required"

- ✅ Much broader appeal
- ✅ Competitive with Scrapy
- ✅ Good for portfolio
- ⏰ Requires 1 week implementation

### Option C: **Current State + Better Docs**
> "ScrapeSuite: Production-grade scraping framework with offline testing, rate limiting, and state management"

- ✅ Emphasizes strong features (robots.txt, rate limits, state)
- ✅ Honest about connector limitations
- ✅ Shippable today
- ⚠️ Users must write Python code for new sites

---

## **My Recommendation**

**Ship Option C today** (emphasize the infrastructure), then **add Option B features** incrementally:

1. **Today:** Market as a framework with excellent infrastructure
   - Robots.txt compliance ✅
   - Per-domain rate limiting ✅
   - State management ✅
   - Failed URL tracking ✅
   - 3 working examples ✅

2. **Week 2:** Add YAML selector support
   - Generic connector with configurable selectors
   - Field mapping in transforms
   - 5-10 more site templates

3. **Week 3:** Add cookbook/templates
   - Reddit template
   - Hacker News template
   - Stack Overflow template
   - E-commerce template
   - Blog template

This gives you something **sellable today** while building toward a more powerful product.
