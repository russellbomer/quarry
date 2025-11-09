"""Interactive wizard for generating job YAML specs."""

import re
import sys
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

try:
    import questionary
    from bs4 import BeautifulSoup
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    HAS_ENHANCED_UI = True
except ImportError:
    from bs4 import BeautifulSoup

    HAS_ENHANCED_UI = False

import yaml
from pydantic import BaseModel, HttpUrl, field_validator

from scrapesuite.core import run_job
from scrapesuite.http import get_html
from scrapesuite.inspector import (
    find_item_selector,
    generate_field_selector,
    inspect_html,
    preview_extraction,
)

console = Console() if HAS_ENHANCED_UI else None

# Named constants to avoid magic values
MIN_RPS = 0.1
MAX_RPS = 2.0
DEFAULT_RPS = 1.0
DEFAULT_MAX_ITEMS = 100


class WizardModel(BaseModel):
    """Wizard data model."""

    job_name: str
    template: Literal["custom", "fda_example", "nws_example"]
    entry: HttpUrl
    allowlist: list[str]
    rps: float
    cursor_field: str
    sink_kind: Literal["parquet", "csv"]
    sink_path: str
    max_items: int

    @field_validator("rps")
    @classmethod
    def validate_rps(cls, v: float) -> float:
        if not MIN_RPS <= v <= MAX_RPS:
            raise ValueError(f"RPS must be between {MIN_RPS} and {MAX_RPS}")
        return v

    @field_validator("max_items")
    @classmethod
    def validate_max_items(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("max_items must be > 0")
        return v


# Template defaults centralized to reduce run_wizard size and magic values.
TEMPLATES_DEFAULTS: dict[str, dict[str, Any]] = {
    "custom": {
        "job_name": "my_job",
        "entry": "https://example.com/",
        "parser": "custom_list",
        "normalize": "custom",
        "allowlist": ["example.com"],
        "rps": DEFAULT_RPS,
        "cursor_field": "id",
        "sink_kind": "parquet",
        "sink_path": "data/cache/%Y%m%dT%H%M%SZ.parquet",
    },
    "fda_example": {
        "job_name": "fda_recalls",
        "entry": "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts",
        "parser": "fda_list",
        "detail_parser": "fda_detail",
        "normalize": "fda_recalls",
        "allowlist": ["fda.gov"],
        "rps": DEFAULT_RPS,
        "cursor_field": "id",
        "sink_kind": "parquet",
        "sink_path": "data/cache/fda/%Y%m%dT%H%M%SZ.parquet",
    },
    "nws_example": {
        "job_name": "nws_alerts",
        "entry": "https://alerts.weather.gov/cap/us.php?x=0",
        "parser": "nws_list",
        "normalize": "nws_alerts",
        "allowlist": ["weather.gov", "alerts.weather.gov"],
        "rps": DEFAULT_RPS,
        "cursor_field": "id",
        "sink_kind": "parquet",
        "sink_path": "data/cache/nws/%Y%m%dT%H%M%SZ.parquet",
    },
}


def _build_spec(
    model: WizardModel,
    parser: str,
    normalize: str,
    template_defaults: dict[str, Any],
    selectors: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the YAML spec dict from validated model and inputs.

    Extracted to reduce run_wizard size and make intent explicit.
    """
    spec: dict[str, Any] = {
        "version": "1",
        "job": model.job_name,
        "source": {
            "kind": "html",
            "entry": str(model.entry),
            "parser": parser,
            "rate_limit_rps": model.rps,
            "cursor": {
                "field": model.cursor_field,
                "stop_when_seen": True,
            },
        },
        "transform": {"pipeline": [{"normalize": normalize}]},
        "sink": {"kind": model.sink_kind, "path": model.sink_path},
        "policy": {"robots": "allow", "allowlist": model.allowlist},
    }

    if template_defaults.get("detail_parser"):
        spec["source"]["detail_parser"] = template_defaults["detail_parser"]

    # Add selectors config if provided (for GenericConnector)
    if selectors:
        spec["selectors"] = selectors

    return spec


def _write_yaml(spec: dict[str, Any], job_name: str) -> None:
    """Write YAML spec to jobs/<job>.yml. Kept as a single-responsibility helper."""
    jobs_dir = Path("jobs")
    jobs_dir.mkdir(exist_ok=True)
    yaml_path = jobs_dir / f"{job_name}.yml"

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(spec, f, default_flow_style=False, sort_keys=False)


def _prompt_text(prompt: str, default: str = "") -> str:
    """Prompt for text input with fallback."""
    if HAS_ENHANCED_UI:
        return questionary.text(prompt, default=default).ask()
    return input(f"{prompt} [{default}]: ").strip() or default


def _prompt_select(prompt: str, choices: list[str], default: str = "") -> str:
    """Prompt for selection with fallback."""
    if HAS_ENHANCED_UI:
        return questionary.select(prompt, choices=choices, default=default).ask()
    print(f"{prompt}")
    for i, choice in enumerate(choices, 1):
        marker = " *" if choice == default else ""
        print(f"  {i}. {choice}{marker}")
    while True:
        try:
            response = input(f"Select [1-{len(choices)}]: ").strip()
            if not response and default:
                return default
            idx = int(response) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except (ValueError, KeyboardInterrupt):
            pass
        print("Invalid selection. Try again.")


def _prompt_confirm(prompt: str, default: bool = True) -> bool:
    """Prompt for yes/no with fallback."""
    if HAS_ENHANCED_UI:
        return questionary.confirm(prompt, default=default).ask()
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_str}]: ").strip().lower()
    if not response:
        return default
    return response in ("y", "yes")


def _validate_listing_url(url: str) -> tuple[bool, str | None]:
    """
    Validate that URL appears to be a listing page, not a detail page.

    Returns:
        (is_valid, error_message)
    """
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")

    # Check for suspicious detail-like patterns (extra path segments after listing segment)
    # For FDA: /safety/recalls-market-withdrawals-safety-alerts/[slug] suggests detail
    # This is heuristic-based
    detail_patterns = [
        r"/recalls-market-withdrawals-safety-alerts/[^/]+$",  # FDA detail-like
        r"/cap/[^/]+/[^/]+$",  # NWS detail-like
    ]

    for pattern in detail_patterns:
        if re.search(pattern, path):
            return (
                False,
                "URL appears to be a detail page (has extra path segments). "
                "Please provide the listing page URL instead.",
            )

    return (True, None)


def _collect_entry_url(template_defaults: dict[str, Any]) -> str:
    """Collect and validate entry URL with listing/detail check."""
    while True:
        entry = _prompt_text(
            "Entry URL (listing page, not a single item)",
            str(template_defaults["entry"]),
        )
        is_valid, error_msg = _validate_listing_url(entry)
        if is_valid:
            return entry
        if console:
            console.print(f"[yellow]Warning: {error_msg}[/yellow]")
        else:
            print(f"Warning: {error_msg}")
        if not _prompt_confirm("Continue anyway?", default=False):
            continue
        return entry


def _collect_allowlist(entry: str, template_defaults: dict[str, Any]) -> list[str]:
    """Collect allowlist and ensure entry netloc is included."""
    entry_netloc = urlparse(entry).netloc
    default_allowlist = list(template_defaults["allowlist"])
    if entry_netloc and entry_netloc not in default_allowlist:
        default_allowlist.insert(0, entry_netloc)

    allowlist_str = _prompt_text(
        "Allowlist domains (comma-separated)",
        ", ".join(default_allowlist),
    )
    allowlist = [d.strip() for d in allowlist_str.split(",") if d.strip()]
    # Ensure entry netloc is always included
    if entry_netloc and entry_netloc not in allowlist:
        allowlist.insert(0, entry_netloc)

    return allowlist


def _collect_rps(template_defaults: dict[str, Any]) -> float:
    """Collect and validate RPS value."""
    rps_str = _prompt_text("Rate limit (RPS)", str(template_defaults["rps"]))
    try:
        rps = float(rps_str)
        if not MIN_RPS <= rps <= MAX_RPS:
            return DEFAULT_RPS
        return rps
    except ValueError:
        return DEFAULT_RPS


def _collect_max_items() -> int:
    """Collect and validate max items for smoke test."""
    max_items_str = _prompt_text("Max items (for smoke test)", str(DEFAULT_MAX_ITEMS))
    try:
        return int(max_items_str)
    except ValueError:
        return DEFAULT_MAX_ITEMS


def _analyze_html_and_build_selectors(entry_url: str) -> dict[str, Any] | None:  # noqa: PLR0912, PLR0915
    """
    Fetch URL, analyze HTML, and interactively build selectors.
    
    Returns selectors dict or None if skipped/failed.
    """
    if console:
        console.print("\n[cyan]Analyzing HTML structure...[/cyan]")
    else:
        print("\nAnalyzing HTML structure...")
    
    try:
        # Fetch HTML
        html = get_html(entry_url)
        
        # Inspect HTML structure
        analysis = inspect_html(html)
        
        # Display page info
        if console:
            console.print(f"[green]✓[/green] Page: {analysis['title']}")
            console.print(f"[green]✓[/green] Total links: {analysis['total_links']}")
        else:
            print(f"✓ Page: {analysis['title']}")
            print(f"✓ Total links: {analysis['total_links']}")
        
        # Find potential item selectors
        candidates = find_item_selector(html, min_items=3)
        
        if not candidates:
            if console:
                console.print("[yellow]No repeated patterns found. Using simple link extraction.[/yellow]")
            else:
                print("No repeated patterns found. Using simple link extraction.")
            return None
        
        # Display candidates
        if console:
            table = Table(title="Detected Item Patterns")
            table.add_column("Option", style="cyan")
            table.add_column("Selector", style="green")
            table.add_column("Count", style="yellow")
            table.add_column("Sample Title", style="white")
            
            for i, candidate in enumerate(candidates[:5], 1):
                table.add_row(
                    str(i),
                    candidate["selector"],
                    str(candidate["count"]),
                    candidate.get("sample_title", "")[:50],
                )
            console.print(table)
        else:
            print("\nDetected Item Patterns:")
            for i, candidate in enumerate(candidates[:5], 1):
                print(f"{i}. {candidate['selector']} ({candidate['count']} items)")
                if candidate.get("sample_title"):
                    print(f"   Sample: {candidate['sample_title'][:50]}")
        
        # Let user select item selector
        choices = [f"{c['selector']} ({c['count']} items)" for c in candidates[:5]]
        choices.append("Skip (use manual config)")
        
        selection = _prompt_select("Select item pattern", choices, default=choices[0])
        
        if "Skip" in selection:
            return None
        
        # Extract selector from selection
        item_selector = selection.split(" (")[0]
        
        # Get sample item for field detection
        soup = BeautifulSoup(html, "html.parser")
        sample_items = soup.select(item_selector)
        
        if not sample_items:
            if console:
                console.print("[red]Could not find items with selected selector[/red]")
            else:
                print("ERROR: Could not find items with selected selector")
            return None
        
        sample_item = sample_items[0]
        
        # Build field selectors interactively
        field_selectors = {}
        
        if console:
            console.print("\n[cyan]Building field selectors...[/cyan]")
        else:
            print("\nBuilding field selectors...")
        
        # Common fields to detect
        field_types = ["title", "url", "date", "author", "score", "image"]
        
        for field_type in field_types:
            suggested_selector = generate_field_selector(sample_item, field_type)
            
            if not suggested_selector:
                continue  # Field type not found
            
            # Preview extracted value
            try:
                if "::attr(" in suggested_selector:
                    # Extract attribute
                    parts = suggested_selector.split("::attr(")
                    child_selector = parts[0].strip()
                    attr_name = parts[1].rstrip(")")
                    
                    if child_selector:
                        elem = sample_item.select_one(child_selector)
                        preview_value = elem.get(attr_name, "") if elem else ""
                    else:
                        preview_value = sample_item.get(attr_name, "")
                else:
                    # Extract text
                    elem = sample_item.select_one(suggested_selector)
                    preview_value = elem.get_text(strip=True)[:100] if elem else ""
            except Exception:
                preview_value = "[error]"
            
            if not preview_value:
                continue  # Skip empty fields
            
            # Ask user if they want this field
            prompt = f"Include '{field_type}'? (preview: {preview_value[:50]}...)"
            if _prompt_confirm(prompt, default=True):
                # Allow customization
                custom_selector = _prompt_text(
                    f"Selector for '{field_type}'",
                    suggested_selector,
                )
                field_selectors[field_type] = custom_selector
        
        # Preview extraction with all fields
        if field_selectors:
            if console:
                console.print("\n[cyan]Preview of extracted data:[/cyan]")
            else:
                print("\nPreview of extracted data:")
            
            previews = preview_extraction(html, item_selector, field_selectors)
            
            if console:
                table = Table()
                for field_name in field_selectors.keys():
                    table.add_column(field_name, style="cyan")
                
                for item_data in previews:
                    table.add_row(*[str(item_data.get(f, ""))[:30] for f in field_selectors.keys()])
                
                console.print(table)
            else:
                for i, item_data in enumerate(previews, 1):
                    print(f"\nItem {i}:")
                    for field_name, value in item_data.items():
                        print(f"  {field_name}: {value[:50]}")
            
            if not _prompt_confirm("Does this look correct?", default=True):
                if console:
                    console.print("[yellow]Skipping selector generation[/yellow]")
                else:
                    print("Skipping selector generation")
                return None
        
        return {
            "item": item_selector,
            "fields": field_selectors,
        }
    
    except Exception as e:
        error_msg = f"HTML analysis failed: {e}"
        if console:
            console.print(f"[red]{error_msg}[/red]")
        else:
            print(f"ERROR: {error_msg}")
        return None


def run_wizard() -> None:  # noqa: PLR0912, PLR0915
    """Run interactive wizard to generate job YAML."""
    if console:
        console.print(Panel.fit("ScrapeSuite Job Wizard", style="bold blue"))

    # Template selection
    template = _prompt_select(
        "Select template",
        choices=["custom", "fda_example", "nws_example"],
        default="custom",
    )

    # Set defaults based on template
    template_defaults = TEMPLATES_DEFAULTS[template]

    # Collect inputs using helper functions
    job_name = _prompt_text("Job name (slug)", template_defaults["job_name"])
    entry = _collect_entry_url(template_defaults)
    
    # HTML Analysis for custom templates
    selectors = None
    if template == "custom":
        if _prompt_confirm("Analyze HTML structure and build selectors?", default=True):
            selectors = _analyze_html_and_build_selectors(entry)
            
            if selectors:
                # Use GenericConnector for selector-based extraction
                parser = "generic"
                normalize = "generic"
            else:
                # Fall back to manual config
                parser = _prompt_text("Parser name", template_defaults.get("parser", "custom_list"))
                normalize = _prompt_text("Normalize function", template_defaults.get("normalize", "custom"))
        else:
            parser = _prompt_text("Parser name", template_defaults.get("parser", "custom_list"))
            normalize = _prompt_text("Normalize function", template_defaults.get("normalize", "custom"))
    else:
        # For examples, use template defaults
        parser = _prompt_text("Parser name", template_defaults.get("parser", ""))
        normalize = _prompt_text("Normalize function", template_defaults.get("normalize", ""))
    
    allowlist = _collect_allowlist(entry, template_defaults)
    rps = _collect_rps(template_defaults)
    
    # Cursor field - suggest based on selectors if available
    if selectors and "url" in selectors.get("fields", {}):
        default_cursor = "url"
    else:
        default_cursor = template_defaults["cursor_field"]
    cursor_field = _prompt_text("Cursor field", default_cursor)

    # Sink
    sink_kind = _prompt_select(
        "Sink kind",
        choices=["parquet", "csv"],
        default=template_defaults["sink_kind"],
    )
    sink_path = _prompt_text("Sink path template", template_defaults["sink_path"])
    max_items = _collect_max_items()

    # Validate with Pydantic
    try:
        model = WizardModel(
            job_name=job_name,
            template=template,
            entry=entry,
            allowlist=allowlist,
            rps=rps,
            cursor_field=cursor_field,
            sink_kind=sink_kind,
            sink_path=sink_path,
            max_items=max_items,
        )
    except Exception as e:
        error_msg = f"Validation error: {e}"
        if console:
            console.print(f"[red]{error_msg}[/red]")
        else:
            print(f"ERROR: {error_msg}")
        sys.exit(1)

    # Build YAML spec
    spec = _build_spec(model, parser, normalize, template_defaults, selectors)

    _write_yaml(spec, model.job_name)
    # yaml_path is created inside _write_yaml; recreate here for the success message
    yaml_path = Path("jobs") / f"{model.job_name}.yml"

    success_msg = f"Job spec written to {yaml_path}"
    if console:
        console.print(f"[green]{success_msg}[/green]")
    else:
        print(f"SUCCESS: {success_msg}")

    # Offer offline smoke test
    if _prompt_confirm("Run offline smoke test?", default=True):
        try:
            df, next_cursor = run_job(spec, max_items=model.max_items, offline=True)
            summary = f"{model.job_name}: {len(df)} rows, next_cursor={next_cursor}"
            if console:
                console.print(f"[green]✓ {summary}[/green]")
            else:
                print(f"✓ {summary}")
        except Exception as e:
            error_msg = f"Smoke test failed: {e}"
            if console:
                console.print(f"[red]{error_msg}[/red]")
            else:
                print(f"ERROR: {error_msg}")
