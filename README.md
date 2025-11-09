# ScrapeSuite

A reusable Python toolkit for web/data collection with offline-first testing.

**👉 New here? Start with [FIRST_RUN.md](FIRST_RUN.md) for a 60-second demo.**

**🚀 Want to scrape ANY website? Check out [WIZARD_USAGE.md](WIZARD_USAGE.md) for the interactive wizard guide.**

ScrapeSuite is a production-quality library and CLI for defining scraping jobs in YAML, running connectors with retry/backoff and rate limits, transforming raw records into normalized tables, and writing outputs to sinks (Parquet/CSV). It maintains idempotent state in SQLite for per-job cursors and deduplication.

---

## Quick Links

- **[FIRST_RUN.md](FIRST_RUN.md)** - 60-second demo for new users
- **[WIZARD_USAGE.md](WIZARD_USAGE.md)** - ⭐ **Create custom scrapers for ANY website with the interactive wizard**
- **[QUICKSTART.md](QUICKSTART.md)** - Complete guide with examples
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Built-in diagnostic commands
- **[examples/jobs/](examples/jobs/)** - Pre-built job templates

---

## Features

- **Interactive wizard**: Generate custom scrapers for ANY website through guided prompts - no coding required!
- **Generic connector**: YAML-driven extraction using CSS selectors works with any site
- **YAML job definitions**: Declarative job specs with source, transform, and sink configuration
- **Offline-first testing**: All tests run with local HTML fixtures (no network required)
- **Polite HTTP**: Built-in per-domain rate limiting with token bucket algorithm
- **Robots.txt support**: Automatic parsing and caching of robots.txt with 24-hour TTL
- **Smart retry logic**: Exponential backoff with jitter, adaptive throttling on 429/503 errors
- **State management**: SQLite-based cursor tracking, idempotent deduplication, and failed URL tracking
- **Type-safe**: Full type hints, pyright-strict compatible
- **Multiple output formats**: Parquet, CSV, and JSONL sinks

## Installation

```bash
pip install -r requirements.txt
```

## Quickstart

### 1. Create a job with the wizard

```bash
make init
# Or: python -m scrapesuite.cli init
```

Follow the prompts to generate a job YAML file in `jobs/`.

### 2. Run a job offline (with fixtures)

```bash
make run-fda
# Or: python -m scrapesuite.cli run jobs/fda.yml --offline true --max-items 100
```

### 3. Run all jobs

```bash
python -m scrapesuite.cli run-all --offline true
```

### 4. Check job state

```bash
python -m scrapesuite.cli state
```

## Example Job YAML

```yaml
version: "1.0"
job: fda_recalls

source:
  parser: fda_list
  entry: https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts

transform:
  pipeline:
    - normalize: fda_recalls

sink:
  kind: parquet
  path: data/cache/{job}/%Y%m%dT%H%M%SZ.parquet

policy:
  allowlist:
    - fda.gov
  
  # Default rate limit (requests per second)
  default_rps: 1.0
  
  # Per-domain rate limits (override default)
  rate_limits:
    fda.gov: 2.0          # 2 requests/sec to FDA
    api.fda.gov: 3.0      # 3 requests/sec for API
    weather.gov: 0.5      # 0.5 requests/sec for weather.gov
```

**Note**: robots.txt checking is automatic. ScrapeSuite will:
- Fetch and cache robots.txt per domain (24-hour TTL)
- Match against User-Agent directives
- Respect Disallow rules
- Honor Crawl-delay as minimum rate limit

## Development

```bash
# Format code
make fmt

# Lint
make lint

# Run tests
make test

# Build batches (offline)
make build-batches
```

## Policy and Live Mode

When running in live mode (`--offline false`), ScrapeSuite enforces:

- **Allowlist**: All outbound URLs must be in the `policy.allowlist` (required for live mode)
- **Per-domain rate limiting**: Token bucket algorithm with configurable rates per domain
- **Robots.txt compliance**: Automatic fetching, parsing, and caching with User-Agent matching
- **Smart retry**: Exponential backoff with jitter; 3x wait time for 429/503 rate limit errors
- **Failed URL tracking**: SQLite table logs all failed fetches with error messages and retry counts

**Important**: Always test jobs offline first using fixtures. Live mode should only be used after careful review of the allowlist and rate limits.

## Error Handling

ScrapeSuite tracks failed URLs in SQLite:

```python
from scrapesuite import get_failed_urls

# Get all failed URLs for a job
failures = get_failed_urls("fda_recalls")
for failure in failures:
    print(f"{failure['url']}: {failure['error_message']} (retries: {failure['retry_count']})")
```

Failed URLs are automatically recorded with:
- URL that failed
- Error message
- Retry count (incremented on each failure)
- Last attempt timestamp

## License

[Add your license here]


