"""UtilityOS Data Fabric CLI — top-level application."""

from __future__ import annotations

import typer

from utilityos.cli.db_commands import db_app
from utilityos.cli.ddl_commands import ddl_app
from utilityos.cli.model_commands import model_app
from utilityos.cli.pipeline_commands import pipeline_app
from utilityos.cli.quality_commands import quality_app
from utilityos.cli.seed_commands import seed_app

app = typer.Typer(
    name="utilityos",
    help="UtilityOS Data Fabric — Canonical data backbone for utility operations.",
    no_args_is_help=True,
)

app.add_typer(model_app, name="model", help="Canonical model operations")
app.add_typer(ddl_app, name="ddl", help="DDL generation and management")
app.add_typer(pipeline_app, name="pipeline", help="Pipeline execution")
app.add_typer(quality_app, name="quality", help="Data quality checks")
app.add_typer(db_app, name="db", help="Database management")
app.add_typer(seed_app, name="seed", help="Seed data loading")


@app.callback()
def main() -> None:
    """UtilityOS Data Fabric CLI."""


if __name__ == "__main__":
    app()
