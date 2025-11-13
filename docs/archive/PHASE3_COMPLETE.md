# Phase 3 Complete: Excavate Extraction Engine ✅

## Summary

Phase 3 of the Quarry suite is complete. The **Excavate** tool is a schema-driven extraction engine that pulls structured data from web pages using Survey schemas.

## What Was Built

### 1. Core Components

- **`quarry/tools/excavate/parser.py`**: SchemaParser class
  - Parses HTML using ExtractionSchema definitions
  - Extracts text or attribute values
  - Handles required/optional fields
  - Validates item completeness

- **`quarry/tools/excavate/executor.py`**: ExcavateExecutor class
  - Orchestrates extraction workflow
  - Supports pagination (URL-based)
  - Handles metadata injection
  - Exports to JSONL format
  - Tracks extraction statistics

- **`quarry/tools/excavate/cli.py`**: Click-based CLI
  - `excavate` command with options:
    - `--url`: Extract from URL
    - `--file`: Extract from local HTML file
    - `--output`: Output file path
    - `--max-pages`: Limit pagination
    - `--no-metadata`: Exclude metadata
    - `--pretty`: Pretty-print output

### 2. Features

✅ **Schema-Driven Extraction**
- Uses Survey schemas (YAML format)
- Supports CSS selectors
- Handles text and attribute extraction
- Required/optional field validation

✅ **Pagination Support**
- Follows next-page links automatically
- Configurable max pages
- Rate limiting between pages

✅ **Metadata Tracking**
- Source URL
- Extraction timestamp
- Schema name

✅ **JSONL Output**
- One JSON object per line
- Streamable format
- Compatible with downstream tools

✅ **Local File Support**
- Extract from HTML files for testing
- Bypasses HTTP client for local files

### 3. Testing

Created comprehensive test suite (`tests/test_forge.py`):
- 14 unit tests covering:
  - Basic field extraction
  - Nested selectors
  - Missing optional fields
  - Required field validation
  - Attribute extraction
  - Empty/malformed HTML handling
  - Metadata inclusion
  - Statistics tracking
  - Real fixture file integration

**Test Results**: 14/14 passing ✅  
**Total Suite**: 152/152 passing ✅

### 4. Integration

- Integrated into `quarry/quarry.py` main CLI
- Works with Survey schemas
- Ready for Polish (Phase 4) integration

## Usage Examples

### Basic Extraction

```bash
# From URL (with schema URL)
quarry excavate schema.yml

# From specific URL
quarry excavate schema.yml --url https://example.com

# From local file
quarry excavate schema.yml --file page.html --output data.jsonl
```

### With Pagination

```bash
# Extract up to 10 pages
quarry excavate schema.yml --max-pages 10
```

### Without Metadata

```bash
# Clean output without _meta field
quarry excavate schema.yml --no-metadata
```

## Example Schema

```yaml
name: fda_recalls
description: Extract FDA food recalls
version: 1

url: https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts
item_selector: ul.fda-recalls > li

fields:
  title:
    selector: h3.headline
    required: true
  
  link:
    selector: a
    attribute: href
  
  date:
    selector: time.published
    attribute: datetime

pagination:
  next_selector: a.pagination__next
  max_pages: 50
  wait_seconds: 2.0
```

## Example Output

```jsonl
{"title": "Acme Foods allergy alert", "link": "/safety/recalls/acme-foods", "date": "2024-01-15", "_meta": {"url": "https://example.com", "fetched_at": "2024-01-15T10:30:00", "schema": "fda_recalls"}}
{"title": "Contoso Dairy recall", "link": "/safety/recalls/contoso-dairy", "date": "2024-01-14", "_meta": {"url": "https://example.com", "fetched_at": "2024-01-15T10:30:01", "schema": "fda_recalls"}}
```

## Pipeline Status

| Phase | Tool | Status |
|-------|------|--------|
| 0 | Foundation | ✅ Complete (117 tests) |
| 1 | **Scout** | ✅ Complete (6 tests) |
| 2 | **Survey** | ✅ Complete (15 tests) |
| 3 | **Excavate** | ✅ Complete (14 tests) |
| 4 | Polish | ⏳ Next |
| 5 | Ship | ⏳ Pending |

## Data Flow

```
HTML → Scout → analysis.json
         ↓
    Survey → schema.yml
         ↓
      Excavate → data.jsonl
         ↓
     Polish → clean_data.jsonl
         ↓
      Ship → destinations (CSV/DB/API)
```

## Next Steps

**Phase 4: Polish Tool** (Data transformation)
- Deduplication
- Field transformations
- Data enrichment
- Validation
- Filtering

## Files Changed

**Created**:
- `quarry/tools/excavate/parser.py` (150 LOC)
- `quarry/tools/excavate/executor.py` (120 LOC)
- `quarry/tools/excavate/cli.py` (140 LOC)
- `quarry/tools/excavate/__init__.py` (10 LOC)
- `tests/test_forge.py` (390 LOC)

**Modified**:
- `quarry/quarry.py` (integrated excavate command)

## Statistics

- **Lines of Code**: ~810 LOC
- **Test Coverage**: 14 comprehensive tests
- **Success Rate**: 100% (14/14 tests passing)
- **Total Suite**: 152 tests passing (100%)
