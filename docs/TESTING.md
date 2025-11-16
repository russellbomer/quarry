# Quarry Testing Guide

## Blind Testing: Wizard + Bot Evasion

This guide helps you test Quarry's wizard and bot evasion features on real websites.

---

## Quick Test (Wizard Only)

### 1. Run the Wizard
```bash
cd /workspaces/quarry
quarry init
```

### 2. Provide Your URL
When prompted for "Start URL", paste your test URL.

### 3. Follow the Wizard
The wizard will:
1. **Fetch the page** (with bot evasion enabled by default)
2. **Detect item selectors** (using all 6 strategies)
3. **Detect field selectors** (title, url, date, author, score, image)
4. **Preview results** (shows what data would be extracted)
5. **Generate job YAML** (saves to `jobs/` directory)

### 4. Check What Was Detected
```bash
# View the generated job file
cat jobs/your_job_name.yml

# Look for:
# - item_selector: Should be specific, not too generic
# - field selectors: Should target the right elements
# - confidence levels in comments
```

---

## Full Test (Wizard + Job Run)

### 1. Run Wizard (as above)
```bash
quarry init
```

### 2. Run the Generated Job
```bash
# Use the job name you created
quarry run jobs/your_job_name.yml
```

### 3. Check Output
```bash
# Default output location
ls -lh data/cache/custom/

# View the data (Parquet)
python -c "import pandas as pd; df = pd.read_parquet('data/cache/custom/LATEST.parquet'); print(df)"

# Or if CSV
cat data/cache/custom/LATEST.csv
```

---

## Testing Bot Evasion Features

### Check Robots.txt Compliance

**Test 1: Allowed URL**
```bash
# Should work
python -c "
from quarry.http import get_html
html = get_html('YOUR_URL_HERE', respect_robots=True)
print(f'Success! Fetched {len(html)} bytes')
"
```

**Test 2: Disallowed URL**
```bash
# Should raise PermissionError
python -c "
from quarry.http import get_html
try:
    html = get_html('YOUR_DISALLOWED_URL', respect_robots=True)
except PermissionError as e:
    print(f'✓ Correctly blocked: {e}')
"
```

**Test 3: Check robots.txt manually**
```bash
# See what's allowed/disallowed
curl YOUR_DOMAIN/robots.txt
```

### Check User-Agent Rotation

```bash
# Run multiple times, check for different UAs
python -c "
from quarry.http import _build_browser_headers
for i in range(5):
    headers = _build_browser_headers('https://example.com')
    print(f'{i+1}. {headers[\"User-Agent\"][:50]}...')
"
```

Expected output: Different browsers (Chrome, Firefox, Safari, Edge)

### Check Session Persistence

```bash
# Verify cookies are maintained
python -c "
from quarry.http import create_session, get_html

session = create_session()
print('Cookies before:', session.cookies)

# First request (may set cookies)
html1 = get_html('YOUR_URL', session=session)
print('Cookies after request 1:', session.cookies)

# Second request (should reuse cookies)
html2 = get_html('YOUR_URL', session=session)
print('Cookies after request 2:', session.cookies)
"
```

### Check Referrer Simulation

```bash
# Run multiple times to see variation
python -c "
from quarry.http import _build_browser_headers
for i in range(10):
    headers = _build_browser_headers('https://example.com')
    referer = headers.get('Referer', 'None')
    print(f'{i+1}. Referer: {referer}')
"
```

Expected: Mix of Google, Bing, and None

---

## Testing Specific Websites

### News Sites (e.g., Hacker News, Reddit)

**Good test because:**
- Well-structured HTML
- Clear item patterns (posts, comments)
- robots.txt allows scraping
- Rate limiting friendly

**Wizard should detect:**
- Item selector: `tr.athing` (HN) or `div.thing` (Reddit)
- Title: `span.titleline a` or similar
- URL: From title link
- Score: Vote count elements
- Date: Time elements

### Blog/Article Sites

**Good test because:**
- Semantic HTML (article tags)
- Data attributes common
- URL patterns (`/posts/`, `/articles/`)
- Various field types

**Wizard should detect:**
- Item selector: `article`, `div.post`, or URL pattern
- Title: `h1`, `h2`, or `[itemprop="headline"]`
- Date: `time[datetime]` or `[data-date]`
- Author: `[rel="author"]` or `.author`

### E-commerce Sites (Product Listings)

**Challenging because:**
- Heavy JavaScript (may not work without browser)
- Obfuscated classes (Tailwind, CSS modules)
- Bot protection (Cloudflare, Akamai)

**What to test:**
- Does wizard find products despite obfuscation?
- Does bot evasion avoid 403 blocks?
- Are fallback selectors generated?

---

## What to Look For

### ✅ Good Signs

**Wizard Detection:**
- Multiple selector candidates with confidence levels
- Specific selectors (classes, IDs) over generic ones
- Field selectors find the right content
- Preview shows actual data from the page

**Bot Evasion:**
- No 403/429 errors with reasonable rate limits
- Requests complete successfully
- Headers look realistic (use browser DevTools to compare)
- robots.txt is respected

**Generated Job:**
- YAML is valid and readable
- Selectors are not overly complex (< 5 levels deep)
- Pagination/cursor logic makes sense
- Allowlist includes the domain

### ⚠️ Warning Signs

**Wizard Issues:**
- Returns generic selectors (`div`, `span` without classes)
- Can't find title or URL
- Preview shows no data or wrong data
- Only 1 item detected (should be multiple)

**Bot Detection:**
- 403 Forbidden errors (Cloudflare/Akamai)
- 429 Too Many Requests (rate limit too high)
- Empty responses or challenge pages
- Captcha pages

**Job Run Issues:**
- No data extracted (selectors wrong)
- Duplicate items (cursor not working)
- Missing fields (selectors too specific)
- Crashes on certain pages

### ❌ Known Limitations (Expected Failures)

**Won't Work:**
- JavaScript-rendered content (React SPAs, etc.)
- Infinite scroll without pagination URLs
- Content behind login (unless session provided)
- Sites with aggressive bot protection (DataDome, PerimeterX)
- Canvas/WebGL fingerprinting detection

**May Struggle:**
- Very deep nesting (10+ levels)
- Completely obfuscated classes (no semantic markers)
- Split titles across many elements
- Custom shadow DOM components

---

## Reporting Issues

When testing reveals problems, note:

1. **URL tested**: (exact page)
2. **What failed**: (wizard detection, job run, bot block, etc.)
3. **Error message**: (full traceback if applicable)
4. **Expected behavior**: (what should have happened)
5. **HTML structure**: (brief description or snippet)
6. **Browsers tested**: (if comparing to manual browsing)

---

## Example Test Session

```bash
# 1. Start wizard
quarry init

# Provide URL when prompted:
# https://news.ycombinator.com

# Expected output:
# - Detects 30 items (front page posts)
# - Item selector: tr.athing or similar
# - Title: span.titleline a
# - URL: from href attribute
# - Score: span.score
# - Generates jobs/hackernews.yml

# 2. Run the job
quarry run jobs/hackernews.yml

# 3. Check output
python -c "
import pandas as pd
df = pd.read_parquet('data/cache/custom/LATEST.parquet')
print(df.head())
print(f'\nExtracted {len(df)} items')
"

# 4. Verify bot evasion
# - No 403 errors? ✓
# - No 429 errors? ✓
# - robots.txt respected? ✓
# - Data extracted? ✓
```

---

## Performance Benchmarks

**Target metrics:**
- **Detection success**: 60-70% of sites work out-of-box
- **With refinement**: 80-90% can be made to work
- **Rate limit**: 1 req/sec default (respectful)
- **Wizard time**: < 5 seconds for small pages
- **Job run time**: Depends on page count and rate limit

**When to tune:**
- Detection fails: Try manual selector refinement
- Bot blocked: Slow rate limit to 0.5 req/sec
- Too slow: Increase rate limit (carefully!)
- Wrong data: Inspect HTML, adjust selectors

---

## Ready to Test!

**Paste your URL below and I'll guide you through testing:**

URL: `_____________________`

Expected site type:
- [ ] News/forum (HN, Reddit)
- [ ] Blog/articles
- [ ] E-commerce/products
- [ ] Documentation/wiki
- [ ] Other: __________

I'll help interpret the results!
