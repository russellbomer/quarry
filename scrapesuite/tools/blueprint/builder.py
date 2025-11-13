"""Interactive blueprint builder."""

import json
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from scrapesuite.lib.http import get_html
from scrapesuite.lib.schemas import ExtractionSchema, FieldSchema, PaginationSchema
from scrapesuite.tools.probe.analyzer import analyze_page
from .templates import list_templates, get_template, create_from_template, suggest_template


def build_schema_interactive(
    url: str | None = None,
    analysis: dict[str, Any] | None = None,
    html: str | None = None
) -> ExtractionSchema:
    """
    Build extraction schema interactively.
    
    Args:
        url: Optional URL to analyze
        analysis: Optional pre-computed analysis from Probe
        html: Optional HTML content
    
    Returns:
        Complete ExtractionSchema
    """
    try:
        from rich.console import Console
        from rich.prompt import Prompt, Confirm
        from rich.panel import Panel
        from rich.table import Table
        from rich import box
        
        console = Console()
        console.print("\n╭─────────────────────────────────────────────────────────────╮", style="cyan")
        console.print("│ [bold cyan]BLUEPRINT BUILDER[/bold cyan]                                       │", style="cyan")
        console.print("╰─────────────────────────────────────────────────────────────╯", style="cyan")
        console.print("[dim]Create an extraction schema interactively[/dim]\n")
    except ImportError:
        # Fallback without rich
        return _build_schema_simple(url, analysis, html)
    
    # Step 1: Schema metadata
    console.print(Panel(
        "[bold]Step 1: Schema Metadata[/bold]",
        title="Schema Info",
        title_align="left",
        border_style="cyan"
    ))
    
    name = Prompt.ask("Schema name", default="extraction")
    description = Prompt.ask("Description (optional)", default="")
    
    # Step 1.5: Ask about templates
    console.print()
    console.print(Panel(
        "[bold]Use a Template?[/bold]\n"
        "Start with a pre-configured template for common data types",
        title="Templates",
        title_align="left",
        border_style="cyan"
    ))
    
    if Confirm.ask("Browse templates?", default=True):
        templates = list_templates()
        
        table = Table(
            title="Available Templates",
            title_style="bold",
            title_justify="left",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        table.add_column("#", style="cyan dim", width=4, justify="right")
        table.add_column("Template", style="yellow bold", width=20)
        table.add_column("Description", style="white", max_width=50)
        
        for idx, template in enumerate(templates, 1):
            table.add_row(str(idx), template["name"], template["description"])
        
        # Add "Custom" option
        table.add_row(str(len(templates) + 1), "Custom", "Build from scratch")
        
        console.print(table)
        console.print()
        
        choice = Prompt.ask(
            "Select template number or enter 'skip'",
            default=str(len(templates) + 1)
        )
        
        template_key = None
        if choice.lower() != "skip" and choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(templates):
                template_key = templates[idx]["key"]
                console.print(f"[green]✓[/green] Using template: [cyan]{templates[idx]['name']}[/cyan]")
        
        if template_key:
            # Use template workflow
            template = get_template(template_key)
            
            # Get URL if not provided
            if not url and not html:
                url = Prompt.ask("\nTarget URL (optional)", default="")
                if url and url.strip():
                    console.print(f"[dim]Fetching {url}...[/dim]")
                    try:
                        html = get_html(url)
                    except Exception as e:
                        console.print(f"[red]Error fetching URL: {e}[/red]")
                        html = None
            
            # Run analysis if we have HTML
            if html and not analysis:
                console.print("[dim]Running Probe analysis...[/dim]")
                try:
                    analysis = analyze_page(html, url=url)
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not analyze page: {e}[/yellow]")
            
            # Show suggested selectors
            console.print()
            console.print(Panel(
                f"[bold]Template: {template['name']}[/bold]\n"
                f"{template['description']}",
                title="Using Template",
                title_align="left",
                border_style="green"
            ))
            
            # Item selector
            console.print()
            suggested_selectors = template["common_selectors"]
            
            if analysis and analysis.get("containers"):
                # Merge template suggestions with detected containers
                detected = [c.get("child_selector") or c.get("selector") for c in analysis["containers"][:3]]
                all_selectors = suggested_selectors + [s for s in detected if s not in suggested_selectors]
            else:
                all_selectors = suggested_selectors
            
            console.print("[bold]Common selectors for this template:[/bold]")
            for idx, sel in enumerate(all_selectors[:5], 1):
                console.print(f"  {idx}. {sel}")
            console.print()
            
            choice = Prompt.ask(
                "Select number or enter custom selector",
                default="1"
            )
            
            if choice.isdigit() and 1 <= int(choice) <= len(all_selectors):
                item_selector = all_selectors[int(choice) - 1]
            else:
                item_selector = choice
            
            console.print(f"[green]✓[/green] Using: [cyan]{item_selector}[/cyan]")
            
            # Use template fields (optionally allow customization)
            console.print()
            if Confirm.ask("Customize template fields?", default=False):
                # Show template fields and allow editing
                fields = dict(template["fields"])
                
                console.print("\n[bold]Template fields:[/bold]")
                for fname, fschema in fields.items():
                    console.print(f"  • {fname}: {fschema.selector}")
                
                console.print()
                if Confirm.ask("Add more fields?", default=False):
                    # Add custom fields
                    while True:
                        field_name = Prompt.ask("Field name (or press Enter to finish)", default="")
                        if not field_name.strip():
                            break
                        
                        selector = Prompt.ask(f"Selector for '{field_name}'")
                        attribute = Prompt.ask("Attribute (optional)", default="")
                        
                        fields[field_name] = FieldSchema(
                            selector=selector,
                            attribute=attribute if attribute.strip() else None
                        )
                        console.print(f"[green]✓[/green] Added: {field_name}")
            else:
                fields = template["fields"]
            
            # Pagination (optional)
            console.print()
            console.print(Panel(
                "[bold]Step 4: Pagination (Optional)[/bold]\n"
                "Configure multi-page extraction",
                title="Pagination",
                title_align="left",
                border_style="cyan"
            ))
            
            pagination = None
            if Confirm.ask("Enable pagination?", default=False):
                next_selector = Prompt.ask("Next page link selector", default="a.next")
                max_pages_str = Prompt.ask("Max pages (leave empty for unlimited)", default="")
                
                pagination = PaginationSchema(
                    next_selector=next_selector,
                    max_pages=int(max_pages_str) if max_pages_str.strip() else None
                )
            
            # Build schema from template
            schema = ExtractionSchema(
                name=name,
                description=description if description.strip() else template["description"],
                url=url if url and url.strip() else None,
                item_selector=item_selector,
                fields=fields,
                pagination=pagination
            )
            
            # Summary
            console.print()
            console.print(Panel(
                f"[bold]Name:[/bold] {schema.name}\n"
                f"[bold]Template:[/bold] {template['name']}\n"
                f"[bold]Item selector:[/bold] [cyan]{schema.item_selector}[/cyan]\n"
                f"[bold]Fields:[/bold] {len(schema.fields)} ({', '.join(schema.fields.keys())})\n" +
                (f"[bold]Pagination:[/bold] enabled" if schema.pagination else "[bold]Pagination:[/bold] disabled"),
                title="Schema Summary",
                title_align="left",
                border_style="green"
            ))
            
            return schema
    
    # Continue with custom build (original flow)
    console.print("[dim]Building custom schema...[/dim]\n")
    
    # Step 2: Get URL if not provided
    if not url and not html:
        url = Prompt.ask("\nTarget URL (optional - can analyze later)", default="")
        if url and url.strip():
            console.print(f"[dim]Fetching {url}...[/dim]")
            try:
                html = get_html(url)
            except Exception as e:
                console.print(f"[red]Error fetching URL: {e}[/red]")
                html = None
    
    # Run Probe analysis if we have HTML but no analysis
    if html and not analysis:
        console.print("\n[dim]Running Probe analysis to detect patterns...[/dim]")
        try:
            analysis = analyze_page(html, url=url)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not analyze page: {e}[/yellow]")
            analysis = None
    
    # Step 3: Item selector
    console.print()
    console.print(Panel(
        "[bold]Step 2: Item Selector[/bold]\n"
        "Select the CSS selector that identifies each item to extract\n"
        "(e.g., article, product card, list item)",
        title="Item Selector",
        title_align="left",
        border_style="cyan"
    ))
    
    if analysis and analysis.get("containers"):
        # Show suggestions from Probe analysis
        containers = analysis["containers"][:8]
        
        table = Table(
            title="Detected Containers",
            title_style="bold",
            title_justify="left",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        table.add_column("#", style="cyan dim", width=4, justify="right")
        table.add_column("CSS Selector", style="yellow", max_width=50, overflow="fold")
        table.add_column("Items", style="green bold", justify="right", width=8)
        table.add_column("Sample", style="dim", max_width=30, overflow="ellipsis")
        
        for idx, container in enumerate(containers, 1):
            selector = container.get("child_selector") or container.get("selector") or "—"
            count = str(container.get("item_count", 0))
            sample = container.get("sample_text", "")
            sample = " ".join(sample.split())[:30]
            
            table.add_row(str(idx), selector, count, sample)
        
        console.print(table)
        console.print()
        
        choice = Prompt.ask(
            "Select number or enter custom selector",
            default="1"
        )
        
        if choice.isdigit() and 1 <= int(choice) <= len(containers):
            item_selector = containers[int(choice) - 1].get("child_selector") or containers[int(choice) - 1].get("selector")
            console.print(f"[green]✓[/green] Using: [cyan]{item_selector}[/cyan]")
        else:
            item_selector = choice
            console.print(f"[green]✓[/green] Using custom: [cyan]{item_selector}[/cyan]")
    else:
        console.print("[yellow]No containers detected. Enter selector manually.[/yellow]\n")
        item_selector = Prompt.ask("Item selector (CSS)", default=".item")
    
    # Step 4: Fields
    console.print()
    console.print(Panel(
        "[bold]Step 3: Fields[/bold]\n"
        "Define fields to extract from each item",
        title="Field Definitions",
        title_align="left",
        border_style="cyan"
    ))
    
    fields = {}
    
    # Suggest fields from Probe if available
    suggested_fields = []
    if analysis and analysis.get("suggestions", {}).get("field_candidates"):
        suggested_fields = analysis["suggestions"]["field_candidates"][:10]
    
    if suggested_fields:
        table = Table(
            title="Suggested Fields",
            title_style="bold",
            title_justify="left",
            box=box.SIMPLE,
            show_header=True,
            header_style="bold yellow"
        )
        table.add_column("#", style="cyan dim", width=4, justify="right")
        table.add_column("Field Name", style="yellow bold", width=15)
        table.add_column("CSS Selector", style="cyan", width=30, overflow="fold")
        table.add_column("Sample Value", style="white dim", max_width=30, overflow="ellipsis")
        
        for idx, field in enumerate(suggested_fields, 1):
            name_str = field.get("name", "").title()
            selector = field.get("selector", "")
            sample = field.get("sample", "")
            sample = " ".join(sample.split())[:30]
            
            table.add_row(str(idx), name_str, selector, sample)
        
        console.print(table)
        console.print()
        
        if Confirm.ask("Use all suggested fields?", default=True):
            for field in suggested_fields:
                field_name = field["name"]
                selector = field["selector"]
                
                # Auto-detect attributes
                attribute = None
                if "href" in selector.lower() or field_name.lower() in ["url", "link"]:
                    attribute = "href"
                elif "src" in selector.lower() or field_name.lower() in ["image", "img"]:
                    attribute = "src"
                
                fields[field_name] = FieldSchema(
                    selector=selector,
                    attribute=attribute
                )
            
            console.print(f"[green]✓[/green] Added {len(fields)} fields")
        else:
            console.print("\n[dim]Select individual fields (comma-separated numbers, e.g., '1,3,5' or 'all'):[/dim]")
            selection = Prompt.ask("Fields to include", default="all")
            
            if selection.lower() == "all":
                selected_indices = list(range(1, len(suggested_fields) + 1))
            else:
                try:
                    selected_indices = [int(x.strip()) for x in selection.split(",")]
                except ValueError:
                    console.print("[yellow]Invalid selection, using all fields[/yellow]")
                    selected_indices = list(range(1, len(suggested_fields) + 1))
            
            for idx in selected_indices:
                if 1 <= idx <= len(suggested_fields):
                    field = suggested_fields[idx - 1]
                    field_name = field["name"]
                    selector = field["selector"]
                    
                    # Auto-detect attributes
                    attribute = None
                    if "href" in selector.lower() or field_name.lower() in ["url", "link"]:
                        attribute = "href"
                    elif "src" in selector.lower() or field_name.lower() in ["image", "img"]:
                        attribute = "src"
                    
                    fields[field_name] = FieldSchema(
                        selector=selector,
                        attribute=attribute
                    )
            
            console.print(f"[green]✓[/green] Added {len(fields)} fields")
    
    # Manual field entry
    console.print()
    while True:
        if fields:
            if not Confirm.ask("Add custom field?", default=False):
                break
        else:
            console.print("[yellow]No fields defined yet. Add at least one field.[/yellow]")
        
        field_name = Prompt.ask("Field name")
        selector = Prompt.ask(f"Selector for '{field_name}'")
        
        # Ask for attribute if it looks like a link/image
        attribute = None
        if "href" in selector.lower() or field_name.lower() in ["url", "link"]:
            if Confirm.ask("Extract 'href' attribute?", default=True):
                attribute = "href"
        elif "src" in selector.lower() or field_name.lower() in ["image", "img"]:
            if Confirm.ask("Extract 'src' attribute?", default=True):
                attribute = "src"
        else:
            custom_attr = Prompt.ask("Extract attribute (leave empty for text)", default="")
            if custom_attr.strip():
                attribute = custom_attr.strip()
        
        required = Confirm.ask(f"Is '{field_name}' required?", default=False)
        
        fields[field_name] = FieldSchema(
            selector=selector,
            attribute=attribute if attribute else None,
            required=required
        )
        
        console.print(f"[green]✓[/green] Added field: {field_name}")
    
    if not fields:
        console.print("[red]Error: At least one field is required[/red]")
        raise ValueError("At least one field is required")
    
    # Step 5: Pagination (optional)
    console.print()
    console.print(Panel(
        "[bold]Step 4: Pagination (Optional)[/bold]\n"
        "Configure multi-page extraction",
        title="Pagination",
        title_align="left",
        border_style="cyan"
    ))
    
    pagination = None
    
    # Check for common pagination patterns
    if html:
        soup = BeautifulSoup(html, "html.parser")
        pagination_candidates = []
        
        # Common pagination selectors
        patterns = [
            ("a.next", "Next link (class='next')"),
            ("a[rel='next']", "Next link (rel='next')"),
            (".pagination a:last-child", "Last pagination link"),
            ("a:contains('Next')", "Link containing 'Next'"),
        ]
        
        for selector, desc in patterns:
            try:
                if soup.select(selector):
                    pagination_candidates.append((selector, desc))
            except Exception:
                pass
        
        if pagination_candidates:
            console.print("[dim]Detected pagination patterns:[/dim]")
            for idx, (sel, desc) in enumerate(pagination_candidates, 1):
                console.print(f"  {idx}. {sel} - {desc}")
            console.print()
    
    if Confirm.ask("Enable pagination?", default=False):
        next_selector = Prompt.ask("Next page link selector", default="a.next")
        max_pages_str = Prompt.ask("Max pages to scrape (leave empty for unlimited)", default="")
        
        pagination = PaginationSchema(
            next_selector=next_selector,
            max_pages=int(max_pages_str) if max_pages_str.strip() else None
        )
        console.print(f"[green]✓[/green] Pagination enabled")
    
    # Build schema
    schema = ExtractionSchema(
        name=name,
        description=description if description.strip() else None,
        url=url if url and url.strip() else None,
        item_selector=item_selector,
        fields=fields,
        pagination=pagination
    )
    
    # Summary
    console.print()
    console.print(Panel(
        f"[bold]Name:[/bold] {schema.name}\n"
        f"[bold]Item selector:[/bold] [cyan]{schema.item_selector}[/cyan]\n"
        f"[bold]Fields:[/bold] {len(schema.fields)} ({', '.join(schema.fields.keys())})\n" +
        (f"[bold]Pagination:[/bold] enabled (max: {schema.pagination.max_pages or 'unlimited'})" if schema.pagination else "[bold]Pagination:[/bold] disabled"),
        title="Schema Summary",
        title_align="left",
        border_style="green"
    ))
    
    return schema


def _build_schema_simple(
    url: str | None = None,
    analysis: dict[str, Any] | None = None,
    html: str | None = None
) -> ExtractionSchema:
    """Fallback builder without rich library."""
    print("\n=== Blueprint Builder ===\n")
    
    # Schema metadata
    name = input("Schema name [extraction]: ").strip() or "extraction"
    description = input("Description (optional): ").strip()
    
    # Item selector
    print("\nItem Selector:")
    if analysis and analysis.get("containers"):
        print("Suggested containers:")
        containers = analysis["containers"][:3]
        for idx, cont in enumerate(containers, 1):
            selector = cont.get("child_selector", cont.get("selector"))
            count = cont.get("item_count", 0)
            print(f"  {idx}. {selector} ({count} items)")
        
        choice = input("\nSelect option or enter custom [1]: ").strip() or "1"
        if choice.isdigit() and 1 <= int(choice) <= len(containers):
            item_selector = containers[int(choice) - 1].get("child_selector")
        else:
            item_selector = choice
    else:
        item_selector = input("Item selector: ").strip()
    
    # Fields
    print("\nFields:")
    fields = {}
    
    while True:
        if fields:
            add_more = input("\nAdd another field? [y/N]: ").strip().lower()
            if add_more not in ["y", "yes"]:
                break
        
        field_name = input("Field name: ").strip()
        if not field_name:
            break
        
        selector = input(f"Selector for '{field_name}': ").strip()
        fields[field_name] = FieldSchema(selector=selector)
    
    if not fields:
        raise ValueError("At least one field is required")
    
    # Build schema
    schema = ExtractionSchema(
        name=name,
        description=description if description else None,
        url=url if url else None,
        item_selector=item_selector,
        fields=fields
    )
    
    print(f"\n✓ Schema created: {name}")
    return schema


def load_analysis_from_file(path: str | Path) -> dict[str, Any]:
    """Load Probe analysis from JSON file."""
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Analysis file not found: {path}")
    
    with path.open() as f:
        return json.load(f)
