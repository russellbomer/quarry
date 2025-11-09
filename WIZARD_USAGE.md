# Wizard Usage Guide

## Overview

The ScrapeSuite wizard helps you create custom scraping jobs for **any website** through an interactive, guided experience. You don't need to know CSS selectors or write Python code - the wizard analyzes the HTML structure and helps you build the configuration.

## Quick Start

```bash
python -m scrapesuite.wizard
```

The wizard will guide you through:

1. **Template selection** - Choose `custom` for generic websites
2. **URL entry** - Provide the listing page URL (not a single article/item)
3. **HTML analysis** - The wizard fetches and analyzes the page structure
4. **Pattern selection** - Choose from detected repeated patterns
5. **Field selection** - Pick which fields to extract (title, URL, date, etc.)
6. **Preview** - See sample extracted data
7. **Configuration** - Set rate limits, output format
8. **Testing** - Run an offline smoke test

## Example: Scraping Hacker News

Here's what the wizard flow looks like for Hacker News:

### Step 1: Start the wizard

```bash
python -m scrapesuite.wizard
```

### Step 2: Select template

```
Select template
  custom
> fda_example
  nws_example
```

Choose **`custom`** for generic websites.

### Step 3: Enter URL

```
Entry URL (listing page, not a single item) [https://example.com/]: 
> https://news.ycombinator.com/
```

**Important**: Enter the **listing page** (e.g., homepage, search results, category page), NOT a single item/article/post URL.

### Step 4: HTML Analysis

The wizard automatically fetches and analyzes the HTML:

```
Analyzing HTML structure...
✓ Page: Hacker News
✓ Total links: 230

Detected Item Patterns:
┏━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Option ┃ Selector   ┃ Count ┃ Sample Title             ┃
┡━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1      │ .athing    │ 30    │ Ironclad OS              │
│ 2      │ .title     │ 61    │                          │
│ 3      │ .rank      │ 30    │                          │
└────────┴────────────┴───────┴──────────────────────────┘
```

### Step 5: Select pattern

```
Select item pattern
> .athing (30 items)
  .title (61 items)
  Skip (use manual config)
```

Choose **`.athing`** (Hacker News story rows).

### Step 6: Field selection

The wizard detects common fields and shows previews:

```
Building field selectors...

Include 'title'? (preview: Ironclad – formally verified, real-time capable...)
> Yes

Selector for 'title' [span.titleline a]: 
> [Enter]

Include 'url'? (preview: https://ironclad-os.org/)
> Yes

Selector for 'url' [span.titleline a::attr(href)]: 
> [Enter]

Include 'date'? (preview: )
> No
```

**Selector syntax**:
- `span.titleline a` - Extract text from element
- `span.titleline a::attr(href)` - Extract attribute (href, src, datetime, etc.)
- `::attr(id)` - Extract attribute from item container itself

### Step 7: Preview extraction

```
Preview of extracted data:
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ title                    ┃ url                      ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Ironclad OS              │ https://ironclad-os.org/ │
│ Tabloid Language         │ https://tabloid.vercel…  │
│ Marko Framework          │ https://markojs.com/     │
└──────────────────────────┴──────────────────────────┘

Does this look correct?
> Yes
```

### Step 8: Configure job

```
Allowlist domains (comma-separated) [news.ycombinator.com]: 
> [Enter]

Rate limit (RPS) [1.0]: 
> [Enter]

Cursor field [url]: 
> [Enter]

Sink kind
  parquet
> csv

Sink path template [data/cache/%Y%m%dT%H%M%SZ.csv]: 
> data/cache/hn/%Y%m%dT%H%M%SZ.csv

Max items (for smoke test) [100]: 
> 5
```

### Step 9: Review generated config

The wizard creates `jobs/hackernews.yml`:

```yaml
version: "1"
job: hackernews
source:
  kind: html
  entry: https://news.ycombinator.com/
  parser: generic
  rate_limit_rps: 1.0
  cursor:
    field: url
    stop_when_seen: true

transform:
  pipeline:
    - normalize: generic

sink:
  kind: csv
  path: data/cache/hn/%Y%m%dT%H%M%SZ.csv

policy:
  robots: allow
  allowlist:
    - news.ycombinator.com

selectors:
  item: ".athing"
  fields:
    title: "span.titleline a"
    url: "span.titleline a::attr(href)"
```

### Step 10: Run the job

```bash
python -c "from scrapesuite.core import load_yaml, run_job; \
spec = load_yaml('jobs/hackernews.yml'); \
df, cursor = run_job(spec, max_items=10, offline=False); \
print(df)"
```

Output:

```
                                   title                              url
0  Ironclad – formally verified OS  https://ironclad-os.org/
1  Tabloid: The Clickbait Language  https://tabloid.vercel.app/
2  Marko – HTML‑based framework     https://markojs.com/
...
```

## Tips for Success

### 1. Use listing pages, not detail pages

✅ **Good** (listing pages):
- `https://news.ycombinator.com/` (homepage with list of stories)
- `https://reddit.com/r/python/` (subreddit with list of posts)
- `https://medium.com/tag/python` (tag page with list of articles)

❌ **Bad** (detail pages):
- `https://news.ycombinator.com/item?id=12345` (single story)
- `https://reddit.com/r/python/comments/abc123/...` (single post)
- `https://medium.com/@user/article-slug-12345` (single article)

### 2. Choose the most specific pattern

If the wizard finds multiple patterns:
- `.article-card` (20 items) - ✅ More specific
- `.card` (100 items) - ❌ Too generic (includes ads, navigation, etc.)
- `.post` (20 items) - ✅ Good

### 3. Use attribute extraction for links/images

- **Text content**: `h2.title` or `span.author`
- **Links**: `a.link::attr(href)`
- **Images**: `img.thumbnail::attr(src)`
- **Dates**: `time::attr(datetime)` or `span.date`
- **IDs**: `::attr(id)` or `::attr(data-id)`

### 4. Preview before finalizing

Always check the preview data. If extraction looks wrong:
- Select "No" to "Does this look correct?"
- Try a different pattern
- Or manually adjust selectors

### 5. Check robots.txt first

```bash
# Check if site allows scraping
python -c "from scrapesuite.policy import check_robots; \
print('Allowed' if check_robots('https://example.com/') else 'Blocked')"
```

### 6. Respect rate limits

- Start with **1.0 RPS** (1 request per second)
- Some sites require slower rates (0.5 or 0.1 RPS)
- Check the site's `robots.txt` for `Crawl-delay` directive

## Advanced: Manual Selector Creation

If the wizard's auto-detection doesn't work, you can manually create the YAML config:

```yaml
selectors:
  item: "article.post"  # CSS selector for repeated items
  fields:
    title: "h2.title"                    # Extract text
    url: "a.permalink::attr(href)"       # Extract href attribute
    date: "time::attr(datetime)"         # Extract datetime attribute
    author: "span.author a"              # Extract nested text
    image: "img.thumbnail::attr(src)"    # Extract src attribute
    id: "::attr(data-id)"                # Extract from item itself
```

### Finding Selectors with Browser DevTools

1. **Open browser DevTools** (F12 or right-click → Inspect)
2. **Use the element picker** (cursor icon in DevTools)
3. **Click on an item** you want to extract
4. **Look at the HTML structure**:
   ```html
   <article class="post" data-id="12345">
     <h2 class="title">
       <a href="/posts/123">My Article</a>
     </h2>
     <time datetime="2024-01-15T10:00:00Z">Jan 15</time>
     <span class="author">
       <a href="/users/john">John Doe</a>
     </span>
   </article>
   ```

5. **Identify patterns**:
   - Item container: `article.post`
   - Title: `h2.title a`
   - URL: `h2.title a::attr(href)`
   - Date: `time::attr(datetime)`
   - Author: `span.author a`
   - ID: `::attr(data-id)`

## Troubleshooting

### "No repeated patterns found"

The HTML structure might be too dynamic (JavaScript-rendered). Try:
1. View the page source (Ctrl+U)
2. If you see `<div id="root"></div>` with no content, the site uses JavaScript rendering
3. ScrapeSuite currently only supports static HTML (server-rendered pages)

### "Extraction shows empty values"

The selector might be wrong. Check:
1. Are you using `::attr()` for attributes?
2. Is the selector too specific? Try removing class names
3. Use browser DevTools to test selectors:
   ```javascript
   // In browser console
   document.querySelectorAll('.athing')  // Should show items
   ```

### "Getting wrong data"

The pattern might be too generic. Try:
1. Use a more specific selector (e.g., `.article.main` instead of `.article`)
2. Check if items have unique class names
3. Manually inspect the HTML to find better patterns

### "Rate limited / Blocked"

The site might be blocking automated access:
1. Check `robots.txt`: `https://example.com/robots.txt`
2. Reduce rate limit to 0.1-0.5 RPS
3. Add delays between runs
4. Some sites prohibit scraping - respect their policies

## Real-World Examples

### Example 1: Product Hunt

```yaml
selectors:
  item: "div[data-test='post-item']"
  fields:
    title: "h3"
    url: "a::attr(href)"
    votes: "button[data-test='vote-button']"
    tagline: "p[data-test='tagline']"
```

### Example 2: GitHub Trending

```yaml
selectors:
  item: "article.Box-row"
  fields:
    title: "h2 a"
    url: "h2 a::attr(href)"
    description: "p.col-9"
    stars: "span.d-inline-block.float-sm-right"
    language: "span[itemprop='programmingLanguage']"
```

### Example 3: Reddit (old.reddit.com)

```yaml
selectors:
  item: "div.thing"
  fields:
    title: "p.title a.title"
    url: "p.title a.title::attr(href)"
    score: "div.score.unvoted::attr(title)"
    author: "a.author"
    subreddit: "a.subreddit"
    comments: "a.comments"
    id: "::attr(data-fullname)"
```

## Next Steps

1. **Run the wizard**: `python -m scrapesuite.wizard`
2. **Test your config**: Start with `max_items=5` to verify extraction
3. **Scale up**: Once verified, increase to 100-1000 items
4. **Schedule jobs**: Use cron/systemd to run jobs periodically
5. **Analyze data**: Open the CSV/Parquet files in pandas, Excel, or BI tools

## Limitations

- **JavaScript-rendered sites**: ScrapeSuite only parses server-rendered HTML. Sites using React/Vue/Angular that render client-side won't work without additional tools.
- **Authentication**: No login/session support yet
- **Pagination**: Currently fetches single pages. For multi-page scraping, manually adjust the entry URL or implement pagination logic.
- **Rate limits**: Respect site policies. ScrapeSuite enforces `robots.txt` but you must configure appropriate delays.

## Getting Help

- Check `TROUBLESHOOTING.md` for common issues
- Review `ARCHITECTURE_LIMITATIONS.md` for technical details
- Inspect generated YAML configs in `jobs/` directory
- Use `scrapesuite inspect <job>` to validate configs
