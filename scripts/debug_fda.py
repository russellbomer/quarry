"""Debug script to investigate FDA selector detection."""

from pathlib import Path
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table

from scrapesuite.http import get_html
from scrapesuite.inspector import find_item_selector, inspect_html

console = Console()

def compare_html_structures():
    """Compare fixture vs live HTML structure."""
    
    # Load fixture
    fixture_path = Path("tests/fixtures/fda_list.html")
    console.print(f"[cyan]Loading fixture: {fixture_path}[/cyan]")
    
    if not fixture_path.exists():
        console.print(f"[red]Fixture not found: {fixture_path}[/red]")
        return
    
    with open(fixture_path, 'r', encoding='utf-8') as f:
        fixture_html = f.read()
    
    # Fetch live HTML
    console.print("\n[cyan]Fetching live FDA page...[/cyan]")
    try:
        live_html = get_html("https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts")
        console.print("[green]✓ Fetched successfully[/green]")
        
        # Save for inspection
        Path("/tmp/fda_live.html").write_text(live_html, encoding='utf-8')
        console.print("[dim]Saved to /tmp/fda_live.html[/dim]")
    except Exception as e:
        console.print(f"[red]Failed to fetch: {e}[/red]")
        live_html = None
    
    # Analyze both
    console.print("\n" + "="*80)
    console.print("[bold cyan]FIXTURE HTML ANALYSIS[/bold cyan]")
    console.print("="*80)
    
    fixture_analysis = inspect_html(fixture_html)
    console.print(f"Title: {fixture_analysis['title']}")
    console.print(f"Total links: {fixture_analysis['total_links']}")
    
    fixture_candidates = find_item_selector(fixture_html, min_items=3)
    
    table = Table(title="Fixture - Detected Patterns")
    table.add_column("Selector", style="green")
    table.add_column("Count", style="yellow")
    table.add_column("Sample", style="white")
    
    for candidate in fixture_candidates[:10]:
        table.add_row(
            candidate["selector"],
            str(candidate["count"]),
            candidate.get("sample_title", "")[:50]
        )
    
    console.print(table)
    
    # Check for expected selector
    expected_selector = ".recall-item"
    fixture_soup = BeautifulSoup(fixture_html, 'html.parser')
    fixture_items = fixture_soup.select(expected_selector)
    console.print(f"\n[cyan]Items with '{expected_selector}': {len(fixture_items)}[/cyan]")
    
    if fixture_items:
        console.print("\n[cyan]Sample item structure:[/cyan]")
        sample = fixture_items[0]
        console.print(f"Tag: {sample.name}")
        console.print(f"Classes: {sample.get('class', [])}")
        console.print(f"First 200 chars: {str(sample)[:200]}")
    
    if live_html:
        console.print("\n" + "="*80)
        console.print("[bold cyan]LIVE HTML ANALYSIS[/bold cyan]")
        console.print("="*80)
        
        live_analysis = inspect_html(live_html)
        console.print(f"Title: {live_analysis['title']}")
        console.print(f"Total links: {live_analysis['total_links']}")
        
        live_candidates = find_item_selector(live_html, min_items=3)
        
        table = Table(title="Live - Detected Patterns")
        table.add_column("Selector", style="green")
        table.add_column("Count", style="yellow")
        table.add_column("Sample", style="white")
        
        for candidate in live_candidates[:10]:
            table.add_row(
                candidate["selector"],
                str(candidate["count"]),
                candidate.get("sample_title", "")[:50]
            )
        
        console.print(table)
        
        # Check for expected selector
        live_soup = BeautifulSoup(live_html, 'html.parser')
        live_items = live_soup.select(expected_selector)
        console.print(f"\n[cyan]Items with '{expected_selector}': {len(live_items)}[/cyan]")
        
        if live_items:
            console.print("\n[cyan]Sample item structure:[/cyan]")
            sample = live_items[0]
            console.print(f"Tag: {sample.name}")
            console.print(f"Classes: {sample.get('class', [])}")
            console.print(f"First 200 chars: {str(sample)[:200]}")
        else:
            # Let's inspect what the actual structure is
            console.print("\n[yellow]Expected selector not found. Let's check what's actually there...[/yellow]")
            
            # Look for common recall/article patterns
            for selector in ["article", ".item", ".result", ".listing", "li", "[class*='recall']"]:
                items = live_soup.select(selector)
                if len(items) >= 3:
                    console.print(f"\n[cyan]Found {len(items)} items with '{selector}'[/cyan]")
                    if items:
                        sample = items[0]
                        console.print(f"Sample structure:\n{str(sample)[:400]}")
                        break
    
    # Compare
    if live_html:
        console.print("\n" + "="*80)
        console.print("[bold yellow]COMPARISON[/bold yellow]")
        console.print("="*80)
        
        fixture_selectors = {c["selector"] for c in fixture_candidates}
        live_selectors = {c["selector"] for c in live_candidates}
        
        only_fixture = fixture_selectors - live_selectors
        only_live = live_selectors - fixture_selectors
        both = fixture_selectors & live_selectors
        
        if both:
            console.print(f"[green]Common selectors ({len(both)}):[/green]")
            for s in sorted(both):
                console.print(f"  • {s}")
        
        if only_fixture:
            console.print(f"\n[yellow]Only in fixture ({len(only_fixture)}):[/yellow]")
            for s in sorted(only_fixture):
                console.print(f"  • {s}")
        
        if only_live:
            console.print(f"\n[cyan]Only in live ({len(only_live)}):[/cyan]")
            for s in sorted(only_live):
                console.print(f"  • {s}")

if __name__ == "__main__":
    compare_html_structures()
