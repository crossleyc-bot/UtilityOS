"""CLI commands for DDL generation and management."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.syntax import Syntax
from sqlalchemy import MetaData
from sqlalchemy.schema import CreateTable

from utilityos.codegen.ddl_generator import generate_table
from utilityos.codegen.layer_generator import (
    generate_bronze_table,
    generate_gold_dimension_table,
    generate_gold_fact_table,
)
from utilityos.codegen.scd_generator import generate_current_view_sql
from utilityos.models.loader import (
    load_all_entities,
    load_common_definitions,
    load_entity_definition,
)

ddl_app = typer.Typer(no_args_is_help=True)
console = Console()


@ddl_app.command("generate")
def generate_ddl(
    layer: str = typer.Option(
        "silver",
        help="Data layer: bronze, silver, gold, or all",
    ),
    entity: Optional[str] = typer.Option(
        None,
        help="Specific entity name (default: all entities)",
    ),
    output: Optional[str] = typer.Option(
        None,
        help="Output file path (default: stdout)",
    ),
) -> None:
    """Generate DDL SQL for entities."""
    try:
        common = load_common_definitions()
    except Exception as e:
        console.print(f"[red]Error loading common definitions: {e}[/red]")
        raise typer.Exit(1)

    if entity:
        try:
            entities = [load_entity_definition(entity)]
        except Exception as e:
            console.print(f"[red]Error loading entity '{entity}': {e}[/red]")
            raise typer.Exit(1)
    else:
        try:
            entities = load_all_entities()
        except Exception as e:
            console.print(f"[red]Error loading entities: {e}[/red]")
            raise typer.Exit(1)

    layers = ["bronze", "silver", "gold"] if layer == "all" else [layer]
    ddl_statements: list[str] = []

    for current_layer in layers:
        ddl_statements.append(f"-- {'=' * 60}")
        ddl_statements.append(f"-- Layer: {current_layer.upper()}")
        ddl_statements.append(f"-- {'=' * 60}")
        ddl_statements.append(f"CREATE SCHEMA IF NOT EXISTS {current_layer};")
        ddl_statements.append("")

        for entity_def in entities:
            try:
                metadata = MetaData(schema=current_layer)

                if current_layer == "bronze":
                    table = generate_bronze_table(entity_def, metadata)
                elif current_layer == "silver":
                    table = generate_table(entity_def, metadata, common)
                elif current_layer == "gold":
                    dim_table = generate_gold_dimension_table(
                        entity_def, metadata, common
                    )
                    fact_table = generate_gold_fact_table(
                        entity_def, metadata, common
                    )
                    table = dim_table or fact_table
                    if table is None:
                        continue
                else:
                    continue

                ddl = str(CreateTable(table).compile(
                    compile_kwargs={"literal_binds": True}
                ))
                ddl_statements.append(f"-- Entity: {entity_def.entity.name}")
                ddl_statements.append(ddl.strip() + ";")
                ddl_statements.append("")

                # Add current-state view for SCD2 silver tables
                if current_layer == "silver":
                    view_sql = generate_current_view_sql(
                        entity_def, schema=current_layer
                    )
                    if view_sql:
                        ddl_statements.append(view_sql)
                        ddl_statements.append("")

            except Exception as e:
                ddl_statements.append(
                    f"-- ERROR generating DDL for "
                    f"{entity_def.entity.name}: {e}"
                )
                ddl_statements.append("")

    full_ddl = "\n".join(ddl_statements)

    if output:
        with open(output, "w") as f:
            f.write(full_ddl)
        console.print(f"[green]DDL written to {output}[/green]")
    else:
        syntax = Syntax(full_ddl, "sql", theme="monokai")
        console.print(syntax)
