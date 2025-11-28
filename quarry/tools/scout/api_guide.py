"""Interactive guide for finding API endpoints in infinite scroll sites."""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from quarry.lib.theme import COLORS, QUARRY_THEME

console = Console(theme=QUARRY_THEME)


API_GUIDE_TEXT = """
# Finding API Endpoints for Infinite Scroll Sites

Many modern websites use **infinite scroll** to load content dynamically. Instead of browser automation, you can find and scrape the underlying **API endpoints** directly.

## 🔍 Quick Steps

### 1. Open Browser DevTools
- **Chrome/Edge**: Press `F12` or `Ctrl+Shift+I`
- **Firefox**: Press `F12` or `Ctrl+Shift+K`

### 2. Go to Network Tab
- Click **Network** tab
- Check **Preserve log** (prevents clearing)
- Filter by **Fetch/XHR** (shows only API calls)

### 3. Trigger Infinite Scroll
- Clear the network log (🗑️ icon)
- Scroll down to load more content
- Watch for new requests

### 4. Find the API Endpoint
Look for requests that:
- Return **JSON** data (check Response tab)
- Contain article/item data
- Have URLs with patterns like:
  - `/api/...`
  - `/svc/...`
  - `/graphql`
  - `?page=2`, `?offset=20`

## 📋 Common Patterns

### News Sites (NYTimes, Guardian)
```
GET /svc/collections/v1/publish/section?offset=0&limit=10
```

### WordPress Sites
```
GET /wp-json/wp/v2/posts?page=1&per_page=10
```

### E-commerce
```
GET /api/products?page=1&filters[category]=electronics
```

### GraphQL
```
POST /graphql
Body: {"query": "{ articles(limit: 10, offset: 0) { ... } }"}
```

## 🔧 Pagination Patterns

**Offset-based:**
- `?offset=0&limit=20` → `?offset=20&limit=20`

**Page-based:**
- `?page=1&per_page=20` → `?page=2&per_page=20`

**Cursor-based:**
- `?cursor=abc123` (token in previous response)

## 🐍 Scraping the API

Once you find the endpoint:

```python
import requests

url = "https://example.com/api/articles"
offset = 0
limit = 20

while offset < 100:
    response = requests.get(
        f"{url}?offset={offset}&limit={limit}",
        headers={"User-Agent": "Mozilla/5.0..."}
    )
    data = response.json()
    
    for item in data.get("results", []):
        print(item["title"])
    
    if len(data["results"]) < limit:
        break
    
    offset += limit
    time.sleep(1)  # Be polite
```

## 💡 Benefits of API Scraping

✅ **Faster** - Direct data access  
✅ **Cleaner** - JSON instead of HTML parsing  
✅ **Reliable** - No JavaScript execution needed  
✅ **Lightweight** - No browser overhead  

## 📚 Full Documentation

For detailed guide with examples and troubleshooting:

```bash
cat docs/INFINITE_SCROLL_API_GUIDE.md
```

Or view online:
https://github.com/russellbomer/foundry/blob/main/docs/INFINITE_SCROLL_API_GUIDE.md

## ⚠️ Legal Considerations

- **Check robots.txt** - Respect site policies
- **Read Terms of Service** - Ensure scraping is permitted  
- **Use rate limiting** - Add delays between requests
- **Identify yourself** - Use descriptive User-Agent

---

**TIP:** Most infinite scroll is just UX sugar on top of paginated APIs.  
Find the API, scrape it directly, skip the browser automation complexity.
"""


def show_api_guide():
    """Display the interactive API finding guide."""
    console.print()
    console.print(
        Panel(
            f"[bold {COLORS['primary']}]Finding API Endpoints for Infinite Scroll Sites[/bold {COLORS['primary']}]",
            subtitle="A Quarry Guide",
            border_style=COLORS["primary"],
            expand=False,
        )
    )
    console.print()

    md = Markdown(API_GUIDE_TEXT)
    console.print(md)

    console.print()
    console.print(
        Panel(
            "💡 [bold]Pro Tip:[/bold] Open DevTools Network tab, scroll the page, "
            "and look for JSON responses in the XHR/Fetch filter.",
            border_style=COLORS["success"],
            expand=False,
        )
    )
    console.print()
