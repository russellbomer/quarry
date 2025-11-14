# Quarry 🪨⛏️

**A modern Python toolkit for web data extraction with robust support for React, Vue, and other JavaScript frameworks.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-199%20passing-success.svg)](./tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## 🌟 What is Quarry?

Quarry provides **two powerful approaches** for web scraping:

1. **⚒️ Quarry Tools** - Interactive CLI pipeline for building extraction workflows
2. **🧙 Wizard Mode** - YAML-driven declarative scraping with automatic framework detection

**Key Feature**: Resilient selectors that survive CSS framework updates (React CSS-in-JS, Vue scoped styles, etc.)

---

## 🚀 Quick Start

### Installation

```bash
pip install -e .  # From source
# or: pip install quarry  # From PyPI (coming soon)
```

**Requirements**: Python 3.11+

### Your First Extraction

```bash
# Analyze a webpage
quarry scout https://example.com

# Extract data
quarry excavate schema.yml --url https://example.com

# Export results
quarry ship output.jsonl results.csv
```

📖 **Full guide**: [USAGE_GUIDE.md](USAGE_GUIDE.md) | [INSTALLATION.md](INSTALLATION.md)

---

## ⚒️ Quarry Tools

**5 integrated tools** for complete extraction pipelines:

| Tool | Purpose | Example |
|------|---------|---------|
| **📡 Scout** | Analyze HTML & detect patterns | `quarry scout <url>` |
| **📐 Survey** | Design extraction schemas & jobs | `quarry survey create` |
| **🔨 Excavate** | Execute data extraction | `quarry excavate schema.yml --url <url>` |
| **✨ Polish** | Transform & clean data | `quarry polish data.jsonl --dedupe` |
| **📦 Ship** | Export to CSV/JSON/SQLite | `quarry ship data.jsonl output.csv` |

**Survey Commands**:
- `quarry survey create` - Build schema interactively (with --job flag for job YAML)
- `quarry survey to-job schema.yml -n my_job` - Convert schema to job file
- `quarry survey preview schema.yml --url <url>` - Test extraction before running
- `quarry survey validate schema.yml` - Check schema validity

**Complete pipeline**:
```bash
quarry scout <url> | quarry excavate | quarry polish --dedupe | quarry ship results.csv
```

**Job Creation**:
```bash
# Create job YAML for scheduled/batch extraction
quarry survey create --job --job-name my_scraper
quarry run jobs/my_scraper.yml --live
```

📚 **Detailed docs**: [docs/QUARRY_COMPLETE.md](docs/QUARRY_COMPLETE.md)

---

## 🎯 Modern Framework Support

**The Problem**: React/Vue sites use dynamic CSS classes (`.css-17p10p8`) that change with every build.

**Quarry's Solution**: Structural selectors that survive CSS changes:

```yaml
# ❌ Brittle - breaks on rebuild
title: h3.css-17p10p8 a

# ✅ Resilient - structural hierarchy
title: h3 a
```

### Tools for Modern Sites

**1. Selector Audit Tool**
```bash
python scripts/audit_schema_selectors.py my_schema.yml
# Detects brittle selectors, suggests fixes
```

**2. Selector Utilities**
```python
from quarry.lib.selectors import build_robust_selector

robust = build_robust_selector('h3.css-xyz a', ['tag'])
# Returns: 'h3 a'
```

**3. Framework Detection**
```python
from quarry.framework_profiles import detect_framework

framework = detect_framework(html, soup, url)
# Automatically detects React, Vue, WordPress, etc.
```

📚 **Complete guide**: [docs/MODERN_FRAMEWORKS.md](docs/MODERN_FRAMEWORKS.md)

---

## 📊 Features

- ✅ **Framework Detection** - Automatic detection of 9+ frameworks
- ✅ **Resilient Selectors** - Survive CSS framework updates  
- ✅ **Rate Limiting** - Token bucket with exponential backoff
- ✅ **Robots.txt** - Automatic parsing and compliance
- ✅ **State Management** - SQLite-based deduplication
- ✅ **Multiple Exports** - CSV, JSON, SQLite, Parquet
- ✅ **Validation** - Schema validation with Pydantic
- ✅ **Testing** - 199 tests, 100% passing

---

## 📁 Project Structure

```
quarry/
├── lib/                 # Core utilities
│   ├── selectors.py    # CSS selector utilities
│   ├── http.py         # HTTP client with rate limiting
│   └── robots.py       # Robots.txt parser
├── tools/              # Quarry suite
│   ├── scout/          # HTML analysis
│   ├── survey/         # Schema designer
│   ├── excavate/       # Extraction engine
│   ├── polish/         # Data transformation
│   └── ship/           # Data export
├── framework_profiles/ # Framework detection
├── connectors/         # Data source connectors
├── transforms/         # Data transformations
└── sinks/              # Output writers
```

---

## 📖 Documentation

- **[Installation](INSTALLATION.md)** - Setup and requirements
- **[Usage Guide](USAGE_GUIDE.md)** - Complete usage documentation
- **[Modern Frameworks](docs/MODERN_FRAMEWORKS.md)** - React/Vue/Next.js guide
- **[Selector Reference](docs/SELECTOR_QUICK_REFERENCE.md)** - Quick selector patterns
- **[Wizard Guide](docs/WIZARD.md)** - YAML-based extraction
- **[Architecture](docs/ARCHITECTURE_V2.md)** - System design
- **[Testing](docs/TESTING.md)** - Running tests
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues

---

## 🧪 Development

```bash
# Run tests
pytest                          # All tests
pytest tests/test_scout.py -v   # Specific tool

# Code quality
ruff format .                   # Format code
ruff check .                    # Lint code

# Quick commands
make test                       # Run tests
make format                     # Format code
make check                      # Lint code
```

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**To add a new framework profile:**

```python
# quarry/framework_profiles/frameworks/my_framework.py
class MyFrameworkProfile(FrameworkProfile):
    name = "MyFramework"
    
    def detect(self, html: str, soup: BeautifulSoup, url: str) -> int:
        score = 0
        if 'framework-marker' in html:
            score += 50
        return score
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

## 🙏 Acknowledgments

- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing
- [Pyarrow](https://arrow.apache.org/docs/python/) - Parquet support
- [Click](https://click.palletsprojects.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Pydantic](https://pydantic.dev/) - Data validation

---

**Happy Scraping! 🎉**

