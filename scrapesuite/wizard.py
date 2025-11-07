"""Interactive wizard for generating job YAML specs."""

import re
import sys
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

try:
    import questionary
    from rich.console import Console
    from rich.panel import Panel

    HAS_ENHANCED_UI = True
except ImportError:
    HAS_ENHANCED_UI = False

import yaml
from pydantic import BaseModel, HttpUrl, field_validator

from scrapesuite.core import run_job

console = Console() if HAS_ENHANCED_UI else None


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
        if not 0.1 <= v <= 2.0:
            raise ValueError("RPS must be between 0.1 and 2.0")
        return v

    @field_validator("max_items")
    @classmethod
    def validate_max_items(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("max_items must be > 0")
        return v


# Named constants to avoid magic values littered through the module.
DEFAULT_RPS = 1.0
DEFAULT_MAX_ITEMS = 100


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


def _build_spec(model: WizardModel, parser: str, normalize: str, template_defaults: dict[str, Any]) -> dict[str, Any]:
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


def run_wizard() -> None:
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

    # Collect inputs
    job_name = _prompt_text("Job name (slug)", template_defaults["job_name"])
    # Entry URL with validation (listing vs detail)
    while True:
        entry = _prompt_text(
            "Entry URL (listing page, not a single item)",
            str(template_defaults["entry"]),
        )
        is_valid, error_msg = _validate_listing_url(entry)
        if is_valid:
            break
        if console:
            console.print(f"[yellow]Warning: {error_msg}[/yellow]")
        else:
            print(f"Warning: {error_msg}")
        if not _prompt_confirm("Continue anyway?", default=False):
            continue
        break

    parser = _prompt_text("Parser name", template_defaults.get("parser", ""))
    normalize = _prompt_text("Normalize function", template_defaults.get("normalize", ""))

    # Allowlist (auto-include entry URL's netloc)
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

    # RPS
    rps_str = _prompt_text("Rate limit (RPS)", str(template_defaults["rps"]))
    try:
        rps = float(rps_str)
        if not 0.1 <= rps <= 2.0:
            rps = 1.0
    except ValueError:
        rps = 1.0

    cursor_field = _prompt_text("Cursor field", template_defaults["cursor_field"])

    # Sink
    sink_kind = _prompt_select(
        "Sink kind",
        choices=["parquet", "csv"],
        default=template_defaults["sink_kind"],
    )
    sink_path = _prompt_text("Sink path template", template_defaults["sink_path"])

    max_items_str = _prompt_text("Max items (for smoke test)", str(DEFAULT_MAX_ITEMS))
    try:
        max_items = int(max_items_str)
    except ValueError:
        max_items = 100

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
    spec = _build_spec(model, parser, normalize, template_defaults)

    _write_yaml(spec, model.job_name)

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
