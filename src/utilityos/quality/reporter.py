"""Rich-formatted quality report generation for terminal output."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from utilityos.quality.schema import QualityReport


def print_quality_report(report: QualityReport, console: Console | None = None) -> None:
    """Print a quality report using Rich formatting."""
    if console is None:
        console = Console()

    # Header
    title = f"Quality Report: {report.entity_name or 'All Entities'}"
    console.print(f"\n[bold]{title}[/bold]")
    console.print(f"Layer: {report.layer}")
    console.print()

    # Summary
    pass_style = "green" if report.failed_checks == 0 else "red"
    console.print(f"Total Checks: {report.total_checks}")
    console.print(f"Passed: [green]{report.passed_checks}[/green]")
    console.print(f"Failed: [{pass_style}]{report.failed_checks}[/{pass_style}]")
    console.print(f"Pass Rate: [{pass_style}]{report.pass_rate:.1%}[/{pass_style}]")
    console.print()

    if not report.results:
        console.print("[dim]No checks were executed.[/dim]")
        return

    # Results table
    table = Table(title="Check Results")
    table.add_column("Check", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Status", justify="center")
    table.add_column("Checked", justify="right")
    table.add_column("Failed", justify="right")
    table.add_column("Rate", justify="right")

    for r in report.results:
        status_style = "green" if r.passed else "red bold"
        status_text = "PASS" if r.passed else "FAIL"

        table.add_row(
            r.check_name,
            r.check_type,
            f"[{status_style}]{status_text}[/{status_style}]",
            str(r.records_checked),
            str(r.records_failed),
            f"{r.failure_rate:.2%}",
        )

    console.print(table)
