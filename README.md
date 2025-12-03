# Quarry 🪨⛏️

**A modern Python toolkit for web data extraction with robust support for React, Vue, and other JavaScript frameworks.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/py-quarry.svg)](https://pypi.org/project/py-quarry/)
[![Tests](https://img.shields.io/badge/tests-passing-success.svg)](./tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

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
pip install py-quarry
```

**Requirements**: Python 3.11+

### New to Quarry? Try the Guided Tutorial

```bash
quarry foreman
```

The **Foreman** walks you through the complete 5-tool pipeline in ~2-3 minutes using Hacker News as a demo.

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
| **📐 Survey** | Design extraction schemas | `quarry survey create schema.yml` |
| **🔨 Excavate** | Execute data extraction | `quarry excavate schema.yml --url <url>` |
| **✨ Polish** | Transform & clean data | `quarry polish data.jsonl --dedupe` |
| **📦 Ship** | Export to CSV/JSON/SQLite/PostgreSQL | `quarry ship data.jsonl output.csv` |

**Complete pipeline**:
```bash
quarry scout <url> | quarry excavate | quarry polish --dedupe | quarry ship results.csv
```

📚 **Detailed docs**: [docs/QUARRY_COMPLETE.md](docs/QUARRY_COMPLETE.md)

---

## 🧙 Wizard Mode

**Zero-code scraping** with automatic framework detection:

```bash
# Launch interactive wizard
quarry init

# Wizard will:
# 1. Detect framework (React, WordPress, etc.)
# 2. Suggest selectors
# 3. Generate YAML job file

# Run generated job
quarry run jobs/my_job.yml --live
```

**Supports 9 frameworks**: WordPress, Drupal, React, Vue, Next.js, Bootstrap, Tailwind, Shopify, Django

📚 **Wizard guide**: [docs/WIZARD.md](docs/WIZARD.md)

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
- ✅ **Multiple Exports** - CSV, JSON, SQLite, Parquet, PostgreSQL
- ✅ **Validation** - Schema validation with Pydantic
- ✅ **Guided Tutorial** - `quarry foreman` for interactive learning
- ✅ **Testing** - 217 tests, 100% passing

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

## ⚙️ Configuration

The CLI and HTTP client can be tuned via environment variables:

**Logging & HTTP:**
- `QUARRY_LOG_LEVEL`: Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). Default `INFO`.
- `QUARRY_LOG_JSON`: Set to `1` to emit JSON logs to stderr.
- `QUARRY_DEFAULT_RPS`: Default requests-per-second per domain (float). Default `1.0`.
- `QUARRY_HTTP_TIMEOUT`: Default request timeout in seconds (int). Default `30`.
- `QUARRY_HTTP_MAX_RETRIES`: Default HTTP retries (int). Default `3`.
- `PROXY_URL`: HTTP/HTTPS proxy URL (also honors standard `HTTP(S)_PROXY`).
- `QUARRY_MAX_CONTENT_MB`: Max response size in MB (int). Rejects larger payloads.
- `QUARRY_INTERACTIVE`: `1` to prompt when robots.txt blocks (ethical default is non-interactive).
- `QUARRY_IGNORE_ROBOTS`: `1` to ignore robots.txt (testing only).

**Database Exports:**
- `QUARRY_POSTGRES_URL`: PostgreSQL connection URL for database exports.

Examples:

```bash
export QUARRY_LOG_LEVEL=INFO
export QUARRY_DEFAULT_RPS=0.5
export QUARRY_HTTP_TIMEOUT=60
export QUARRY_HTTP_MAX_RETRIES=5
export QUARRY_MAX_CONTENT_MB=10
export PROXY_URL=http://proxy.internal:8080
export QUARRY_POSTGRES_URL=postgresql://user:pass@localhost:5432/extractions

quarry excavate schemas/example.yml --url https://example.com -o out.jsonl
quarry ship out.jsonl postgresql://localhost/db  # Export to PostgreSQL
```

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

