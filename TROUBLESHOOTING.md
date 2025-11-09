# Troubleshooting Guide

ScrapeSuite includes built-in troubleshooting commands to help diagnose issues.

## Quick Diagnostics

### Check Robots.txt Compliance

Before scraping a URL, check if it's allowed:

```bash
python -m scrapesuite.cli check-robots https://example.com/page
```

**Output shows:**
- ✅/❌ Whether the URL is allowed
- Crawl-delay directive (minimum wait between requests)
- User-Agent being checked

**Example:**
```bash
$ python -m scrapesuite.cli check-robots https://github.com/explore

        Robots.txt Check: github.com
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property    ┃ Value                      ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ URL         │ https://github.com/explore │
│ User-Agent  │ ScrapeSuite                │
│ Allowed     │ ✅ YES                     │
│ Crawl-delay │ 1.0s                       │
└─────────────┴────────────────────────────┘
```

**Custom User-Agent:**
```bash
python -m scrapesuite.cli check-robots https://example.com -ua "MyBot/1.0"
```

---

### Inspect Job Configuration

Validate a job YAML without running it:

```bash
python -m scrapesuite.cli inspect jobs/my_job.yml
```

**Shows:**
- Job name, version, parser
- Entry URL and sink configuration
- Rate limits and allowlist
- ⚠️ Configuration warnings (missing allowlist, high rates, etc.)

**Example:**
```bash
$ python -m scrapesuite.cli inspect examples/jobs/fda_advanced.yml

          Job Inspection: examples/jobs/fda_advanced.yml
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Property      ┃ Value                         ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Job Name      │ fda_recalls_advanced          │
│ Parser        │ fda_list                      │
│ Allowlist     │ fda.gov                       │
│ Default RPS   │ 1.0                           │
│   fda.gov     │ 2.0 req/sec                   │
└───────────────┴───────────────────────────────┘

Validation:
✅ No issues found
```

---

### View Failed URLs

See which URLs failed to fetch and why:

```bash
# All failed URLs
python -m scrapesuite.cli failed

# Failures for specific job
python -m scrapesuite.cli failed fda_recalls
```

**Shows:**
- URL that failed
- Error message
- Retry count (how many times it failed)
- Last attempt timestamp

**Example:**
```bash
$ python -m scrapesuite.cli failed

                  All Failed URLs
┏━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Job    ┃ URL          ┃ Error       ┃ Retries ┃ Last       ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━┩
│ my_job │ example.com… │ Timeout     │       3 │ 2025-11-09 │
│ my_job │ example.com… │ HTTP 404    │       1 │ 2025-11-09 │
└────────┴──────────────┴─────────────┴─────────┴────────────┘

Total failed URLs: 2
```

---

### Check Cache Status

View what's cached in SQLite:

```bash
python -m scrapesuite.cli cache-info
```

**Shows:**
- Robots.txt cache (domains, crawl-delays, timestamps)
- Cached items per job

**Example:**
```bash
$ python -m scrapesuite.cli cache-info

Cache Information

Robots.txt Cache: 2 domains
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ Domain     ┃ Crawl-delay ┃ Cached At         ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ github.com │ 1.0s        │ 2025-11-09T03:48  │
│ reddit.com │ 0.0s        │ 2025-11-09T04:01  │
└────────────┴─────────────┴───────────────────┘

Cached Items:
┏━━━━━━━━━━━━━┳━━━━━━━┓
┃ Job         ┃ Items ┃
┡━━━━━━━━━━━━━╇━━━━━━━┩
│ fda_recalls │     6 │
└─────────────┴───────┘
```

---

## Common Issues

### Issue: "Domain not in allowlist"

**Symptom:** Error when running in live mode

```
Error: Domain not in allowlist for live mode: example.com
```

**Fix:** Add domain to job YAML:

```yaml
policy:
  allowlist:
    - example.com
```

---

### Issue: "Unknown parser 'xyz'"

**Symptom:** Error loading job YAML

```
Error: Unknown parser 'xyz'. Available: fda_list, nws_list, custom_list
```

**Fix:** Use one of the available parsers:
- `fda_list` - FDA recalls
- `nws_list` - Weather alerts
- `custom_list` - Generic HTML

---

### Issue: No output files created

**Check:**

```bash
# Find recent output
find data/cache -name "*.parquet" -mtime -1

# Check job state
python -m scrapesuite.cli state

# Inspect configuration
python -m scrapesuite.cli inspect jobs/your_job.yml
```

**Common causes:**
- Empty result set (max_items too low)
- Wrong parser for HTML structure
- Offline mode but no fixtures

---

### Issue: Rate limit errors (429/503)

**Symptom:** Frequent HTTP 429 or 503 errors

**Fix 1:** Lower rate limit in YAML:

```yaml
policy:
  default_rps: 0.5  # Slower = more polite
```

**Fix 2:** Check robots.txt crawl-delay:

```bash
python -m scrapesuite.cli check-robots https://example.com
```

If crawl-delay is 2.0s, use `default_rps: 0.5` (1/2 = 0.5)

---

### Issue: Robots.txt blocking

**Symptom:** URL shows ❌ NO when checking

```bash
$ python -m scrapesuite.cli check-robots https://reddit.com/r/python
⚠️  This URL is disallowed by robots.txt
```

**Options:**
1. **Respect it** - Don't scrape that URL
2. **Check alternative paths** - Different URL might be allowed
3. **Contact site owner** - Request permission

---

### Issue: High retry counts

**Symptom:** Same URL failing repeatedly

```bash
python -m scrapesuite.cli failed
# Shows: example.com/page - Retries: 15
```

**Fix:**
- Check if URL is valid (maybe it's a 404)
- Check if site is blocking your User-Agent
- Lower rate limit (might be getting throttled)
- Verify allowlist includes the domain

---

## Debug Mode

Run with verbose output:

```bash
# Run and see detailed timing
python -m scrapesuite.cli run jobs/my_job.yml --offline -n 5

# Check state immediately after
python -m scrapesuite.cli state
python -m scrapesuite.cli failed my_job
```

---

## Clear Cache

**Clear robots.txt cache:**
```bash
rm data/cache/robots.sqlite
```

**Clear job state:**
```bash
rm data/cache/state.sqlite
```

**Clear all output:**
```bash
rm -rf data/cache/*/
```

**Caution:** This deletes all scraped data and state!

---

## Getting More Help

1. **Inspect your job:** `python -m scrapesuite.cli inspect jobs/your_job.yml`
2. **Check robots.txt:** `python -m scrapesuite.cli check-robots YOUR_URL`
3. **View failures:** `python -m scrapesuite.cli failed`
4. **Check cache:** `python -m scrapesuite.cli cache-info`
5. **Read the logs:** Output shows success/failure for each run

All commands have `--help`:

```bash
python -m scrapesuite.cli check-robots --help
python -m scrapesuite.cli inspect --help
python -m scrapesuite.cli failed --help
```
