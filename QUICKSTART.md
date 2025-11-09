# ScrapeSuite Quickstart Guide

**Get scraping in 2 minutes.**

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

## Your First Scrape (30 seconds)

Run a pre-built example offline (no network, uses cached HTML):

```bash
python -m scrapesuite.cli run examples/jobs/fda.yml --offline
```

**Output:**
- ✅ Scrapes FDA recall data from cached HTML fixture
- ✅ Writes to `data/cache/fda_recalls/TIMESTAMP.parquet`
- ✅ Tracks state in SQLite (`data/cache/state.sqlite`)

**What just happened?**
- Parsed HTML using BeautifulSoup
- Normalized data into a DataFrame
- Deduplicated by item ID
- Wrote to Parquet file with timestamp

## See What You Got

```bash
# Show output files
ls -lh data/cache/fda_recalls/

# Inspect the data (requires pandas)
python -c "
import pandas as pd
import glob
latest = sorted(glob.glob('data/cache/fda_recalls/*.parquet'))[-1]
df = pd.read_parquet(latest)
print(df.head())
print(f'\nTotal records: {len(df)}')
"

# Check job state
python -m scrapesuite.cli state
```

## Available Parsers (Connectors)

ScrapeSuite has 3 built-in parsers:

| Parser | Description | Example URL |
|--------|-------------|-------------|
| `fda_list` | FDA recalls list page | https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts |
| `nws_list` | NWS weather alerts | https://www.weather.gov/alerts |
| `custom_list` | Generic HTML list parser | Any list/table HTML |

## Create Your Own Job

Interactive wizard guides you:

```bash
python -m scrapesuite.cli init
```

**Prompts you for:**
- Job name
- Source URL
- Which parser to use
- Output format (Parquet, CSV, JSONL)
- Rate limits

**Generates:** `jobs/YOUR_JOB.yml`

## Job YAML Structure

```yaml
version: "1.0"
job: my_scrape_job

source:
  parser: custom_list        # Which parser to use
  entry: https://example.com # Starting URL

transform:
  pipeline:
    - normalize: custom      # Data transformation

sink:
  kind: parquet              # Output format: parquet, csv, jsonl
  path: data/cache/{job}/%Y%m%dT%H%M%SZ.parquet

policy:
  allowlist:                 # Only scrape these domains (live mode)
    - example.com
  
  default_rps: 1.0           # Default: 1 request/second
  
  rate_limits:               # Per-domain overrides
    api.example.com: 3.0     # 3 req/sec for API
```

## Offline vs Live Mode

**Offline (default, safe):**
- Uses local HTML fixtures from `tests/fixtures/`
- No network requests
- Fast, repeatable testing
- Can't scrape new URLs

```bash
python -m scrapesuite.cli run jobs/my_job.yml --offline
```

**Live (careful, hits real URLs):**
- Makes actual HTTP requests
- Respects robots.txt automatically
- Enforces rate limits
- Requires allowlist in job YAML

```bash
python -m scrapesuite.cli run jobs/my_job.yml --live
```

## Advanced Features

### Per-Domain Rate Limiting

```yaml
policy:
  default_rps: 1.0
  rate_limits:
    fast-api.com: 5.0     # 5 req/sec
    slow-site.com: 0.5    # 1 req every 2 sec
```

Uses token bucket algorithm with independent buckets per domain.

### Robots.txt Compliance

**Automatic in live mode!**
- Fetches robots.txt per domain
- Caches for 24 hours
- Matches User-Agent directives
- Respects Crawl-delay

Check what's cached:

```bash
python -c "
from scrapesuite.robots import RobotsCache
cache = RobotsCache()
is_ok = cache.is_allowed('https://github.com/explore', 'ScrapeSuite')
delay = cache.get_crawl_delay('github.com')
print(f'Allowed: {is_ok}, Crawl-delay: {delay}s')
"
```

### Failed URL Tracking

Automatically logs failures to SQLite:

```python
from scrapesuite import get_failed_urls

failures = get_failed_urls('my_job')
for f in failures:
    print(f"{f['url']}: {f['error_message']} (×{f['retry_count']})")
```

## Common Commands

```bash
# Run one job offline
python -m scrapesuite.cli run jobs/fda.yml --offline

# Run one job live (careful!)
python -m scrapesuite.cli run jobs/fda.yml --live --max-items 10

# Run all jobs in jobs/ directory
python -m scrapesuite.cli run-all --offline

# Create new job interactively
python -m scrapesuite.cli init

# View job state
python -m scrapesuite.cli state

# Batch scrape URL list
python -m scrapesuite.cli batch urls.txt output.jsonl --offline
```

## Troubleshooting Commands

```bash
# Check if a URL is allowed by robots.txt
python -m scrapesuite.cli check-robots https://github.com/explore

# Inspect a job without running it
python -m scrapesuite.cli inspect jobs/my_job.yml

# View failed URLs for a job
python -m scrapesuite.cli failed fda_recalls

# Show cache information
python -m scrapesuite.cli cache-info
```

## Output Formats

| Format | Extension | Use Case |
|--------|-----------|----------|
| **Parquet** | `.parquet` | Analytics, big data (default) |
| **CSV** | `.csv` | Excel, spreadsheets |
| **JSONL** | `.jsonl` | APIs, streaming, text processing |

Change in job YAML:

```yaml
sink:
  kind: jsonl  # or csv, parquet
  path: data/cache/{job}/%Y%m%dT%H%M%SZ.jsonl
```

## What's Next?

1. **Try the examples:**
   - `examples/jobs/fda.yml` - FDA recalls
   - `examples/jobs/nws.yml` - Weather alerts
   - `examples/jobs/fda_advanced.yml` - Shows all policy options

2. **Create your own job:**
   - Use `init` wizard
   - Test offline first
   - Review allowlist carefully
   - Run live with `--max-items 5` first

3. **Explore the Python API:**
   ```python
   from scrapesuite import run_job
   
   job_dict = {...}  # Load from YAML
   df, next_cursor = run_job(job_dict, offline=True)
   print(df.head())
   ```

4. **Check the docs:**
   - Full README: [README.md](README.md)
   - Example jobs: [examples/jobs/](examples/jobs/)
   - Tests for examples: [tests/](tests/)

## Getting Help

**Something not working?**

1. Check job state: `python -m scrapesuite.cli state`
2. Look at test examples: `tests/test_run_job.py`
3. Verify YAML syntax: `cat jobs/yourjob.yml`
4. Run in offline mode first to test logic

**Common errors:**
- `Unknown parser 'xyz'` → Use `fda_list`, `nws_list`, or `custom_list`
- `Domain not in allowlist` → Add domain to `policy.allowlist` for live mode
- `ModuleNotFoundError` → Run `pip install -e .`
