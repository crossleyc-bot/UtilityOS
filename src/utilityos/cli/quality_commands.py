"""CLI commands for data quality checks."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

from utilityos.models.loader import (
    discover_entity_files,
    load_all_entities,
    load_common_definitions,
    load_enum_definitions,
)
from utilityos.models.registry import ModelRegistry
from utilityos.quality.engine import QualityEngine
from utilityos.quality.reporter import print_quality_report

quality_app = typer.Typer(no_args_is_help=True)
console = Console()


def _build_registry() -> ModelRegistry:
    """Build a model registry with all definitions loaded."""
    registry = ModelRegistry()
    registry.set_common(load_common_definitions())
    registry.set_enums(load_enum_definitions())
    for entity in load_all_entities():
        registry.register(entity)
    return registry


@quality_app.command("rules")
def list_rules(
    entity: Optional[str] = typer.Option(
        None, help="Entity name (default: all)"
    ),
    layer: str = typer.Option("silver", help="Data layer"),
) -> None:
    """List all quality rules for entities."""
    try:
        registry = _build_registry()
    except Exception as e:
        console.print(f"[red]Error loading models: {e}[/red]")
        raise typer.Exit(1)

    engine = QualityEngine(registry)
    entity_names = [entity] if entity else registry.list_entities()

    for name in entity_names:
        checks = engine.derive_checks_for_entity(name, layer)
        console.print(f"\n[bold]{name}[/bold] ({len(checks)} checks):")
        for check in checks:
            col = check.get("column") or check.get("columns", "")
            console.print(f"  - {check['type']}: {col}")


@quality_app.command("run")
def run_checks(
    entity: Optional[str] = typer.Option(
        None, help="Entity name (default: all)"
    ),
    layer: str = typer.Option("silver", help="Data layer"),
) -> None:
    """Run quality checks (reports derived rules — requires DB for full execution)."""
    try:
        registry = _build_registry()
    except Exception as e:
        console.print(f"[red]Error loading models: {e}[/red]")
        raise typer.Exit(1)

    engine = QualityEngine(registry)
    entity_names = [entity] if entity else registry.list_entities()

    total_checks = 0
    for name in entity_names:
        checks = engine.derive_checks_for_entity(name, layer)
        total_checks += len(checks)

    console.print(
        f"\n[bold]Quality Rules Summary[/bold]\n"
        f"Entities: {len(entity_names)}\n"
        f"Total Checks: {total_checks}\n"
    )
    console.print(
        "[yellow]Note: Full check execution requires a database connection. "
        "Use 'utilityos db init' and 'utilityos ddl apply' first.[/yellow]"
    )


@quality_app.command("report")
def show_report() -> None:
    """Show quality report for recent check runs."""
    console.print(
        "[yellow]No quality check runs found. "
        "Run 'utilityos quality run' first.[/yellow]"
    )
