"""CLI commands for pipeline execution."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from utilityos.pipeline.registry import PipelineRegistry

pipeline_app = typer.Typer(no_args_is_help=True)
console = Console()

# Global registry — pipelines are registered at import time
_registry = PipelineRegistry()


def get_registry() -> PipelineRegistry:
    """Get the global pipeline registry."""
    return _registry


@pipeline_app.command("list")
def list_pipelines() -> None:
    """List all registered pipelines."""
    registry = get_registry()
    names = registry.list_pipelines()

    if not names:
        console.print("[dim]No pipelines registered.[/dim]")
        console.print(
            "[dim]Create pipeline modules in utilityos.pipeline.steps[/dim]"
        )
        return

    table = Table(title="Registered Pipelines")
    table.add_column("Name", style="cyan")
    table.add_column("Source System")
    table.add_column("Target Entity")
    table.add_column("Steps", justify="right")

    for name in names:
        pipeline = registry.get(name)
        table.add_row(
            pipeline.name,
            pipeline.source_system,
            pipeline.target_entity,
            str(len(pipeline.steps)),
        )

    console.print(table)


@pipeline_app.command("run")
def run_pipeline(
    name: str = typer.Argument(help="Pipeline name to execute"),
    full: bool = typer.Option(
        False, "--full", help="Force full reload (ignore incremental)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Validate without executing"
    ),
) -> None:
    """Run a named pipeline."""
    from utilityos.pipeline.context import PipelineContext

    registry = get_registry()

    try:
        pipeline = registry.get(name)
    except Exception as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    context = PipelineContext(
        pipeline_name=name,
        source_system=pipeline.source_system,
        target_entity=pipeline.target_entity,
        dry_run=dry_run,
    )

    console.print(f"Running pipeline: [bold]{name}[/bold]")
    if dry_run:
        console.print("[yellow]DRY RUN — no data will be loaded[/yellow]")

    result = pipeline.run(context)

    if result.status == "success":
        console.print(f"\n[green]Pipeline completed successfully[/green]")
        console.print(f"Duration: {result.total_duration_seconds:.2f}s")
    else:
        console.print(f"\n[red]Pipeline failed: {result.error_message}[/red]")
        raise typer.Exit(1)

    # Print step results
    if result.step_results:
        step_table = Table(title="Step Results")
        step_table.add_column("Step", style="cyan")
        step_table.add_column("Status")
        step_table.add_column("Duration", justify="right")

        for sr in result.step_results:
            status_style = "green" if not sr.failed else "red"
            step_table.add_row(
                sr.step_name,
                f"[{status_style}]{sr.status}[/{status_style}]",
                f"{sr.duration_seconds or 0:.3f}s",
            )

        console.print(step_table)
