# 🚀 First Run - Quick Demo

**See Quarry in action in 60 seconds.**

## Step 1: Run the Example

```bash
python -m quarry.cli run examples/jobs/fda.yml --offline --max-items 10
```

You should see:
```
fda_recalls: 6 new, 3 in batch, next_cursor=acme-foods...
```

## Step 2: See What You Got

```bash
# View job state
python -m quarry.cli state

# Find the output file
ls -lh data/cache/fda/

# Peek at the data
python -c "
import pandas as pd
import glob
file = sorted(glob.glob('data/cache/fda/*.parquet'))[-1]
df = pd.read_parquet(file)
print(df[['id', 'title', 'url']].head())
print(f'\nTotal: {len(df)} records')
"
```

## Step 3: Create Your Own Job

```bash
python -m quarry.cli init
```

Follow the prompts to create a job in `jobs/YOUR_JOB.yml`.

## Step 4: Run Your Job

```bash
# Test offline first (uses fixtures if available)
python -m quarry.cli run jobs/YOUR_JOB.yml --offline

# Then try live mode (careful! hits real URLs)
python -m quarry.cli run jobs/YOUR_JOB.yml --live --max-items 5
```

## What Just Happened?

1. **Scraped data** from FDA website (using cached HTML fixture)
2. **Normalized** it into a clean table
3. **Deduplicated** by item ID
4. **Wrote to Parquet** with timestamp
5. **Tracked state** in SQLite (cursor + seen items)

## Available Parsers

- `fda_list` - FDA recalls
- `nws_list` - Weather alerts  
- `custom_list` - Generic HTML list

## Next Steps

- Read [QUICKSTART.md](QUICKSTART.md) for full guide
- Check [examples/jobs/](examples/jobs/) for more examples
- Read [README.md](README.md) for API details

## Common Issues

**Can't find output?**
```bash
find data/cache -name "*.parquet" -mtime -1
```

**Want to see raw HTML being parsed?**
```bash
cat tests/fixtures/fda_list.html
```

**Want to customize the job?**
```bash
cat examples/jobs/fda_advanced.yml  # Shows all options
```
