# Finding API Endpoints for Infinite Scroll Sites

Many modern websites use infinite scroll to load content dynamically via JavaScript. Instead of adding complex browser automation to Quarry, you can often find and scrape the underlying API endpoints directly.

## Why This Approach?

- **Faster**: Direct API calls vs. rendering full pages
- **Cleaner data**: JSON responses are easier to parse than HTML
- **More reliable**: No need to handle JavaScript execution
- **Lower resource usage**: No browser overhead
- **Stays within Quarry's design**: Lightweight HTTP + parsing

## Step-by-Step Guide

### 1. Open Browser DevTools

**Chrome/Edge/Brave:**
- Press `F12` or `Ctrl+Shift+I` (Windows/Linux)
- Press `Cmd+Option+I` (Mac)

**Firefox:**
- Press `F12` or `Ctrl+Shift+K` (Windows/Linux)
- Press `Cmd+Option+K` (Mac)

### 2. Go to Network Tab

1. Click the **Network** tab in DevTools
2. Make sure **Preserve log** is checked (prevents clearing on navigation)
3. Filter by **Fetch/XHR** (shows only API calls, not images/CSS/etc.)

### 3. Trigger the Infinite Scroll

1. Clear the network log (trash can icon)
2. Scroll down the page to trigger new content loading
3. Watch for new network requests to appear

### 4. Identify the API Endpoint

Look for requests that:
- Return **JSON** data (check Response tab)
- Contain article/item data matching what you see on the page
- Have URLs with patterns like:
  - `/api/...`
  - `/graphql`
  - `/feed`
  - `/load-more`
  - Query parameters: `?page=2`, `?offset=20`, `?limit=10`

**Example patterns:**
```
GET https://www.nytimes.com/svc/collections/v1/publish/https://www.nytimes.com/section/us?limit=10&offset=20
GET https://example.com/api/articles?page=2&per_page=20
POST https://example.com/graphql (with query in body)
GET https://site.com/wp-json/wp/v2/posts?offset=10
```

### 5. Inspect the Request

Click on the API request and examine:

**Headers tab:**
- **Request URL**: The endpoint you'll scrape
- **Request Method**: Usually GET, sometimes POST
- **Query String Parameters**: Pagination params (page, offset, limit)
- **Request Headers**: Any special headers needed (API keys, tokens, etc.)

**Payload tab** (for POST requests):
- GraphQL queries
- Filter parameters
- Search criteria

**Response tab:**
- Verify it returns the data you need
- Check the JSON structure

### 6. Test the Endpoint

Copy the request as cURL:
1. Right-click the request
2. Select **Copy** → **Copy as cURL**
3. Paste in terminal to test

Or reconstruct manually:
```bash
curl 'https://example.com/api/articles?page=1&limit=20' \
  -H 'User-Agent: Mozilla/5.0...'
```

### 7. Identify Pagination Pattern

Common patterns:

**Offset-based:**
```
?offset=0&limit=20
?offset=20&limit=20
?offset=40&limit=20
```

**Page-based:**
```
?page=1&per_page=20
?page=2&per_page=20
```

**Cursor-based:**
```
?cursor=eyJpZCI6MTIzfQ==
?cursor=eyJpZCI6MTQ1fQ==
```

**Token in response:**
```json
{
  "items": [...],
  "next_page_token": "abc123"
}
```

## Common Website Patterns

### News Sites (NYTimes, Guardian, etc.)

**Typical endpoint:**
```
GET /svc/collections/v1/publish/{section}?offset=0&limit=10
```

**Look for:**
- `svc/` or `api/` in URL
- `offset` and `limit` parameters
- JSON response with article array

### WordPress Sites

**Typical endpoint:**
```
GET /wp-json/wp/v2/posts?page=1&per_page=10
```

**Look for:**
- `/wp-json/` in URL
- Standard REST API format
- `page` parameter

### E-commerce (Product listings)

**Typical endpoint:**
```
GET /api/products?page=1&sort=newest&filters[category]=electronics
```

**Look for:**
- `/api/products` or similar
- Filter and sort parameters
- Product data in JSON

### GraphQL Sites

**Typical endpoint:**
```
POST /graphql
```

**Payload example:**
```json
{
  "query": "query { articles(limit: 10, offset: 0) { title url author } }"
}
```

**Look for:**
- Single `/graphql` endpoint
- POST method
- Query in request body

### Social Media Feeds

**Typical endpoint:**
```
GET /api/feed?cursor=abc123&count=20
```

**Look for:**
- Cursor-based pagination
- `count` or `limit` parameter
- May require authentication

## Creating a Quarry Schema for API Data

### For JSON APIs (Most Common)

Instead of HTML selectors, you can:

1. **Fetch the API directly** with Python:
   ```python
   import requests
   import json
   
   url = "https://example.com/api/articles?page=1&limit=20"
   response = requests.get(url, headers={"User-Agent": "..."})
   data = response.json()
   
   # Extract items from JSON structure
   for item in data["results"]:
       print(item["title"], item["url"])
   ```

2. **Build pagination loop**:
   ```python
   for page in range(1, 6):  # Pages 1-5
       url = f"https://example.com/api/articles?page={page}&limit=20"
       # ... fetch and process
   ```

### For APIs Returning HTML Fragments

Some APIs return HTML snippets instead of JSON:
```json
{
  "html": "<article>...</article><article>...</article>",
  "has_more": true
}
```

You can still use Quarry:
1. Extract the HTML from the JSON response
2. Parse with BeautifulSoup as normal
3. Loop through pages by incrementing offset/page

## Troubleshooting

### API Returns 403/401 Errors

**Problem:** Missing authentication or anti-bot headers

**Solutions:**
- Copy **all** headers from browser request
- Include `User-Agent`, `Referer`, `Cookie` headers
- Check if site requires login (use browser's auth token)

### API Returns Different Data Than Website

**Problem:** Response doesn't match what you see on page

**Solutions:**
- Check if you copied the right request (some sites make multiple calls)
- Verify query parameters match
- Look for additional filter/sort parameters

### Can't Find the API Request

**Problem:** No obvious API calls in Network tab

**Solutions:**
- Try filtering by different types (Fetch/XHR, JS, All)
- Check the **Initiator** column to find what triggered the request
- Look for WebSocket connections (real-time updates)
- Some sites embed data in `<script>` tags instead of separate API calls

### Pagination Token Not Obvious

**Problem:** Can't figure out next page URL

**Solutions:**
- Look for `next`, `next_page`, `cursor` fields in response
- Check response headers for `Link` header (RFC 5988)
- Some use base64-encoded cursors (decode to see structure)

## Authentication & Legal Considerations

### Public APIs
- No authentication required
- Usually documented (check `/api/docs` or similar)
- Safer legally (intended for public use)

### Private/Undocumented APIs
- May require authentication tokens
- Terms of Service may prohibit scraping
- Could break without notice (not a stable interface)
- **Always check robots.txt and Terms of Service**

### Best Practices
1. **Respect rate limits** - Add delays between requests
2. **Use caching** - Don't re-fetch data unnecessarily  
3. **Identify yourself** - Use descriptive User-Agent
4. **Read ToS** - Ensure scraping is permitted
5. **Be gentle** - Don't overload servers

## Example: NYTimes Section Page

### Finding the Endpoint

1. Visit https://www.nytimes.com/section/us
2. Open DevTools → Network tab
3. Scroll down to trigger loading
4. Look for request like:
   ```
   GET https://www.nytimes.com/svc/collections/v1/publish/...
   ```

### Analyzing the Response

```json
{
  "results": [
    {
      "title": "Article Title",
      "url": "https://www.nytimes.com/...",
      "byline": "By Author Name",
      "published_date": "2025-11-13",
      "summary": "Article summary..."
    }
  ],
  "next": "?offset=20"
}
```

### Scraping It

```python
import requests

base_url = "https://www.nytimes.com/svc/collections/v1/publish/..."
offset = 0
limit = 10

while offset < 100:  # Scrape first 100 items
    url = f"{base_url}?offset={offset}&limit={limit}"
    
    response = requests.get(url, headers={
        "User-Agent": "Mozilla/5.0 ..."
    })
    
    data = response.json()
    
    for article in data.get("results", []):
        print(f"{article['title']} - {article['url']}")
    
    # Check if there's more data
    if not data.get("results") or len(data["results"]) < limit:
        break
    
    offset += limit
    time.sleep(1)  # Be polite, wait 1 second between requests
```

## When to Use This vs. Traditional Scraping

### Use API Scraping When:
- ✅ Site uses infinite scroll with no "Load More" button
- ✅ API returns clean JSON data
- ✅ Pagination is simple (offset/page-based)
- ✅ You need to scrape many pages efficiently
- ✅ Site is JavaScript-heavy (React/Vue/Angular SPA)

### Use Traditional HTML Scraping When:
- ✅ All data is in initial HTML response
- ✅ Site has traditional pagination with page links
- ✅ API requires complex authentication
- ✅ API is heavily rate-limited
- ✅ You only need a few pages

## Tools to Help

### Browser Extensions
- **JSON Formatter** - Pretty-print JSON responses in browser
- **JSONView** - Make JSON responses readable
- **EditThisCookie** - Copy cookies for authentication

### Command Line Tools
- `curl` - Test API requests
- `jq` - Parse and filter JSON responses
- `httpie` - User-friendly HTTP client

### Python Libraries
- `requests` - Make HTTP requests
- `httpx` - Async HTTP client
- `scrapy` - Full-featured scraping framework (heavier alternative)

## Summary

For infinite scroll sites:

1. **Don't automate the browser** - Too complex, slow, and fragile
2. **Find the API endpoint** - Use browser DevTools Network tab
3. **Scrape the API directly** - Usually returns cleaner JSON data
4. **Build pagination logic** - Increment offset/page/cursor parameters
5. **Stay within ToS** - Respect rate limits and robots.txt

This approach keeps your scraping:
- **Fast** (no browser overhead)
- **Reliable** (no JavaScript rendering)
- **Simple** (HTTP requests + JSON parsing)
- **Maintainable** (clean code, no Selenium complexity)

Most infinite scroll is just UX sugar on top of paginated APIs. Bypass the sugar and get the data directly.
