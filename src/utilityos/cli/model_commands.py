"""CLI commands for canonical model operations."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from utilityos.models.loader import (
    discover_entity_files,
    load_all_entities,
    load_common_definitions,
    load_entity_definition,
    load_enum_definitions,
)
from utilityos.models.registry import ModelRegistry
from utilityos.models.relationships import build_relationship_graph, validate_relationships

model_app = typer.Typer(no_args_is_help=True)
console = Console()


@model_app.command("validate")
def validate_models() -> None:
    """Validate all YAML model definitions."""
    try:
        common = load_common_definitions()
        console.print("[green]_common.yaml: valid[/green]")
    except Exception as e:
        console.print(f"[red]_common.yaml: INVALID - {e}[/red]")
        raise typer.Exit(1)

    try:
        enums = load_enum_definitions()
        console.print(
            f"[green]_enums.yaml: valid "
            f"({len(enums.enums)} enum definitions)[/green]"
        )
    except Exception as e:
        console.print(f"[red]_enums.yaml: INVALID - {e}[/red]")
        raise typer.Exit(1)

    entity_names = discover_entity_files()
    errors = []

    for name in entity_names:
        try:
            load_entity_definition(name)
            console.print(f"[green]{name}.yaml: valid[/green]")
        except Exception as e:
            console.print(f"[red]{name}.yaml: INVALID - {e}[/red]")
            errors.append(name)

    if errors:
        console.print(f"\n[red]{len(errors)} invalid definitions[/red]")
        raise typer.Exit(1)

    console.print(
        f"\n[bold green]All {len(entity_names)} entity definitions are valid.[/bold green]"
    )


@model_app.command("list")
def list_models() -> None:
    """List all defined entities with summary info."""
    entity_names = discover_entity_files()

    table = Table(title="Canonical Model Entities")
    table.add_column("Entity", style="cyan")
    table.add_column("Display Name")
    table.add_column("Domain", style="magenta")
    table.add_column("SCD Type", justify="center")
    table.add_column("Attributes", justify="right")
    table.add_column("Version")

    for name in entity_names:
        try:
            defn = load_entity_definition(name)
            table.add_row(
                defn.entity.name,
                defn.entity.display_name,
                defn.entity.domain,
                str(defn.entity.scd_type.value),
                str(len(defn.attributes)),
                defn.entity.version,
            )
        except Exception:
            table.add_row(name, "[red]ERROR[/red]", "", "", "", "")

    console.print(table)


@model_app.command("inspect")
def inspect_model(
    name: str = typer.Argument(help="Entity name to inspect"),
) -> None:
    """Show details of a specific entity definition."""
    try:
        defn = load_entity_definition(name)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]{defn.entity.display_name}[/bold] ({defn.entity.name})")
    console.print(f"Domain: {defn.entity.domain}")
    console.print(f"Version: {defn.entity.version}")
    console.print(f"SCD Type: {defn.entity.scd_type.value}")
    console.print(f"Description: {defn.entity.description}")

    # Keys
    console.print(f"\n[bold]Keys:[/bold]")
    console.print(f"  Surrogate: {defn.keys.surrogate.name} ({defn.keys.surrogate.data_type.value})")
    for bk in defn.keys.business:
        console.print(f"  Business:  {bk.name} ({bk.data_type.value})")

    # Attributes table
    attr_table = Table(title="Attributes")
    attr_table.add_column("Name", style="cyan")
    attr_table.add_column("Type")
    attr_table.add_column("Nullable", justify="center")
    attr_table.add_column("PII", justify="center")
    attr_table.add_column("Enum Ref")

    for attr in defn.attributes:
        type_str = attr.data_type.value
        if attr.length:
            type_str += f"({attr.length})"
        elif attr.precision:
            type_str += f"({attr.precision},{attr.scale or 0})"

        attr_table.add_row(
            attr.name,
            type_str,
            "Y" if attr.nullable else "N",
            attr.pii_classification.value if attr.pii else "",
            attr.enum_ref or "",
        )

    console.print(attr_table)

    # Relationships
    if defn.relationships:
        console.print(f"\n[bold]Relationships:[/bold]")
        for rel in defn.relationships:
            console.print(
                f"  {rel.name}: {rel.type.value} -> {rel.target_entity}"
            )


@model_app.command("graph")
def show_graph() -> None:
    """Show entity relationship graph."""
    try:
        entities = load_all_entities()
    except Exception as e:
        console.print(f"[red]Error loading entities: {e}[/red]")
        raise typer.Exit(1)

    registry = ModelRegistry()
    for entity in entities:
        registry.register(entity)

    graph = build_relationship_graph(registry)

    console.print("\n[bold]Entity Relationship Graph[/bold]\n")

    for entity_name in registry.list_entities():
        rels = graph.get_relationships(entity_name)
        if rels:
            for rel in rels:
                arrow = "-->" if "one_to_many" in rel.relationship_type else "---"
                console.print(
                    f"  {rel.source_entity} {arrow} {rel.target_entity} "
                    f"[dim]({rel.relationship_name}: {rel.relationship_type})[/dim]"
                )

    # Validation
    errors = validate_relationships(registry, graph)
    if errors:
        console.print(f"\n[red]Relationship Errors:[/red]")
        for err in errors:
            console.print(f"  [red]- {err}[/red]")
    else:
        console.print(f"\n[green]All relationships valid.[/green]")
