# Quarry

**A modern, production-ready Python toolkit for web data extraction, transformation, and export.**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-197%20passing-success.svg)](./tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## 🌟 Overview

Quarry combines **two powerful toolkits** for different web scraping workflows:

1. **🧙 Legacy Wizard Suite** - YAML-driven declarative scraping with interactive job generation
2. **⚒️ Quarry Suite** - Modern command-line tools for extraction pipelines

Choose the approach that fits your workflow, or use both together!

---

## 🚀 Quick Start

```bash
# Clone and install
git clone https://github.com/russellbomer/quarry.git
cd quarry
pip install -r requirements.txt

# Option 1: Use the Wizard (guided scraper creation)
quarry init

# Option 2: Use Quarry tools (command-line pipeline)
quarry scout https://example.com
```

**Requirements**: Python 3.12+

---

## ⚒️ Quarry Suite (v2.0)

A complete toolkit for building extraction pipelines with **5 integrated tools**:

### The 5 Tools

| Tool | Purpose | Usage |
|------|---------|-------|
| **📡 Scout** | Analyze HTML & detect patterns | `quarry scout <url\|file>` |
| **📐 Survey** | Design extraction schemas | `quarry survey create schema.yml` |
| **🔨 Excavate** | Execute data extraction | `quarry excavate schema.yml --url <url>` |
| **✨ Polish** | Transform & clean data | `quarry polish data.jsonl --dedupe` |
| **📦 Ship** | Export to multiple formats | `quarry ship data.jsonl output.csv` |

### Complete Pipeline Example

```bash
# 1. Analyze HTML structure
quarry scout https://example.com/blog --format json --output analysis.json

# 2. Design extraction schema
quarry survey create blog_schema.yml
# (Interactive editor opens - define containers & fields)

# 3. Preview extraction
quarry survey preview blog_schema.yml --file page.html

# 4. Execute extraction
quarry excavate blog_schema.yml --url https://example.com/blog --output raw.jsonl

# 5. Clean & deduplicate
quarry polish raw.jsonl --dedupe --dedupe-keys title --output clean.jsonl

# 6. Export to CSV
quarry ship clean.jsonl blog_posts.csv
```

### Tool Features

**🔍 Scout** - HTML Analysis
- Framework detection (React, WordPress, Django, etc.)
- Container pattern finding with confidence scores
- Field suggestions based on HTML structure
- JSON/terminal output formats

**📐 Survey** - Schema Designer  
- Interactive schema builder with validation
- Live extraction preview
- Pydantic-based schema validation
- Pagination configuration support

**🔨 Excavate** - Extraction Engine
- Schema-driven extraction
- Built-in pagination support
- Rate limiting & robots.txt compliance
- JSONL streaming output

**✨ Polish** - Data Transformation
- Deduplication (first/last strategies)
- 10+ built-in transformers (normalize_text, parse_date, extract_domain, etc.)
- Validation rules (email, URL, date, pattern matching)
- Field filtering & statistics

**📦 Ship** - Data Export
- CSV, JSON, SQLite exports
- Format auto-detection
- Custom table names & schema options
- PostgreSQL/MySQL ready (coming soon)

**📚 Detailed Quarry Documentation**: [docs/QUARRY_COMPLETE.md](docs/QUARRY_COMPLETE.md)

---

## 🧙 Legacy Wizard Suite

Interactive, YAML-driven scraping with zero coding required.

### Key Features

**Interactive Wizard**
- Generate scrapers through guided prompts
- Automatic framework detection (9 frameworks)
- Smart selector suggestions
- Offline mode (paste HTML directly)

**YAML-Based Jobs**
- Declarative job definitions
- Reusable configurations
- Multiple output formats (Parquet, CSV, JSONL)
- Connector/transform/sink pipeline

**Framework-Aware Extraction**
- Detects: WordPress, Drupal, React, Vue, Next.js, Bootstrap, Tailwind, Shopify, Django
- 17+ field types (title, url, date, author, category, tags, rating, etc.)
- Framework-specific selector patterns
- Multi-framework site support

**State Management**
- SQLite-based cursor tracking
- Idempotent deduplication
- Failed URL recovery
- Batch tracking with timestamps

**Polite Scraping**
- Per-domain rate limiting (token bucket)
- Robots.txt parsing & caching (24h TTL)
- Exponential backoff with jitter
- Adaptive throttling (429/503 errors)

### Wizard Quick Start

```bash
# Launch interactive wizard
quarry init

# The wizard will:
# 1. Ask for URL to scrape
# 2. Detect framework (WordPress, React, etc.)
# 3. Analyze HTML and suggest selectors
# 4. Let you pick containers & fields
# 5. Generate YAML job file

# Run generated job
quarry run jobs/my_job.yml --live --max-items 20

# View state & results
quarry state
```

### Example Job File

```yaml
id: blog_posts
connector:
  type: custom
  url: https://blog.example.com
  item_selector: article.post
  fields:
    - field: title
      selector: h2.entry-title
    - field: url
      selector: a.permalink::attr(href)
    - field: date
      selector: time.published::attr(datetime)
    - field: author
      selector: .author-name
  pagination:
    next_selector: a.next-page::attr(href)
    max_pages: 10

sink:
  type: parquet
  path: data/cache/blog_posts
```

**📚 Wizard Documentation**: [docs/WIZARD.md](docs/WIZARD.md)

---

## 📊 Project Statistics

**Status**: ✅ Production Ready

```
Total Tests:        197 (100% passing)
Total Code:         ~5,000 LOC
Tools:              5 Quarry + Legacy CLI
Export Formats:     CSV, JSON, SQLite, Parquet
Frameworks:         9 detected
Python Version:     3.12+
```

---

## 📁 Project Structure

```
quarry/
├── quarry/              # Main package
│   ├── lib/                  # Foundation library
│   │   ├── http.py          # HTTP client with rate limiting
│   │   ├── ratelimit.py     # Token bucket rate limiter
│   │   ├── selectors.py     # CSS selector utilities
│   │   ├── robots.py        # Robots.txt parser
│   │   └── policy.py        # Policy enforcement
│   ├── tools/                # Quarry suite
│   │   ├── scout/           # HTML analysis tool
│   │   ├── survey/       # Schema designer
│   │   ├── excavate/           # Extraction engine
│   │   ├── polish/          # Data transformation
│   │   └── ship/           # Data export
│   ├── framework_profiles/   # Framework detection
│   ├── connectors/          # Data source connectors
│   ├── transforms/          # Data transformations
│   ├── sinks/               # Output writers
│   ├── quarry.py           # Quarry CLI
│   ├── cli.py               # Legacy CLI
│   ├── wizard.py            # Interactive wizard
│   ├── inspector.py         # HTML analysis
│   └── core.py              # Job runner
├── tests/                    # Test suite (197 tests)
├── docs/                     # Documentation
│   ├── QUARRY_COMPLETE.md  # Quarry guide
│   ├── WIZARD.md            # Wizard guide
│   ├── FRAMEWORK_PROFILES.md
│   ├── ARCHITECTURE_V2.md
│   ├── TESTING.md
│   └── TROUBLESHOOTING.md
├── examples/                 # Example job files
└── scripts/                  # Utility scripts
```

---

## 📖 Documentation

### User Guides
- **[Quarry Suite](docs/QUARRY.md)** - Complete guide to the 5 extraction tools
- **[Framework Profiles](docs/FRAMEWORK_PROFILES.md)** - Understanding framework detection
- **[Infinite Scroll API Guide](docs/INFINITE_SCROLL_API_GUIDE.md)** - Finding API endpoints for dynamic sites
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

### Developer Guides
- **[Architecture](docs/ARCHITECTURE_V2.md)** - System design and structure
- **[Testing](docs/TESTING.md)** - Running and writing tests
- **[Security](docs/SECURITY.md)** - Bot evasion and best practices

### Quick Reference
- **[Examples](examples/jobs/)** - Pre-built job templates
- **[Contributing](CONTRIBUTING.md)** - How to contribute

---

## 🧪 Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=quarry --cov-report=html

# Run specific tool tests
pytest tests/test_probe.py -v
pytest tests/test_forge.py -v
pytest tests/test_polish.py -v
pytest tests/test_crate.py -v

# Quick test
make test
```

### Code Quality

```bash
# Format code
make format

# Lint code  
make check

# Run all checks
make all
```

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Adding Framework Profiles

To add support for a new framework:

1. Create profile class in `framework_profiles/`
2. Implement detection with confidence scoring (0-100)
3. Add field mappings for common field types
4. Write tests with real-world HTML samples
5. Update documentation

Example:
```python
class AngularProfile(FrameworkProfile):
    name = "angular"
    
    @classmethod
    def detect(cls, html: str, item_element: Tag | None = None) -> int:
        score = 0
        if "ng-app" in html:
            score += 40
        if "ng-controller" in html:
            score += 30
        return min(score, 100)
```

---

## 🗺️ Roadmap

### Completed ✅
- Quarry Suite (5 tools)
- Multi-framework detection
- 197 comprehensive tests
- Complete pipeline support
- CSV/JSON/SQLite exports

### In Progress 🚧
- PostgreSQL/MySQL exporters
- Cloud storage exports (S3, GCS)
- Performance optimization

### Planned 📋
- API exports (REST, GraphQL)
- Web UI dashboard
- Docker deployment
- Scheduled extraction jobs
- PyPI packaging

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing
- [Pyarrow](https://arrow.apache.org/docs/python/) - Parquet output
- [Click](https://click.palletsprojects.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Pydantic](https://pydantic.dev/) - Data validation

---

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Examples**: [examples/jobs/](examples/jobs/)
- **Issues**: [GitHub Issues](https://github.com/russellbomer/quarry/issues)

**Happy Scraping! 🎉**
