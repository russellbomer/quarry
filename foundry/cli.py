"""CLI interface for Foundry."""

import os
import sqlite3
import sys
from pathlib import Path
from urllib.parse import urlparse

import typer
from rich.console import Console
from rich.table import Table

from foundry.core import load_yaml, run_job
from foundry.lib.robots import RobotsCache
from foundry.state import open_db
from foundry.wizard import run_wizard

# Constants
HIGH_RATE_LIMIT_THRESHOLD = 5.0

app = typer.Typer(
    help=(
        "Foundry - Web scraping toolkit with offline testing, "
        "rate limiting, and robots.txt compliance."
    ),
    add_completion=False,
)
console = Console()


@app.command()
def init() -> None:
    """
    Run interactive wizard to create a new job YAML.

    Guides you through:
    - Job name
    - Source URL and parser
    - Output format (Parquet/CSV/JSONL)
    - Rate limits and policy

    Example:
        $ python -m foundry.cli init
    """
    try:
        run_wizard()
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def run(
    job_yaml: str = typer.Argument(..., help="Path to job YAML file (e.g., jobs/fda.yml)"),
    max_items: int = typer.Option(200, "--max-items", "-n", help="Maximum items to collect"),
    offline: bool = typer.Option(True, "--offline/--live", help="Offline=fixtures, Live=HTTP"),
    db: str | None = typer.Option(None, "--db", help="SQLite DB path"),
    timezone: str = typer.Option("America/New_York", "--timezone", "-tz", help="Timezone"),
    ignore_robots: bool = typer.Option(False, "--ignore-robots", help="Bypass robots.txt checks (testing only)"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Prompt when robots.txt blocks access"),
) -> None:
    """
    Run a single scraping job from YAML file.

    Offline mode (default): Uses cached HTML fixtures, no network requests.
    Live mode: Makes real HTTP requests, respects robots.txt and rate limits.

    Examples:
        # Run FDA example offline (safe, fast)
        $ python -m scrapesuite.cli run examples/jobs/fda.yml --offline

        # Run your job live (careful! hits real URLs)
        $ python -m scrapesuite.cli run jobs/my_job.yml --live --max-items 10

        # Interactive mode: prompt when sites block
        $ python -m scrapesuite.cli run jobs/my_job.yml --live --interactive

        # Check what was scraped
        $ python -m scrapesuite.cli state
    """
    try:
        # Set environment variables for robots.txt handling
        if ignore_robots:
            os.environ["FOUNDRY_IGNORE_ROBOTS"] = "1"
        if interactive:
            os.environ["FOUNDRY_INTERACTIVE"] = "1"
        
        job_dict = load_yaml(job_yaml)
        df, next_cursor = run_job(
            job_dict,
            max_items=max_items,
            offline=offline,
            db_path=db,
            timezone=timezone,
        )

        # Count new items (first_seen = last_seen means newly inserted)
        conn = open_db(db)
        cursor_row = conn.execute(
            "SELECT COUNT(*) as count FROM items WHERE job = ? AND first_seen = last_seen",
            (job_dict["job"],),
        ).fetchone()
        new_count = cursor_row["count"] if cursor_row else 0
        conn.close()

        summary = (
            f"{job_dict['job']}: {new_count} new, {len(df)} in batch, next_cursor={next_cursor}"
        )
        console.print(f"[green]{summary}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    finally:
        # Clean up environment variables
        os.environ.pop("FOUNDRY_IGNORE_ROBOTS", None)
        os.environ.pop("FOUNDRY_INTERACTIVE", None)


@app.command("run-all")
def run_all(
    max_items: int = typer.Option(200, "--max-items", "-n"),
    offline: bool = typer.Option(True, "--offline/--live"),
    db: str | None = typer.Option(None, "--db", help="SQLite database path"),
    timezone: str = typer.Option("America/New_York", "--timezone", "-tz"),
    ignore_robots: bool = typer.Option(False, "--ignore-robots", help="Bypass robots.txt checks (testing only)"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Prompt when robots.txt blocks access"),
) -> None:
    """Run all jobs in the jobs/ directory."""
    # Set environment variables for robots.txt handling
    if ignore_robots:
        os.environ["FOUNDRY_IGNORE_ROBOTS"] = "1"
    if interactive:
        os.environ["FOUNDRY_INTERACTIVE"] = "1"
    
    try:
        jobs_dir = Path("jobs")
        if not jobs_dir.exists():
            console.print("[red]jobs/ directory not found[/red]")
            sys.exit(1)

        yaml_files = sorted(jobs_dir.glob("*.yml"))
        if not yaml_files:
            console.print("[yellow]No job YAML files found[/yellow]")
            return

        for yaml_file in yaml_files:
            try:
                job_dict = load_yaml(str(yaml_file))
                df, next_cursor = run_job(
                    job_dict,
                    max_items=max_items,
                    offline=offline,
                    db_path=db,
                    timezone=timezone,
                )

                conn = open_db(db)
                cursor_row = conn.execute(
                    "SELECT COUNT(*) as count FROM items WHERE job = ? AND first_seen = last_seen",
                    (job_dict["job"],),
                ).fetchone()
                new_count = cursor_row["count"] if cursor_row else 0
                conn.close()

                summary = (
                    f"{job_dict['job']}: {new_count} new, {len(df)} in batch, next_cursor={next_cursor}"
                )
                console.print(f"[green]{summary}[/green]")
            except Exception as e:
                console.print(f"[red]Error in {yaml_file}: {e}[/red]")
                continue
    finally:
        # Clean up environment variables
        os.environ.pop("FOUNDRY_IGNORE_ROBOTS", None)
        os.environ.pop("FOUNDRY_INTERACTIVE", None)


@app.command()
def state(
    db: str | None = typer.Option(None, "--db", help="SQLite database path"),
) -> None:
    """Show job state (last cursor and last run time)."""
    try:
        conn = open_db(db)
        rows = conn.execute(
            "SELECT job, last_cursor, last_run FROM jobs_state ORDER BY job"
        ).fetchall()
        conn.close()

        if not rows:
            console.print("[yellow]No job state found[/yellow]")
            return

        table = Table(title="Job State")
        table.add_column("Job", style="cyan")
        table.add_column("Last Cursor", style="green")
        table.add_column("Last Run", style="yellow")

        for row in rows:
            table.add_row(
                row["job"] or "",
                row["last_cursor"] or "(none)",
                row["last_run"] or "(never)",
            )

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def batch(
    urls_file: str = typer.Argument(..., help="File with URLs (one per line)"),
    out: str = typer.Option("data/out/results.jsonl", "--out", "-o"),
    max_items: int = typer.Option(200, "--max-items", "-n"),
    offline: bool = typer.Option(False, "--offline/--live"),
    db: str | None = typer.Option(None, "--db"),
    ignore_robots: bool = typer.Option(False, "--ignore-robots", help="Bypass robots.txt checks (testing only)"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Prompt when robots.txt blocks access"),
) -> None:
    """
    Scrape a list of URLs and write results to JSONL.

    Creates an ephemeral job using the custom connector.
    """
    # Default timezone for batch operations
    timezone = "America/New_York"

    try:
        # Set environment variables for robots.txt handling
        if ignore_robots:
            os.environ["FOUNDRY_IGNORE_ROBOTS"] = "1"
        if interactive:
            os.environ["FOUNDRY_INTERACTIVE"] = "1"
        
        # Read URLs
        urls_path = Path(urls_file)
        if not urls_path.exists():
            console.print(f"[red]File not found: {urls_file}[/red]")
            sys.exit(1)

        with open(urls_path, encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

        if not urls:
            console.print("[yellow]No URLs found in file[/yellow]")
            return

        # Build allowlist from URL domains
        allowlist = list({urlparse(url).netloc for url in urls})

        # Create ephemeral job spec
        job_dict = {
            "version": "1",
            "job": "batch_urls",
            "source": {
                "kind": "html",
                "entry": urls[0],  # Use first URL as entry point
                "parser": "custom_list",
                "rate_limit_rps": 1.0,
                "cursor": {"field": "id", "stop_when_seen": False},
            },
            "transform": {"pipeline": [{"normalize": "custom"}]},
            "sink": {"kind": "jsonl", "path": out},
            "policy": {"robots": "allow", "allowlist": allowlist},
        }

        df, _ = run_job(
            job_dict, max_items=max_items, offline=offline, db_path=db, timezone=timezone
        )

        console.print(f"[green]Processed {len(df)} URLs → {out}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    finally:
        # Clean up environment variables
        os.environ.pop("FOUNDRY_IGNORE_ROBOTS", None)
        os.environ.pop("FOUNDRY_INTERACTIVE", None)


@app.command()
def check_robots(
    url: str = typer.Argument(..., help="URL to check against robots.txt"),
    user_agent: str = typer.Option("Foundry", "--user-agent", "-ua", help="User-Agent string"),
) -> None:
    """
    Check if a URL is allowed by robots.txt.

    Fetches and caches robots.txt for the domain, then checks if the URL
    is allowed for the specified User-Agent.

    Examples:
        $ python -m foundry.cli check-robots https://github.com/explore
        $ python -m foundry.cli check-robots https://reddit.com/r/python -ua "MyBot"
    """
    try:
        cache = RobotsCache()
        parsed = urlparse(url)
        domain = parsed.netloc

        # Check if allowed
        is_allowed = cache.is_allowed(url, user_agent)
        crawl_delay = cache.get_crawl_delay(domain)

        # Display results
        table = Table(title=f"Robots.txt Check: {domain}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("URL", url)
        table.add_row("User-Agent", user_agent)
        table.add_row("Allowed", "✅ YES" if is_allowed else "❌ NO")
        table.add_row("Crawl-delay", f"{crawl_delay}s" if crawl_delay > 0 else "None")

        console.print(table)

        if not is_allowed:
            console.print("\n[yellow]⚠️  This URL is disallowed by robots.txt[/yellow]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def failed(
    job: str = typer.Argument(None, help="Job name to show failures for (or all jobs)"),
    db: str | None = typer.Option(None, "--db", help="SQLite database path"),
) -> None:
    """
    Show failed URLs for a job.

    Lists all URLs that failed to fetch, with error messages and retry counts.

    Examples:
        $ python -m foundry.cli failed fda_recalls
        $ python -m foundry.cli failed  # Show all failed URLs
    """
    try:
        conn = open_db(db)

        if job:
            query = (
                "SELECT url, error_message, retry_count, last_attempt "
                "FROM failed_urls WHERE job = ? ORDER BY retry_count DESC"
            )
            rows = conn.execute(query, (job,)).fetchall()
            title = f"Failed URLs: {job}"
        else:
            query = (
                "SELECT job, url, error_message, retry_count, last_attempt "
                "FROM failed_urls ORDER BY retry_count DESC"
            )
            rows = conn.execute(query).fetchall()
            title = "All Failed URLs"

        conn.close()

        if not rows:
            console.print("[green]✅ No failed URLs[/green]")
            return

        table = Table(title=title)
        if not job:
            table.add_column("Job", style="cyan")
        table.add_column("URL", style="yellow", max_width=50)
        table.add_column("Error", style="red", max_width=40)
        table.add_column("Retries", style="magenta", justify="right")
        table.add_column("Last Attempt", style="dim")

        for row in rows:
            if job:
                table.add_row(
                    row["url"],
                    row["error_message"],
                    str(row["retry_count"]),
                    row["last_attempt"],
                )
            else:
                table.add_row(
                    row["job"],
                    row["url"],
                    row["error_message"],
                    str(row["retry_count"]),
                    row["last_attempt"],
                )

        console.print(table)
        console.print(f"\n[yellow]Total failed URLs: {len(rows)}[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def inspect(
    job_yaml: str = typer.Argument(..., help="Path to job YAML file"),
) -> None:
    """
    Inspect a job configuration without running it.

    Shows parsed job details, validates YAML, and checks for common issues.

    Examples:
        $ python -m foundry.cli inspect jobs/fda.yml
        $ python -m foundry.cli inspect examples/jobs/nws.yml
    """
    try:
        job_dict = load_yaml(job_yaml)

        # Basic info
        table = Table(title=f"Job Inspection: {job_yaml}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Job Name", job_dict["job"])
        table.add_row("Version", job_dict["version"])
        table.add_row("Parser", job_dict["source"]["parser"])
        table.add_row("Entry URL", job_dict["source"].get("entry", "(none)"))
        table.add_row("Sink Type", job_dict["sink"]["kind"])
        table.add_row("Sink Path", job_dict["sink"]["path"])

        # Policy
        policy = job_dict.get("policy", {})
        if policy:
            allowlist = policy.get("allowlist", [])
            rate_limits = policy.get("rate_limits", {})
            default_rps = policy.get("default_rps", 1.0)

            table.add_row("Allowlist", ", ".join(allowlist) if allowlist else "(none)")
            table.add_row("Default RPS", str(default_rps))
            if rate_limits:
                for domain, rps in rate_limits.items():
                    table.add_row(f"  {domain}", f"{rps} req/sec")

        console.print(table)

        # Validation warnings
        console.print("\n[bold]Validation:[/bold]")

        warnings = []

        if not policy.get("allowlist") and job_dict["source"].get("entry"):
            warnings.append("⚠️  No allowlist defined (required for live mode)")

        if policy.get("default_rps", 1.0) > HIGH_RATE_LIMIT_THRESHOLD:
            warnings.append("⚠️  High default rate limit (>5 req/sec) - be careful!")

        if not warnings:
            console.print("[green]✅ No issues found[/green]")
        else:
            for warning in warnings:
                console.print(f"[yellow]{warning}[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def cache_info(
    db: str | None = typer.Option(None, "--db", help="SQLite database path"),
) -> None:
    """
    Show information about cached data.

    Displays robots.txt cache, job state, and item counts.

    Examples:
        $ python -m foundry.cli cache-info
    """
    try:
        console.print("[bold]Cache Information[/bold]\n")

        # Robots cache
        robots_db = "data/cache/robots.sqlite"
        if os.path.exists(robots_db):
            conn = sqlite3.connect(robots_db)
            conn.row_factory = sqlite3.Row
            query = "SELECT domain, crawl_delay, fetched_at FROM robots_cache"
            rows = conn.execute(query).fetchall()
            conn.close()

            console.print(f"[cyan]Robots.txt Cache:[/cyan] {len(rows)} domains")
            if rows:
                table = Table()
                table.add_column("Domain", style="cyan")
                table.add_column("Crawl-delay", style="green")
                table.add_column("Cached At", style="dim")

                for row in rows:
                    table.add_row(row["domain"], f"{row['crawl_delay']}s", row["fetched_at"][:19])

                console.print(table)
        else:
            console.print("[dim]No robots.txt cache found[/dim]")

        console.print()

        # Job state
        conn = open_db(db)

        # Item counts per job
        rows = conn.execute(
            "SELECT job, COUNT(*) as count FROM items GROUP BY job ORDER BY count DESC"
        ).fetchall()

        if rows:
            console.print("[cyan]Cached Items:[/cyan]")
            table = Table()
            table.add_column("Job", style="cyan")
            table.add_column("Items", style="green", justify="right")

            for row in rows:
                table.add_row(row["job"], str(row["count"]))

            console.print(table)

        conn.close()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    app()
