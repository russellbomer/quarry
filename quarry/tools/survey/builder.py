"""Interactive blueprint builder."""

import json
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from quarry.lib.http import get_html
from quarry.lib.schemas import ExtractionSchema, FieldSchema, PaginationSchema
from quarry.tools.scout.analyzer import analyze_page

from .templates import get_template, list_templates


def _clone_fields(fields: dict[str, FieldSchema]) -> dict[str, FieldSchema]:
    """Create a deep copy of template fields."""

    return {name: schema.model_copy() for name, schema in fields.items()}


def _merge_template_fields(
    template_fields: dict[str, FieldSchema],
    candidates: list[dict[str, Any]],
) -> tuple[dict[str, FieldSchema], list[dict[str, Any]]]:
    """Merge Scout field candidates into template field definitions."""

    if not candidates:
        return _clone_fields(template_fields), []

    normalized_candidates: list[tuple[str, dict[str, Any]]] = []
    for cand in candidates:
        name = cand.get("name")
        if not name:
            continue
        normalized_candidates.append((name.replace("_", " ").lower(), cand))

    merged = _clone_fields(template_fields)
    applied: list[dict[str, Any]] = []
    used_indices: set[int] = set()

    for field_name, schema in merged.items():
        target = field_name.replace("_", " ").lower()
        match_idx: int | None = None
        match_candidate: dict[str, Any] | None = None

        for idx, (candidate_name, candidate) in enumerate(normalized_candidates):
            if idx in used_indices:
                continue
            if candidate_name == target or candidate_name in target or target in candidate_name:
                match_idx = idx
                match_candidate = candidate
                break

        if match_idx is None or match_candidate is None:
            continue

        selector = match_candidate.get("selector")
        if not selector:
            continue

        attribute = match_candidate.get("attribute") or schema.attribute
        merged[field_name] = schema.model_copy(
            update={
                "selector": selector,
                "attribute": attribute,
            }
        )

        applied.append(
            {
                "field": field_name,
                "selector": selector,
                "attribute": attribute,
                "sample": match_candidate.get("sample", ""),
            }
        )
        used_indices.add(match_idx)

    return merged, applied


def build_schema_interactive(
    url: str | None = None, analysis: dict[str, Any] | None = None, html: str | None = None
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
    # Ensure item selector is initialized before any branch uses it
    item_selector: str | None = None
    # Initialize fields once for the interactive flow
    fields: dict[str, FieldSchema] = {}

    try:
        from rich import box
        from rich.console import Console
        from rich.panel import Panel
        from rich.prompt import Confirm, Prompt
        from rich.table import Table

        console = Console()
        console.print(
            "\n╭─────────────────────────────────────────────────────────────╮", style="cyan"
        )
        console.print(
            "│ [bold cyan]SURVEY BUILDER[/bold cyan]                                         │",
            style="cyan",
        )
        console.print(
            "╰─────────────────────────────────────────────────────────────╯", style="cyan"
        )
        console.print("[dim]Create an extraction schema interactively[/dim]\n")
    except ImportError:
        # Fallback without rich
        return _build_schema_simple(url, analysis, html)

    def _prompt_pagination_config(
        pagination_candidates: list[dict[str, Any]],
    ) -> PaginationSchema | None:
        """Interactive helper for configuring pagination."""

        soup = BeautifulSoup(html, "html.parser") if html else None

        # Step 1: Choose pagination type
        console.print("\n[bold]Pagination Type:[/bold]")
        console.print("  1. Next page link (most common)")
        console.print("  2. Load more button")
        console.print("  3. Skip pagination setup")
        console.print()

        pagination_type = Prompt.ask(
            "Select pagination type",
            choices=["1", "2", "3"],
            default="1",
        )

        if pagination_type == "3":
            console.print("[dim]Pagination skipped[/dim]")
            return None

        # Step 2: Select or enter selector
        next_selector: str | None = None

        if pagination_candidates:
            console.print()
            table = Table(
                title="Detected Pagination Links",
                title_style="bold",
                box=box.SIMPLE,
                show_header=True,
                header_style="bold cyan",
            )
            table.add_column("#", style="cyan dim", width=4, justify="right")
            table.add_column("Selector", style="yellow", max_width=50, overflow="fold")
            table.add_column("Link Text", style="white", max_width=20, overflow="ellipsis")
            table.add_column("Href", style="cyan", max_width=25, overflow="ellipsis")
            table.add_column("Confidence", style="green", width=12)

            for idx, candidate in enumerate(pagination_candidates, 1):
                score = candidate.get("score", 0)
                confidence = "High" if score >= 60 else "Medium" if score >= 40 else "Low"
                table.add_row(
                    str(idx),
                    candidate.get("selector", "—"),
                    candidate.get("text", "")[:20],
                    candidate.get("href", "")[:25],
                    f"[{'green' if score >= 60 else 'yellow'}]{confidence}[/]",
                )

            console.print(table)
            console.print()
            console.print("[dim]Enter a number to select, or type a custom CSS selector[/dim]")
            console.print("[dim]Type 'skip' to cancel pagination setup[/dim]")
            console.print()

            choice = Prompt.ask(
                "Selector",
                default="1",
            )

            if choice.lower() == "skip":
                console.print("[dim]Pagination skipped[/dim]")
                return None

            if choice.isdigit() and 1 <= int(choice) <= len(pagination_candidates):
                next_selector = pagination_candidates[int(choice) - 1]["selector"]
            else:
                next_selector = choice.strip()
        else:
            console.print()
            console.print("[yellow]No pagination links detected automatically.[/yellow]")
            console.print(
                "[dim]Common patterns: a[rel='next'], .next-page a, .pagination .next[/dim]"
            )
            console.print()

            default_selector = "a[rel='next']" if pagination_type == "1" else "button.load-more"
            next_selector = Prompt.ask(
                "Enter pagination selector (or 'skip' to cancel)",
                default=default_selector,
            ).strip()

            if next_selector.lower() == "skip":
                console.print("[dim]Pagination skipped[/dim]")
                return None

        if not next_selector:
            console.print(
                "[yellow]Pagination selector cannot be empty. Skipping pagination setup.[/yellow]"
            )
            return None

        # Step 3: Validate selector against current HTML
        if soup:
            try:
                sample_link = soup.select_one(next_selector)
            except Exception as e:
                console.print(f"[red]Invalid selector syntax: {e}[/red]")
                if not Confirm.ask("Continue anyway?", default=False):
                    return None
                sample_link = None

            if sample_link:
                sample_href = sample_link.get("href") or ""
                sample_text = sample_link.get_text(" ", strip=True)[:30]

                console.print("\n[green]✓[/green] Selector matched!")
                if sample_href:
                    console.print(f"  Link: [cyan]{sample_href}[/cyan]")
                if sample_text:
                    console.print(f"  Text: [dim]{sample_text}[/dim]")

                if not sample_href and pagination_type == "1":
                    console.print("\n[yellow]⚠ Element has no href attribute.[/yellow]")
                    console.print(
                        "[dim]This may be a JavaScript-driven button instead of a link.[/dim]"
                    )
                    if not Confirm.ask("Continue with this selector?", default=True):
                        return None
            else:
                console.print(
                    "\n[yellow]⚠ Selector did not match any elements in the current HTML.[/yellow]"
                )
                console.print("[dim]This could mean:[/dim]")
                console.print("[dim]  • The selector syntax is incorrect[/dim]")
                console.print("[dim]  • This is the last page (no 'next' link)[/dim]")
                console.print("[dim]  • The pagination is loaded dynamically via JavaScript[/dim]")

                if not Confirm.ask("Continue anyway?", default=False):
                    return None

        # Step 4: Configure timing and limits
        console.print()
        console.print("[bold]Pagination Settings:[/bold]")

        wait_input = Prompt.ask(
            "Seconds to wait between pages",
            default="1.0",
        ).strip()
        try:
            wait_seconds = float(wait_input) if wait_input else 1.0
            if wait_seconds < 0:
                wait_seconds = 1.0
        except ValueError:
            console.print("[yellow]Invalid wait value. Using 1.0 seconds.[/yellow]")
            wait_seconds = 1.0

        console.print()
        console.print("[dim]Tip: Set a max to avoid scraping too many pages accidentally[/dim]")
        max_pages_input = Prompt.ask(
            "Max pages to scrape (0 = unlimited)",
            default="10",
        ).strip()
        max_pages_value: int | None
        try:
            if max_pages_input and int(max_pages_input) > 0:
                max_pages_value = int(max_pages_input)
            else:
                max_pages_value = None
        except ValueError:
            console.print("[yellow]Invalid max pages value. Using 10.[/yellow]")
            max_pages_value = 10

        # Summary
        console.print()
        console.print(
            Panel(
                f"[bold]Selector:[/bold] [cyan]{next_selector}[/cyan]\n"
                f"[bold]Wait:[/bold] {wait_seconds}s between pages\n"
                f"[bold]Max pages:[/bold] {max_pages_value or 'unlimited'}",
                title="Pagination Summary",
                title_align="left",
                border_style="green",
                expand=False,
            )
        )

        return PaginationSchema(
            next_selector=next_selector,
            max_pages=max_pages_value,
            wait_seconds=wait_seconds,
        )

    # Step 1: Schema metadata
    console.print(
        Panel(
            "[bold]Step 1: Schema Metadata[/bold]",
            title="Schema Info",
            title_align="left",
            border_style="cyan",
            expand=False,
        )
    )

    name = Prompt.ask("Schema name", default="extraction")
    description = Prompt.ask("Description (optional)", default="")

    # Step 1.5: Ask about templates
    console.print()
    console.print(
        Panel(
            "[bold]Use a Template?[/bold]\n"
            "Start with a pre-configured template for common data types",
            title="Templates",
            title_align="left",
            border_style="cyan",
            expand=False,
        )
    )

    if Confirm.ask("Browse templates?", default=True):
        templates = list_templates()

        table = Table(
            title="Available Templates",
            title_style="bold",
            title_justify="left",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
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
            "Select template number or enter 'skip'", default=str(len(templates) + 1)
        )

        template_key = None
        if choice.lower() != "skip" and choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(templates):
                template_key = templates[idx]["key"]
                console.print(
                    f"[green]✓[/green] Using template: [cyan]{templates[idx]['name']}[/cyan]"
                )

        if template_key:
            # Use template workflow
            template = get_template(template_key)

            # Ensure we have HTML (fetch if necessary)
            if not html:
                if url:
                    console.print(f"[dim]Fetching {url}...[/dim]")
                    try:
                        html = get_html(url)
                    except Exception as e:
                        console.print(f"[red]Error fetching URL: {e}[/red]")
                        html = None
                else:
                    url = Prompt.ask("\nTarget URL (optional)", default="")
                    if url and url.strip():
                        console.print(f"[dim]Fetching {url}...[/dim]")
                        try:
                            html = get_html(url)
                        except Exception as e:
                            console.print(f"[red]Error fetching URL: {e}[/red]")
                            html = None

            # Run Scout analysis whenever we have HTML but no analysis yet
            if html and not analysis:
                console.print("[dim]Running Scout analysis...[/dim]")
                try:
                    analysis = analyze_page(html, url=url)
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not analyze page: {e}[/yellow]")
                    analysis = None

            # Surface high-level insights if available
            if analysis:
                console.print()
                frameworks = analysis.get("frameworks") or []
                if frameworks:
                    top_framework = f"{frameworks[0]['name']} ({frameworks[0]['confidence'] * 100:.0f}% confidence)"
                else:
                    top_framework = "None detected"
                console.print(
                    Panel(
                        "\n".join(
                            [
                                f"Framework: {top_framework}",
                                f"Detected containers: {len(analysis.get('containers') or [])}",
                                f"Suggested item selector (default shown below): {analysis.get('suggestions', {}).get('item_selector') or 'n/a'}",
                            ]
                        ),
                        title="Scout Insights",
                        title_align="left",
                        border_style="blue",
                        expand=False,
                    )
                )

            # Show suggested selectors
            console.print()
            console.print(
                Panel(
                    f"[bold]Template: {template['name']}[/bold]\n{template['description']}",
                    title="Using Template",
                    title_align="left",
                    border_style="green",
                    expand=False,
                )
            )

            # Item selector
            console.print()
            base_selectors = list(template["common_selectors"])
            all_selectors: list[str] = []

            def _add_selector(candidate: str | None) -> None:
                if not candidate:
                    return
                candidate = candidate.strip()
                if candidate and candidate not in all_selectors:
                    all_selectors.append(candidate)

            if analysis:
                best_selector = (analysis.get("suggestions") or {}).get("item_selector")
                _add_selector(best_selector)
                for container in analysis.get("containers") or []:
                    _add_selector(container.get("child_selector") or container.get("selector"))

            for selector in base_selectors:
                _add_selector(selector)

            if not all_selectors:
                all_selectors = base_selectors

            console.print("[bold]Selector suggestions:[/bold]")
            for idx, sel in enumerate(all_selectors[:5] or all_selectors, 1):
                console.print(f"  {idx}. {sel}")
            console.print()

            choice = Prompt.ask("Select number or enter custom selector", default="1")

            if choice.isdigit() and 1 <= int(choice) <= len(all_selectors):
                item_selector = all_selectors[int(choice) - 1]
            else:
                item_selector = choice

            console.print(f"[green]✓[/green] Using: [cyan]{item_selector}[/cyan]")

            candidate_fields = (
                (analysis.get("suggestions") or {}).get("field_candidates") if analysis else None
            )
            fields = _clone_fields(template["fields"])
            applied_matches: list[dict[str, Any]] = []

            if candidate_fields:
                merged_fields, applied_matches = _merge_template_fields(
                    template["fields"], candidate_fields
                )
                if applied_matches:
                    table = Table(
                        title="Detected Field Matches",
                        title_style="bold",
                        box=box.SIMPLE,
                        show_header=True,
                        header_style="bold cyan",
                    )
                    table.add_column("Field", style="yellow", width=15)
                    table.add_column("Selector", style="cyan", max_width=40, overflow="fold")
                    table.add_column("Attribute", style="magenta", width=12)
                    table.add_column("Sample", style="dim", max_width=30, overflow="ellipsis")

                    for match in applied_matches:
                        table.add_row(
                            match["field"],
                            match["selector"],
                            match["attribute"] or "—",
                            match.get("sample", ""),
                        )

                    console.print(table)
                    console.print()

                    if Confirm.ask("Apply detected selectors to template fields?", default=True):
                        fields = merged_fields

            # Use template fields (optionally allow customization)
            console.print()
            if Confirm.ask("Customize template fields?", default=False):
                console.print("\n[bold]Template fields:[/bold]")
                for fname, fschema in fields.items():
                    console.print(f"  • {fname}: {fschema.selector}")

                console.print()
                suggested_fields = []
                if applied_matches:
                    suggested_fields = applied_matches
                elif candidate_fields:
                    suggested_fields = candidate_fields[:5]

                if Confirm.ask("Add more fields?", default=False):
                    selector_options: list[str] = []
                    if suggested_fields:
                        console.print("\n[bold]Selector suggestions from Scout analysis:[/bold]")
                        for idx, match in enumerate(suggested_fields, 1):
                            label = match.get("field") or match.get("name") or "field"
                            console.print(
                                f"  {idx}. [cyan]{match['selector']}[/cyan]"
                                f"  ({label}, support={match.get('support', 1)})"
                            )
                            selector_options.append(match["selector"])
                        console.print(
                            "(Enter number to use a suggestion, or provide your own selector)"
                        )
                        console.print()

                    # Add custom fields
                    while True:
                        field_name = Prompt.ask("Field name (or press Enter to finish)", default="")
                        if not field_name.strip():
                            break

                        default_selector = selector_options[0] if selector_options else ""
                        selector_input = Prompt.ask(
                            f"Selector for '{field_name}'",
                            default=str(1) if selector_options else default_selector,
                        )

                        if selector_input.isdigit() and selector_options:
                            index = int(selector_input) - 1
                            if 0 <= index < len(selector_options):
                                selector = selector_options[index]
                            else:
                                console.print(
                                    "[yellow]Invalid choice, please enter a valid selector.[/yellow]"
                                )
                                continue
                        else:
                            selector = selector_input

                        if not selector.strip():
                            console.print("[yellow]Selector cannot be empty.[/yellow]")
                            continue

                        attr_input = Prompt.ask("Attribute (optional)", default="")

                        fields[field_name] = FieldSchema(
                            selector=selector.strip(),
                            attribute=attr_input.strip() if attr_input.strip() else None,
                        )
                        console.print(f"[green]✓[/green] Added: {field_name}")

            # Pagination (optional)
            console.print()
            console.print(
                Panel(
                    "[bold]Step 4: Pagination (Optional)[/bold]\nConfigure multi-page extraction",
                    title="Pagination",
                    title_align="left",
                    border_style="cyan",
                    expand=False,
                )
            )

            pagination: PaginationSchema | None = None
            pagination_candidates: list[dict[str, Any]] = []
            if analysis:
                pagination_candidates = (analysis.get("suggestions") or {}).get(
                    "pagination_candidates"
                ) or []

            enable_default = bool(pagination_candidates)
            if Confirm.ask("Enable pagination?", default=enable_default):
                pagination = _prompt_pagination_config(pagination_candidates)

            # Build schema from template
            schema = ExtractionSchema(
                name=name,
                description=description if description.strip() else template["description"],
                url=url if url and url.strip() else None,
                item_selector=item_selector,
                fields=fields,
                pagination=pagination,
            )

            # Summary
            console.print()
            console.print(
                Panel(
                    f"[bold]Name:[/bold] {schema.name}\n"
                    f"[bold]Template:[/bold] {template['name']}\n"
                    f"[bold]Item selector:[/bold] [cyan]{schema.item_selector}[/cyan]\n"
                    f"[bold]Fields:[/bold] {len(schema.fields)} ({', '.join(schema.fields.keys())})\n"
                    + (
                        "[bold]Pagination:[/bold] enabled"
                        if schema.pagination
                        else "[bold]Pagination:[/bold] disabled"
                    ),
                    title="Schema Summary",
                    title_align="left",
                    border_style="green",
                    expand=False,
                )
            )

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
    console.print(
        Panel(
            "[bold]Step 2: Item Selector[/bold]\n"
            "Select the CSS selector that identifies each item to extract\n"
            "(e.g., article, product card, list item)",
            title="Item Selector",
            title_align="left",
            border_style="cyan",
            expand=False,
        )
    )

    # item_selector declared above to avoid redefinition warnings
    suggested_selector: str | None = None
    if analysis:
        suggested_selector = (analysis.get("suggestions") or {}).get("item_selector")

    if suggested_selector:
        console.print(
            Panel(
                f"[bold]Scout suggestion:[/bold] [cyan]{suggested_selector}[/cyan]\n"
                "Matches containers that share the same structure (including variants).",
                title="Suggested Selector",
                title_align="left",
                border_style="green",
                expand=False,
            )
        )
        if Confirm.ask("Use suggested selector?", default=True):
            item_selector = suggested_selector
            console.print(f"[green]✓[/green] Using Scout suggestion: [cyan]{item_selector}[/cyan]")

    if analysis and analysis.get("containers"):
        # Show suggestions from Probe analysis
        containers = analysis["containers"][:8]

        table = Table(
            title="Detected Containers",
            title_style="bold",
            title_justify="left",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("#", style="cyan dim", width=4, justify="right")
        table.add_column("CSS Selector", style="yellow", max_width=40, overflow="fold")
        table.add_column("Items", style="green bold", justify="right", width=6)
        table.add_column("Confidence", style="magenta", width=10)
        table.add_column("Why", style="dim", max_width=28, overflow="ellipsis")

        for idx, container in enumerate(containers, 1):
            selector = container.get("child_selector") or container.get("selector") or "—"
            count = str(container.get("item_count", 0))

            # Calculate confidence from score
            score = container.get("content_score", 0)
            if score >= 80:
                confidence = "[green]High[/]"
            elif score >= 50:
                confidence = "[yellow]Medium[/]"
            else:
                confidence = "[dim]Low[/]"

            # Get hints or fall back to sample text
            hints = container.get("hints", [])
            why = ", ".join(hints) if hints else ""
            if not why:
                sample = container.get("sample_text", "")
                why = " ".join(sample.split())[:25]

            table.add_row(str(idx), selector, count, confidence, why)

        console.print(table)
        console.print()

        default_choice = "1"
        prompt_message = "Select number or enter custom selector"
        if item_selector == suggested_selector and item_selector is not None:
            default_choice = "keep"
            prompt_message = (
                "Select number, enter custom selector, or type 'keep' to reuse suggestion"
            )

        choice = Prompt.ask(prompt_message, default=default_choice)

        if choice.lower() == "keep" and item_selector:
            console.print(f"[green]✓[/green] Keeping: [cyan]{item_selector}[/cyan]")
        elif choice.isdigit() and 1 <= int(choice) <= len(containers):
            selected = containers[int(choice) - 1]
            item_selector = selected.get("child_selector") or selected.get("selector")
            # Show why this container was selected
            hints = selected.get("hints", [])
            if hints:
                console.print(f"[green]✓[/green] Using: [cyan]{item_selector}[/cyan]")
                console.print(f"    [dim]({', '.join(hints)})[/dim]")
            else:
                console.print(f"[green]✓[/green] Using: [cyan]{item_selector}[/cyan]")
        else:
            item_selector = choice
            console.print(f"[green]✓[/green] Using custom: [cyan]{item_selector}[/cyan]")

    if not item_selector:
        console.print("[yellow]No containers detected. Enter selector manually.[/yellow]\n")
        item_selector = Prompt.ask("Item selector (CSS)", default=".item")
        console.print(f"[green]✓[/green] Using custom: [cyan]{item_selector}[/cyan]")

    # Step 4: Fields
    console.print()
    console.print(
        Panel(
            "[bold]Step 3: Fields[/bold]\nDefine fields to extract from each item",
            title="Field Definitions",
            title_align="left",
            border_style="cyan",
            expand=False,
        )
    )

    # Fields dict initialized at function start

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
            header_style="bold yellow",
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
            before_count = len(fields)
            for field in suggested_fields:
                field_name = field["name"]
                selector = field["selector"]

                # Auto-detect attributes
                attr: str | None = None
                if "href" in selector.lower() or field_name.lower() in ["url", "link"]:
                    attr = "href"
                elif "src" in selector.lower() or field_name.lower() in ["image", "img"]:
                    attr = "src"

                fields[field_name] = FieldSchema(selector=selector, attribute=attr)
            added_count = len(fields) - before_count
            console.print(f"[green]✓[/green] Added {added_count} fields")
        else:
            console.print(
                "\n[dim]Select individual fields (comma-separated numbers, e.g., '1,3,5', 'all', or 'none'):[/dim]"
            )
            selection = Prompt.ask("Fields to include", default="all")

            selected_indices: list[int]
            while True:
                normalized = selection.strip().lower()
                if normalized in {"all", "*"}:
                    selected_indices = list(range(1, len(suggested_fields) + 1))
                    break
                if normalized in {"none", ""}:
                    selected_indices = []
                    break

                try:
                    selected_indices = [int(x.strip()) for x in selection.split(",") if x.strip()]
                except ValueError:
                    console.print("[yellow]Invalid selection. Try again.[/yellow]")
                    selection = Prompt.ask("Fields to include", default="none")
                    continue

                valid_indices = [
                    idx for idx in selected_indices if 1 <= idx <= len(suggested_fields)
                ]
                if valid_indices:
                    selected_indices = valid_indices
                    break

                console.print(
                    "[yellow]No valid field numbers found. Try again or enter 'none'.[/yellow]"
                )
                selection = Prompt.ask("Fields to include", default="none")

            before_count = len(fields)
            for idx in selected_indices:
                field = suggested_fields[idx - 1]
                field_name = field["name"]
                selector = field["selector"]

                # Auto-detect attributes
                attr = None
                if "href" in selector.lower() or field_name.lower() in ["url", "link"]:
                    attr = "href"
                elif "src" in selector.lower() or field_name.lower() in ["image", "img"]:
                    attr = "src"

                fields[field_name] = FieldSchema(selector=selector, attribute=attr)

            added_count = len(fields) - before_count
            console.print(f"[green]✓[/green] Added {added_count} fields")

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
        attr_choice: str | None = None
        if "href" in selector.lower() or field_name.lower() in ["url", "link"]:
            if Confirm.ask("Extract 'href' attribute?", default=True):
                attr_choice = "href"
        elif "src" in selector.lower() or field_name.lower() in ["image", "img"]:
            if Confirm.ask("Extract 'src' attribute?", default=True):
                attr_choice = "src"
        else:
            custom_attr = Prompt.ask("Extract attribute (leave empty for text)", default="")
            if custom_attr.strip():
                attr_choice = custom_attr.strip()

        required = Confirm.ask(f"Is '{field_name}' required?", default=False)

        fields[field_name] = FieldSchema(
            selector=selector, attribute=attr_choice if attr_choice else None, required=required
        )

        console.print(f"[green]✓[/green] Added field: {field_name}")

    if not fields:
        console.print("[red]Error: At least one field is required[/red]")
        raise ValueError("At least one field is required")

    # Step 5: Pagination (optional)
    console.print()
    console.print(
        Panel(
            "[bold]Step 4: Pagination (Optional)[/bold]\nConfigure multi-page extraction",
            title="Pagination",
            title_align="left",
            border_style="cyan",
            expand=False,
        )
    )

    pagination_candidates = []
    if analysis:
        pagination_candidates = (analysis.get("suggestions") or {}).get(
            "pagination_candidates"
        ) or []

    pagination = None
    enable_default = bool(pagination_candidates)
    if Confirm.ask("Enable pagination?", default=enable_default):
        pagination = _prompt_pagination_config(pagination_candidates)

    # Build schema
    # Ensure item_selector is set
    if item_selector is None:
        raise ValueError("Item selector cannot be empty")

    schema = ExtractionSchema(
        name=name,
        description=description if description.strip() else None,
        url=url if url and url.strip() else None,
        item_selector=item_selector,
        fields=fields,
        pagination=pagination,
    )

    # Summary
    console.print()
    console.print(
        Panel(
            f"[bold]Name:[/bold] {schema.name}\n"
            f"[bold]Item selector:[/bold] [cyan]{schema.item_selector}[/cyan]\n"
            f"[bold]Fields:[/bold] {len(schema.fields)} ({', '.join(schema.fields.keys())})\n"
            + (
                f"[bold]Pagination:[/bold] enabled (max: {schema.pagination.max_pages or 'unlimited'})"
                if schema.pagination
                else "[bold]Pagination:[/bold] disabled"
            ),
            title="Schema Summary",
            title_align="left",
            border_style="green",
            expand=False,
        )
    )

    return schema


def _build_schema_simple(
    url: str | None = None, analysis: dict[str, Any] | None = None, html: str | None = None
) -> ExtractionSchema:
    """Fallback builder without rich library."""
    print("\n=== Survey Builder ===")

    # Schema metadata
    name = input("Schema name [extraction]: ").strip() or "extraction"
    description = input("Description (optional): ").strip()

    # Item selector
    print("\nItem Selector:")
    if analysis and analysis.get("containers"):
        print("Suggested containers:")
        containers = analysis["containers"][:3]
        for idx, cont in enumerate(containers, 1):
            selector = cont.get("child_selector") or cont.get("selector") or "—"
            count = cont.get("item_count", 0)
            print(f"  {idx}. {selector} ({count} items)")

        choice = input("\nSelect option or enter custom [1]: ").strip() or "1"
        if choice.isdigit() and 1 <= int(choice) <= len(containers):
            item_selector = (
                containers[int(choice) - 1].get("child_selector")
                or containers[int(choice) - 1].get("selector")
                or ".item"
            )
        else:
            item_selector = choice
    else:
        item_selector = input("Item selector: ").strip()

    # Ensure we have a usable selector string
    if not item_selector:
        item_selector = ".item"

    # Fields
    print("\nFields:")
    fields: dict[str, FieldSchema] = {}

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
        fields=fields,
    )

    print(f"\n✓ Schema created: {name}")
    return schema


def load_analysis_from_file(path: str | Path) -> dict[str, Any]:
    """Load Probe analysis from JSON file."""
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Analysis file not found: {path}")

    with path.open() as f:
        data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("Analysis file must be a JSON object")
        return data
