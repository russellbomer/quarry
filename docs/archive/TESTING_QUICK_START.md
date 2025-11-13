# Testing Quick Start

## Correct API Usage

### ✅ Correct: get_html(url)

```python
from quarry.http import get_html
from quarry.framework_profiles import detect_framework

# Fetch and detect
html = get_html('https://example.com')
framework = detect_framework(html)
print(f'Detected: {framework.name if framework else None}')
```

### ❌ Incorrect: get_html(url, offline=False)

```python
# This will raise TypeError!
html = get_html(url, offline=False)  # ❌ No 'offline' parameter
```

### get_html() Parameters

```python
def get_html(
    url: str,
    *,
    ua: str | None = None,           # Custom User-Agent
    timeout: int = 30,                # Request timeout (seconds)
    max_retries: int = 3,             # Max retry attempts
    respect_robots: bool = True,      # Check robots.txt
    session: requests.Session | None = None  # Reuse session
) -> str:
```

**Examples:**

```python
# Custom User-Agent
html = get_html(url, ua='MyBot/1.0')

# Longer timeout
html = get_html(url, timeout=60)

# Disable robots.txt (testing only!)
html = get_html(url, respect_robots=False)

# Reuse session for cookies
import requests
session = requests.Session()
html1 = get_html(url1, session=session)
html2 = get_html(url2, session=session)
```

---

## Quick Test Commands

### Test Framework Detection

```bash
# Single framework
python -c "
from quarry.http import get_html
from quarry.framework_profiles import detect_framework

html = get_html('https://www.allrecipes.com/recipe/10813/best-chocolate-chip-cookies/')
fw = detect_framework(html)
print(fw.name if fw else 'None')
"
```

### Test All Frameworks

```bash
# All frameworks with scores
python -c "
from quarry.http import get_html
from quarry.framework_profiles import detect_all_frameworks

html = get_html('https://techcrunch.com/')
for fw, score in detect_all_frameworks(html)[:5]:
    print(f'{fw.name}: {score}')
"
```

### Test Metadata Extraction

```bash
# Open Graph
python -c "
from quarry.http import get_html
from quarry.framework_profiles import OpenGraphProfile

html = get_html('https://medium.com/')
metadata = OpenGraphProfile.extract_metadata(html)
for k, v in list(metadata.items())[:5]:
    print(f'{k}: {v[:80]}')
"
```

### Test Schema.org

```bash
# Schema.org microdata
python -c "
from quarry.http import get_html
from quarry.framework_profiles import SchemaOrgProfile
from bs4 import BeautifulSoup

html = get_html('https://www.allrecipes.com/recipes/')
soup = BeautifulSoup(html, 'html.parser')

itemscope = len(soup.find_all(attrs={'itemscope': True}))
itemprop = len(soup.find_all(attrs={'itemprop': True}))

print(f'Microdata elements:')
print(f'  itemscope: {itemscope}')
print(f'  itemprop: {itemprop}')
"
```

---

## Performance Testing

```bash
# Run profiler
python scripts/profile_framework_detection.py
```

## Regression Testing

```bash
# Run all tests
python -m pytest -q

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/test_framework_profiles.py -v
```

---

## Common Issues

### Issue: TypeError: get_html() got an unexpected keyword argument 'offline'

**Solution:** Remove `offline=False` - this parameter doesn't exist.

```python
# ❌ Wrong
html = get_html(url, offline=False)

# ✅ Correct
html = get_html(url)
```

### Issue: Rate limiting / 429 errors

**Solution:** Add delays between requests

```bash
# In bash scripts
sleep 2

# In Python
import time
time.sleep(2)
```

### Issue: Robots.txt blocking

**Solution:** For testing only, disable robots.txt checks

```python
html = get_html(url, respect_robots=False)  # Testing only!
```

---

## CLI Commands (These ARE correct)

```bash
# Run wizard
python -m quarry wizard

# Run job
python -m quarry run job.yml

# Run with offline mode (uses fixtures)
python -m quarry run job.yml --offline

# Run tests
python -m pytest -q
```

The `--offline` flag is valid for **CLI commands** but not for the `get_html()` Python function.

---

## Full Test Example

```bash
# Complete test
cd /c/path/to/quarry

python -c "
from quarry.http import get_html
from quarry.framework_profiles import (
    detect_framework,
    detect_all_frameworks,
    SchemaOrgProfile,
    OpenGraphProfile,
    TwitterCardsProfile,
    WooCommerceProfile
)

url = 'https://www.allrecipes.com/recipe/10813/best-chocolate-chip-cookies/'
print(f'Testing: {url}')

# Fetch HTML
html = get_html(url)
print(f'✅ Fetched {len(html):,} bytes')

# Detect best framework
framework = detect_framework(html)
print(f'✅ Best match: {framework.name if framework else \"None\"}')

# Show all detections
all_fw = detect_all_frameworks(html)
print(f'\\nAll frameworks ({len(all_fw)} detected):')
for fw, score in all_fw[:5]:
    print(f'  {fw.name}: {score}')

# Extract metadata if OG detected
if any(fw.name == 'opengraph' for fw, _ in all_fw):
    og_meta = OpenGraphProfile.extract_metadata(html)
    print(f'\\nOpen Graph: {len(og_meta)} tags')
"
```

---

**Full testing guide:** See `docs/USER_TESTING_PLAN.md`
