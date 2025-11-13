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

from foundry.core import run_job
from foundry.framework_profiles import detect_framework
from foundry.lib.http import get_html
from foundry.inspector import (
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
    if console:
        console.print("\n[cyan]ℹ Allowlist:[/cyan] Domains the scraper is allowed to visit (prevents following external links)")
    else:
        print("\nℹ Allowlist: Domains the scraper is allowed to visit (prevents following external links)")
    
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


def _collect_max_items() -> int:
    """Collect and validate max items for smoke test."""
    max_items_str = _prompt_text("Max items (for smoke test)", str(DEFAULT_MAX_ITEMS))
    try:
        return int(max_items_str)
    except ValueError:
        return DEFAULT_MAX_ITEMS


def _get_pasted_html() -> str | None:
    """
    Collect HTML pasted by user from browser.
    
    Returns HTML string or None if cancelled/empty.
    """
    if console:
        console.print("\n[cyan]Copy HTML from your browser:[/cyan]")
        console.print("1. Open the URL in your browser")
        console.print("2. Right-click → 'Inspect' or press F12")
        console.print("3. Right-click on <html> or <body> in Elements panel")
        console.print("4. Select 'Copy → Copy outerHTML'")
        console.print("5. Paste below (press Ctrl+D or type 'END' on a new line when done)\n")
    else:
        print("\nCopy HTML from your browser:")
        print("1. Open the URL in your browser")
        print("2. Right-click → 'Inspect' or press F12")
        print("3. Right-click on <html> or <body> in Elements panel")
        print("4. Select 'Copy → Copy outerHTML'")
        print("5. Paste below (press Ctrl+D or type 'END' on a new line when done)\n")
    
    # Collect multi-line HTML input
    html_lines = []
    print("Paste HTML here:")
    try:
        while True:
            line = input()
            if line.strip() == "END":
                break
            html_lines.append(line)
    except EOFError:
        pass  # Ctrl+D pressed
    
    pasted_html = "\n".join(html_lines)
    
    if pasted_html.strip():
        if console:
            console.print(f"[green]✓ Received {len(pasted_html)} characters of HTML[/green]")
        else:
            print(f"✓ Received {len(pasted_html)} characters of HTML")
        return pasted_html
    else:
        if console:
            console.print("[yellow]No HTML provided.[/yellow]")
        else:
            print("No HTML provided.")
        return None


def _analyze_html_and_build_selectors(entry_url: str) -> dict[str, Any] | None:  # noqa: PLR0912, PLR0915
    """
    Fetch URL, analyze HTML, and interactively build selectors.
    
    Returns selectors dict or None if skipped/failed.
    """
    if console:
        console.print("\n[cyan]Analyzing HTML structure...[/cyan]")
    else:
        print("\nAnalyzing HTML structure...")
    
    html = None
    
    try:
        # Fetch HTML
        html = get_html(entry_url)
    except Exception as fetch_error:
        # Handle fetch errors and offer to paste HTML
        error_msg = f"Failed to fetch URL: {fetch_error}"
        
        # Provide helpful context for common errors
        if "robots.txt disallows" in str(fetch_error):
            help_msg = (
                "\n\n💡 This URL is blocked by robots.txt. "
                "The site owner has explicitly disallowed scraping this page.\n"
                "\nOptions:\n"
                "  1. Check robots.txt manually: [domain]/robots.txt\n"
                "  2. Try a different page on the same site\n"
                "  3. Contact the site owner for permission\n"
                "  4. Look for an official API instead\n"
                "\nYou can continue the wizard with respect_robots=False (not recommended for production)."
            )
            error_msg += help_msg
        elif "403" in str(fetch_error) or "Forbidden" in str(fetch_error):
            help_msg = (
                "\n\n💡 This website is blocking automated requests. "
                "This often happens with sites using:\n"
                "  • Cloudflare, Akamai, or other bot protection\n"
                "  • Anti-scraping measures\n"
                "\nOptions:\n"
                "  1. Try a slower rate limit (default is already 1 req/sec)\n"
                "  2. Check if the site has robots.txt restrictions\n"
                "  3. Use browser developer tools to inspect the HTML manually\n"
                "  4. Check if the site has an API available\n"
                "  5. Contact the site owner for permission\n"
                "\nYou can continue the wizard without HTML analysis and write selectors manually."
            )
            error_msg += help_msg
        elif "404" in str(fetch_error) or "Not Found" in str(fetch_error):
            error_msg += "\n\n💡 The URL returned 404. Please check the URL is correct."
        elif "timeout" in str(fetch_error).lower() or "timed out" in str(fetch_error).lower():
            error_msg += (
                "\n\n💡 Request timed out. The server is not responding.\n"
                "\nPossible causes:\n"
                "  • Server is slow or temporarily unavailable\n"
                "  • Server is blocking datacenter IPs (common for government sites)\n"
                "  • Firewall or bot protection is rejecting the request\n"
                "\nOptions:\n"
                "  1. Try from a different network (local machine vs cloud)\n"
                "  2. Check if the site loads in your browser from this network\n"
                "  3. Use browser dev tools to copy HTML manually\n"
                "  4. Continue wizard and paste HTML when prompted\n"
                "\nYou can continue without HTML analysis and write selectors manually."
            )
        elif "connection" in str(fetch_error).lower() or "network" in str(fetch_error).lower():
            error_msg += "\n\n💡 Network connection failed. Check your internet connection and verify the domain is accessible."
        elif "ssl" in str(fetch_error).lower() or "certificate" in str(fetch_error).lower():
            error_msg += "\n\n💡 SSL/TLS certificate error. The site may have an invalid or expired certificate."
        elif "429" in str(fetch_error) or "Too Many Requests" in str(fetch_error):
            error_msg += "\n\n💡 Rate limited by the server. The site is asking us to slow down. This is unusual for a single request."
        
        if console:
            console.print(f"[red]{error_msg}[/red]")
        else:
            print(f"ERROR: {error_msg}")
        
        # Offer option to paste HTML manually
        if _prompt_confirm("\nDo you want to paste HTML from your browser instead?", default=True):
            html = _get_pasted_html()
            if not html:
                return None
        else:
            return None
    
    if not html:
        return None
    
    try:
        # Inspect HTML structure
        analysis = inspect_html(html)
        
        # Detect framework
        framework = detect_framework(html)
        framework_name = framework.name if framework else "unknown"
        
        # Display page info
        if console:
            console.print(f"[green]✓[/green] Page: {analysis['title']}")
            console.print(f"[green]✓[/green] Total links: {analysis['total_links']}")
            if framework:
                console.print(f"[green]✓[/green] Framework detected: {framework_name}")
        else:
            print(f"✓ Page: {analysis['title']}")
            print(f"✓ Total links: {analysis['total_links']}")
            if framework:
                print(f"✓ Framework detected: {framework_name}")
        
        # Find potential item selectors
        candidates = find_item_selector(html, min_items=3)
        
        if not candidates:
            if console:
                console.print("[yellow]No repeated patterns found. Using simple link extraction.[/yellow]")
            else:
                print("No repeated patterns found. Using simple link extraction.")
            return None
        
        # Loop to allow user to go back and try different patterns
        while True:
            # Display candidates (show up to 25 for better coverage)
            max_display = min(25, len(candidates))
            
            if console:
                console.print("\n[cyan]💡 Tip: Look for a selector that represents the whole item/row, not individual fields.[/cyan]")
                console.print("[cyan]   Good: A row containing title + date + author[/cyan]")
                console.print("[cyan]   Bad: Just the title field or just the date field[/cyan]\n")
                
                table = Table(title="Detected Item Patterns")
                table.add_column("Option", style="cyan", width=6)
                table.add_column("Selector", style="green", width=20)
                table.add_column("Count", style="yellow", width=6)
                table.add_column("Sample Content", style="white")
                
                for i, candidate in enumerate(candidates[:max_display], 1):
                    # Truncate sample title intelligently
                    sample = candidate.get("sample_title", "")
                    if len(sample) > 60:
                        sample = sample[:57] + "..."
                    
                    table.add_row(
                        str(i),
                        candidate["selector"],
                        str(candidate["count"]),
                        sample,
                    )
                console.print(table)
            else:
                print("\n💡 Tip: Look for a selector that represents the whole item/row, not individual fields.")
                print("   Good: A row containing title + date + author")
                print("   Bad: Just the title field or just the date field\n")
                print("\nDetected Item Patterns:")
                for i, candidate in enumerate(candidates[:max_display], 1):
                    print(f"{i}. {candidate['selector']} ({candidate['count']} items)")
                    if candidate.get("sample_title"):
                        sample = candidate['sample_title']
                        if len(sample) > 70:
                            sample = sample[:67] + "..."
                        print(f"   Sample: {sample}")
            
            # Let user select item selector
            choices = [f"{i}. {c['selector']} ({c['count']} items)" for i, c in enumerate(candidates[:max_display], 1)]
            choices.append("Enter custom selector manually")
            choices.append("Skip (use manual config)")
            
            selection = _prompt_select("Select item pattern", choices, default=choices[0])
            
            if "Skip" in selection:
                return None
            
            # Handle manual selector input
            if "custom selector" in selection.lower():
                item_selector = _prompt_text("Enter CSS selector for item container", ".views-row")
                if console:
                    console.print(f"[cyan]Using custom selector: {item_selector}[/cyan]")
                else:
                    print(f"Using custom selector: {item_selector}")
            else:
                # Extract selector from selection (remove option number and count)
                # Format: "1. .selector (10 items)" -> ".selector"
                item_selector = selection.split(". ", 1)[1].split(" (")[0]
            
            # Get sample item for field detection
            soup = BeautifulSoup(html, "html.parser")
            sample_items = soup.select(item_selector)
            
            if not sample_items:
                if console:
                    console.print("[red]Could not find items with selected selector[/red]")
                else:
                    print("ERROR: Could not find items with selected selector")
                # Go back to selection
                continue
            
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
            
            # Check if we found any fields
            if not field_selectors:
                if console:
                    console.print("[yellow]⚠ No fields were auto-detected. You'll need to add them manually to the YAML.[/yellow]")
                    console.print("[yellow]💡 Tip: The selected container might be too specific (e.g., a single field instead of the whole item).[/yellow]")
                    console.print("[yellow]   Try selecting a broader container that includes title, URL, date, etc.[/yellow]")
                else:
                    print("⚠ No fields were auto-detected. You'll need to add them manually to the YAML.")
                    print("💡 Tip: The selected container might be too specific (e.g., a single field instead of the whole item).")
                    print("   Try selecting a broader container that includes title, URL, date, etc.")
                
                # Ask if user wants to continue without fields or go back to select a different pattern
                if _prompt_confirm("Go back and select a different pattern?", default=True):
                    if console:
                        console.print("[yellow]Please select a broader container (e.g., the row/item, not individual fields)[/yellow]")
                    else:
                        print("Please select a broader container (e.g., the row/item, not individual fields)")
                    # Continue the loop to show patterns again
                    continue
                
                # If user insists on continuing, warn them
                if not _prompt_confirm("Continue anyway? (You'll need to manually edit the YAML)", default=False):
                    if console:
                        console.print("[yellow]Skipping selector generation[/yellow]")
                    else:
                        print("Skipping selector generation")
                    return None
                
                # Return "skip" signal - don't use GenericConnector without fields
                if console:
                    console.print("[yellow]Skipping GenericConnector - you'll need to write a custom parser[/yellow]")
                else:
                    print("Skipping GenericConnector - you'll need to write a custom parser")
                return None  # Return None to skip GenericConnector
            
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
                        console.print("[yellow]Let's try a different pattern[/yellow]")
                    else:
                        print("Let's try a different pattern")
                    # Continue the loop to show patterns again
                    continue
            
            # Success! Return the selectors
            return {
                "item": item_selector,
                "fields": field_selectors,
            }
    
    except Exception as e:
        # Catch any analysis errors that occur after successful fetch
        error_msg = f"HTML analysis failed: {e}"
        if console:
            console.print(f"[red]{error_msg}[/red]")
        else:
            print(f"ERROR: {error_msg}")
        return None


def run_wizard() -> None:  # noqa: PLR0912, PLR0915
    """Run interactive wizard to generate job YAML."""
    if console:
        console.print(Panel.fit("Foundry Job Wizard", style="bold blue"))

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
    
    # Use a sensible default rate limit (1 req/sec is polite and reliable)
    rps = DEFAULT_RPS
    
    # Cursor field - suggest based on selectors if available
    if console:
        console.print("\n[cyan]ℹ Cursor field:[/cyan] Field used to track progress and avoid re-scraping items")
    else:
        print("\nℹ Cursor field: Field used to track progress and avoid re-scraping items")
    
    if selectors and "url" in selectors.get("fields", {}):
        default_cursor = "url"
    else:
        default_cursor = template_defaults["cursor_field"]
    cursor_field = _prompt_text("Cursor field (typically 'id' or 'url')", default_cursor)

    # Sink
    if console:
        console.print("\n[cyan]ℹ Output format:[/cyan] Parquet is faster and smaller, CSV is more portable")
    else:
        print("\nℹ Output format: Parquet is faster and smaller, CSV is more portable")
    
    sink_kind = _prompt_select(
        "Sink kind",
        choices=["parquet", "csv"],
        default=template_defaults["sink_kind"],
    )
    
    # Generate appropriate path based on sink kind
    default_path = template_defaults["sink_path"]
    if sink_kind == "csv" and default_path.endswith(".parquet"):
        default_path = default_path.replace(".parquet", ".csv")
    elif sink_kind == "parquet" and default_path.endswith(".csv"):
        default_path = default_path.replace(".csv", ".parquet")
    
    sink_path = _prompt_text("Sink path template (supports strftime like %Y%m%d)", default_path)
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

    # Offer smoke test
    # For GenericConnector, we need to run live (no fixtures)
    is_generic = parser == "generic"
    test_mode = "live" if is_generic else "offline"
    
    if _prompt_confirm(f"Run {test_mode} smoke test?", default=True):
        try:
            # GenericConnector needs live mode, others use offline with fixtures
            if console:
                console.print(f"[dim]Running with offline={not is_generic}...[/dim]")
                # Debug: show what we're passing
                if is_generic:
                    console.print(f"[dim]Selectors in spec: {spec.get('selectors')}[/dim]")
            
            df, next_cursor = run_job(spec, max_items=model.max_items, offline=not is_generic)
            summary = f"{model.job_name}: {len(df)} rows, next_cursor={next_cursor}"
            if console:
                console.print(f"[green]✓ {summary}[/green]")
            else:
                print(f"✓ {summary}")
        except Exception as e:
            error_msg = f"Smoke test failed: {e}"
            if console:
                console.print(f"[red]{error_msg}[/red]")
                console.print(f"[dim]Debug: parser={parser}, offline={not is_generic}[/dim]")
            else:
                print(f"ERROR: {error_msg}")
                print(f"Debug: parser={parser}, offline={not is_generic}")


if __name__ == "__main__":
    try:
        run_wizard()
    except KeyboardInterrupt:
        # Friendly shutdown if user presses Ctrl-C while interacting
        print("\nWizard aborted by user.")
