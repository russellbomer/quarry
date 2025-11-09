# Blind Test Guide - Interactive Wizard

Follow these steps to test the interactive wizard from scratch. No prior knowledge needed!

## Pre-Test Checklist

```bash
# 1. Verify you're in the right directory
pwd
# Should show: /workspaces/scrapesuite

# 2. Verify all tests pass
python -m pytest -q
# Should show: 32 passed

# 3. Verify no lint errors on critical files
python -m ruff check scrapesuite/wizard.py scrapesuite/inspector.py scrapesuite/connectors/generic.py
# Should show: All checks passed! (or just warnings, not errors)
```

## Test 1: Simple Website (Hacker News)

**Goal**: Create a scraper for Hacker News stories in 5 minutes.

### Step 1: Start the wizard

```bash
python -m scrapesuite.wizard
```

**Expected**: You see a welcome banner and template selection.

### Step 2: Select "custom" template

```
Select template
> custom          ← SELECT THIS (use arrow keys + Enter)
  fda_example
  nws_example
```

**Why**: "custom" enables the HTML analyzer for any website.

### Step 3: Enter job name

```
Job name (slug) [my_job]: hackernews_stories
```

**Type**: `hackernews_stories` and press Enter

### Step 4: Enter URL

```
Entry URL (listing page, not a single item) [https://example.com/]: 
```

**Type**: `https://news.ycombinator.com/` and press Enter

**Important**: This is the LISTING page (shows multiple stories), not a single story URL.

### Step 5: Analyze HTML

```
Analyze HTML structure and build selectors? (Y/n):
```

**Type**: `Y` or just press Enter

**Expected**: 
- You see "Analyzing HTML structure..."
- You see "✓ Page: Hacker News"
- You see a table of detected patterns

### Step 6: Review detected patterns

**Expected output**:
```
Detected Item Patterns:
┏━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Option ┃ Selector   ┃ Count ┃ Sample Title             ┃
┡━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1      │ .athing    │ 30    │ Some article title       │
│ 2      │ .title     │ 61    │                          │
│ 3      │ .rank      │ 30    │                          │
└────────┴────────────┴───────┴──────────────────────────┘
```

**What to look for**:
- Option 1 (`.athing`) shows article titles in the "Sample Title" column
- It has 30 items (reasonable number for a page of stories)
- Other options either show no title or wrong counts

### Step 7: Select the best pattern

```
Select item pattern
> .athing (30 items)    ← SELECT THIS
  .title (61 items)
  .rank (30 items)
  Skip (use manual config)
```

**Choose**: `.athing` (option 1) because it has sample titles

### Step 8: Field selection - Title

```
Include 'title'? (preview: Ironclad – formally verified...) (Y/n):
```

**Type**: `Y` or just press Enter

```
Selector for 'title' [span.titleline a]:
```

**Type**: Just press Enter to accept the suggestion

**What happened**: Wizard detected the title is in `span.titleline a` and showed you a preview.

### Step 9: Field selection - URL

```
Include 'url'? (preview: https://ironclad-os.org/) (Y/n):
```

**Type**: `Y` or just press Enter

```
Selector for 'url' [span.titleline a::attr(href)]:
```

**Type**: Just press Enter

**Note**: `::attr(href)` means "extract the href attribute from the link"

### Step 10: Field selection - Other fields

The wizard might ask about date, author, score, image.

**For Hacker News**:
- Date: Not visible in listing, type `N`
- Author: Not visible in listing, type `N`  
- Score: Might be detected, type `Y` if you want it
- Image: Not visible, type `N`

**Don't worry**: You only need title and URL for a basic scraper!

### Step 11: Preview extraction

**Expected**:
```
Preview of extracted data:
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ title                    ┃ url                      ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Ironclad OS              │ https://ironclad-os.org/ │
│ Tabloid Language         │ https://tabloid.vercel…  │
│ Marko Framework          │ https://markojs.com/     │
└──────────────────────────┴──────────────────────────┘
```

**Check**:
- Do the titles look correct? (Real article titles, not navigation)
- Do the URLs look correct? (Point to actual articles, not `#` or `/new`)

### Step 12: Confirm extraction

```
Does this look correct? (Y/n):
```

**If YES**: Type `Y` or press Enter  
**If NO**: Type `N`, wizard will skip selectors and you can try again

### Step 13: Configure allowlist

```
Allowlist domains (comma-separated) [news.ycombinator.com]:
```

**Type**: Just press Enter (accepts the auto-detected domain)

**What this does**: Only allows fetching from news.ycombinator.com (safety feature)

### Step 14: Set rate limit

```
Rate limit (RPS) [1.0]:
```

**Type**: Just press Enter (1 request per second is polite)

**What this does**: Don't hammer the server with requests

### Step 15: Set cursor field

```
Cursor field [url]:
```

**Type**: Just press Enter

**What this does**: Tracks which items you've seen before to avoid duplicates

### Step 16: Choose output format

```
Sink kind
  parquet
> csv          ← SELECT CSV (easier to open)
```

**Choose**: `csv` (you can open this in Excel/Google Sheets)

### Step 17: Set output path

```
Sink path template [data/cache/%Y%m%dT%H%M%SZ.csv]:
```

**Type**: `data/cache/hn/%Y%m%dT%H%M%SZ.csv` and press Enter

**What this does**: Saves files like `data/cache/hn/20241109T143000Z.csv`

### Step 18: Set test limit

```
Max items (for smoke test) [100]:
```

**Type**: `5` and press Enter

**What this does**: Only fetch 5 items for testing (faster)

### Step 19: Run smoke test

```
Run offline smoke test? (Y/n):
```

**Type**: `N` (we want to test REAL fetching, not cached data)

**Expected**:
```
SUCCESS: Job spec written to jobs/hackernews_stories.yml
```

### Step 20: Verify the config was created

```bash
ls jobs/hackernews_stories.yml
cat jobs/hackernews_stories.yml
```

**Expected**: File exists and contains:
```yaml
version: "1"
job: hackernews_stories
source:
  kind: html
  entry: https://news.ycombinator.com/
  parser: generic
  ...
selectors:
  item: ".athing"
  fields:
    title: "span.titleline a"
    url: "span.titleline a::attr(href)"
```

### Step 21: Test the scraper FOR REAL

```bash
python -c "
from scrapesuite.core import load_yaml, run_job
spec = load_yaml('jobs/hackernews_stories.yml')
df, cursor = run_job(spec, max_items=5, offline=False)
print(f'\n✓ Collected {len(df)} items\n')
print(df[['title', 'url']].to_string())
"
```

**Expected output**:
```
✓ Collected 5 items

                                   title                              url
0  Ironclad – formally verified OS  https://ironclad-os.org/
1  Tabloid: The Clickbait Language  https://tabloid.vercel.app/
2  Marko – HTML‑based framework     https://markojs.com/
3  Some other article              https://example.com/article
4  Another story                   https://news.example.com/story
```

**Success criteria**:
- ✓ You got 5 items (or fewer if HN has fewer stories)
- ✓ Titles are real article titles (not "1.", "2.", "Hacker News")
- ✓ URLs are real article URLs (not vote links, not empty)

---

## Test 2: Different Website (Product Hunt)

**Goal**: Prove the wizard works on a DIFFERENT site.

### Quick Test

```bash
python -m scrapesuite.wizard
```

**Settings**:
1. Template: `custom`
2. Job name: `producthunt_test`
3. URL: `https://www.producthunt.com/` 
4. Analyze HTML: `Y`
5. Select pattern: Look for one with product names in "Sample Title"
6. Include fields: title, url (say No to others for speed)
7. Confirm preview: `Y` if it looks right
8. Rate limit: `0.5` (be extra polite to PH)
9. Output: `csv`
10. Path: `data/cache/ph/%Y%m%dT%H%M%SZ.csv`
11. Max items: `3`
12. Smoke test: `N`

**Then test**:
```bash
python -c "
from scrapesuite.core import load_yaml, run_job
spec = load_yaml('jobs/producthunt_test.yml')
df, cursor = run_job(spec, max_items=3, offline=False)
print(f'\n✓ Collected {len(df)} items\n')
print(df[['title', 'url']].to_string())
"
```

**Expected**: 3 product names with URLs

---

## Test 3: Robots.txt Check

**Goal**: Verify robots.txt checking works.

### Test on a site that BLOCKS scraping

```bash
python -c "
from scrapesuite.policy import check_robots
url = 'https://www.reddit.com/'
allowed = check_robots(url)
print(f'Reddit scraping allowed: {allowed}')
"
```

**Expected**: `False` (Reddit blocks scrapers)

### Test on a site that ALLOWS scraping

```bash
python -c "
from scrapesuite.policy import check_robots
url = 'https://github.com/'
allowed = check_robots(url)
print(f'GitHub scraping allowed: {allowed}')
"
```

**Expected**: `True` (GitHub allows with crawl-delay)

---

## Test 4: Error Handling

**Goal**: Verify wizard handles bad input gracefully.

### Test 1: Bad URL

```bash
python -m scrapesuite.wizard
```

**Enter**:
- Template: `custom`
- Job name: `error_test`
- URL: `not-a-valid-url`
- Analyze: `Y`

**Expected**: Error message about invalid URL, wizard stops gracefully

### Test 2: No patterns found

Some sites with heavy JavaScript won't work:

```bash
python -m scrapesuite.wizard
```

**Enter**:
- Template: `custom`
- URL: `https://twitter.com/` (might not work - JS-heavy)
- Analyze: `Y`

**Expected**: "No repeated patterns found. Using simple link extraction." message

---

## Test 5: Existing Tests

**Goal**: Ensure nothing broke.

```bash
# Run all 32 tests
python -m pytest -v

# Should see:
# tests/test_generic_connector.py::test_generic_connector_basic PASSED
# tests/test_generic_connector.py::test_generic_connector_attribute_extraction PASSED
# tests/test_generic_connector.py::test_generic_connector_missing_selectors PASSED
# ... (29 more tests)
# ======================== 32 passed ========================
```

---

## Troubleshooting Guide

### Problem: "ImportError: cannot import name..."

**Fix**:
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Problem: "No module named scrapesuite"

**Fix**:
```bash
# Make sure you're in the right directory
cd /workspaces/scrapesuite
pwd  # Should show /workspaces/scrapesuite
```

### Problem: Wizard extracts wrong data

**Check**:
1. Did you choose the right pattern? (Look at "Sample Title" column)
2. Is the preview correct? (If not, say "N" and try different pattern)
3. Is the site JavaScript-heavy? (View source - if you see mostly `<div id="root">`, it won't work)

### Problem: "Offline mode not supported"

**This is expected** - GenericConnector requires live fetching. Just use `offline=False`:

```python
df, cursor = run_job(spec, max_items=5, offline=False)
```

### Problem: Empty results (0 items)

**Debug**:
```bash
# Check if the site blocks you
python -c "
from scrapesuite.policy import check_robots
print(check_robots('https://YOURSITE.com/'))
"

# Try fetching manually
python -c "
from scrapesuite.http import get_html
html = get_html('https://YOURSITE.com/')
print(f'Fetched {len(html)} bytes')
print(html[:500])  # First 500 chars
"
```

---

## Success Criteria Summary

After running all tests, you should have:

✅ **Test 1**: `jobs/hackernews_stories.yml` that successfully extracts 5 HN stories  
✅ **Test 2**: `jobs/producthunt_test.yml` that successfully extracts 3 products  
✅ **Test 3**: robots.txt checks return correct True/False  
✅ **Test 4**: Wizard handles errors without crashing  
✅ **Test 5**: All 32 tests passing  

**If all 5 pass**: The wizard is production-ready! 🎉

---

## Next Steps After Testing

1. **Read `WIZARD_USAGE.md`** for detailed docs
2. **Try more sites**: Medium, GitHub trending, dev.to
3. **Check `TROUBLESHOOTING.md`** for diagnostic commands
4. **Share your configs**: Save working YAMLs in `jobs/` for reuse

---

## Quick Reference Card

```bash
# Start wizard
python -m scrapesuite.wizard

# Test a job
python -c "from scrapesuite.core import load_yaml, run_job; spec = load_yaml('jobs/JOBNAME.yml'); df, _ = run_job(spec, max_items=5, offline=False); print(df)"

# Check robots.txt
python -c "from scrapesuite.policy import check_robots; print(check_robots('https://example.com/'))"

# Run all tests
python -m pytest -q

# Validate a job config
cat jobs/JOBNAME.yml
```

---

**YOU GOT THIS!** 💪 Follow the steps, read the output, and the wizard will guide you.
