"""CLI commands for database management."""

from __future__ import annotations

import typer
from rich.console import Console

from utilityos.config.settings import get_settings

db_app = typer.Typer(no_args_is_help=True)
console = Console()


@db_app.command("status")
def db_status() -> None:
    """Show database connection status and schema info."""
    settings = get_settings()
    console.print(f"\n[bold]Database Configuration[/bold]")
    console.print(f"Host:     {settings.db.host}")
    console.print(f"Port:     {settings.db.port}")
    console.print(f"Database: {settings.db.name}")
    console.print(f"User:     {settings.db.user}")
    console.print(f"Schemas:  {settings.db.schema_bronze}, "
                  f"{settings.db.schema_silver}, "
                  f"{settings.db.schema_gold}, "
                  f"{settings.db.schema_meta}")

    try:
        from utilityos.db.engine import create_db_engine
        from utilityos.db.schemas import list_schemas

        engine = create_db_engine(settings)
        existing = list_schemas(engine)
        engine.dispose()

        if existing:
            console.print(f"\n[green]Connected. Existing schemas: {', '.join(existing)}[/green]")
        else:
            console.print(f"\n[yellow]Connected but no UtilityOS schemas found.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Connection failed: {e}[/red]")
        console.print("[dim]Set UTILITYOS_DB_* environment variables to configure.[/dim]")


@db_app.command("init")
def db_init() -> None:
    """Initialize database schemas (bronze, silver, gold, meta)."""
    settings = get_settings()

    try:
        from utilityos.db.engine import create_db_engine
        from utilityos.db.schemas import create_schemas

        engine = create_db_engine(settings)
        created = create_schemas(engine)
        engine.dispose()

        console.print("[green]Database schemas initialized:[/green]")
        for schema in created:
            console.print(f"  [green]+ {schema}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to initialize database: {e}[/red]")
        raise typer.Exit(1)


@db_app.command("reset")
def db_reset(
    confirm: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt"
    ),
) -> None:
    """Drop and recreate all schemas. THIS DESTROYS ALL DATA."""
    if not confirm:
        confirmed = typer.confirm(
            "This will DROP ALL UtilityOS schemas and data. Continue?"
        )
        if not confirmed:
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit()

    settings = get_settings()

    try:
        from utilityos.db.engine import create_db_engine
        from utilityos.db.schemas import create_schemas, drop_schemas

        engine = create_db_engine(settings)
        dropped = drop_schemas(engine)
        console.print("[yellow]Schemas dropped:[/yellow]")
        for schema in dropped:
            console.print(f"  [yellow]- {schema}[/yellow]")

        created = create_schemas(engine)
        console.print("[green]Schemas recreated:[/green]")
        for schema in created:
            console.print(f"  [green]+ {schema}[/green]")

        engine.dispose()
    except Exception as e:
        console.print(f"[red]Failed to reset database: {e}[/red]")
        raise typer.Exit(1)
