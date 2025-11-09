# Bot Evasion & Legitimate Scraping Techniques

ScrapeSuite implements several **legitimate** techniques to avoid being flagged as a bot while remaining respectful and compliant with website policies.

## Why This Matters

Modern websites use bot detection services (Akamai, Cloudflare, PerimeterX, etc.) to block automated traffic. However, **ethical scrapers with proper rate limiting should not be blocked**. The techniques below help distinguish legitimate scraping from abusive bot behavior.

## Implemented Techniques

### 1. **Realistic Browser Headers** ✅

**Problem**: Generic or missing headers flag requests as non-browser traffic.

**Solution**: ScrapeSuite sends complete, realistic browser headers that vary naturally:

```python
from scrapesuite.http import get_html

# Automatically uses realistic headers with variation
html = get_html("https://example.com/page")
```

**What we do**:
- Rotate User-Agents from real browser pool (Chrome, Firefox, Safari, Edge)
- Include browser-specific headers (Sec-Ch-Ua for Chrome, etc.)
- Vary Accept-Language, Accept-Encoding realistically
- Add optional Cache-Control headers (like user hitting refresh)

### 2. **Respect robots.txt** ✅

**Problem**: Ignoring robots.txt signals malicious intent.

**Solution**: Check robots.txt before every request (enabled by default):

```python
# Respects robots.txt (default)
html = get_html("https://example.com/page")

# Skip for testing (not recommended for production)
html = get_html("https://example.com/page", respect_robots=False)
```

**What we do**:
- Cache robots.txt per domain (efficient)
- Raise `PermissionError` if URL is disallowed
- Fall back to "allow" if robots.txt fetch fails (permissive)

### 3. **Referrer Simulation** ✅

**Problem**: Missing referrers look suspicious (browsers always send them).

**Solution**: Simulate natural browsing patterns:

```python
# Automatically adds referrers:
# - 30% from search engines (Google, Bing)
# - 70% direct/none (natural mix)
html = get_html("https://example.com/article")
```

**Custom referrer**:
```python
from scrapesuite.http import _build_browser_headers

headers = _build_browser_headers(
    "https://example.com/page2",
    referrer="https://example.com/page1"
)
```

### 4. **Session Persistence** ✅

**Problem**: Each request from new session looks like different users/bots.

**Solution**: Reuse sessions to maintain cookies and TCP connections:

```python
from scrapesuite.http import create_session, get_html

# Create persistent session
session = create_session()

# All requests share cookies, connection pool
page1 = get_html("https://example.com/page1", session=session)
page2 = get_html("https://example.com/page2", session=session)
page3 = get_html("https://example.com/page3", session=session)
```

**Benefits**:
- Cookies persist (login state, preferences, anti-bot tokens)
- Connection reuse (faster, more natural)
- Session state accumulates (like real browser)

### 5. **Natural Timing Variance** ✅

**Problem**: Perfectly timed requests at exact intervals look robotic.

**Solution**: Add random micro-delays and jitter:

```python
# Built into get_html():
# - 70% of requests: 0-200ms random delay
# - Retry backoff: 0.5s → 1s → 2s with 0-30% jitter
# - Rate limit errors: 3x longer wait + honor Retry-After
html = get_html("https://example.com/page")
```

**What we do**:
- Micro-delays before request (0-200ms, 70% of time)
- Exponential backoff with jitter on retries
- Respect `Retry-After` header from servers
- Triple wait time for 429/503 errors

### 6. **Per-Domain Rate Limiting** ✅

**Already implemented** in earlier phases:

```python
from scrapesuite.ratelimit import DomainRateLimiter

# Default: 1 request/second per domain
limiter = DomainRateLimiter(default_rps=1.0)

# Custom rates for specific domains
limiter.set_domain_rps("news.ycombinator.com", 0.5)  # Slower
limiter.set_domain_rps("example.com", 2.0)  # Faster
```

## Best Practices

### ✅ DO:
1. **Use reasonable rate limits** (1-2 req/sec max, lower for fragile sites)
2. **Respect robots.txt** (shows good faith)
3. **Identify yourself** in User-Agent if scraping at scale:
   ```python
   html = get_html(url, ua="MyBot/1.0 (+https://mysite.com/bot-info)")
   ```
4. **Use persistent sessions** for multi-page scraping
5. **Cache aggressively** (avoid re-fetching same pages)
6. **Honor rate limit signals** (429, 503, Retry-After header)
7. **Provide contact info** in User-Agent for site owners to reach you

### ❌ DON'T:
1. **Don't scrape faster than 2-3 req/sec** per domain
2. **Don't ignore robots.txt** in production
3. **Don't rotate IPs to bypass blocks** (looks like DDoS)
4. **Don't scrape user-gated content** without permission
5. **Don't ignore 403/429 errors** (respect the signal)
6. **Don't use datacenter IPs** if residential proxies are needed
7. **Don't lie about your identity** (fake Google bot, etc.)

## Handling Blocks

If you get blocked despite following best practices:

### 1. **Check robots.txt First**
```bash
curl https://example.com/robots.txt
```
Look for `Disallow` rules that apply to your scraper.

### 2. **Slow Down Rate Limit**
```python
# Reduce from 1.0 to 0.5 req/sec
limiter.set_domain_rps("example.com", 0.5)
```

### 3. **Use Session Persistence**
```python
session = create_session()
# Reuse session for all requests to this domain
```

### 4. **Add Contact Info to User-Agent**
```python
html = get_html(
    url,
    ua="MyResearchBot/1.0 (+https://example.edu/research; contact@example.edu)"
)
```

### 5. **Check for Terms of Service**
Some sites explicitly allow/disallow scraping in their ToS. Respect their wishes.

### 6. **Contact Site Owners**
If you need legitimate access, reach out! Many sites offer:
- **API access** (preferred method)
- **Data exports** (easier than scraping)
- **Whitelisting** for researchers/non-commercial use

## Advanced: What We DON'T Handle

ScrapeSuite focuses on **static HTML scraping**. We do NOT handle:

❌ **JavaScript-rendered content** (use Playwright/Selenium if needed)  
❌ **CAPTCHA solving** (indicates site doesn't want scraping)  
❌ **IP rotation / proxies** (indicates you're being blocked for a reason)  
❌ **TLS fingerprinting evasion** (advanced, requires curl_cffi/tls-client)  
❌ **Canvas fingerprinting** (requires headless browser)  
❌ **Session replay detection** (requires real browser)

If you need these, consider:
1. **Official API** (always best option)
2. **Playwright** with stealth plugins
3. **Commercial scraping services** (ScrapingBee, Apify, etc.)

## Detection Service Specific Tips

### Cloudflare
- **Signals**: `cf-ray` header, `__cf_bm` cookie, 403 with "Attention Required"
- **Solution**: Slower rate limit (0.5 req/sec), session persistence, don't use datacenter IPs

### Akamai
- **Signals**: `Server: AkamaiGHost`, 403 with reference number
- **Solution**: Realistic headers (Sec-Ch-Ua critical), session persistence, honor robots.txt

### PerimeterX
- **Signals**: `_px` cookies, JavaScript challenges
- **Solution**: Often requires browser automation (Playwright), not solvable with requests

## Summary

ScrapeSuite's bot evasion is **ethical and transparent**:
- ✅ We mimic real browsers (not deceive)
- ✅ We respect rate limits (not circumvent)
- ✅ We follow robots.txt (not ignore)
- ✅ We identify ourselves (not lie)

If you're still getting blocked, it likely means:
1. Your rate limit is too aggressive
2. The site explicitly doesn't want scraping
3. You need to use their API instead

**When in doubt: slow down, identify yourself, and contact the site owner.**
