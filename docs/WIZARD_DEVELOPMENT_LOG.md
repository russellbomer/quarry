# ScrapeSuite Wizard Development Log

## Session: November 9, 2025

### Project Goal
Build an interactive CLI wizard (`python -m scrapesuite.wizard`) that enables non-programmers to create web scrapers by:
1. Entering a URL
2. Automatically analyzing HTML structure
3. Suggesting CSS selectors for repeated items
4. Previewing extraction results
5. Generating working YAML job configs
6. Running smoke tests

### What We Accomplished Today

#### 1. **Enhanced Field Selector Generation** (Commit: 5e323b8)
**Problem**: Wizard was generating `fields: {}` because it found empty vote buttons instead of actual title links on sites like Hacker News.

**Solution**: Replaced simple "first link" logic with intelligent scoring system:
- Scores links by text length, semantic attributes (`rel="bookmark"`, `itemprop="name"`), and UI patterns
- Penalizes navigation/action links (vote, reply, share, flag buttons)
- Handles non-English text and emoji titles
- Uses parent class context for more specific selectors (`.titleline a` instead of generic `a`)

**Improvements to date/author/score fields**:
- Added regex pattern matching (language-agnostic)
- Supports semantic HTML5 (`<time>`, `itemprop`, `rel` attributes)
- Works across languages by detecting patterns, not just English keywords

**Test Results**:
```
HN (vote buttons)    -> .titleline a          ✓ Skips vote buttons
Breadcrumb nav       -> h2                    ✓ Prefers semantic headings
Chinese text         -> .item a               ✓ Supports unicode
Emoji title          -> .entry a              ✓ Handles emoji
ISO date             -> .meta                 ✓ Detects 2024-11-09
Relative time        -> small                 ✓ Detects "2 hours ago"
```

#### 2. **Bot Detection & Error Handling** (Commit: cda2187)
**Problem**: User tried MTA website and got `403 Forbidden` with no helpful context.

**Solution**: 
- Added realistic browser headers (Chrome UA, Accept headers, Sec-Fetch-* headers)
- Detect bot protection services (Akamai, Cloudflare) from Server headers
- Provide actionable guidance when sites block requests:
  ```
  💡 This website is blocking automated requests. Options:
    1. Try accessing the page in a browser first
    2. Use browser developer tools to inspect HTML manually
    3. Check if the site has an API available
    4. Contact the site owner for permission
  ```
- Wizard continues gracefully even if HTML analysis fails (allows manual selector entry)
- Added helpful messages for 404, timeout, and other common errors

### Current State

**What Works**:
✅ Wizard executes: `python -m scrapesuite.wizard`
✅ Interactive prompts with helpful explanatory text
✅ HTML analysis and selector generation for most sites
✅ Handles tricky structures (vote buttons, breadcrumbs, unicode, emoji)
✅ CSV/Parquet sink auto-detection and path generation
✅ Live smoke tests for GenericConnector
✅ Hardcoded sensible rate limit (1.0 RPS)
✅ Graceful degradation when sites block requests
✅ All 32 tests passing

**Known Limitations**:
⚠️ Bot protection: Sites using Akamai, Cloudflare, etc. block automated requests (MTA, some gov sites)
⚠️ Selector detection: May not find correct items on all sites (FDA real site vs fixture difference)
⚠️ JavaScript-rendered content: Requires headless browser (not yet implemented)
⚠️ Complex/unusual markup: May need manual selector refinement

### Open Issues / Next Steps

#### Immediate: FDA Selector Detection Issue
**User Report**: "selector options don't include the correct item but contain other options"

**Context**:
- Fixture (`tests/fixtures/fda_list.html`) uses `.recall-item` class
- Real FDA website may have different structure
- FDA website also has abuse detection (returned 404 on apology page)

**Investigation Needed**:
1. Access real FDA recalls page to see actual HTML structure
2. Compare real structure vs fixture
3. May need to adjust `find_item_selector()` algorithm to detect their actual pattern
4. Possible issues:
   - Items might not have consistent classes
   - Might use more generic tags (div, li without classes)
   - Might have nested structures we're not detecting

**Debugging Approach**:
```python
# Test selector detection on real FDA HTML
from scrapesuite.inspector import find_item_selector
# Get real HTML (may need to bypass protection)
candidates = find_item_selector(html, min_items=3)
# Check if correct selector is in candidates
# If not, analyze what patterns are being detected instead
```

#### Future Enhancements
1. **Headless browser support**: For JavaScript-heavy sites (Playwright/Selenium)
2. **Improved item detection**: Better algorithm for sites without consistent classes
3. **Selector validation**: Check if generated selectors actually work before showing preview
4. **Multi-page support**: Handle pagination patterns automatically
5. **Schema detection**: Auto-detect common patterns (blog posts, products, news articles)
6. **User feedback loop**: Learn from corrections when users fix selectors

### Technical Architecture

**Key Files Modified**:
- `scrapesuite/wizard.py`: Main wizard flow, prompts, YAML generation
- `scrapesuite/inspector.py`: HTML analysis, selector generation, preview extraction
- `scrapesuite/http.py`: HTTP client with browser headers, retry logic, rate limiting
- `scrapesuite/connectors/generic.py`: YAML-driven connector using CSS selectors

**Dependencies**:
- `questionary`: Enhanced interactive prompts (with fallback to input())
- `rich`: Tables, panels, formatted output (with fallback to print())
- `beautifulsoup4`: HTML parsing
- `requests`: HTTP client
- `pyyaml`: YAML generation

**Important Constants**:
```python
DEFAULT_RPS = 1.0  # Default rate limit (requests per second)
MIN_RPS = 0.1
MAX_RPS = 2.0
```

### Testing Notes

**Test Coverage**: 32/32 tests passing
- `test_wizard_smoke.py`: Basic wizard flow validation
- `test_parsers.py`: Field extraction with fixtures
- `test_run_job.py`: End-to-end job execution
- `test_state.py`: State management

**Fixtures**:
- `tests/fixtures/fda_list.html`: FDA recalls list (may not match real site)
- `tests/fixtures/fda_detail.html`: FDA detail page
- `tests/fixtures/nws_list.html`: Weather alerts
- `tests/fixtures/custom_list.html`: Custom test case

### Git State
- **Branch**: `chore/context-freeze` (also default branch)
- **Latest commits**:
  - `cda2187`: Bot detection handling with helpful errors
  - `5e323b8`: Flexible field selector generation
  - `8a3a7e6`: Fix empty fields issue (vote button skipping)
  - `32fae15`: Hardcode rate limit to 1.0 RPS
  - `262e530`: CSV sink fix, helpful prompts, live smoke test

### Commands for Next Session

```bash
# Run wizard
python -m scrapesuite.wizard

# Run specific tests
python -m pytest tests/test_wizard_smoke.py -v

# Test selector detection on fixture
python -c "from scrapesuite.inspector import find_item_selector; import open; html = open('tests/fixtures/fda_list.html').read(); print(find_item_selector(html))"

# Format code
python -m ruff format .

# Lint code
python -m ruff check .

# Run all tests
python -m pytest -q
```

### Questions for Next Session
1. What specific selectors is the wizard showing for FDA recalls? (Need actual output)
2. What should the correct selector be? (Need to see real FDA HTML)
3. Are other sites working correctly, or is this a general issue?
4. Should we prioritize fixing FDA detection or adding headless browser support?

---

**Session End**: November 9, 2025  
**Status**: ✅ All changes committed and pushed  
**Next Priority**: Debug FDA selector detection issue
