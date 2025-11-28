# Strategic Positioning Report

**Date:** November 28, 2025  
**Project:** Quarry  
**Repository:** russellbomer/scrapesuite

---

## 1. Current Project Understanding

### Domain & Purpose (Inferred)
Quarry is a **Python-based web data extraction toolkit** designed for structured scraping of HTML content. It positions itself as a modern alternative to ad-hoc scraping scripts, emphasizing:
- Resilient CSS selectors that survive CSS framework updates (React, Vue, Tailwind, etc.)
- A declarative YAML-based schema system for reproducible extraction
- A 5-tool CLI pipeline (Scout → Survey → Excavate → Polish → Ship) following a mining metaphor

### Primary Tech Stack & Architecture Notes
- **Language**: Python 3.11+ with modern type hints
- **CLI Framework**: Click + Rich (terminal UI) + questionary (interactive prompts)
- **HTML Parsing**: BeautifulSoup4
- **Data Handling**: Pandas, PyArrow (Parquet)
- **Validation**: Pydantic for schema validation
- **Architecture**: Modular tool-based design with shared `lib/` utilities and `framework_profiles/` for detection heuristics
- **Testing**: pytest with 208 tests (unit + integration), mypy for typing

### Key Existing Strengths
1. **Complete 5-Tool Pipeline** - Scout, Survey, Excavate, Polish, Ship are all functional with both interactive and batch modes
2. **Framework Detection** - 13+ profiles for detecting React, Vue, WordPress, Bootstrap, etc.
3. **Robust Selector System** - `SelectorChain` with fallbacks, dynamic class detection (`_looks_dynamic()`), semantic-aware selector generation
4. **Polite HTTP Client** - Rate limiting (token bucket), robots.txt compliance, retries with backoff, user-agent rotation
5. **Extensive Test Suite** - 208 tests including BI use-case integration tests
6. **15 Domain Templates** - Article, product, financial_data, job_listing, real_estate, recipe, etc.
7. **Rich Interactive Experience** - Questionary prompts, Rich tables, confidence scores, hints

### Notable Gaps or Unfinished Areas
1. **No Browser Automation** - Cannot handle JavaScript-rendered pages (Playwright/Selenium not integrated)
2. **No Parallel Extraction** - Single-threaded execution only
3. **Limited Sink Destinations** - CSV, JSON, SQLite, Parquet only; no PostgreSQL, MongoDB, S3, or webhooks
4. **No Scheduling/Orchestration** - No cron integration, job queuing, or cloud deployment patterns
5. **PyPI Not Published** - Package not yet on PyPI (`pip install quarry` not working)
6. **Plugin System Absent** - No extension API for custom connectors or transforms
7. **No Web UI** - CLI-only; no dashboard or visual schema builder

---

## 2. SWOT Analysis

### Strengths
- **Resilient Selector Engine** - Unique value prop: selectors survive CSS framework rebuilds (React CSS-in-JS, etc.) via structural/semantic strategies
- **Complete Pipeline** - End-to-end workflow from analysis to export, not just an extraction library
- **Framework Detection** - Automatic detection of 13+ frameworks enables smart defaults and selector suggestions
- **Interactive UX** - Rich terminal UI with confidence scores, hints, and smart prompts reduces guesswork
- **Strong Typing** - Pydantic schemas + mypy ensure reliability for production use
- **Test Coverage** - 208 tests with BI use-case scenarios provide confidence in core functionality
- **Template System** - 15 domain-specific templates accelerate common extraction tasks
- **Ethical Defaults** - Robots.txt compliance, rate limiting, and user-agent rotation built-in

### Weaknesses
- **No JS Rendering** - Cannot extract from SPAs that require JavaScript execution
- **Single-Threaded** - Performance bottleneck for large-scale extraction jobs
- **Limited Export Targets** - Missing database and cloud destinations (Postgres, S3)
- **Not Published to PyPI** - Requires source installation, limiting discoverability
- **Legacy Code Coexistence** - Both "wizard" (legacy job YAML) and "quarry tools" (new schema YAML) exist, causing conceptual overlap
- **Thin Documentation** - README is solid, but API reference and advanced usage guides are incomplete
- **No Plugin Architecture** - Cannot extend with custom connectors without modifying source

### Opportunities
- **Data Engineering Toolchains** - Position as an ETL "extract" stage that feeds dbt, Airflow, or data warehouses
- **Business Intelligence Workflows** - Templates for financial, market, and competitor data align with BI analyst needs
- **Open Source Community** - Python scraping community is active; a polished, opinionated tool can gain traction
- **Low-Code/No-Code Trend** - Interactive schema builder could evolve into a web-based UI for non-developers
- **Enterprise Compliance** - Built-in robots.txt and rate limiting appeal to companies with ethical scraping requirements

### Threats
- **Scrapy Dominance** - Mature ecosystem with Scrapy, Splash, Playwright integration; hard to displace for heavy users
- **Commercial Competitors** - Apify, Diffbot, ParseHub offer hosted solutions with JS rendering
- **AI Extraction** - LLM-based extraction (e.g., GPT-4 with vision) may commoditize simple scraping
- **Maintenance Burden** - 13+ framework profiles require ongoing updates as frameworks evolve
- **Adoption Risk** - If not published to PyPI soon, momentum may stall

---

## 3. Proposed Primary Use Case

### Use Case One-Liner
**A CLI toolkit for data analysts and engineers to build reproducible, resilient web extraction pipelines for structured business data (financial, e-commerce, news, government).**

### Target User(s)
1. **Data Engineers** - Building ETL pipelines that ingest web data into warehouses
2. **Business Intelligence Analysts** - Extracting competitor pricing, news feeds, or regulatory filings
3. **Research Teams** - Collecting structured datasets for academic or market research
4. **DevOps/SRE** - Running scheduled extraction jobs in containers or CI pipelines

### Core Scenario / User Journey
1. Analyst identifies a target website (e.g., SEC filings, competitor product pages)
2. Runs `quarry scout <url>` to detect structure and get selector suggestions
3. Uses `quarry survey create --template financial_data` to build a schema interactively
4. Tests with `quarry excavate schema.yml --url <url>` and iterates
5. Deploys as a scheduled job (cron/Airflow) with `quarry excavate schema.yml --url <url> -o /data/output.jsonl`
6. Pipes to `quarry polish --dedupe` and `quarry ship output.jsonl data.csv` for downstream consumption

### Why This Fits the Current Project
- **Templates exist** for financial, e-commerce, real estate, news—core BI domains
- **Resilient selectors** matter most for long-running data pipelines (sites update CSS frequently)
- **CLI-first design** fits engineering/analyst workflows (scripting, cron, CI/CD)
- **Existing test coverage** for BI use cases (`test_bi_use_cases.py`) validates this direction
- **Rate limiting and robots.txt** satisfy enterprise compliance needs

### How It Differentiates vs. Generic Templates/Boilerplates
- **Not a library; a workflow** - Complete pipeline from analysis to export, not just BeautifulSoup wrappers
- **Resilience as a feature** - Selector chain fallbacks and dynamic class detection are uncommon in open-source tools
- **Interactive schema builder** - Reduces guesswork compared to writing raw CSS selectors
- **Domain templates** - Pre-configured for BI use cases, not just generic "scrape this page"

---

## 4. Recommended Strategic Tweaks

### 4.1 Product & Feature Focus
- **Deprecate legacy wizard/job system** (`wizard.py`, job YAML format) in favor of the cleaner `ExtractionSchema` approach; remove conceptual overlap
- **Prioritize database sinks** - Add PostgreSQL and SQLite as first-class export targets for BI workflows
- **Add `--dry-run` to all tools** - Preview changes without writing, critical for production pipelines
- **Implement `quarry validate schema.yml`** - Pre-flight check for schemas before deployment
- **Consider minimal JS rendering** - A single optional `--render` flag using Playwright for JS-heavy pages (not full integration, just a fallback)

### 4.2 Architecture & Code Structure
- **Consolidate connectors and executor** - `GenericConnector` and `ExcavateExecutor` overlap; unify around `ExcavateExecutor`
- **Formalize `lib/` as public API** - Document `quarry.lib.http`, `quarry.lib.selectors`, `quarry.lib.schemas` for programmatic use
- **Add `quarry.api` module** - Clean Python API surface for calling from scripts without CLI
- **Remove `connectors/fda.py`, `connectors/nws.py`** - Site-specific connectors dilute the generic tool identity; move to `examples/`

### 4.3 UX, Routing, and Navigation
- **Rename `quarry scout` → `quarry analyze`** (or keep, but marketing as "analyze" is clearer)
- **Add `quarry status schema.yml`** - Show schema summary, last run, stats
- **Improve error messages** - Include actionable suggestions (e.g., "Selector `.foo` not found; try `quarry scout` to verify")
- **Streamline wizard entry** - `quarry` (no subcommand) should default to interactive wizard, not require `quarry init`

### 4.4 Documentation & Onboarding
- **Write "Getting Started for BI Analysts"** - Focused tutorial: scrape SEC filings or competitor products in 10 minutes
- **Publish API reference** - Auto-generate from docstrings using Sphinx/mkdocs
- **Add `examples/` for BI workflows** - Real-world YAML schemas for FDA, CFPB, financial news
- **Create TROUBLESHOOTING.md** - Common errors and fixes (selector failures, rate limiting, robots.txt blocks)

### 4.5 Testing, Observability, and Quality
- **Add Codecov integration** - Visible coverage badge increases trust
- **Enable strict mypy** for all modules (not just `framework_profiles/` and `http.py`)
- **Add performance benchmarks** - Test extraction speed for 100+ pages
- **Log structured JSON** - `--log-format json` for production pipelines

---

## 5. Strategic Handoff Document (For Coding Agents)

### 5.1 Objectives for Implementation Agents
- Implement and refine the project primarily as: **A CLI toolkit for reproducible, resilient web extraction pipelines for structured business data.**
- Prioritize the core scenario: **Analyst builds schema → runs extraction → exports to CSV/database.**

### 5.2 High-Priority Tasks (Order Matters)

#### 1. Publish to PyPI
- **Files**: `pyproject.toml`, add `README.md` as long description
- **Action**: `python -m build && twine upload dist/*`
- **Validation**: `pip install quarry` works from fresh venv

#### 2. Deprecate Legacy Job System
- **Files**: `quarry/wizard.py`, `quarry/core.py`, `jobs/*.yml`
- **Action**: Move `core.run_job()` logic to `quarry/tools/excavate/executor.py`, mark old APIs deprecated with warnings
- **Validation**: `quarry run job.yml` emits deprecation warning but still works

#### 3. Add PostgreSQL Sink
- **Files**: Create `quarry/sinks/postgres.py`, update `quarry/tools/ship/cli.py`
- **Action**: Implement `PostgresSink` using `psycopg2` or `sqlalchemy`
- **Validation**: `quarry ship data.jsonl --to postgres --connection "postgresql://..."` works

#### 4. Unify Connectors into Executor
- **Files**: `quarry/connectors/generic.py`, `quarry/tools/excavate/executor.py`
- **Action**: Merge `GenericConnector.collect()` logic into `ExcavateExecutor.fetch_url()`
- **Validation**: Remove `connectors/` imports from `core.py`

#### 5. Add `quarry validate` Command
- **Files**: Create `quarry/tools/validate/cli.py`
- **Action**: Load schema, check selectors against sample HTML, report errors
- **Validation**: `quarry validate schema.yml --url <url>` prints validation report

#### 6. Enable Strict mypy Across All Modules
- **Files**: `pyproject.toml` (`[tool.mypy]` section)
- **Action**: Set `disallow_untyped_defs = true` globally, fix type errors
- **Validation**: `mypy quarry/` passes with no errors

### 5.3 Medium-Priority Tasks

- **Move site-specific connectors to examples/** (`fda.py`, `nws.py`)
- **Add `--dry-run` flag to Excavate and Polish**
- **Write "BI Analyst Getting Started" guide** (`docs/GETTING_STARTED_BI.md`)
- **Add Codecov to GitHub Actions CI**
- **Implement minimal Playwright fallback** for `excavate --render`
- **Create `quarry.api` module** for programmatic access

### 5.4 Non-Goals / De-prioritized Work

- **Web UI / Dashboard** - Too large a scope; stay CLI-first for now
- **Distributed/Parallel Extraction** - Valuable but complex; defer to post-2.0
- **Full Playwright Integration** - Optional minimal fallback only, not a core feature
- **Plugin System** - Nice-to-have, but focus on core pipeline first
- **Cloud Sinks (S3, GCS)** - Lower priority than Postgres for BI workflows

### 5.5 Constraints, Assumptions, and Notes

**Assumptions:**
- Target users are comfortable with CLI and YAML configuration
- Extraction jobs are moderate scale (hundreds to low thousands of pages, not millions)
- Primary export destinations are local files, SQLite, or Postgres

**Constraints:**
- Maintain Python 3.11+ compatibility
- Keep core dependencies minimal (avoid heavy frameworks)
- Preserve backward compatibility for `ExtractionSchema` YAML format

**Risks to Watch:**
- Framework profile maintenance as CSS frameworks evolve
- Selector fragility for highly dynamic SPAs (JS rendering may be necessary)
- PyPI name conflict (check `quarry` availability; have fallback names ready)

**Tech Decisions to Preserve:**
- Pydantic for schema validation (do not replace)
- BeautifulSoup for HTML parsing (do not replace with lxml unless performance-critical)
- Rich for terminal UI (excellent UX, keep it)
- Click for CLI routing (stable, well-integrated)

---

## Appendix: Project Structure Reference

```
quarry/
├── lib/                     # Shared libraries
│   ├── http.py             # HTTP client with rate limiting
│   ├── selectors.py        # CSS selector utilities
│   ├── schemas.py          # Pydantic schema definitions
│   ├── ratelimit.py        # Token bucket rate limiter
│   └── robots.py           # Robots.txt parser
├── tools/                   # CLI tools
│   ├── scout/              # HTML analysis
│   ├── survey/             # Schema designer
│   ├── excavate/           # Extraction engine
│   ├── polish/             # Data transformation
│   └── ship/               # Data export
├── framework_profiles/      # Framework detection (13+ profiles)
├── connectors/             # Data source connectors (legacy)
├── transforms/             # Data transformations
└── sinks/                  # Output writers
```

---

**End of Strategic Positioning Report**
