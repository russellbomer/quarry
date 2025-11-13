# Quarry 2.0: Architecture & Implementation Plan

**Date:** November 11, 2025  
**Version:** 2.0 (Refactor from v1.0)  
**Strategy:** Refactor existing codebase (70% reuse)

---

## Table of Contents

1. [Product Vision](#product-vision)
2. [Architecture Survey](#architecture-survey)
3. [Integration Map](#integration-map)
4. [Implementation Roadmap](#implementation-roadmap)
5. [Success Criteria](#success-criteria)

---

## Product Vision

### Overview

Quarry 2.0 is a **suite of 5 integrated CLI tools** for intelligent web scraping. Each tool:
- **Works independently** (useful on its own)
- **Chains together** (seamless data flow)
- **Implies workflow** (numbered sequence: inspect → design → fetch → transform → export)
- **Prioritizes simplicity** (focused responsibility, clear interfaces)

### The 5 Tools

```
scrape inspect   → Analyze HTML structure, detect frameworks
scrape design    → Build extraction schemas interactively
scrape fetch     → Execute extraction at scale
scrape transform → Clean, validate, enrich data
scrape export    → Output to any destination
```

### Data Flow

```
HTML → [inspect] → analysis.json
                       ↓
                  [design] → schema.yml
                       ↓
URLs + schema → [fetch] → raw.jsonl
                       ↓
                 [transform] → clean.jsonl
                       ↓
                  [export] → CSV/DB/API/etc.
```

### Standard Data Format

**Primary:** JSONL (JSON Lines)
- One JSON object per line
- Streamable, appendable
- Works with Unix pipes
- Schema-flexible

**Alternative:** JSON, CSV, Parquet (as needed by specific tools)

---

## Architecture Survey

### Directory Structure (Target)

```
quarry/
├── lib/                          # Shared libraries (extracted from current code)
│   ├── __init__.py
│   ├── http.py                   # HTTP client with retry/rate limiting (KEEP AS-IS)
│   ├── ratelimit.py              # Token bucket rate limiter (KEEP AS-IS)
│   ├── selectors.py              # Selector building (from selector_builder.py)
│   ├── parsing.py                # HTML parsing utilities (NEW)
│   ├── state.py                  # State management (REFACTOR from state.py)
│   └── schemas.py                # Schema loading/validation (NEW)
│
├── framework_profiles/           # Framework detection (KEEP AS-IS)
│   ├── __init__.py              # 13 profiles, well-tested
│   ├── base.py
│   ├── css/
│   ├── cms/
│   ├── frameworks/
│   ├── ecommerce/
│   └── universal/
│
├── tools/                        # The 5 tools (NEW STRUCTURE)
│   ├── __init__.py
│   │
│   ├── inspect/                  # Tool 1: HTML Analysis
│   │   ├── __init__.py
│   │   ├── analyzer.py          # From inspector.py
│   │   ├── reporter.py          # JSON/terminal output (NEW)
│   │   └── cli.py               # Subcommand entry point
│   │
│   ├── design/                   # Tool 2: Schema Builder
│   │   ├── __init__.py
│   │   ├── builder.py           # Interactive schema builder (NEW)
│   │   ├── validator.py         # Schema validation (NEW)
│   │   ├── preview.py           # Live extraction preview (NEW)
│   │   └── cli.py
│   │
│   ├── fetch/                    # Tool 3: Extraction Engine
│   │   ├── __init__.py
│   │   ├── executor.py          # Schema execution (REFACTOR from core.py)
│   │   ├── parser.py            # HTML parsing (from connectors/)
│   │   ├── pagination.py        # Auto-pagination (NEW)
│   │   ├── progress.py          # Progress tracking (NEW)
│   │   └── cli.py
│   │
│   ├── transform/                # Tool 4: Data Pipeline
│   │   ├── __init__.py
│   │   ├── pipeline.py          # Pipeline executor (NEW)
│   │   ├── validators.py        # Data validation (NEW)
│   │   ├── transformers.py      # Data transformations (EXPAND transforms/)
│   │   ├── enrichers.py         # Data enrichment (NEW)
│   │   └── cli.py
│   │
│   └── export/                   # Tool 5: Multi-Sink Output
│       ├── __init__.py
│       ├── exporter.py          # Export orchestrator (NEW)
│       ├── sinks/               # Output adapters
│       │   ├── __init__.py
│       │   ├── files.py         # CSV, JSON, Parquet (from sinks/)
│       │   ├── databases.py     # SQL, MongoDB (NEW)
│       │   ├── apis.py          # Webhooks, REST (NEW)
│       │   ├── cloud.py         # S3, GCS, BigQuery (NEW)
│       │   └── streaming.py     # Kafka, RabbitMQ (NEW)
│       └── cli.py
│
├── cli.py                        # Main CLI dispatcher (REWRITE)
├── __init__.py
└── __main__.py
```

### Module Dependencies

```
┌─────────────────────────────────────────────────┐
│                   CLI Layer                     │
│  (cli.py dispatches to tool subcommands)        │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│                  Tool Layer                     │
│  inspect / design / fetch / transform / export  │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│               Library Layer                     │
│  http / ratelimit / selectors / parsing / etc.  │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│           Framework Profiles Layer              │
│  (framework detection, field hints)             │
└─────────────────────────────────────────────────┘
```

**Dependency Rules:**
- Tools can depend on: lib/, framework_profiles/
- Tools CANNOT depend on: other tools
- lib/ can depend on: framework_profiles/
- framework_profiles/ has no dependencies (self-contained)

---

## Integration Map

### What to Keep, Refactor, Replace

#### ✅ **KEEP AS-IS** (36% - 2,685 LOC)

**http.py → lib/http.py**
- **Why:** Just enhanced with robots.txt improvements, production-ready
- **Changes:** Move to lib/, no code changes
- **Functions:** `get_html()`, `create_session()`, `_check_robots_txt()`, `_prompt_robots_override()`
- **Used by:** fetch, inspect

**ratelimit.py → lib/ratelimit.py**
- **Why:** Battle-tested token bucket implementation
- **Changes:** Move to lib/, no code changes
- **Classes:** `TokenBucket`, `DomainRateLimiter`
- **Used by:** fetch (via http.py)

**selector_builder.py → lib/selectors.py**
- **Why:** Robust selector generation, already modular
- **Changes:** Move to lib/, rename file
- **Functions:** `build_robust_selector()`, `simplify_selector()`
- **Used by:** design, inspect

**framework_profiles/ → framework_profiles/**
- **Why:** 13 profiles, significant IP, well-architected
- **Changes:** None - stays in place
- **Profiles:** Bootstrap, Tailwind, React, Vue, Django, Next.js, WordPress, Drupal, Shopify, WooCommerce, Schema.org, OpenGraph, Twitter Cards
- **Used by:** inspect, design, fetch

---

#### 🔧 **REFACTOR** (34% - 2,530 LOC)

**inspector.py → tools/inspect/analyzer.py**
- **Keep:**
  - `inspect_html()` - page statistics
  - `find_item_selector()` - container detection
  - `generate_field_selector()` - field generation
- **Extract:**
  - Move HTML analysis logic to analyzer.py
  - Keep BeautifulSoup utilities
- **Remove:**
  - Wizard-specific coupling
  - Duplicate logic from detection_strategies.py
- **New home:** `tools/inspect/analyzer.py`
- **Used by:** inspect tool, design tool (for suggestions)

**state.py → lib/state.py**
- **Keep:**
  - `open_db()` - SQLite connection
  - `upsert_items()` - item deduplication
  - Cursor management concepts
- **Refactor:**
  - Decouple from job-centric model
  - Generic state management (not just jobs)
  - Support incremental scraping
- **New interface:**
  ```python
  class StateManager:
      def __init__(self, db_path: str)
      def get_cursor(self, key: str) -> str | None
      def set_cursor(self, key: str, value: str)
      def has_item(self, key: str, item_id: str) -> bool
      def add_item(self, key: str, item: dict)
  ```
- **Used by:** fetch (incremental mode)

**sinks/ → tools/export/sinks/files.py**
- **Keep:**
  - CSVSink, JSONLSink, ParquetSink (all working)
- **Extend:**
  - Add ExcelSink, SQLiteSink
  - Standardize interface
- **New interface:**
  ```python
  class Sink(Protocol):
      def write(self, records: Iterable[dict]) -> int
      def close(self) -> None
  ```
- **Used by:** export tool

**connectors/ → tools/fetch/parser.py**
- **Keep:**
  - HTML parsing logic
  - Field extraction concepts
- **Remove:**
  - Connector-specific code (FDA, NWS are too specific)
  - Tight coupling to old job model
- **Refactor into:**
  - `SchemaParser` - executes schema.yml against HTML
  - Generic, not site-specific
- **New interface:**
  ```python
  class SchemaParser:
      def __init__(self, schema: dict)
      def parse(self, html: str) -> list[dict]
  ```
- **Used by:** fetch tool

**transforms/ → tools/transform/transformers.py**
- **Keep:**
  - Basic normalization functions
  - DataFrame conversion concepts
- **Expand significantly:**
  - Add validation, deduplication, filtering
  - Add enrichment (sentiment, classification)
  - Pipeline execution
- **New modules:**
  - `validators.py` - field validation
  - `transformers.py` - data transformations
  - `enrichers.py` - data enrichment
  - `pipeline.py` - pipeline executor
- **Used by:** transform tool

**detection_strategies.py → lib/parsing.py**
- **Keep:**
  - `detect_by_table_headers()` - useful heuristic
  - `detect_by_semantic_structure()` - HTML5 patterns
- **Refactor:**
  - Merge with inspector.py logic
  - Remove duplication
  - Cleaner API
- **Used by:** design tool (field suggestions)

---

#### ❌ **REPLACE** (30% - 2,319 LOC)

**wizard.py → tools/design/builder.py**
- **Why replace:** Tightly coupled to old monolithic workflow
- **What to salvage:**
  - Interactive prompt patterns (`_prompt_text`, `_prompt_select`)
  - URL validation logic
  - HTML preview/pasting
- **New approach:**
  - Focused on schema building only
  - Uses inspect output as input
  - Live preview of extraction
  - Generates schema.yml, not job.yml
- **New module:** `tools/design/builder.py` (800 LOC new code)

**core.py → tools/fetch/executor.py**
- **Why replace:** Wrong abstraction (job-centric, not schema-centric)
- **What to salvage:**
  - Connector resolution concept → Schema loading
  - Transform pipeline → Kept in transform tool
  - Sink creation → Moved to export tool
- **New approach:**
  - Schema-driven extraction
  - No "jobs" concept
  - Simpler execution model
- **New module:** `tools/fetch/executor.py` (400 LOC new code)

**cli.py → cli.py**
- **Why replace:** Wrong command structure (flat commands, not subcommands)
- **Current:**
  ```bash
  quarry init
  quarry run job.yml
  quarry state
  quarry batch urls.txt
  ```
- **New:**
  ```bash
  scrape inspect URL
  scrape design [--from-inspection FILE]
  scrape fetch SCHEMA URLS
  scrape transform INPUT [--pipeline FILE]
  scrape export INPUT --to FORMAT
  ```
- **Implementation:** New CLI using Typer subcommands
- **New module:** `cli.py` (300 LOC new code)

**policy.py → (merge into lib/http.py)**
- **Why replace:** Tiny module, redundant with http.py
- **What to salvage:**
  - `is_allowed_domain()` → merge into http.py
  - Domain allowlist logic → part of fetch executor
- **Action:** Merge 40 useful lines into http.py, delete file

**robots.py → (merge into lib/http.py)**
- **Why replace:** Duplicates http.py functionality
- **What to salvage:**
  - RobotFileParser caching → already in http.py
- **Action:** http.py is better, delete this file

---

### Code Migration Table

| Current File | LOC | Action | New Location | New LOC | Notes |
|--------------|-----|--------|--------------|---------|-------|
| http.py | 335 | MOVE | lib/http.py | 335 | No changes |
| ratelimit.py | 150 | MOVE | lib/ratelimit.py | 150 | No changes |
| selector_builder.py | 200 | MOVE | lib/selectors.py | 200 | Rename only |
| framework_profiles/ | 2,000 | KEEP | framework_profiles/ | 2,000 | No changes |
| inspector.py | 1,500 | REFACTOR | tools/inspect/analyzer.py | 1,200 | Extract, simplify |
| state.py | 180 | REFACTOR | lib/state.py | 250 | New interface |
| sinks/ | 250 | EXTEND | tools/export/sinks/files.py | 400 | Add formats |
| connectors/ | 600 | REFACTOR | tools/fetch/parser.py | 300 | Generic parser |
| transforms/ | 200 | EXPAND | tools/transform/*.py | 800 | Add validation/enrichment |
| detection_strategies.py | 200 | REFACTOR | lib/parsing.py | 150 | Merge with inspector |
| wizard.py | 800 | REPLACE | tools/design/builder.py | 800 | Fresh interactive design |
| core.py | 250 | REPLACE | tools/fetch/executor.py | 400 | Schema executor |
| cli.py | 500 | REPLACE | cli.py | 300 | Subcommand structure |
| policy.py | 100 | DELETE | lib/http.py | +40 | Merge into http.py |
| robots.py | 180 | DELETE | - | 0 | Redundant with http.py |
| **TOTAL** | **7,445** | | **NEW TOTAL** | **7,325** | Similar size, better structure |

---

## Implementation Roadmap

### Overview

**Timeline:** 7 weeks to MVP  
**Strategy:** Build tools sequentially, test each before moving to next  
**Approach:** Refactor as we go (not big-bang refactor)

### Phase 0: Foundation (Week 1)

**Goal:** Extract shared libraries, establish new structure

**Tasks:**
1. Create new directory structure
   ```bash
   mkdir -p lib tools/{inspect,design,fetch,transform,export}
   ```

2. Move core libraries (no code changes)
   ```bash
   mv quarry/http.py lib/http.py
   mv quarry/ratelimit.py lib/ratelimit.py
   mv quarry/selector_builder.py lib/selectors.py
   ```

3. Create lib/__init__.py with clean exports
   ```python
   from .http import get_html, create_session
   from .ratelimit import DomainRateLimiter
   from .selectors import build_robust_selector
   ```

4. Update imports in framework_profiles/ to use lib/
   ```python
   # Old: from quarry.http import get_html
   # New: from quarry.lib import get_html
   ```

5. Create new CLI skeleton
   ```python
   # cli.py
   app = typer.Typer()
   
   @app.command()
   def inspect(...):
       from tools.inspect.cli import main
       main(...)
   
   # etc for all 5 tools
   ```

6. Run tests - ensure nothing broke
   ```bash
   python -m pytest -q
   ```

**Deliverables:**
- ✅ lib/ folder with 3 modules
- ✅ tools/ folder structure
- ✅ New CLI skeleton
- ✅ All existing tests pass

**Time:** 2-3 days

---

### Phase 1: Tool 1 - `scrape inspect` (Week 2)

**Goal:** First working tool as proof-of-concept for architecture

**Tasks:**

1. **Extract inspector logic** (2 days)
   ```bash
   # Create analyzer.py from inspector.py
   cp quarry/inspector.py tools/inspect/analyzer.py
   ```
   
   Refactor analyzer.py:
   - Keep: `inspect_html()`, `find_item_selector()`, `generate_field_selector()`
   - Remove: Wizard coupling, print statements
   - Clean API:
     ```python
     def analyze_page(html: str) -> dict:
         """Return complete page analysis."""
         return {
             "frameworks": detect_all_frameworks(html),
             "containers": find_item_selector(html),
             "metadata": extract_metadata(html),
             "statistics": page_statistics(html)
         }
     ```

2. **Create reporter** (1 day)
   ```python
   # tools/inspect/reporter.py
   def format_as_json(analysis: dict) -> str:
       """JSON output for piping."""
   
   def format_as_terminal(analysis: dict) -> None:
       """Rich terminal output with colors."""
   ```

3. **Build CLI** (1 day)
   ```python
   # tools/inspect/cli.py
   @app.command()
   def main(
       url: str = typer.Argument(...),
       output: str | None = typer.Option(None, "--output", "-o"),
       format: str = typer.Option("terminal", "--format")
   ):
       # Fetch HTML
       html = get_html(url)
       
       # Analyze
       analysis = analyze_page(html)
       
       # Output
       if format == "json":
           print(format_as_json(analysis))
       else:
           format_as_terminal(analysis)
   ```

4. **Test** (1 day)
   ```python
   # tests/test_inspect_tool.py
   def test_analyze_page():
       html = Path("fixtures/hackernews.html").read_text()
       result = analyze_page(html)
       assert "frameworks" in result
       assert len(result["containers"]) > 0
   
   def test_cli_inspect():
       # Integration test
       result = subprocess.run([
           "scrape", "inspect", "https://news.ycombinator.com"
       ])
       assert result.returncode == 0
   ```

**Deliverables:**
- ✅ `scrape inspect URL` works end-to-end
- ✅ JSON and terminal output
- ✅ Tests pass
- ✅ Documentation updated

**Time:** 5 days

**Validation Checkpoint:**
```bash
# Should work:
scrape inspect https://news.ycombinator.com
scrape inspect https://github.com/explore --output analysis.json
scrape inspect --file test.html
```

---

### Phase 2: Tool 2 - `scrape design` (Week 3)

**Goal:** Interactive schema builder

**Tasks:**

1. **Create schema format** (1 day)
   ```python
   # lib/schemas.py
   from pydantic import BaseModel
   
   class FieldSchema(BaseModel):
       selectors: list[str]
       required: bool = False
       transforms: list[str] = []
       validation: dict = {}
   
   class ExtractionSchema(BaseModel):
       name: str
       version: int = 1
       item_selector: str
       fields: dict[str, FieldSchema]
       pagination: dict | None = None
   
   def load_schema(path: str) -> ExtractionSchema:
       """Load and validate schema.yml."""
   
   def save_schema(schema: ExtractionSchema, path: str):
       """Save to YAML."""
   ```

2. **Build interactive builder** (2 days)
   ```python
   # tools/design/builder.py
   from rich.prompt import Prompt, Confirm
   
   def build_schema_interactive(
       analysis: dict | None = None
   ) -> ExtractionSchema:
       """Interactive schema builder."""
       
       # Step 1: Item container
       if analysis:
           # Suggest from analysis
           containers = analysis["containers"]
           choice = Prompt.ask(
               "Choose item container",
               choices=[c["selector"] for c in containers]
           )
       else:
           choice = Prompt.ask("Enter item selector")
       
       # Step 2: Fields
       fields = {}
       while Confirm.ask("Add field?"):
           name = Prompt.ask("Field name")
           selector = Prompt.ask("CSS selector")
           fields[name] = FieldSchema(selectors=[selector])
       
       return ExtractionSchema(
           name="untitled",
           item_selector=choice,
           fields=fields
       )
   ```

3. **Add live preview** (2 days)
   ```python
   # tools/design/preview.py
   def preview_extraction(
       html: str,
       schema: ExtractionSchema
   ) -> list[dict]:
       """Extract sample items using schema."""
       from tools.fetch.parser import SchemaParser
       parser = SchemaParser(schema.dict())
       return parser.parse(html)[:5]  # First 5 items
   ```

4. **Build CLI** (1 day)
   ```python
   # tools/design/cli.py
   @app.command()
   def main(
       from_inspection: str | None = typer.Option(None),
       edit: str | None = typer.Option(None),
       output: str | None = typer.Option(None)
   ):
       if from_inspection:
           analysis = json.load(open(from_inspection))
       else:
           analysis = None
       
       schema = build_schema_interactive(analysis)
       
       # Preview
       if Confirm.ask("Preview extraction?"):
           html = get_html(Prompt.ask("Test URL"))
           items = preview_extraction(html, schema)
           console.print(items)
       
       # Save
       save_schema(schema, output or f"schemas/{schema.name}.yml")
   ```

**Deliverables:**
- ✅ `scrape design` interactive builder works
- ✅ Can import from `scrape inspect` output
- ✅ Live preview of extraction
- ✅ Saves valid schema.yml

**Time:** 6 days

**Validation Checkpoint:**
```bash
scrape inspect https://news.ycombinator.com > hn.json
scrape design --from-inspection hn.json
# Interactive session, saves to schemas/hackernews.yml
```

---

### Phase 3: Tool 3 - `scrape fetch` (Week 4)

**Goal:** Execute schemas at scale

**Tasks:**

1. **Create schema parser** (2 days)
   ```python
   # tools/fetch/parser.py
   class SchemaParser:
       def __init__(self, schema: dict):
           self.schema = ExtractionSchema(**schema)
       
       def parse(self, html: str) -> list[dict]:
           """Extract items from HTML using schema."""
           soup = BeautifulSoup(html, "html.parser")
           items = soup.select(self.schema.item_selector)
           
           results = []
           for item in items:
               record = {}
               for field_name, field_spec in self.schema.fields.items():
                   record[field_name] = self._extract_field(item, field_spec)
               results.append(record)
           
           return results
       
       def _extract_field(self, element: Tag, field: FieldSchema) -> Any:
           """Extract single field with fallback selectors."""
           for selector in field.selectors:
               try:
                   value = self._select(element, selector)
                   if value:
                       return self._apply_transforms(value, field.transforms)
               except Exception:
                   continue
           return None
   ```

2. **Build executor** (2 days)
   ```python
   # tools/fetch/executor.py
   class FetchExecutor:
       def __init__(self, schema_path: str):
           self.schema = load_schema(schema_path)
           self.parser = SchemaParser(self.schema.dict())
       
       def fetch_url(self, url: str) -> list[dict]:
           """Fetch and parse single URL."""
           html = get_html(url)
           items = self.parser.parse(html)
           # Add metadata
           for item in items:
               item["_meta"] = {
                   "url": url,
                   "fetched_at": datetime.now().isoformat(),
                   "schema": self.schema.name
               }
           return items
       
       def fetch_batch(
           self,
           urls: list[str],
           output: str,
           progress: bool = True
       ):
           """Fetch multiple URLs with progress."""
           with open(output, "w") as f:
               for url in track(urls, description="Fetching"):
                   try:
                       items = self.fetch_url(url)
                       for item in items:
                           f.write(json.dumps(item) + "\n")
                   except Exception as e:
                       console.print(f"[red]Failed {url}: {e}")
   ```

3. **Add progress tracking** (1 day)
   ```python
   # tools/fetch/progress.py
   from rich.progress import Progress, TaskID
   
   class FetchProgress:
       def __init__(self):
           self.progress = Progress()
           self.stats = {
               "success": 0,
               "failed": 0,
               "items": 0
           }
       
       def update(self, url: str, success: bool, item_count: int):
           if success:
               self.stats["success"] += 1
               self.stats["items"] += item_count
           else:
               self.stats["failed"] += 1
   ```

4. **Build CLI** (1 day)
   ```python
   # tools/fetch/cli.py
   @app.command()
   def main(
       schema: str,
       urls: str | None = None,
       url: str | None = None,
       output: str = "output.jsonl",
       rate_limit: float = 1.0,
       timeout: int = 30
   ):
       executor = FetchExecutor(schema)
       
       if url:
           # Single URL
           items = executor.fetch_url(url)
           print(json.dumps(items, indent=2))
       elif urls:
           # Batch from file
           url_list = Path(urls).read_text().splitlines()
           executor.fetch_batch(url_list, output)
   ```

**Deliverables:**
- ✅ `scrape fetch SCHEMA URL` works
- ✅ Batch fetching from file
- ✅ Progress tracking
- ✅ JSONL output

**Time:** 6 days

**Validation Checkpoint:**
```bash
scrape fetch schemas/hackernews.yml https://news.ycombinator.com
scrape fetch schemas/hackernews.yml --urls urls.txt --output hn.jsonl
```

---

### Phase 4: Tool 4 - `scrape transform` (Week 5)

**Goal:** Data cleaning and validation pipeline

**Tasks:**

1. **Validation engine** (2 days)
   ```python
   # tools/transform/validators.py
   class Validator:
       def validate_required(self, value: Any) -> bool:
           return value is not None and value != ""
       
       def validate_type(self, value: Any, expected: str) -> bool:
           if expected == "integer":
               return isinstance(value, int) or value.isdigit()
           # etc
       
       def validate_pattern(self, value: str, pattern: str) -> bool:
           return re.match(pattern, value) is not None
   ```

2. **Transformation engine** (2 days)
   ```python
   # tools/transform/transformers.py
   class Transformer:
       TRANSFORMS = {
           "trim": lambda x: x.strip(),
           "lowercase": lambda x: x.lower(),
           "to_int": lambda x: int(x),
           "extract_regex": lambda x, pattern: re.findall(pattern, x)[0],
           # etc
       }
       
       def apply(self, value: Any, transform: str) -> Any:
           if ":" in transform:
               name, arg = transform.split(":", 1)
               return self.TRANSFORMS[name](value, arg)
           return self.TRANSFORMS[transform](value)
   ```

3. **Pipeline executor** (1 day)
   ```python
   # tools/transform/pipeline.py
   class TransformPipeline:
       def __init__(self, config: dict):
           self.config = config
           self.validator = Validator()
           self.transformer = Transformer()
       
       def process(self, records: Iterable[dict]) -> Iterable[dict]:
           for record in records:
               # Validate
               if not self._validate(record):
                   continue
               
               # Transform
               record = self._transform(record)
               
               # Filter
               if not self._filter(record):
                   continue
               
               yield record
   ```

4. **Build CLI** (1 day)
   ```python
   # tools/transform/cli.py
   @app.command()
   def main(
       input_file: str,
       output: str = "clean.jsonl",
       pipeline: str | None = None,
       dedupe: bool = False,
       validate: bool = False
   ):
       # Load records
       records = (json.loads(line) for line in open(input_file))
       
       # Apply pipeline
       if pipeline:
           config = yaml.safe_load(open(pipeline))
           pipe = TransformPipeline(config)
           records = pipe.process(records)
       
       # Write output
       with open(output, "w") as f:
           for record in records:
               f.write(json.dumps(record) + "\n")
   ```

**Deliverables:**
- ✅ `scrape transform INPUT` works
- ✅ Pipeline from YAML config
- ✅ Validation, transformation, filtering
- ✅ Deduplication

**Time:** 6 days

---

### Phase 5: Tool 5 - `scrape export` (Week 6)

**Goal:** Multi-destination output

**Tasks:**

1. **Extend file sinks** (2 days)
   ```python
   # tools/export/sinks/files.py
   # Move from quarry/sinks/
   # Add: ExcelSink, SQLiteSink
   ```

2. **Add database sinks** (2 days)
   ```python
   # tools/export/sinks/databases.py
   class PostgresSink:
       def __init__(self, connection: str, table: str):
           self.engine = create_engine(connection)
           self.table = table
       
       def write(self, records: Iterable[dict]) -> int:
           df = pd.DataFrame(records)
           df.to_sql(self.table, self.engine, if_exists="append")
           return len(df)
   ```

3. **Add API/webhook sinks** (1 day)
   ```python
   # tools/export/sinks/apis.py
   class WebhookSink:
       def __init__(self, url: str, batch_size: int = 100):
           self.url = url
           self.batch_size = batch_size
       
       def write(self, records: Iterable[dict]) -> int:
           batch = []
           count = 0
           for record in records:
               batch.append(record)
               if len(batch) >= self.batch_size:
                   requests.post(self.url, json=batch)
                   count += len(batch)
                   batch = []
           # Send remaining
           if batch:
               requests.post(self.url, json=batch)
               count += len(batch)
           return count
   ```

4. **Build CLI** (1 day)
   ```python
   # tools/export/cli.py
   @app.command()
   def main(
       input_file: str,
       format: str | None = None,
       output: str | None = None,
       to: str | None = None,
       # DB options
       connection: str | None = None,
       table: str | None = None,
       # API options
       url: str | None = None
   ):
       records = (json.loads(line) for line in open(input_file))
       
       if format == "csv":
           sink = CSVSink(output)
       elif to == "postgres":
           sink = PostgresSink(connection, table)
       elif to == "webhook":
           sink = WebhookSink(url)
       
       count = sink.write(records)
       console.print(f"✓ Exported {count} records")
   ```

**Deliverables:**
- ✅ `scrape export INPUT --format csv` works
- ✅ Database export (Postgres, SQLite)
- ✅ Webhook/API export
- ✅ Multi-destination support

**Time:** 6 days

---

### Phase 6: Integration & Testing (Week 7)

**Goal:** End-to-end workflows, documentation, polish

**Tasks:**

1. **Pipeline orchestration** (2 days)
   - Add pipe support: `scrape fetch ... | scrape transform | scrape export`
   - Test complete workflows
   - Handle errors gracefully

2. **Comprehensive testing** (2 days)
   - Integration tests for each tool
   - End-to-end workflow tests
   - Performance benchmarks

3. **Documentation** (2 days)
   - Update README with new architecture
   - Tool-specific guides
   - Migration guide from v1
   - Example schemas

4. **Polish** (1 day)
   - Error messages
   - Progress indicators
   - Help text
   - Examples in --help

**Deliverables:**
- ✅ All 5 tools work independently
- ✅ Tools chain together seamlessly
- ✅ Comprehensive documentation
- ✅ Migration guide

---

## Success Criteria

### MVP Definition

Quarry 2.0 MVP is complete when:

1. **All 5 tools work independently**
   - `scrape inspect URL` → analysis.json
   - `scrape design` → schema.yml
   - `scrape fetch SCHEMA URLS` → data.jsonl
   - `scrape transform INPUT` → clean.jsonl
   - `scrape export INPUT --to FORMAT` → output

2. **Tools chain together**
   ```bash
   scrape inspect URL > analysis.json
   scrape design --from-inspection analysis.json
   scrape fetch schema.yml --urls urls.txt | \
   scrape transform --pipeline clean.yml | \
   scrape export --to postgres
   ```

3. **Core features work**
   - Framework detection (13 profiles)
   - Interactive schema builder
   - Batch fetching with rate limiting
   - Data validation and transformation
   - Export to 5+ destinations (CSV, JSON, Parquet, Postgres, Webhook)

4. **Production-ready**
   - Error handling (graceful failures)
   - Progress tracking (user visibility)
   - State management (resume after crash)
   - robots.txt respect (ethical scraping)
   - Logging (debug issues)

5. **Well-documented**
   - README with examples
   - Tool-specific guides
   - Schema format documentation
   - Pipeline configuration examples
   - Migration guide from v1

### Quality Gates

Each tool must pass:
- ✅ Unit tests (>80% coverage)
- ✅ Integration tests (end-to-end)
- ✅ Type safety (mypy strict)
- ✅ Code quality (ruff)
- ✅ Performance (<1s for typical operations)
- ✅ Documentation (examples work)

### Non-Goals for MVP

**Not included in MVP** (future enhancements):
- GUI/TUI interfaces
- Cloud deployment
- Scheduled jobs (use cron)
- Real-time streaming
- ML-based extraction
- Browser automation (Selenium/Playwright)
- Distributed scraping
- Template marketplace

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Refactor breaks existing tests | High | Run tests after each module move |
| Module coupling issues | Medium | Clear interfaces, dependency injection |
| Performance regression | Medium | Benchmark against v1 |
| Schema format too complex | High | Start simple, iterate with feedback |
| Export to many formats = complexity | Medium | Standardize sink interface |

### Schedule Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Tools take longer than estimated | High | Build sequentially, validate each |
| Scope creep | High | Stick to MVP, defer enhancements |
| Testing takes longer | Medium | Write tests as we build |

### Adoption Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking changes from v1 | Low | Migration guide, backward compat where possible |
| Learning curve for new CLI | Medium | Good documentation, examples |
| Schema format confusion | High | Interactive builder makes it easy |

---

## Next Steps

When ready to implement:

1. **Create feature branch**
   ```bash
   git checkout -b feature/architecture-v2
   ```

2. **Start with Phase 0** (Foundation)
   - Extract lib/
   - New directory structure
   - Update imports

3. **Build Tool 1** (scrape inspect)
   - Proof of concept for architecture
   - Validate approach

4. **Iterate through remaining tools**
   - One tool at a time
   - Test thoroughly before moving on

5. **Merge when complete**
   - All tests pass
   - Documentation complete
   - Ready for users

---

**Ready to start implementation?** Let me know and we'll begin with Phase 0!
