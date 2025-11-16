"""Output formatting for Probe tool."""

import json
from typing import Any


def format_as_json(analysis: dict[str, Any], pretty: bool = True) -> str:
    """
    Format analysis as JSON.
    
    Args:
        analysis: Analysis result from analyze_page()
        pretty: Whether to pretty-print (default True)
    
    Returns:
        JSON string
    """
    if pretty:
        return json.dumps(analysis, indent=2, ensure_ascii=False)
    return json.dumps(analysis, ensure_ascii=False)


def format_as_terminal(analysis: dict[str, Any]) -> str:
    """
    Format analysis for terminal output with colors and structure.
    
    Args:
        analysis: Analysis result from analyze_page()
    
    Returns:
        Formatted string for terminal display
    """
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich import box
        
        # Create output buffer
        from io import StringIO
        output = StringIO()
        console = Console(file=output, width=100, force_terminal=True)
        
        # Header with elegant spacing
        url = analysis.get("url", "")
        console.print()
        console.print("╭────────────────────────────────────────────────────╮", style="cyan")
        console.print("│ [bold cyan]SCOUT ANALYSIS[/bold cyan]                            │", style="cyan")
        console.print("╰────────────────────────────────────────────────────╯", style="cyan")
        
        if url:
            console.print(f"[dim]{url}[/dim]")
        console.print()
        
        # Metadata section
        metadata = analysis.get("metadata", {})
        if metadata.get("title"):
            title_text = metadata["title"]
            desc_text = metadata.get("description", "")
            
            content = f"[bold white]{title_text}[/bold white]"
            if desc_text:
                content += f"\n[dim]{desc_text}[/dim]"
            
            console.print(Panel(
                content,
                title="Page Info",
                title_align="left",
                border_style="blue",
                padding=(0, 1),
                expand=False
            ))
            console.print()
        
        # Framework detection
        frameworks = analysis.get("frameworks", [])
        if frameworks:
            table = Table(
                title="Detected Frameworks",
                title_style="bold",
                title_justify="left",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold cyan",
                border_style="cyan"
            )
            table.add_column("Framework", style="cyan bold", no_wrap=True)
            table.add_column("Confidence", style="green", justify="right", width=12)
            table.add_column("Version", style="yellow dim", width=15)
            
            for fw in frameworks[:5]:  # Top 5
                name = fw.get("name", "unknown").title()
                conf_pct = f"{fw.get('confidence', 0) * 100:.1f}%"
                version = fw.get("version") or "—"
                table.add_row(name, conf_pct, version)
            
            console.print(table)
            console.print()
        
        # Containers (item patterns)
        containers = analysis.get("containers", [])
        if containers:
            table = Table(
                title="Detected Item Containers",
                title_style="bold",
                title_justify="left",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta",
                border_style="magenta"
            )
            table.add_column("CSS Selector", style="magenta", max_width=60, overflow="fold")
            table.add_column("Count", style="green bold", justify="right", width=8)
            table.add_column("Sample Text", style="dim", max_width=35, overflow="ellipsis")
            
            for cont in containers[:5]:  # Top 5
                selector = (
                    cont.get("child_selector")
                    or cont.get("direct_child_selector")
                    or cont.get("selector")
                    or "—"
                )
                count = str(cont.get("item_count", 0))
                sample = cont.get("sample_text", "")
                # Clean and truncate sample
                sample = " ".join(sample.split())[:35]
                
                table.add_row(selector, count, sample)
            
            console.print(table)
            console.print()
        
        # Best container suggestion
        suggestions = analysis.get("suggestions", {})
        best_container = suggestions.get("best_container")
        if best_container:
            selector = (
                best_container.get("child_selector")
                or best_container.get("direct_child_selector")
                or best_container.get("selector")
                or "—"
            )
            count = best_container.get("item_count", 0)
            
            console.print(Panel(
                f"[bold green]Recommended Selector[/bold green]\n\n"
                f"[cyan]{selector}[/cyan]\n"
                f"[dim]Found {count} items matching this pattern[/dim]",
                title="Best Container",
                title_align="left",
                border_style="green",
                padding=(0, 1),
                expand=False
            ))
            console.print()
        
        # Field suggestions
        field_candidates = suggestions.get("field_candidates", [])
        if field_candidates:
            table = Table(
                title="Suggested Fields",
                title_style="bold",
                title_justify="left",
                box=box.SIMPLE,
                show_header=True,
                header_style="bold yellow",
                border_style="yellow"
            )
            table.add_column("Field Name", style="yellow bold", width=15)
            table.add_column("CSS Selector", style="cyan", width=30, overflow="fold")
            table.add_column("Sample Value", style="white dim", max_width=35, overflow="ellipsis")
            
            for field in field_candidates[:8]:  # Top 8
                name = field.get("name", "").title()
                selector = field.get("selector", "")
                sample = field.get("sample", "")
                # Clean sample text
                sample = " ".join(sample.split())[:35]
                
                table.add_row(name, selector, sample)
            
            console.print(table)
            console.print()
        
        # Framework hint
        framework_hint = suggestions.get("framework_hint")
        if framework_hint:
            name = framework_hint.get("name", "").title()
            recommendation = framework_hint.get("recommendation", "")
            confidence = framework_hint.get("confidence", 0)
            
            console.print(Panel(
                f"[bold cyan]{name}[/bold cyan] detected\n\n"
                f"[white]{recommendation}[/white]",
                title="Framework Recommendation",
                title_align="left",
                border_style="yellow",
                padding=(0, 1),
                expand=False
            ))
            console.print()
        
        # Infinite scroll detection warning
        infinite_scroll = suggestions.get("infinite_scroll", {})
        if infinite_scroll.get("detected"):
            confidence = infinite_scroll.get("confidence", 0) * 100
            signals = infinite_scroll.get("signals", [])
            
            warning_text = f"[bold yellow]⚠ Infinite Scroll Detected[/bold yellow] ({confidence:.0f}% confidence)\n\n"
            warning_text += "[dim]This page appears to use infinite scroll. Traditional selectors may not work.[/dim]\n\n"
            warning_text += "[bold]Detected signals:[/bold]\n"
            for signal in signals[:5]:
                warning_text += f"  • {signal}\n"
            
            warning_text += "\n[bold cyan]💡 Solution:[/bold cyan] Find the underlying API endpoint\n"
            warning_text += "[dim]Run:[/dim] [cyan]quarry scout --find-api[/cyan]"
            
            console.print(Panel(
                warning_text,
                title="Infinite Scroll Warning",
                title_align="left",
                border_style="yellow",
                padding=(0, 1)
            ))
            console.print()
        
        # Statistics
        stats = analysis.get("statistics", {})
        if stats:
            console.print(Panel(
                f"[cyan]•[/cyan] Elements: [bold]{stats.get('total_elements', 0):,}[/bold]\n"
                f"[cyan]•[/cyan] Links: [bold]{stats.get('total_links', 0):,}[/bold]\n"
                f"[cyan]•[/cyan] Images: [bold]{stats.get('total_images', 0):,}[/bold]\n"
                f"[cyan]•[/cyan] Forms: [bold]{stats.get('total_forms', 0):,}[/bold]\n"
                f"[cyan]•[/cyan] Text: [bold]{stats.get('text_words', 0):,}[/bold] words",
                title="Page Statistics",
                title_align="left",
                border_style="blue",
                padding=(0, 1),
                expand=False
            ))
        
        console.print()
        return output.getvalue()
        
    except ImportError:
        # Fallback to simple text if rich is not available
        return _format_as_simple_text(analysis)


def _format_as_simple_text(analysis: dict[str, Any]) -> str:
    """Fallback formatter without rich library."""
    lines = []
    lines.append("\n=== Probe Analysis Results ===\n")
    
    url = analysis.get("url")
    if url:
        lines.append(f"URL: {url}\n")
    
    # Metadata
    metadata = analysis.get("metadata", {})
    if metadata.get("title"):
        lines.append(f"\nTitle: {metadata['title']}")
        if metadata.get("description"):
            lines.append(f"Description: {metadata['description']}\n")
    
    # Frameworks
    frameworks = analysis.get("frameworks", [])
    if frameworks:
        lines.append("\n--- Detected Frameworks ---")
        for fw in frameworks[:5]:
            conf = f"{fw['confidence'] * 100:.1f}%"
            version = fw.get("version") or "unknown"
            lines.append(f"  • {fw['name']} ({conf}) - v{version}")
    
    # Containers
    containers = analysis.get("containers", [])
    if containers:
        lines.append("\n--- Item Containers ---")
        for cont in containers[:5]:
            selector = cont.get("child_selector", "")
            count = cont.get("item_count", 0)
            lines.append(f"  • {selector} ({count} items)")
    
    # Suggestions
    suggestions = analysis.get("suggestions", {})
    if suggestions.get("item_selector"):
        lines.append(f"\n--- Suggestion ---")
        lines.append(f"Best selector: {suggestions['item_selector']}")
    
    # Stats
    stats = analysis.get("statistics", {})
    if stats:
        lines.append(f"\n--- Statistics ---")
        lines.append(f"  Elements: {stats.get('total_elements', 0):,}")
        lines.append(f"  Links: {stats.get('total_links', 0):,}")
        lines.append(f"  Images: {stats.get('total_images', 0):,}")
    
    lines.append("\n")
    return "\n".join(lines)
