# Contributing to Quarry

Thank you for your interest in contributing to Quarry! This guide will help you add new framework profiles, fix bugs, and improve the codebase.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Workflow](#development-workflow)
3. [Adding Framework Profiles](#adding-framework-profiles)
4. [Code Standards](#code-standards)
5. [Testing](#testing)
6. [Documentation](#documentation)
7. [Performance](#performance)

---

## Getting Started

### Prerequisites

- Python 3.12+
- Git
- Familiarity with BeautifulSoup and CSS selectors

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/quarry.git
cd quarry

# Install dependencies
pip install -r requirements.txt

# Run tests to verify setup
python -m pytest -q
```

### Repository Structure

```
quarry/
├── quarry/              # Main package
│   ├── cli.py               # Command-line interface
│   ├── wizard.py            # Interactive wizard
│   ├── inspector.py         # HTML analysis
│   ├── http.py              # HTTP client with rate limiting
│   ├── framework_profiles/  # Framework detection (MODULAR)
│   ├── connectors/          # Data source connectors
│   ├── transforms/          # Data transformation
│   └── sinks/               # Data output
├── tests/                   # Test suite
├── docs/                    # Documentation
├── scripts/                 # Development tools
└── examples/                # Example job files
```

---

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/add-angular-profile
```

### 2. Make Changes

Follow the [Code Standards](#code-standards) below.

### 3. Run Tests

```bash
# Run all tests
python -m pytest -q

# Run specific test file
python -m pytest tests/test_framework_profiles.py -v

# Run with coverage
python -m pytest --cov=quarry tests/
```

### 4. Check Type Safety

```bash
# Check mypy (strict mode for framework_profiles and http)
mypy quarry/framework_profiles/ quarry/http.py

# Check all modules
mypy quarry/
```

### 5. Format Code

```bash
# Auto-format with ruff
python -m ruff format .

# Check for issues
python -m ruff check .
```

### 6. Commit Changes

```bash
git add -A
git commit -m "feat: Add AngularProfile for SPA detection

- Detects ng-app, ng-controller, ng-repeat patterns
- Container patterns: [ng-repeat], .ng-scope
- Field mappings for common Angular directives
- Tests for Angular v1 and v2+ patterns
"
```

### 7. Push and Create Pull Request

```bash
git push origin feature/add-angular-profile
```

Then create a PR on GitHub with:
- Clear description of changes
- Link to related issues
- Test results showing all tests pass

---

## Adding Framework Profiles

Adding a new framework profile is the most common contribution. Follow this step-by-step guide.

### Step 1: Choose the Category

Place your profile in the appropriate category:

- **cms/**: Content Management Systems (WordPress, Drupal, Joomla, etc.)
- **frameworks/**: JavaScript frameworks (React, Vue, Angular, Svelte, etc.)
- **css/**: CSS frameworks (Bootstrap, Tailwind, Foundation, etc.)
- **ecommerce/**: E-commerce platforms (Shopify, WooCommerce, Magento, etc.)
- **universal/**: Universal patterns (Schema.org, Open Graph, semantic HTML, etc.)

### Step 2: Create the Profile File

Example: Adding AngularProfile

```python
# quarry/framework_profiles/frameworks/angular.py
"""Angular / AngularJS framework profile."""

from bs4 import Tag

from quarry.framework_profiles.base import FrameworkProfile


class AngularProfile(FrameworkProfile):
    """Detect Angular / AngularJS applications."""

    name = "angular"

    @classmethod
    def detect(cls, html: str, item_element: Tag | None = None) -> int:
        """
        Detect Angular with confidence scoring.

        Returns:
            Confidence score 0-100. Threshold for detection is 40.
        """
        score = 0

        # Strong indicators (high weight)
        if "ng-app" in html:
            score += 40  # Angular bootstrap
        if "data-ng-app" in html:
            score += 35  # Alternative syntax

        # Medium indicators
        if "ng-controller" in html:
            score += 20
        if "ng-repeat" in html:
            score += 20
        if "[ng-" in html:  # Angular 2+ style
            score += 25

        # Script indicators
        if "angular.js" in html or "angular.min.js" in html:
            score += 30
        if "@angular/core" in html:
            score += 35  # Angular 2+

        # Weak indicators
        if "{{" in html and "}}" in html:
            score += 10  # Template syntax (common but not specific)

        return score

    @classmethod
    def get_item_selector_hints(cls) -> list[str]:
        """
        Get CSS selector patterns likely to match item containers.

        Returns:
            List of selector patterns to try
        """
        return [
            "[ng-repeat]",
            ".ng-scope",
            "[data-ng-repeat]",
            "[class*='item']",
            "[class*='list-item']",
        ]

    @classmethod
    def get_field_mappings(cls) -> dict[str, list[str]]:
        """
        Get field type to CSS selector/class pattern mappings.

        Returns:
            Dict mapping field types to list of selector patterns
        """
        return {
            "title": [
                "[ng-bind='title']",
                "[data-ng-bind='title']",
                "h2",
                "h3",
                "[class*='title']",
            ],
            "link": [
                "a[ng-href]::attr(ng-href)",
                "a[href]::attr(href)",
            ],
            "date": [
                "[ng-bind='date']",
                "time",
                "[class*='date']",
            ],
            "description": [
                "[ng-bind='description']",
                "p",
                "[class*='description']",
            ],
            "author": [
                "[ng-bind='author']",
                "[class*='author']",
            ],
        }
```

### Step 3: Register the Profile

Add your profile to `quarry/framework_profiles/__init__.py`:

```python
# Add import
from .frameworks import AngularProfile

# Add to FRAMEWORK_PROFILES list (order matters!)
FRAMEWORK_PROFILES: list[type[FrameworkProfile]] = [
    DjangoAdminProfile,     # Very specific
    NextJSProfile,
    ReactComponentProfile,
    VueJSProfile,
    AngularProfile,         # <-- Add here
    DrupalViewsProfile,
    # ...
]

# Add to __all__ exports
__all__ = [
    # ...
    "AngularProfile",
    # ...
]
```

### Step 4: Create Test Fixture

Add an HTML fixture for testing:

```html
<!-- tests/fixtures/angular_list.html -->
<!DOCTYPE html>
<html ng-app="myApp">
<head>
    <title>Angular App</title>
    <script src="angular.min.js"></script>
</head>
<body ng-controller="MainCtrl">
    <div class="items">
        <div class="item" ng-repeat="item in items">
            <h2 ng-bind="item.title">Article Title</h2>
            <p ng-bind="item.description">Description text</p>
            <span ng-bind="item.date">2025-01-15</span>
            <a ng-href="{{item.url}}">Read more</a>
        </div>
    </div>
</body>
</html>
```

### Step 5: Write Tests

```python
# tests/test_angular_profile.py
"""Tests for AngularProfile."""

from pathlib import Path

from quarry.framework_profiles import AngularProfile, detect_framework


def test_angular_detection():
    """Test Angular framework detection."""
    fixture = Path(__file__).parent / "fixtures" / "angular_list.html"
    html = fixture.read_text()

    # Should detect with good confidence
    score = AngularProfile.detect(html)
    assert score >= 40, f"Expected score ≥40, got {score}"

    # Should be selected as best framework
    framework = detect_framework(html)
    assert framework == AngularProfile


def test_angular_item_selectors():
    """Test Angular item selector hints."""
    hints = AngularProfile.get_item_selector_hints()

    assert "[ng-repeat]" in hints
    assert ".ng-scope" in hints


def test_angular_field_mappings():
    """Test Angular field mappings."""
    mappings = AngularProfile.get_field_mappings()

    assert "title" in mappings
    assert "link" in mappings
    assert "date" in mappings

    # Check for Angular-specific patterns
    title_patterns = mappings["title"]
    assert any("ng-bind" in p for p in title_patterns)
```

### Step 6: Run Tests

```bash
# Run your new tests
python -m pytest tests/test_angular_profile.py -v

# Run all tests to ensure no regressions
python -m pytest -q

# Check type safety
mypy quarry/framework_profiles/
```

### Step 7: Document Your Profile

Add an entry to `docs/FRAMEWORK_PROFILES.md`:

```markdown
#### 9. **AngularProfile** - Single Page Applications
- **Usage**: 20%+ of SPAs, especially enterprise
- **Detection**:
  - `ng-app`, `ng-controller`, `ng-repeat`, `[ng-*]`
  - `<script src="angular.js">`
  - `data-ng-*` attributes
- **Container patterns**: `[ng-repeat]`, `.ng-scope`, custom directives
- **Field patterns**: `{{}}` template syntax, `ng-bind` attributes
- **Confidence scoring**: 40+ for Angular v1, 35+ for Angular 2+
```

---

## Code Standards

### Type Hints

All new code must include type hints:

```python
# ✅ Good
def detect(cls, html: str, item_element: Tag | None = None) -> int:
    """Detect framework with confidence scoring."""
    score: int = 0
    return score

# ❌ Bad
def detect(cls, html, item_element=None):
    score = 0
    return score
```

### Docstrings

Use Google-style docstrings:

```python
def detect(cls, html: str, item_element: Tag | None = None) -> int:
    """
    Detect framework with confidence scoring.

    Args:
        html: Full page HTML as string
        item_element: Optional BeautifulSoup Tag element

    Returns:
        Confidence score 0-100. Threshold for detection is 40.

    Example:
        >>> score = MyProfile.detect("<html>...</html>")
        >>> print(f"Confidence: {score}")
        Confidence: 75
    """
    pass
```

### BeautifulSoup Class Handling

Use the `_get_element_classes()` helper for type safety:

```python
from quarry.framework_profiles.base import _get_element_classes

# ✅ Good - Type safe
classes = _get_element_classes(element)
if "card" in classes:
    score += 20

# ❌ Bad - Type unsafe
classes = " ".join(element.get("class", []))  # Fails mypy strict
```

### Confidence Scoring Guidelines

Use these weights for detection signals:

```python
# Very strong (30-40 points)
if "ng-app" in html:          score += 40  # Unique identifier
if meta_generator == "Drupal":  score += 40  # Official meta tag

# Strong (20-30 points)
if "ng-controller" in html:    score += 20  # Common pattern
if ".views-row" in html:       score += 25  # Framework-specific class

# Medium (10-20 points)
if "angular.js" in html:       score += 15  # Script include
if ".btn" in html:             score += 10  # Generic class

# Weak (5-10 points)
if "{{" in html:               score += 5   # Template syntax (not specific)
```

**Scoring Philosophy:**
- **Threshold: 40** - Framework must score ≥40 to be detected
- **High confidence: 70+** - Multiple strong signals
- **Low confidence: 40-60** - Single strong signal or several weak ones
- **False positive prevention**: Weak signals alone shouldn't exceed threshold

### Formatting

Run `ruff format` before committing:

```bash
# Auto-format all files
python -m ruff format .

# Check for issues
python -m ruff check .
```

### Linting

Address all `ruff` warnings:

```bash
# Check for lint issues
python -m ruff check .

# Auto-fix safe issues
python -m ruff check --fix .
```

---

## Testing

### Test Organization

```
tests/
├── test_framework_profiles.py   # Generic framework tests
├── test_angular_profile.py      # Angular-specific tests
├── test_wordpress_profile.py    # WordPress-specific tests
├── test_wizard.py               # Wizard integration tests
└── fixtures/
    ├── angular_list.html
    ├── wordpress_post.html
    └── drupal_views.html
```

### Writing Good Tests

**Test the detection logic:**
```python
def test_detection_threshold():
    """Framework should only detect with score >= 40."""
    weak_html = "<div class='item'></div>"  # Generic
    score = AngularProfile.detect(weak_html)
    assert score < 40, "Should not detect generic HTML"

    strong_html = "<div ng-app='app' ng-controller='Ctrl'></div>"
    score = AngularProfile.detect(strong_html)
    assert score >= 40, "Should detect Angular-specific HTML"
```

**Test field mappings:**
```python
def test_field_selectors():
    """Field mappings should include framework-specific patterns."""
    mappings = AngularProfile.get_field_mappings()

    # Should have all standard fields
    assert all(
        field in mappings
        for field in ["title", "link", "date", "description"]
    )

    # Should include framework-specific selectors
    assert any("ng-bind" in p for p in mappings["title"])
```

**Test with real fixtures:**
```python
def test_real_world_html():
    """Test against real-world HTML fixture."""
    fixture = Path(__file__).parent / "fixtures" / "angular_list.html"
    html = fixture.read_text()

    framework = detect_framework(html)
    assert framework == AngularProfile

    # Should extract item selectors
    hints = AngularProfile.get_item_selector_hints()
    assert "[ng-repeat]" in hints
```

### Running Tests

```bash
# Run all tests
python -m pytest -q

# Run specific test file
python -m pytest tests/test_angular_profile.py -v

# Run specific test
python -m pytest tests/test_angular_profile.py::test_detection_threshold -v

# Run with coverage
python -m pytest --cov=quarry --cov-report=html tests/

# View coverage report
open htmlcov/index.html
```

### Testing with Real Websites

When testing framework detection with live websites, follow these guidelines to respect robots.txt and avoid rate limiting.

#### ✅ Bot-Friendly Test Sites (Safe for Testing)

Use these sites for testing - they allow bot access and have good framework diversity:

| Site | Frameworks | Usage Notes |
|------|-----------|-------------|
| **GitHub** (github.com) | OpenGraph, Twitter Cards | Excellent for social metadata |
| **Stack Overflow** (stackoverflow.com) | OpenGraph, Twitter Cards | Q&A content, allows bots |
| **AllRecipes** (allrecipes.com) | Bootstrap, Tailwind, WordPress | Recipe content, bot-friendly |
| **Amazon** (amazon.com) | Bootstrap, proprietary | Product pages, respects rate limits |
| **Target** (target.com) | OpenGraph, Next.js, Tailwind | Modern tech stack |

**Testing command:**
```bash
# Interactive mode - prompts when robots.txt blocks
python -m quarry.cli run job.yml --live --interactive

# Direct URL test
python -c "
from quarry.http import get_html
from quarry.framework_profiles import detect_all_frameworks

html = get_html('https://github.com/explore')
frameworks = detect_all_frameworks(html)
print(frameworks[:5])
"
```

#### ❌ Sites That Block Bots (Do NOT Use)

These sites block automated access via robots.txt - do not use for testing:

- ❌ **Medium.com** - User-Agent: * Disallow: /
- ❌ **DEV.to** - User-Agent: * Disallow: /

**If you encounter robots.txt blocks:**

```bash
# Option 1: Test with bot-friendly alternatives (recommended)
# See list above

# Option 2: Fetch HTML manually for local testing
curl 'URL' -H 'User-Agent: Mozilla/5.0' > test.html
python -c "
from pathlib import Path
html = Path('test.html').read_text()
from quarry.framework_profiles import detect_all_frameworks
print(detect_all_frameworks(html)[:5])
"

# Option 3: Interactive mode (prompts before bypassing)
python -m quarry.cli run job.yml --live --interactive

# Option 4: Testing only (NOT for production)
python -c "
from quarry.http import get_html
html = get_html('URL', respect_robots=False)  # Testing only!
"
```

**Important:**
- Respecting robots.txt is **required for production** code
- Bypassing robots.txt is **only acceptable for testing/debugging**
- Always use `--interactive` mode for ad-hoc exploration
- Add `--ignore-robots` only in controlled test environments

#### ⚠️ Sites with Aggressive Rate Limiting

These sites may timeout or require very slow crawling:

- ⚠️ **Best Buy** (bestbuy.com) - 30+ second timeouts
- ⚠️ **Walmart** (walmart.com) - Similar aggressive rate limiting

**Testing with slow sites:**

```bash
# Increase timeout (default is 30s)
python -c "
from quarry.http import get_html
html = get_html('URL', timeout=60)  # Wait up to 60 seconds
"

# Reduce rate limit in job YAML
# Edit your job file:
#   rate_limit_rps: 0.2  # 1 request per 5 seconds

# Use session with cookies (may avoid bot detection)
python -c "
from quarry.http import get_html, create_session
session = create_session()
html = get_html('URL', session=session)
"
```

#### Testing Best Practices

1. **Always respect robots.txt in production code**
2. **Use bot-friendly sites for framework detection testing**
3. **Test with fixtures for CI/CD** (no network requests)
4. **Manual testing on local HTML files** when sites block bots
5. **Slow down requests** (0.5-1.0 rps) when testing live sites
6. **Use `--interactive` mode** for exploratory testing
7. **Document which sites work** in your tests/documentation

Example test with bot-friendly site:

```python
# tests/test_live_github.py
"""Test framework detection with GitHub (bot-friendly)."""

import pytest
from quarry.http import get_html
from quarry.framework_profiles import detect_all_frameworks


@pytest.mark.live  # Mark as live test (optional to skip in CI)
def test_github_opengraph_detection():
    """Test OpenGraph detection on GitHub (allows bots)."""
    try:
        html = get_html("https://github.com/explore", timeout=10)
        frameworks = detect_all_frameworks(html)
        
        # GitHub uses OpenGraph and Twitter Cards
        framework_names = [fw.name for fw, _ in frameworks[:5]]
        assert "opengraph" in framework_names or "twitter_cards" in framework_names
        
    except Exception as e:
        pytest.skip(f"Live test failed (network issue): {e}")


# Run live tests:
# pytest tests/test_live_github.py -m live -v
```

---

## Documentation

### Update FRAMEWORK_PROFILES.md

When adding a profile, document:

1. **Profile name and category**
2. **Usage statistics** (% of sites)
3. **Detection patterns** (what signals are used)
4. **Container patterns** (item selector hints)
5. **Field patterns** (field mappings)
6. **Example HTML** (if helpful)

### Update README.md

If your contribution adds major functionality:

1. Update feature list
2. Add example usage
3. Update installation instructions (if needed)

### Add Inline Comments

Explain non-obvious logic:

```python
# Check for Angular 2+ bracket syntax
# Example: <div [ng-if]="condition">
if "[ng-" in html:
    score += 25

# Avoid detecting {{}}'s in JSON or unrelated code
# Only add points if multiple mustache patterns found
if html.count("{{") > 3 and html.count("}}") > 3:
    score += 10
```

---

## Performance

### Profile Performance

Keep detection fast:

```python
# ✅ Good - String checks are fast
if "ng-app" in html:
    score += 40

# ⚠️ Acceptable - Simple BeautifulSoup find
soup = BeautifulSoup(html, "html.parser")
if soup.find(attrs={"ng-app": True}):
    score += 40

# ❌ Slow - Avoid expensive parsing in detect()
soup = BeautifulSoup(html, "html.parser")
for elem in soup.find_all(True):  # Iterates ALL elements
    # ... complex logic
```

### Benchmark Your Profile

Use the profiling script:

```bash
# Add your fixture to tests/fixtures/
# Then run profiler
PYTHONPATH=/workspaces/quarry python scripts/profile_framework_detection.py
```

**Target performance:**
- Detection: < 1ms per page
- Selector generation: < 0.5ms per field

### Optimization Tips

1. **String checks before parsing**: Use `"pattern" in html` before `BeautifulSoup()`
2. **Cache compiled regexes**: Define at class level
3. **Early returns**: Exit fast when confidence is clear
4. **Lazy evaluation**: Don't check all signals if already high confidence

```python
@classmethod
def detect(cls, html: str, item_element: Tag | None = None) -> int:
    score = 0

    # Quick string checks first (fast)
    if "ng-app" in html:
        score += 40
    if "angular.js" in html:
        score += 30

    # Early exit if already confident
    if score >= 70:
        return score  # Don't waste time on more checks

    # More expensive checks only if needed
    soup = BeautifulSoup(html, "html.parser")
    if soup.find(attrs={"ng-controller": True}):
        score += 20

    return score
```

---

## Common Patterns

### Handling Multiple Framework Versions

```python
class AngularProfile(FrameworkProfile):
    """Detect Angular v1 and v2+."""

    @classmethod
    def detect(cls, html: str, item_element: Tag | None = None) -> int:
        score = 0

        # Angular v1 patterns
        if "ng-app" in html or "data-ng-app" in html:
            score += 40
        if "angular.js" in html or "angular.min.js" in html:
            score += 30

        # Angular 2+ patterns (TypeScript-based)
        if "[ng-" in html:  # Bracket syntax
            score += 25
        if "@angular/core" in html or "__ng" in html:
            score += 35

        return score
```

### Framework Combination Detection

```python
class WordPressWooCommerceProfile(FrameworkProfile):
    """Detect WordPress + WooCommerce combination."""

    @classmethod
    def detect(cls, html: str, item_element: Tag | None = None) -> int:
        score = 0

        # Require both WordPress and WooCommerce signals
        has_wordpress = "wp-content" in html or "hentry" in html
        has_woocommerce = "woocommerce" in html or "product-card" in html

        if has_wordpress and has_woocommerce:
            score += 60  # Strong combination signal
        elif has_woocommerce:
            score += 30  # WooCommerce alone (might be headless)

        return score
```

### Handling Nested Selectors

```python
@classmethod
def get_field_mappings(cls) -> dict[str, list[str]]:
    return {
        "title": [
            ".card-header .card-title",  # Nested selector
            "h2.product-title",          # Tag + class
            "[data-product] h2",         # Attribute + descendant
        ],
        "price": [
            ".price .amount::attr(data-price)",  # Attribute extraction
            ".price-wrapper span.price",
        ],
    }
```

---

## Review Checklist

Before submitting a pull request, verify:

- [ ] Code follows type hint standards (passes `mypy`)
- [ ] All tests pass (`pytest -q`)
- [ ] Code formatted with `ruff format`
- [ ] No lint warnings (`ruff check`)
- [ ] New profile registered in `__init__.py`
- [ ] Test fixture added to `tests/fixtures/`
- [ ] Tests written for new profile
- [ ] Documentation updated in `FRAMEWORK_PROFILES.md`
- [ ] Performance benchmarked (`scripts/profile_framework_detection.py`)
- [ ] Commit message follows conventional commits format
- [ ] Branch name describes feature (`feature/add-angular-profile`)

---

## Getting Help

- **Documentation**: See `docs/` directory
- **Examples**: See `examples/jobs/` directory
- **Issues**: Open a GitHub issue
- **Discussions**: Use GitHub Discussions for questions

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

Thank you for contributing to Quarry! 🎉
