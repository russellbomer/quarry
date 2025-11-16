# Quarry API & CLI Reference

This document summarizes the **supported public interfaces** for Quarry: the primary command-line entry points and the stable Python APIs intended for direct use.

## CLI Surface (Public)

The recommended way to interact with Quarry is via the unified `quarry` command with subcommands:

- `quarry scout` – Analyze HTML, detect frameworks, and suggest selectors.
- `quarry survey` – Interactively design or refine extraction schemas.
- `quarry excavate` – Execute extraction jobs using YAML schemas.
- `quarry polish` – Clean and transform extracted data.
- `quarry ship` – Export data to CSV/JSON/SQLite/Parquet.
- `quarry init` / `quarry run` – Wizard-mode workflow for YAML jobs.

> The older dot-style entrypoints (`quarry.scout`, `quarry.survey`, etc.) remain available for compatibility but **new usage should prefer `quarry <subcommand>`**.

### CLI Help

Each subcommand exposes `--help`:

```bash
quarry --help
quarry scout --help
quarry survey --help
quarry excavate --help
quarry polish --help
quarry ship --help
```

Refer to `USAGE_GUIDE.md` and `INSTALLATION.md` for more detailed CLI examples.

## Python API (Public)

The following Python functions are intended as **stable integration points** for library users.

### `quarry.inspector`

High-level utilities for inspecting HTML and generating selectors.

```python
from quarry.inspector import (
    inspect_html,
    find_item_selector,
    generate_field_selector,
)
```

- `inspect_html(html: str) -> dict[str, Any]`
  - Runs a lightweight analysis of the page: repeated classes, sample links, detected containers, etc.
- `find_item_selector(html: str, min_items: int = 3) -> list[dict[str, Any]]`
  - Suggests item-level CSS selectors (e.g. `.item`, `.post`, `.data-row`) suitable as container selectors for extraction.
  - Returns ranked candidates with fields like `selector`, `count`, `sample_title`, `sample_url`, `confidence`, `framework_match`.
- `generate_field_selector(item_element: Tag, field_type: str) -> str | None`
  - Given a BeautifulSoup element representing a single item and a logical field name (e.g. `'title'`, `'date'`, `'author'`, `'score'`), suggests a selector (possibly with `::attr(...)`) for that field.

These APIs are designed to remain stable across releases; internal details of the Scout analyzer may change but `find_item_selector` / `generate_field_selector` contracts should not.

### `quarry.lib.selectors`

Low-level selector helpers:

```python
from quarry.lib.selectors import build_robust_selector, SelectorChain
```

- `build_robust_selector(element: Tag, root: Tag | None = None) -> str`
  - Builds a resilient CSS selector for `element`, avoiding dynamic IDs/classes and overly rigid nesting where possible.
- `SelectorChain`
  - Utility for trying a sequence of selectors in order until one matches.

These utilities are useful when you want finer control over selector generation but still want Quarry’s resilience heuristics.

## Internal Modules (Subject to Change)

The following modules underpin the public APIs but should be treated as **internal** unless you are contributing to Quarry itself:

- `quarry.tools.scout.analyzer` – Core analysis engine used by `quarry scout` and `quarry.inspector`.
- `quarry.tools.scout.reporter` – Formatting helpers for Scout output.
- `quarry.tools.survey.*`, `quarry.tools.excavate.*`, `quarry.tools.polish.*`, `quarry.tools.ship.*` – Implementation details of the CLI tools.
- `quarry.framework_profiles.*` – Framework detection profiles and scoring.

These modules may evolve more aggressively than the documented CLI and Python APIs.

## Archive & Historical Docs

Older design notes, early architecture drafts, and historical quickstarts are kept under `docs/archive/`. They are useful for understanding project evolution but may describe behavior that has since changed.

For current behavior and recommended usage, prefer:

- `README.md`
- `INSTALLATION.md`
- `USAGE_GUIDE.md`
- `docs/ARCHITECTURE_V2.md`
- `docs/MODERN_FRAMEWORKS.md`
- `docs/SELECTOR_QUICK_REFERENCE.md`
