"""CLI commands for seed data loading."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from utilityos.config.settings import get_settings

seed_app = typer.Typer(no_args_is_help=True)
console = Console()


@seed_app.command("load")
def seed_load(
    entity: list[str] | None = typer.Option(
        None, "--entity", "-e", help="Specific entities to seed (repeatable)"
    ),
) -> None:
    """Load seed data through the full bronze → silver → gold pipeline."""
    settings = get_settings()

    try:
        from utilityos.db.engine import create_db_engine
        from utilityos.seed.runner import ENTITY_LOAD_ORDER, SeedRunner

        engine = create_db_engine(settings)
        runner = SeedRunner(engine=engine, source_system="seed")

        entities = entity if entity else None
        console.print("\n[bold]Loading seed data...[/bold]\n")

        report = runner.run(entities=entities)

        # Display results
        table = Table(title="Seed Data Load Results")
        table.add_column("Entity", style="cyan")
        table.add_column("Bronze", justify="right")
        table.add_column("Silver", justify="right")
        table.add_column("Gold", justify="right")
        table.add_column("Status", style="bold")

        for result in report.results:
            status = (
                "[green]OK[/green]"
                if not result.errors
                else f"[red]ERROR: {result.errors[0]}[/red]"
            )
            table.add_row(
                result.entity_name,
                str(result.bronze_rows),
                str(result.silver_rows),
                str(result.gold_rows),
                status,
            )

        console.print(table)
        console.print(f"\n[bold]Totals:[/bold] Bronze={report.total_bronze} "
                      f"Silver={report.total_silver} Gold={report.total_gold}")

        if report.success:
            console.print("\n[green]Seed data loaded successfully![/green]")
        else:
            console.print("\n[red]Some entities had errors. Check above.[/red]")
            raise typer.Exit(1)

        engine.dispose()

    except Exception as e:
        console.print(f"\n[red]Seed load failed: {e}[/red]")
        raise typer.Exit(1)


@seed_app.command("verify")
def seed_verify() -> None:
    """Verify seed data was loaded correctly by checking row counts."""
    settings = get_settings()

    try:
        from sqlalchemy import text as sa_text

        from utilityos.db.engine import create_db_engine
        from utilityos.seed.runner import ENTITY_LOAD_ORDER

        engine = create_db_engine(settings)

        table = Table(title="Seed Data Verification")
        table.add_column("Entity", style="cyan")
        table.add_column("Bronze", justify="right")
        table.add_column("Silver", justify="right")
        table.add_column("Gold", justify="right")

        with engine.connect() as conn:
            for entity_name in ENTITY_LOAD_ORDER:
                bronze_count = _safe_count(conn, f"bronze.seed_{entity_name}")
                silver_count = _safe_count(conn, f"silver.{entity_name}")

                # Check for dim_ or fact_ table
                gold_count = _safe_count(conn, f"gold.dim_{entity_name}")
                if gold_count == 0:
                    gold_count = _safe_count(conn, f"gold.fact_{entity_name}")

                table.add_row(
                    entity_name,
                    str(bronze_count),
                    str(silver_count),
                    str(gold_count),
                )

        console.print(table)
        engine.dispose()

    except Exception as e:
        console.print(f"\n[red]Verification failed: {e}[/red]")
        raise typer.Exit(1)


def _safe_count(conn, table_ref: str) -> int:
    """Count rows in a table, returning 0 if table doesn't exist."""
    from sqlalchemy import text as sa_text

    try:
        result = conn.execute(sa_text(f"SELECT COUNT(*) FROM {table_ref}"))
        return result.scalar() or 0
    except Exception:
        return 0
